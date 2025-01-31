'''
@Author Eirian Perkins

this file contains logic for validating the spreadsheet format,
i.e. did the user remove fields that are expected?
'''

from agdrvalidator.utils import logger
from agdrvalidator.utils.rich_tabular import SpreadsheetRow, SpreadsheetNode, SpreadsheetProperty, CellLocation
#from agdrvalidator.schema.node.property.gen3property import *
from agdrvalidator.schema.node.property.agdrproperty_2024_09_10 import AGDR as AGDRProperty
from agdrvalidator.schema.node.agdrnode_2024_09_10 import AGDR as AGDRNode
#from agdrvalidator.schema.node.property.gen3property import Gen3 as Gen3Property
#from agdrvalidator.schema.node.gen3node import Gen3 as Gen3Node
from agdrvalidator import * # import AGDR exception types

from alive_progress import alive_bar


logger = logger.setUp(__name__)

class AGDRSpreadsheetValidator(object):
    '''
    This class will accept an entire table of data from a 
    tab in the spreadsheet input (an AGDRNode object) and
    keep a running list of *spreadsheet* validation errors

    spreadsheet validation is limited to checking whether a
    field expected to be in the spreadsheet is missing (removed by user)

    it does not check the validity of the data itself, which is the job 
    of the AGDRValidator class
    '''

    EXPECTED_COLUMNS = {
        "project": ["name", "project_description"],
        "dataset": [
            "dataset_id", "dataset_name", "dataset_description",
            "investigator_affiliation", "investigator_name", "contact", "support_source",
            "data_availability", "agdr_doi", "access_request_form_link",
        ],
        "external_dataset": [
            "dataset_name", "dataset_description", "investigator_affiliation",
            "investigator_name", "contact", "support_source", "submitted_to_insdc",
            "bioproject_accession", "biosample_accession", "dataset_accession", "external_doi", 
        ],
        "contributors": ["name", "institution", "dataset_name"],
        "experiment": ["experiment_name", "dataset_name", "data_description"],
        "genomics_assay": [
            "sample_id", "platform", "instrument_model", "adapter_name", "adapter_sequence",
            "barcoding_applied", "base_caller_name", "base_caller_version", "flow_cell_barcode",
            "includes_spike_ins", "is_paired_end", "library_name",
            "library_preparation_kit_catalog_number", "library_preparation_kit_name",
            "library_preparation_kit_vendor", "library_preparation_kit_version", "library_selection",
            "library_strand", "library_strategy", "read_group_name", "read_length",
            "sequencing_center", "sequencing_date", "size_selection_range", "spike_ins_concentration",
            "spike_ins_fasta", "target_capture_kit", "target_capture_kit_catalog_number",
            "target_capture_kit_name", "target_capture_kit_target_region", "target_capture_kit_vendor",
            "target_capture_kit_version", "to_trim_adapter_sequence", "fragment_maximum_length",
            "fragment_mean_length", "fragment_minimum_length", "fragment_standard_deviation_length",
            "multiplex_barcode"
        ],
        "supplementary_file": [
            "md5sum", "file_size", "file_name", "data_type", "data_format",
            "data_category", "sample_id", "file_name"
        ],
        "raw_read_file": [
            "md5sum", "file_size", "file_name", "data_type", "data_format",
            "data_category", "sample_id", "file_name", "read_pair_number"
        ],
        "processed_file": [
            "md5sum", "file_size", "file_name", "data_type", "data_format",
            "data_category", "sample_id", "file_name", "experimental_strategy"
        ],
        "sample": [
            "sample_id", "genomic_specimen_ID or metagenomic_sample_ID", "secondary_identifier",
            "specimen_voucher", "sample_title", "environmental_medium", "collection_date",
            "collected_by", "geo_loc_name", "habitat", "latitude_decimal_degrees",
            "longitude_decimal_degrees", "coordinate_uncertainty_in_meters", "developmental_stage",
            "tissue", "sample_collect_device", "sample_mat_process", "sample_size_value",
            "sample_size_unit", "store_cond"
        ],
        "genome": [
            "specimen_id", "experiment_name", "specimen_voucher", "secondary_identifier",
            "collection_date", "specimen_scientific_name", "specimen_maori_name",
            "specimen_common_name", "basis_of_record", "geo_loc_name", "environmental_medium",
            "habitat", "latitude_decimal_degrees", "longitude_decimal_degrees",
            "coordinate_uncertainty_in_meters", "** age", "age_unit", "** dev_stage",
            "birth_date", "birth_location", "sex", "collected_by", "biomaterial_provider",
            "breeding_history", "breeding_method", "breed", "cell_line", "culture_collection",
            "death_date", "disease", "genotype", "phenotype", "growth_protocol", "health_state",
            "store_cond", "cultivar", "ecotype", "maximum_elevation_in_meters",
            "minimum_elevation_in_meters", "maximum_depth_in_meters", "minimum_depth_in_meters",
            "specimen_collect_device", "strain"
        ],
        "metagenome": [
            "sample_id", "experiment_name", "secondary_identifier", "basis_of_record",
            "collection_date", "host", "environmental_medium", "habitat", "geo_loc_name",
            "latitude_decimal_degrees", "longitude_decimal_degrees",
            "coordinate_uncertainty_in_meters", "samp_collect_device", "collected_by",
            "store_cond", "biomaterial_provider", "breeding_history", "breeding_method",
            "cell_line", "culture_collection", "maximum_elevation_in_meters",
            "minimum_elevation_in_meters", "maximum_depth_in_meters", "minimum_depth_in_meters"
        ]
    }

    def __init__(self):
        self.validation_errors = []
        self.headers = {}

    def validate(self, nodes):
        """Runs validation for all nodes in the provided dictionary."""
        for node_type, node in nodes.items():
            self._validate_node(node, node_type)

    def _validate_node(self, node, node_type):
        """Generalized validation function for all nodes, including file-based nodes."""
        if not node.data or len(node.data) == 0:
            self.validation_errors.append(f"{node_type.capitalize()} validation failed: No data found in sheet.")
            return

        first_row = node.data
        #print(f"first_row: {first_row}")
        actual_headers = {prop.name for prop in first_row}  # Extract header names
        sheet_name = node.sheet_name  # Get sheet name

        required_columns = self.EXPECTED_COLUMNS.get(node_type, [])
        missing_headers = [col for col in required_columns if col not in actual_headers]
        #print(f"required_columns: {required_columns}")
        #print(f"missing_headers: {missing_headers}")
        #print()

        if missing_headers:
            self.validation_errors.append(
                f"Missing required headers in sheet '{sheet_name}' for {node_type} node: {', '.join(missing_headers)}"
            )

        # Special case: File nodes have additional conditional checks
        if node_type in ["raw_read_file", "processed_file"]:
            data_category_column = "data_category"
            if data_category_column in actual_headers:
                first_row_category = next(
                    (prop.data for prop in first_row.data if prop.name == data_category_column), ""
                ).lower()
                if node_type == "raw_read_file" and first_row_category == "raw read file":
                    if "read_pair_number" not in actual_headers:
                        self.validation_errors.append(
                            f"Missing `read_pair_number` in sheet '{sheet_name}' for raw read files."
                        )
                if node_type == "processed_file" and first_row_category == "processed file":
                    if "experimental_strategy" not in actual_headers:
                        self.validation_errors.append(
                            f"Missing `experimental_strategy` in sheet '{sheet_name}' for processed files."
                        )


    def add(self, nodes):
        """
        "Add" an AGDRNode object to be validated.
        (Data isn't actually added to the object, just validated.)
        """
        ordered_keys = [
            "project", "dataset", "external_dataset", "contributors", "experiment",
            "genomics_assay", "sample", "genome", "metagenome", "supplementary_file",
            "raw_read_file", "processed_file"
        ]

        # as of Python 3.8+, dictionaries maintain insertion order
        # the ordered_keys is just here to make the intent explicit
        # however the implementation in agdrschema_2024_09_10.py will
        # guarantee the order of the nodes

        with alive_bar(len(nodes), title="\tValidating SPREADSHEET  ") as bar:
            for key in ordered_keys:
                if key in nodes:
                    self._validate_node(nodes[key], key)
                    bar()

    #def validate(self):
    #    is_valid = True
    #    reasons = []

    def validate(self, file_path=None):
        """
        Runs validation and outputs results.

        If `file_path` is provided, writes validation errors to the file.
        Otherwise, prints errors to the screen.
        """
        if not self.validation_errors:
            print("✅ Validation passed: No missing headers detected.")
            return True

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(self.validation_errors) + "\n")
                print(f"❌ Validation failed: Errors written to {file_path}")
            except Exception as e:
                print(f"⚠️ Failed to write validation errors to file: {e}")
        else:
            print("❌ Validation failed. The following issues were found:")
            for error in self.validation_errors:
                print(f"  - {error}")

        return False
    

    def add(self, node_name, header):
        self.headers[node_name] = header

    def validate(self, file_path=None):
        ordered_keys = [
            "project", "dataset", "external_dataset", "contributors", "experiment",
            "genomics_assay", "sample", "genome", "metagenome", "supplementary_file",
            "raw_read_file", "processed_file"
        ]

        # as of Python 3.8+, dictionaries maintain insertion order
        # the ordered_keys is just here to make the intent explicit
        # however the implementation in agdrschema_2024_09_10.py will
        # guarantee the order of the nodes

        with alive_bar(len(self.headers), title="\tValidating SPREADSHEET  ") as bar:
            for key in ordered_keys:
                if key in self.headers:
                    self._validate_node(self.headers[key], key)
                    bar()        
            if not self.validation_errors:
                print("✅ Spreadsheet validation passed: No missing headers detected.")
                return True

            if file_path:
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write("\n".join(self.validation_errors) + "\n")
                    print(f"❌ Validation failed: Errors written to {file_path}")
                except Exception as e:
                    print(f"⚠️ Failed to write validation errors to file: {e}")
            else:
                print("❌ Validation failed. The following issues were found:")
                for error in self.validation_errors:
                    print(f"  - {error}")

        return False