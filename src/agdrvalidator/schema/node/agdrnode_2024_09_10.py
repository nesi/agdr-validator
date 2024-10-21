'''
@Author Eirian Perkins

this file contains data container classes used to represent 
metadata from excel workbook input.
'''

from agdrvalidator.utils import logger
from agdrvalidator.utils.rich_tabular import SpreadsheetRow, SpreadsheetNode, SpreadsheetProperty, CellLocation
#from agdrvalidator.schema.node.property.gen3property import *
from agdrvalidator.schema.node.property.agdrproperty_2024_09_10 import AGDR as AGDRProperty
from agdrvalidator.schema.node.property.gen3property import Gen3 as Gen3Property
from agdrvalidator.schema.node.gen3node import Gen3 as Gen3Node
from agdrvalidator import * # import AGDR exception types

from alive_progress import alive_bar


logger = logger.setUp(__name__)

class AGDRRow(SpreadsheetRow):
    '''
    This class represents an entire row of data from a 
    table in the spreadsheet input

    The implementation is the same as the base class, except the 
    properties are AGDRProperty objects instead of SpreadsheetProperty objects, 
    which combine the data from the spreadsheet with the 2024_09_10 AGDR 
    metadata dictionary
    '''
    #@classmethod
    #def convertProperties(cls, properties):
    #    '''
    #    input: list of SpreadsheetProperty objects
    #    output: list of AGDRProperty objects
    @classmethod
    def convertProperties(cls, md_node:list[AGDRProperty], gen3_node: Gen3Node):
        # TODO
        # this isn't doing what I want it to
        # I need to extract the gen3 property and add it to the AGDRProperty object
        #
        # the trouble is, I've created an AGDRProperty manually in another function
        # so, I'm doubling up on the work
        # (and this function doesn't work as intended)

        # this function is basically useless
        # originally was going to map the AGDRProperty to the Gen3Property
        # here, but split it out into encapsulated functions so that 
        # all the logic for each node would be co-located
        def dictifyPropertyName(name):
            '''
            convert the name of the property to the Gen3 name
            '''
            if not name:
                return name

            if name.lower() == "project_description":
                return "detailed_description"
            return name

        dcp = dictifyPropertyName
        logger.debug(f"converting properties for {md_node}")
        logger.debug(f"gen3 node: {gen3_node}")
        properties = []
        logger.debug("______________")
        logger.debug(f"{gen3_node.name}")
        logger.debug("______________")
        for property in md_node:
            g3_property = gen3_node.getProperty(dcp(property.name))
            logger.debug(f"___property name from AGDR: {property.name}")
            logger.debug(f"___specific property: {property} in \n\t\t__ {gen3_node.getProperty(property.name)}")
            properties.append(AGDRProperty(property, g3_property))
        logger.debug()
        logger.debug(f"properties: {properties}")
        return properties

    #    TODO: may need some adjustment
    #    '''
    #    return [AGDRProperty(p.name, p.data, p.location, p.required) for p in properties]

    #def __init__(self, properties: list[SpreadsheetProperty], sheet_name):
    #    self.data = self.convertProperties(properties) # list of SpreadsheetProperty objects
    #    self.sheet_name = sheet_name

    def __init__(self, data: list[AGDRProperty], gen3node: Gen3Node, sheet_name):
        # ??? is the call to convertProperties required?
        # should be handled in populate_node() explicitly
        #self.data = AGDRRow.convertProperties(data, gen3node) # returns list of AGDRProperty objects
        self.data = data
        self.sheet_name = sheet_name    # the sheet where the data was entered
        # don't need this, is in AGDRNode anyway
        #self.table_name = data.name     # what the researcher calls the table
        self.gen3_name = gen3node.name  # what the dictionary calls the table
        self.gen3node = gen3node

    def __getitem__(self, index):
        return self.data[index]

    def __str__(self):
        #return f"{self.data}"
        #return f"AGDRRow(data=[\n\t" + ",\n\t".join(str(prop) for prop in self.data) + "\n])"
        #return f"AGDRRow(data={self.data}"
        #return f"AGDRRow(data={self.data}; gen3node={self.gen3node})"
        return f"AGDRRow(data=[\n\t" + ",\n\t".join(str(prop) for prop in self.data) + f"\n])\n\tALL PROPERTIES: \n\t{self.gen3node}"

    def __repr__(self):
        return self.__str__()

    def getProperty(self, name):
        for prop in self.data:
            if prop.name == name or prop.gen3_name == name:
                return prop
        return None

class AGDR(SpreadsheetNode):
    '''
    This class represents all rows of data for a particular 
    node type, such as Project, Dataset, or File metadata.

    self.name represents the table name
    '''
    # TODO items:
    #
    # split `file` into supplementary_file, raw, and processed_file
    @classmethod
    def convertName(cls, name):
        '''
        helper function to convert the name of the node to the
        Gen3 node name
        '''
        name = name.lower().strip()
        lookup = {
            "instrument": "genomics_assay"
        }
        if name in lookup:
            return lookup[name]
        return name

    def __init__(self, name, data, gen3node:Gen3Node, project="AGDR999999", program="TAONGA", parents={}):
        self.name = name
        self.gen3name = AGDR.convertName(name)
        self.gen3node = gen3node
        self.project_name = project
        self.program_name = program

        # dictionary of node_name: [sample ids] for when it is ambiguous
        # in the spreadsheet which parent this instance of a node belongs to
        # (this was implemented specifically for sample nodes)
        self._potential_parents = parents


        # check that all expected fields 
        # are still present in the metadata
        # (researcher did not delete them)
        self.bad_spreadsheet_validation_errors = []
        # check that all required fields are present
        self.bad_required_validation_errors = []

        #self.data: list[AGDRRow] = self._populate_node(data)
        the_data = self._populate_node(data)
        self.data = self._populate_node(data)

        #print(f"AGDRNode: {self.name}, data={self.data}")
        logger.debug(f"AGDRNode: {self.name}")
        for row in self.data if self.data else []:
            logger.debug(f"\t{row}")

    def __len__(self):
        if not self.data:
            return 0
        return len(self.data)

    def getGen3Node(self):
        return self.gen3node

    def getGen3NodeName(self):
        if self.gen3node:
            return self.gen3node.name
        return self.gen3name

    def uniqueId(self):
        raise "Not currently implemented"
        return self._unique_id

    def getProperty(self, name):
        raise "Not currently implemented"

    def getProperties(self, name):
        properties = []
        for row in self.data:
            prop = row.getProperty(name)
            if prop:
                properties.append(prop)
        return properties


    def __str__(self):
        if not self.data:
            return f"SpreadsheetNode(name={self.name}, data=[])"
        rows_str = "\n\t".join([str(row) for row in self.data])
        return f"SpreadsheetNode(name={self.name}, data=[\n\t{rows_str}\n])"
        #return f"{self.name}:\tdata={self.data})"


    def __repr__(self):
        return self.__str__()


    def _extract_spreadsheet_name(self, data:SpreadsheetNode):
        sheet_name = set()
        for row in data.data:
            sheet_name.add(row.sheet_name)
        if len(sheet_name) > 1:
            # TODO: add to validation errors, something wrong with the data
            #raise AGDRValidationError("Multiple sheets found for Project node")
            raise Exception("spreadsheet parsing error; multiple sheets listed for Project node")
        return sheet_name.pop()

    def _generate_property(self, name, value, g3property:Gen3Property):
        '''
        Generate a property that is not collected in the spreadsheet.
        This is required, e.g. for dbgap_accession_number in the Project node,
        which is required on Gen3, but meaningless for AGDR.

        This way, we can inject the property into the AGDR schema
        '''
        cl = CellLocation(None, None)
        #property = AGDRProperty(name, value, cl, g3property.isRequired(), g3property.get_name(), g3property)
        logger.debug(f"gen3property: {g3property}")
        isRequired = False
        if g3property:
            isRequired = g3property.isRequired()
        property = AGDRProperty(SpreadsheetProperty(name, value, cl, isRequired), g3property)
        return property

    def _populate_node(self, data:SpreadsheetNode):
        '''
        populate the AGDR node (self) with AGDRRow objects
        '''
        def populate_project_node():
            # this appears to be called twice? why?
            # TODO: understand why this is called twice

            #logger.debug(f"looking at gen3node: {self.gen3node.name}")
            prop_name = "dbgap_accession_number"
            #logger.debug(f"getting property: {prop_name} from {self.gen3node}")
            agdr_dbgap = self._generate_property(prop_name, self.project_name, self.gen3node.getProperty(prop_name))
            prop_name = "code"
            #logger.debug(f"getting property: {prop_name} from {self.gen3node}")
            agdr_code = self._generate_property(prop_name, self.project_name, self.gen3node.getProperty(prop_name))

            # there should only be one project node, but iterate anyway
            # TODO: collect validation error if there is more than one project
            nodes = []
            sheet_name = self._extract_spreadsheet_name(data)
            for row in data:
                g3_property = self.gen3node.getProperty("detailed_description")
                property = row.get("project_description")
                agdr_description = AGDRProperty(property, g3_property)
                property = row.get("name")
                agdr_name = AGDRProperty(property, g3_property)
                # need to create a property list
                row_data = [
                    agdr_dbgap, 
                    agdr_code,
                    agdr_description,
                    agdr_name
                    ]
                nodes.append(AGDRRow(row_data, self.gen3node, sheet_name))

            return nodes

        def populate_dataset_node():
            nodes = []
            sheet_name = None
            try:
                sheet_name = self._extract_spreadsheet_name(data)
            except Exception:
                # no data for this entry
                # (ok, it's either dataaset or external_dataset)
                return []

            agdr_projects = self._generate_property("project_id", self.project_name, self.gen3node.getProperty("project_id"))

            agdr_type = self._generate_property("type", self.gen3name, self.gen3node.getProperty("type"))
            for row in data:
                '''
                it would be simpler code if we would iterate over the
                properties and then have some function that maps the 
                spreadsheet property name to the Gen3 property name

                the reason to do it so explicitly is so that 
                we do the mapping between the spreadsheet
                and the Gen3 property names on a per-table basis rather 
                than having a single function that does it for all tables,
                which would be more error-prone, because logic will not be 
                co-located

                (but feel free to adapt it whichever way when you refactor
                or extend this code if you prefer one tradeoff over the other)
                '''

                # properties ordered by order displayed in spreadsheet
                # (not a requirement, a preference)

                # name
                g3prop = self.gen3node.getProperty("name")
                property = row.get("dataset_name")
                agdr_name = AGDRProperty(property, g3prop)

                # date collected
                # TODO: (Ask Claire, not in dictionary)
                # decision: get rid of it
                #g3prop = None #self.gen3node.getProperty("date_collected")
                #property = row.get("date_collected")
                #agdr_date_collected = AGDRProperty(property, g3prop)

                # detailed_description
                g3prop = self.gen3node.getProperty("detailed_description")
                property = row.get("datatset_description")
                agdr_detailed_description = AGDRProperty(property, g3prop)

                # investigator_affiliation
                g3prop = self.gen3node.getProperty("investigator_affiliation")
                property = row.get("investigator_affiliation")
                agdr_investigator_affiliation = AGDRProperty(property, g3prop)

                # investigator_name
                g3prop = self.gen3node.getProperty("investigator_name")
                property = row.get("investigator_name")
                agdr_investigator_name = AGDRProperty(property, g3prop)

                # contact
                g3prop = self.gen3node.getProperty("contact")
                property = row.get("contact") 
                agdr_contact = AGDRProperty(property, g3prop)

                # support_source
                g3prop = self.gen3node.getProperty("support_source")
                property = row.get("support_source")
                agdr_support_source = AGDRProperty(property, g3prop)

                # data_availability
                g3prop = self.gen3node.getProperty("data_availability")
                property = row.get("data_availability")
                agdr_data_availability = AGDRProperty(property, g3prop)

                # publication -- not in dataset node, but in publication node
                # indigenous_governance -- not in dataset node
                #   local_context_hub_project_id
                #   local_context_hub_project_url
                # iwi -- not in dataset node
                #   iwi

                # agdr_doi
                g3prop = self.gen3node.getProperty("agdr_doi")
                property = row.get("agdr_doi")
                agdr_doi = AGDRProperty(property, g3prop)

                # application_form
                g3prop = self.gen3node.getProperty("access_request_form_link")
                property = None #row.get("application_form")
                agdr_application_form = AGDRProperty(property, g3prop)

                # submitter_id -- in red at the end
                g3prop = self.gen3node.getProperty("submitter_id")
                property = row.get("dataset_id")
                agdr_submitter_id = AGDRProperty(property, g3prop)

                # properties ordered by order displayed in the portal
                # (not a requirement, a preference)
                row_data = [
                    agdr_submitter_id,
                    agdr_projects,
                    #agdr_date_collected,
                    agdr_doi,
                    agdr_application_form,
                    agdr_contact,
                    agdr_data_availability,
                    agdr_detailed_description,
                    agdr_investigator_affiliation,
                    agdr_investigator_name,
                    agdr_name,
                    agdr_support_source,
                    agdr_type
                ]
                nodes.append(AGDRRow(row_data, self.gen3node, sheet_name))
            return nodes

        def populate_external_dataset_node():
            nodes = []
            sheet_name = None
            try:
                sheet_name = self._extract_spreadsheet_name(data)
            except Exception:
                # no data for this entry
                # (ok, it's either dataaset or external_dataset)
                return []
            agdr_type = self._generate_property("type", self.gen3name, self.gen3node.getProperty("type"))
            agdr_projects = self._generate_property("projects", self.project_name, self.gen3node.getProperty("projects"))
            for row in data:
                # properties ordered by order displayed in spreadsheet
                # (not a requirement, a preference)

                # submitter_id
                g3prop = self.gen3node.getProperty("submitter_id")
                property = row.get("dataset_name")
                agdr_submitter_id = AGDRProperty(property, g3prop)

                # date collected
                # TODO: (Ask Claire, not in dictionary)
                # decision: get rid of it
                g3prop = None #self.gen3node.getProperty("date_collected")
                property = row.get("date_collected")
                agdr_date_collected = AGDRProperty(property, g3prop)

                # detailed_description
                g3prop = self.gen3node.getProperty("detailed_description")
                property = row.get("datatset_description")
                agdr_detailed_description = AGDRProperty(property, g3prop)

                # investigator_affiliation
                g3prop = self.gen3node.getProperty("investigator_affiliation")
                property = row.get("investigator_affiliation")
                agdr_investigator_affiliation = AGDRProperty(property, g3prop)

                # investigator_name
                g3prop = self.gen3node.getProperty("investigator_name")
                property = row.get("investigator_name")
                agdr_investigator_name = AGDRProperty(property, g3prop)

                # contact
                g3prop = self.gen3node.getProperty("contact")
                property = row.get("contact") 
                agdr_contact = AGDRProperty(property, g3prop)

                # support_source
                g3prop = self.gen3node.getProperty("support_source")
                property = row.get("support_source")
                agdr_support_source = AGDRProperty(property, g3prop)

                # submitted_to_insdc
                g3prop = self.gen3node.getProperty("submitted_to_insdc")
                property = row.get("submitted_to_insdc")
                agdr_submitted_to_insdc = AGDRProperty(property, g3prop)

                # bioproject_accession
                g3prop = self.gen3node.getProperty("bioproject_accession")
                property = row.get("bioproject_accession")
                agdr_bioproject_accession = AGDRProperty(property, g3prop)

                # biosample_accession
                g3prop = self.gen3node.getProperty("biosample_accession")
                property = row.get("biosample_accession")
                agdr_biosample_accession = AGDRProperty(property, g3prop)

                # dataset_accession
                g3prop = self.gen3node.getProperty("dataset_accession")
                property = row.get("dataset_accession")
                agdr_dataset_accession = AGDRProperty(property, g3prop)

                # external_doi
                g3prop = self.gen3node.getProperty("external_doi")
                property = row.get("external_doi")
                agdr_external_doi = AGDRProperty(property, g3prop)

                # name
                # duplicate of submitter_id... TODO: ask Claire
                g3prop = self.gen3node.getProperty("name")
                property = row.get("dataset_name")
                agdr_name = AGDRProperty(property, g3prop)

                # properties ordered by order displayed in the portal
                # (not a requirement, a preference)
                row_data = [
                    agdr_submitter_id,
                    agdr_projects,
                    agdr_bioproject_accession,
                    agdr_biosample_accession,
                    #agdr_date_collected,
                    agdr_contact,
                    agdr_dataset_accession,
                    agdr_detailed_description,
                    agdr_external_doi,
                    agdr_investigator_affiliation,
                    agdr_investigator_name,
                    agdr_name,
                    agdr_submitted_to_insdc,
                    agdr_support_source,
                    agdr_type
                ]
                nodes.append(AGDRRow(row_data, self.gen3node, sheet_name))
            return nodes


        def populate_contributors():
            nodes = []
            sheet_name = self._extract_spreadsheet_name(data)
            agdr_type = self._generate_property("type", self.gen3name, self.gen3node.getProperty("type"))
            count = 0
            for row in data:
                # properties ordered by order displayed in spreadsheet
                # (not a requirement, a preference)

                # name
                g3prop = self.gen3node.getProperty("name")
                property = row.get("name")
                agdr_name = AGDRProperty(property, g3prop)

                # institution
                g3prop = self.gen3node.getProperty("institution")
                property = row.get("institution")
                agdr_institution = AGDRProperty(property, g3prop)

                # dataset_name
                g3prop = self.gen3node.getProperty("dataset") # it is None, because it is not extracted from the dictionary by the parser
                dataset = row.get("dataset_name")
                agdr_dataset = AGDRProperty(dataset, g3prop)
                agdr_dataset.gen3_name = "dataset.submitter_id" # override name

                # TODO: implement function to generate submitter_id for all nodes
                g3prop = self.gen3node.getProperty("submitter_id")
                submitter_id = dataset.data + "_" + "CONTACT_" + str(count)
                property = self._generate_property("submitter_id", submitter_id, g3prop)
                agdr_submitter_id = AGDRProperty(property, g3prop)

                count += 1

                # properties ordered by order displayed in the portal
                # (not a requirement, a preference)
                row_data = [
                    agdr_submitter_id,
                    agdr_dataset,
                    agdr_institution,
                    agdr_name,
                    agdr_type
                ]
                nodes.append(AGDRRow(row_data, self.gen3node, sheet_name))
            return nodes

        def populate_experiment():
            nodes = []
            sheet_name = self._extract_spreadsheet_name(data)
            agdr_type = self._generate_property("type", self.gen3name, self.gen3node.getProperty("type"))
            for row in data:
                # properties ordered by order displayed in spreadsheet
                # (not a requirement, a preference)

                # submitter_id
                g3prop = self.gen3node.getProperty("submitter_id")
                property = row.get("experiment_name")
                agdr_submitter_id = AGDRProperty(property, g3prop)

                # dataset_name
                # not able to find dataset? Need to instantiate a Gen3Property object
                # create a dataset.submitter_id property
                g3prop = self.gen3node.getProperty("dataset") 
                property = row.get("dataset_name")
                agdr_dataset = AGDRProperty(property, g3prop)
                agdr_dataset.gen3_name = "dataset.submitter_id" # override name

                # data_description
                g3prop = self.gen3node.getProperty("data_description")
                property = row.get("data_description")
                agdr_data_description = AGDRProperty(property, g3prop)

                row_data = [
                    agdr_submitter_id,
                    agdr_dataset,
                    agdr_data_description,
                    agdr_type
                ]
                nodes.append(AGDRRow(row_data, self.gen3node, sheet_name))
            return nodes

        def populate_genome():
            nodes = []
            sheet_name = None
            try:
                sheet_name = self._extract_spreadsheet_name(data)
            except Exception:
                # no data for this entry
                # (ok, it's either genome or metagenome)
                return []
            agdr_type = self._generate_property("type", self.gen3name, self.gen3node.getProperty("type"))
            for row in data:
                # properties ordered by order displayed in spreadsheet
                # (not a requirement, a preference)

                # specimen_id
                g3prop = self.gen3node.getProperty("submitter_id")
                property = row.get("specimen_id")
                agdr_submitter_id = AGDRProperty(property, g3prop)

                # experiment_name
                g3prop = self.gen3node.getProperty("experiment") # experiment.submitter_id, will be None
                property = row.get("experiment_name")
                agdr_experiment = AGDRProperty(property, g3prop)
                agdr_experiment.gen3_name = "experiment.submitter_id" # override name

                # specimen_voucher
                g3prop = self.gen3node.getProperty("specimen_voucher")
                property = row.get("specimen_voucher")
                agdr_specimen_voucher = AGDRProperty(property, g3prop)

                # secondary_identifier
                g3prop = self.gen3node.getProperty("secondary_identifier")
                property = row.get("secondary_identifier")
                agdr_secondary_identifier = AGDRProperty(property, g3prop)

                # collection_date
                g3prop = self.gen3node.getProperty("collection_date")
                property = row.get("collection_date")
                agdr_collection_date = AGDRProperty(property, g3prop)

                # specimen_scientific_name
                g3prop = self.gen3node.getProperty("specimen_scientific_name")
                property = row.get("specimen_scientific_name")
                agdr_specimen_scientific_name = AGDRProperty(property, g3prop)

                # specimen_maori_name
                g3prop = self.gen3node.getProperty("specimen_maori_name")
                property = row.get("specimen_maori_name")
                agdr_specimen_maori_name = AGDRProperty(property, g3prop)

                # specimen_common_name
                g3prop = self.gen3node.getProperty("specimen_common_name")
                property = row.get("specimen_common_name")
                agdr_specimen_common_name = AGDRProperty(property, g3prop)

                # basis_of_record
                g3prop = self.gen3node.getProperty("basis_of_record")
                property = row.get("basis_of_record")
                agdr_basis_of_record = AGDRProperty(property, g3prop)

                # geo_loc_name
                g3prop = self.gen3node.getProperty("geo_loc_name")
                property = row.get("geo_loc_name")
                agdr_geo_loc_name = AGDRProperty(property, g3prop)

                # environmental_medium
                g3prop = self.gen3node.getProperty("environmental_medium")
                property = row.get("environmental_medium")
                agdr_environmental_medium = AGDRProperty(property, g3prop)

                # habitat
                g3prop = self.gen3node.getProperty("habitat")
                property = row.get("habitat")
                agdr_habitat = AGDRProperty(property, g3prop)

                # latitude_decimal_degrees
                g3prop = self.gen3node.getProperty("latitude_decimal_degrees")
                property = row.get("latitude_decimal_degrees")
                agdr_latitude_decimal_degrees = AGDRProperty(property, g3prop)

                # longitude_decimal_degrees
                g3prop = self.gen3node.getProperty("longitude_decimal_degrees")
                property = row.get("longitude_decimal_degrees")
                agdr_longitude_decimal_degrees = AGDRProperty(property, g3prop)

                # coordinate_uncertainty_in_meters
                g3prop = self.gen3node.getProperty("coordinate_uncertainty_in_meters")
                property = row.get("coordinate_uncertainty_in_meters")
                agdr_coordinate_uncertainty_in_meters = AGDRProperty(property, g3prop)

                # ** age     # weird that there's **'s
                # TODO: check that one or the other is filled, don't need both
                g3prop = self.gen3node.getProperty("age")
                property = row.get("** age")
                agdr_age = AGDRProperty(property, g3prop)

                # ** dev_stage
                g3prop = self.gen3node.getProperty("developmental_stage")
                property = row.get("** dev_stage")
                agdr_developmental_stage = AGDRProperty(property, g3prop)

                # birth_date
                g3prop = self.gen3node.getProperty("birth_date")
                property = row.get("birth_date")
                agdr_birth_date = AGDRProperty(property, g3prop)
                # due to limitation in the parser, gen3 properties with 
                # $ref are not currently extracted
                agdr_birth_date.gen3_name = "birth_date"

                # birth_location
                g3prop = self.gen3node.getProperty("birth_location")
                property = row.get("birth_location")
                agdr_birth_location = AGDRProperty(property, g3prop)

                # sex
                g3prop = self.gen3node.getProperty("sex")
                property = row.get("sex")
                agdr_sex = AGDRProperty(property, g3prop)

                # collected_by
                g3prop = self.gen3node.getProperty("collected_by")
                property = row.get("collected_by")
                agdr_collected_by = AGDRProperty(property, g3prop)

                # biomaterial_provider
                g3prop = self.gen3node.getProperty("biomaterial_provider")
                property = row.get("biomaterial_provider")
                agdr_biomaterial_provider = AGDRProperty(property, g3prop)

                # breeding_history
                g3prop = self.gen3node.getProperty("breeding_history")
                property = row.get("breeding_history")
                agdr_breeding_history = AGDRProperty(property, g3prop)

                # breeding_method
                g3prop = self.gen3node.getProperty("breeding_method")
                property = row.get("breeding_method")
                agdr_breeding_method = AGDRProperty(property, g3prop)

                # breed
                g3prop = self.gen3node.getProperty("breed")
                property = row.get("breed")
                agdr_breed = AGDRProperty(property, g3prop)

                # cell_line
                g3prop = self.gen3node.getProperty("cell_line")
                property = row.get("cell_line")
                agdr_cell_line = AGDRProperty(property, g3prop)

                # culture_collection
                g3prop = self.gen3node.getProperty("culture_collection")
                property = row.get("culture_collection")
                agdr_culture_collection = AGDRProperty(property, g3prop)

                # death_date
                g3prop = self.gen3node.getProperty("death_date")
                property = row.get("death_date")
                agdr_death_date = AGDRProperty(property, g3prop)
                agdr_death_date.gen3_name = "death_date" # issue with lookup

                # disease
                g3prop = self.gen3node.getProperty("disease")
                property = row.get("disease")
                agdr_disease = AGDRProperty(property, g3prop)

                # disease_stage
                # TODO -- ask Claire to remove from template, it is not in dictionary
                # decision: remove
                #g3prop = self.gen3node.getProperty("disease_stage")
                #property = row.get("disease_stage")
                #agdr_disease_stage = AGDRProperty(property, g3prop)

                # genotype
                g3prop = self.gen3node.getProperty("genotype")
                property = row.get("genotype")
                agdr_genotype = AGDRProperty(property, g3prop)

                # phenotype
                g3prop = self.gen3node.getProperty("phenotype")
                property = row.get("phenotype")
                agdr_phenotype = AGDRProperty(property, g3prop)

                # growth_protocol
                g3prop = self.gen3node.getProperty("growth_protocol")
                property = row.get("growth_protocol")
                agdr_growth_protocol = AGDRProperty(property, g3prop)

                # health_state
                g3prop = self.gen3node.getProperty("health_state")
                property = row.get("health_state")
                agdr_health_state = AGDRProperty(property, g3prop)

                # store_cond
                g3prop = self.gen3node.getProperty("store_cond")
                property = row.get("store_cond")
                agdr_store_cond = AGDRProperty(property, g3prop)

                # cultivar
                g3prop = self.gen3node.getProperty("cultivar")
                property = row.get("cultivar")
                agdr_cultivar = AGDRProperty(property, g3prop)

                # ecotype
                g3prop = self.gen3node.getProperty("ecotype")
                property = row.get("ecotype")
                agdr_ecotype = AGDRProperty(property, g3prop)

                # maximum_elevation_in_meters
                g3prop = self.gen3node.getProperty("maximum_elevation_in_meters")
                property = row.get("maximum_elevation_in_meters")
                agdr_maximum_elevation_in_meters = AGDRProperty(property, g3prop)

                # minimum_elevation_in_meters
                g3prop = self.gen3node.getProperty("minimum_elevation_in_meters")
                property = row.get("minimum_elevation_in_meters")
                agdr_minimum_elevation_in_meters = AGDRProperty(property, g3prop)

                # maximum_depth_in_meters
                g3prop = self.gen3node.getProperty("maximum_depth_in_meters")
                property = row.get("maximum_depth_in_meters")
                agdr_maximum_depth_in_meters = AGDRProperty(property, g3prop)

                # minimum_depth_in_meters
                g3prop = self.gen3node.getProperty("minimum_depth_in_meters")
                property = row.get("minimum_depth_in_meters")
                agdr_minimum_depth_in_meters = AGDRProperty(property, g3prop)

                # specimen_collect_device
                g3prop = self.gen3node.getProperty("specimen_collect_device")
                property = row.get("specimen_collect_device")
                agdr_specimen_collect_device = AGDRProperty(property, g3prop)

                # strain
                g3prop = self.gen3node.getProperty("strain")
                property = row.get("strain")
                agdr_strain = AGDRProperty(property, g3prop)

                row_data = [
                    agdr_submitter_id,
                    agdr_geo_loc_name,
                    agdr_experiment,
                    agdr_age,
                    agdr_basis_of_record,
                    agdr_biomaterial_provider,
                    agdr_birth_date,
                    agdr_birth_location,
                    agdr_breed,
                    agdr_breeding_history,
                    agdr_breeding_method,
                    agdr_cell_line,
                    agdr_collected_by,
                    agdr_collection_date,
                    agdr_coordinate_uncertainty_in_meters,
                    agdr_cultivar,
                    agdr_culture_collection,
                    agdr_death_date,
                    agdr_developmental_stage,
                    agdr_disease,
                    agdr_ecotype,
                    agdr_environmental_medium,
                    agdr_genotype,
                    agdr_growth_protocol,
                    agdr_habitat,
                    agdr_health_state,
                    agdr_latitude_decimal_degrees,
                    agdr_longitude_decimal_degrees,
                    agdr_maximum_depth_in_meters,
                    agdr_maximum_elevation_in_meters,
                    agdr_minimum_depth_in_meters,
                    agdr_minimum_elevation_in_meters,
                    agdr_phenotype,
                    agdr_secondary_identifier,
                    agdr_sex,
                    #agdr_source_material_id, # not in template, should it be?
                    agdr_specimen_collect_device,
                    agdr_specimen_common_name,
                    agdr_specimen_maori_name,
                    agdr_specimen_scientific_name,
                    agdr_specimen_voucher,
                    agdr_store_cond,
                    agdr_strain,
                    agdr_type
                ]
                nodes.append(AGDRRow(row_data, self.gen3node, sheet_name))
            return nodes

        def populate_metagenome():
            nodes = []
            try:
                sheet_name = self._extract_spreadsheet_name(data)
            except Exception:
                # no data for this entry
                # (ok, it's either genome or metagenome)
                return []
            agdr_type = self._generate_property("type", self.gen3name, self.gen3node.getProperty("type"))
            for row in data:
                # properties ordered by order displayed in spreadsheet
                # (not a requirement, a preference)

                # TODO: tell Claire, should really be specimen_id?
                # decision: will have a think about it
                # sample_id 
                g3prop = self.gen3node.getProperty("submitter_id")
                property = row.get("sample_id")
                agdr_submitter_id = AGDRProperty(property, g3prop)

                # experiment_name
                g3prop = self.gen3node.getProperty("experiment") # experiment.submitter_id
                property = row.get("experiment_name")
                agdr_experiment = AGDRProperty(property, g3prop)
                agdr_experiment.gen3_name = "experiment.submitter_id" # override name

                # secondary_identifier
                g3prop = self.gen3node.getProperty("secondary_identifier")
                property = row.get("secondary_identifier")
                agdr_secondary_identifier = AGDRProperty(property, g3prop)

                # basis_of_record
                g3prop = self.gen3node.getProperty("basis_of_record")
                property = row.get("basis_of_record")
                agdr_basis_of_record = AGDRProperty(property, g3prop)

                # collection_date
                g3prop = self.gen3node.getProperty("collection_date")
                property = row.get("collection_date")
                agdr_collection_date = AGDRProperty(property, g3prop)

                # host
                g3prop = self.gen3node.getProperty("host")
                property = row.get("host")
                agdr_host = AGDRProperty(property, g3prop)

                # environmental_medium
                g3prop = self.gen3node.getProperty("environmental_medium")
                property = row.get("environmental_medium")
                agdr_environmental_medium = AGDRProperty(property, g3prop)

                # habitat
                g3prop = self.gen3node.getProperty("habitat")
                property = row.get("habitat")
                agdr_habitat = AGDRProperty(property, g3prop)

                '''
                # TODO: thought: want to add some wrapper around 
                # SpreadsheetRow.get() that will populate some 
                # validation error if the field is missing
                #
                # maybe that's something for the AGDRRow object
                # to do, it can check if any fields are missing
                # and report the node type and spreadsheet name
                '''

                # geo_loc_name
                g3prop = self.gen3node.getProperty("geo_loc_name")
                property = row.get("geo_loc_name")
                agdr_geo_loc_name = AGDRProperty(property, g3prop)

                # latitude_decimal_degrees
                g3prop = self.gen3node.getProperty("latitude_decimal_degrees")
                property = row.get("latitude_decimal_degrees")
                agdr_latitude_decimal_degrees = AGDRProperty(property, g3prop)

                # longitude_decimal_degrees
                g3prop = self.gen3node.getProperty("longitude_decimal_degrees")
                property = row.get("longitude_decimal_degrees")
                agdr_longitude_decimal_degrees = AGDRProperty(property, g3prop)

                # coordinate_uncertainty_in_meters
                g3prop = self.gen3node.getProperty("coordinate_uncertainty_in_meters")
                property = row.get("coordinate_uncertainty_in_meters")
                agdr_coordinate_uncertainty_in_meters = AGDRProperty(property, g3prop)

                # samp_collect_device
                # TODO: should be named specimen_collect_device?
                g3prop = self.gen3node.getProperty("specimen_collect_device")
                property = row.get("samp_collect_device")
                agdr_specimen_collect_device = AGDRProperty(property, g3prop)

                # collected_by
                g3prop = self.gen3node.getProperty("collected_by")
                property = row.get("collected_by")
                agdr_collected_by = AGDRProperty(property, g3prop)

                # store_cond 
                g3prop = self.gen3node.getProperty("store_cond")
                property = row.get("store_cond")
                agdr_store_cond = AGDRProperty(property, g3prop)

                # biomaterial_provider
                g3prop = self.gen3node.getProperty("biomaterial_provider")
                property = row.get("biomaterial_provider")
                agdr_biomaterial_provider = AGDRProperty(property, g3prop)

                # breeding_history
                g3prop = self.gen3node.getProperty("breeding_history")
                property = row.get("breeding_history")
                agdr_breeding_history = AGDRProperty(property, g3prop)

                # breeding_method
                g3prop = self.gen3node.getProperty("breeding_method")
                property = row.get("breeding_method")
                agdr_breeding_method = AGDRProperty(property, g3prop)

                # cell_line
                g3prop = self.gen3node.getProperty("cell_line")
                property = row.get("cell_line")
                agdr_cell_line = AGDRProperty(property, g3prop)

                # culture_collection
                g3prop = self.gen3node.getProperty("culture_collection")
                property = row.get("culture_collection")
                agdr_culture_collection = AGDRProperty(property, g3prop)

                # maximum_elevation_in_meters
                g3prop = self.gen3node.getProperty("maximum_elevation_in_meters")
                property = row.get("maximum_elevation_in_meters")
                agdr_maximum_elevation_in_meters = AGDRProperty(property, g3prop)

                # minimum_elevation_in_meters
                g3prop = self.gen3node.getProperty("minimum_elevation_in_meters")
                property = row.get("minimum_elevation_in_meters")
                agdr_minimum_elevation_in_meters = AGDRProperty(property, g3prop)

                # maximum_depth_in_meters
                g3prop = self.gen3node.getProperty("maximum_depth_in_meters")
                property = row.get("maximum_depth_in_meters")
                agdr_maximum_depth_in_meters = AGDRProperty(property, g3prop)

                # minimum_depth_in_meters
                g3prop = self.gen3node.getProperty("minimum_depth_in_meters")
                property = row.get("minimum_depth_in_meters")
                agdr_minimum_depth_in_meters = AGDRProperty(property, g3prop)

                row_data = [
                    agdr_submitter_id,
                    agdr_habitat,
                    agdr_geo_loc_name,
                    agdr_experiment,
                    agdr_environmental_medium,
                    agdr_basis_of_record,
                    agdr_biomaterial_provider,
                    agdr_breeding_history,
                    agdr_breeding_method,
                    agdr_cell_line,
                    agdr_collected_by,
                    agdr_collection_date,
                    agdr_coordinate_uncertainty_in_meters,
                    agdr_culture_collection,
                    agdr_host,
                    agdr_latitude_decimal_degrees,
                    agdr_longitude_decimal_degrees,
                    agdr_maximum_depth_in_meters,
                    agdr_maximum_elevation_in_meters,
                    agdr_minimum_depth_in_meters,
                    agdr_minimum_elevation_in_meters,
                    agdr_secondary_identifier,
                    #agdr_source_material_id,      # not in template, should it be?
                    agdr_specimen_collect_device,
                    agdr_store_cond,
                    agdr_type
                ]
                nodes.append(AGDRRow(row_data, self.gen3node, sheet_name))
            return nodes

        def populate_sample():
            nodes = []
            sheet_name = self._extract_spreadsheet_name(data)
            agdr_type = self._generate_property("type", self.gen3name, self.gen3node.getProperty("type"))
            for row in data:
                # sample_id
                g3prop = self.gen3node.getProperty("submitter_id")
                property = row.get("sample_id")
                agdr_submitter_id = AGDRProperty(property, g3prop)

                # genome or metagenome ID that this sample is
                # TODO TODO TODO TODO TODO
                # cannot actually determine from AgdrNode object which
                # the parent is, it must be figured out from the schema level
                # so, I guess, return some meta object to be post-processed
                property = row.get("genomic_specimen_ID or metagenomic_sample_ID")

                #agdr_genomes = AGDRProperty(property, g3prop)
                parent_id = property.data
                property_name = None
                if "genome" in self._potential_parents and self._potential_parents["genome"]:
                    if parent_id in self._potential_parents["genome"]:
                        property_name = "genome.submitter_id"
                elif "metagenome" in self._potential_parents and self._potential_parents["metagenome"]:
                    if parent_id in self._potential_parents["metagenome"]:
                        property_name = "metagenome.submitter_id"
                if not property_name:
                    # assume whichever one was populated
                    # there will be a validation error
                    if "genome" in self._potential_parents and self._potential_parents["genome"]:
                        property_name = "genome.submitter_id"
                    elif "metagenome" in self._potential_parents and self._potential_parents["metagenome"]:
                        property_name = "metagenome.submitter_id"
                g3prop = self.gen3node.getProperty(property_name) # expect this property to be None though
                agdr_parent = AGDRProperty(property, g3prop)
                agdr_parent.gen3_name = property_name

                # secondary_identifier
                g3prop = self.gen3node.getProperty("secondary_identifier")
                property = row.get("secondary_identifier")
                agdr_secondary_identifier = AGDRProperty(property, g3prop)

                # specimen_voucher
                g3prop = self.gen3node.getProperty("specimen_voucher")
                property = row.get("specimen_voucher")
                agdr_specimen_voucher = AGDRProperty(property, g3prop)

                # sample_title
                g3prop = self.gen3node.getProperty("sample_title")
                property = row.get("sample_title")
                agdr_sample_title = AGDRProperty(property, g3prop)

                # environmental_medium
                g3prop = self.gen3node.getProperty("environmental_medium")
                property = row.get("environmental_medium")
                agdr_environmental_medium = AGDRProperty(property, g3prop)

                # collection_date
                g3prop = self.gen3node.getProperty("collection_date")
                property = row.get("collection_date")
                agdr_collection_date = AGDRProperty(property, g3prop)

                # collected_by
                g3prop = self.gen3node.getProperty("collected_by")
                property = row.get("collected_by")
                agdr_collected_by = AGDRProperty(property, g3prop)

                # geo_loc_name
                g3prop = self.gen3node.getProperty("geo_loc_name")
                property = row.get("geo_loc_name")
                agdr_geo_loc_name = AGDRProperty(property, g3prop)

                # habitat
                g3prop = self.gen3node.getProperty("habitat")
                property = row.get("habitat")
                agdr_habitat = AGDRProperty(property, g3prop)

                # latitude_decimal_degrees
                g3prop = self.gen3node.getProperty("latitude_decimal_degrees")
                property = row.get("latitude_decimal_degrees")
                agdr_latitude_decimal_degrees = AGDRProperty(property, g3prop)

                # longitude_decimal_degrees
                g3prop = self.gen3node.getProperty("longitude_decimal_degrees")
                property = row.get("longitude_decimal_degrees")
                agdr_longitude_decimal_degrees = AGDRProperty(property, g3prop)

                # coordinate_uncertainty_in_meters
                g3prop = self.gen3node.getProperty("coordinate_uncertainty_in_meters")
                property = row.get("coordinate_uncertainty_in_meters")
                agdr_coordinate_uncertainty_in_meters = AGDRProperty(property, g3prop)

                # developmental_stage
                g3prop = self.gen3node.getProperty("developmental_stage")
                property = row.get("developmental_stage")
                agdr_developmental_stage = AGDRProperty(property, g3prop)

                # tissue
                g3prop = self.gen3node.getProperty("tissue")
                property = row.get("tissue")
                agdr_tissue = AGDRProperty(property, g3prop)

                # sample_collect_device
                g3prop = self.gen3node.getProperty("sample_collect_device")
                property = row.get("sample_collect_device")
                agdr_sample_collect_device = AGDRProperty(property, g3prop)

                # sample_mat_process
                g3prop = self.gen3node.getProperty("sample_mat_process")
                property = row.get("sample_mat_process")
                agdr_sample_mat_process = AGDRProperty(property, g3prop)

                # sample_size_value
                g3prop = self.gen3node.getProperty("sample_size_value")
                property = row.get("sample_size_value")
                agdr_sample_size_value = AGDRProperty(property, g3prop)

                # sample_size_unit
                g3prop = self.gen3node.getProperty("sample_size_unit")
                property = row.get("sample_size_unit")
                agdr_sample_size_unit = AGDRProperty(property, g3prop)

                # store_cond
                g3prop = self.gen3node.getProperty("store_cond")
                property = row.get("store_cond")
                agdr_store_cond = AGDRProperty(property, g3prop)

                row_data = [
                    agdr_submitter_id,
                    #agdr_biomaterial_provider, # not in template
                    agdr_collected_by,
                    agdr_collection_date,
                    agdr_coordinate_uncertainty_in_meters,
                    agdr_developmental_stage,
                    agdr_environmental_medium,
                    #agdr_genomes, # cannot be determined here
                    agdr_geo_loc_name,
                    agdr_habitat,
                    #agdr_host, # not in template
                    agdr_latitude_decimal_degrees,
                    agdr_longitude_decimal_degrees,
                    #agdr_metagenomes, # cannot be determined here
                    agdr_sample_collect_device,
                    agdr_sample_mat_process,
                    agdr_sample_size_unit,
                    agdr_sample_size_value,
                    agdr_sample_title,
                    agdr_secondary_identifier,
                    #agdr_source_material_id, # not in template
                    #agdr_specimen_collect_device, # not in template
                    agdr_specimen_voucher,
                    agdr_store_cond,
                    agdr_tissue,
                    agdr_parent, # either genome or metagenome submitter_id
                    agdr_type
                ]
                nodes.append(AGDRRow(row_data, self.gen3node, sheet_name))
            return nodes

        def populate_publication():
            # need to determine whether this comes from dataset or external_datasetmm
            nodes = []
            sheet_name = None
            try:
                sheet_name = self._extract_spreadsheet_name(data)
            except Exception:
                # no data for this entry, no worries
                return []

            agdr_type = self._generate_property("type", self.gen3name, self.gen3node.getProperty("type"))
            is_external_dataset = False
            for row in data:
                # look for entry that's only in external_dataset
                if row.get("external_doi") is not None:
                    is_external_dataset = True
                break

            count = 0
            for row in data:
                # doi
                g3prop = self.gen3node.getProperty("doi")
                property = row.get("publication")
                agdr_doi = AGDRProperty(property, g3prop)

                # dataset_name
                g3prop = None
                # TODO: create real g3prop object
                parent = ""
                if is_external_dataset:
                    parent = "external_dataset.submitter_id"
                    #g3prop = self.gen3node.getProperty("external_dataset.submitter_id")
                else:
                    #g3prop = self.gen3node.getProperty("dataset.submitter_id")
                    parent = "dataset.submitter_id"
                g3prop = self.gen3node.getProperty(parent)
                dataset = row.get("dataset_name")
                agdr_dataset = AGDRProperty(dataset, g3prop)
                agdr_dataset.gen3_name = parent # override name

                # submitter_id
                g3prop = self.gen3node.getProperty("submitter_id")
                property = row.get("dataset_name")
                submitter_id = dataset.data + "_" + "PUBLICATION_" + str(count)
                property = self._generate_property("submitter_id", submitter_id, g3prop)
                agdr_submitter_id = AGDRProperty(property, g3prop)
                count += 1

                row_data = [
                    agdr_doi,
                    #agdr_citation_string # not in template
                    agdr_dataset,
                    agdr_submitter_id,
                    agdr_type
                ]
                nodes.append(AGDRRow(row_data, self.gen3node, sheet_name))
            return nodes

        def populate_indigenous_governance():
            pass

        def populate_iwi():
            pass

        def populate_genomics_assay():
            nodes = []
            sheet_name = None
            try:
                sheet_name = self._extract_spreadsheet_name(data)
            except Exception:
                # no file or instrument data
                return []

            agdr_type = self._generate_property("type", self.gen3name, self.gen3node.getProperty("type"))
            count = 0
            for row in data:
                # sample_id
                g3prop = self.gen3node.getProperty("submitter_id")
                property = row.get("sample_id")
                submitter_id = property.data + "_" + "GENOMICS_ASSAY_" + str(count)
                property = self._generate_property("submitter_id", submitter_id, g3prop)
                agdr_submitter_id = AGDRProperty(property, g3prop)

                # sample
                # TODO: generate a real Gen3Property object for sample.submitter_id
                g3prop = self.gen3node.getProperty("sample.submitter_id")
                property = row.get("sample_id")
                agdr_sample = AGDRProperty(property, g3prop)
                agdr_sample.gen3_name = "sample.submitter_id" # override name

                # platform
                g3prop = self.gen3node.getProperty("platform")
                property = row.get("platform")
                agdr_platform = AGDRProperty(property, g3prop)

                # instrument_model
                g3prop = self.gen3node.getProperty("instrument_model")
                property = row.get("instrument_model")
                agdr_instrument_model = AGDRProperty(property, g3prop)

                # adapter_name
                g3prop = self.gen3node.getProperty("adapter_name")
                property = row.get("adapter_name")
                agdr_adapter_name = AGDRProperty(property, g3prop)

                # adapter_sequence
                g3prop = self.gen3node.getProperty("adapter_sequence")
                property = row.get("adapter_sequence")
                agdr_adapter_sequence = AGDRProperty(property, g3prop)

                # barcoding_applied
                g3prop = self.gen3node.getProperty("barcoding_applied")
                property = row.get("barcoding_applied")
                agdr_barcoding_applied = AGDRProperty(property, g3prop)

                # base_caller_name
                g3prop = self.gen3node.getProperty("base_caller_name")
                property = row.get("base_caller_name")
                agdr_base_caller_name = AGDRProperty(property, g3prop)

                # base_caller_version
                g3prop = self.gen3node.getProperty("base_caller_version")
                property = row.get("base_caller_version")
                agdr_base_caller_version = AGDRProperty(property, g3prop)

                # flow_cell_barcode
                g3prop = self.gen3node.getProperty("flow_cell_barcode")
                property = row.get("flow_cell_barcode")
                agdr_flow_cell_barcode = AGDRProperty(property, g3prop)
                
                # includes_spike_ins
                g3prop = self.gen3node.getProperty("includes_spike_ins")
                property = row.get("includes_spike_ins")
                agdr_includes_spike_ins = AGDRProperty(property, g3prop)

                # is_paired_end
                g3prop = self.gen3node.getProperty("is_paired_end")
                property = row.get("is_paired_end")
                agdr_is_paired_end = AGDRProperty(property, g3prop)

                # library_name
                g3prop = self.gen3node.getProperty("library_name")
                property = row.get("library_name")
                agdr_library_name = AGDRProperty(property, g3prop)

                # library_preparation_kit_catalog_number
                g3prop = self.gen3node.getProperty("library_preparation_kit_catalog_number")
                property = row.get("library_preparation_kit_catalog_number")
                agdr_library_preparation_kit_catalog_number = AGDRProperty(property, g3prop)

                # library_preparation_kit_name
                g3prop = self.gen3node.getProperty("library_preparation_kit_name")
                property = row.get("library_preparation_kit_name")
                agdr_library_preparation_kit_name = AGDRProperty(property, g3prop)

                # library_preparation_kit_vendor
                g3prop = self.gen3node.getProperty("library_preparation_kit_vendor")
                property = row.get("library_preparation_kit_vendor")
                agdr_library_preparation_kit_vendor = AGDRProperty(property, g3prop)

                # library_preparation_kit_version
                g3prop = self.gen3node.getProperty("library_preparation_kit_version")
                property = row.get("library_preparation_kit_version")
                agdr_library_preparation_kit_version = AGDRProperty(property, g3prop)

                # library_selection
                g3prop = self.gen3node.getProperty("library_selection")
                property = row.get("library_selection")
                agdr_library_selection = AGDRProperty(property, g3prop)

                # library_strand
                g3prop = self.gen3node.getProperty("library_strand")
                property = row.get("library_strand")
                agdr_library_strand = AGDRProperty(property, g3prop)

                # library_strategy
                g3prop = self.gen3node.getProperty("library_strategy")
                property = row.get("library_strategy")
                agdr_library_strategy = AGDRProperty(property, g3prop)

                # read_group_name
                g3prop = self.gen3node.getProperty("read_group_name")
                property = row.get("read_group_name")
                agdr_read_group_name = AGDRProperty(property, g3prop)

                # read_length
                g3prop = self.gen3node.getProperty("read_length")
                property = row.get("read_length")
                agdr_read_length = AGDRProperty(property, g3prop)

                # sequencing_center
                g3prop = self.gen3node.getProperty("sequencing_center")
                property = row.get("sequencing_center")
                agdr_sequencing_center = AGDRProperty(property, g3prop)

                # sequencing_date
                g3prop = self.gen3node.getProperty("sequencing_date")
                property = row.get("sequencing_date")
                agdr_sequencing_date = AGDRProperty(property, g3prop)

                # size_selection_range
                g3prop = self.gen3node.getProperty("size_selection_range")
                property = row.get("size_selection_range")
                agdr_size_selection_range = AGDRProperty(property, g3prop)

                # spike_ins_concentration
                g3prop = self.gen3node.getProperty("spike_ins_concentration")
                property = row.get("spike_ins_concentration")
                agdr_spike_ins_concentration = AGDRProperty(property, g3prop)

                # spike_ins_fasta
                g3prop = self.gen3node.getProperty("spike_ins_fasta")
                property = row.get("spike_ins_fasta")
                agdr_spike_ins_fasta = AGDRProperty(property, g3prop)

                # target_capture_kit
                g3prop = self.gen3node.getProperty("target_capture_kit")
                property = row.get("target_capture_kit")
                agdr_target_capture_kit = AGDRProperty(property, g3prop)

                # target_capture_kit_catalog_number
                g3prop = self.gen3node.getProperty("target_capture_kit_catalog_number")
                property = row.get("target_capture_kit_catalog_number")
                agdr_target_capture_kit_catalog_number = AGDRProperty(property, g3prop)

                # target_capture_kit_name
                g3prop = self.gen3node.getProperty("target_capture_kit_name")
                property = row.get("target_capture_kit_name")
                agdr_target_capture_kit_name = AGDRProperty(property, g3prop)

                # target_capture_kit_target_region
                g3prop = self.gen3node.getProperty("target_capture_kit_target_region")
                property = row.get("target_capture_kit_target_region")
                agdr_target_capture_kit_target_region = AGDRProperty(property, g3prop)

                # target_capture_kit_vendor
                g3prop = self.gen3node.getProperty("target_capture_kit_vendor")
                property = row.get("target_capture_kit_vendor")
                agdr_target_capture_kit_vendor = AGDRProperty(property, g3prop)

                # target_capture_kit_version
                g3prop = self.gen3node.getProperty("target_capture_kit_version")
                property = row.get("target_capture_kit_version")
                agdr_target_capture_kit_version = AGDRProperty(property, g3prop)

                # to_trim_adapter_sequence
                g3prop = self.gen3node.getProperty("to_trim_adapter_sequence")
                property = row.get("to_trim_adapter_sequence")
                agdr_to_trim_adapter_sequence = AGDRProperty(property, g3prop)

                # fragment_maximum_length
                g3prop = self.gen3node.getProperty("fragment_maximum_length")
                property = row.get("fragment_maximum_length")
                agdr_fragment_maximum_length = AGDRProperty(property, g3prop)

                # fragment_mean_length 
                g3prop = self.gen3node.getProperty("fragment_mean_length")
                property = row.get("fragment_mean_length")
                agdr_fragment_mean_length = AGDRProperty(property, g3prop)

                # fragment_minimum_length
                g3prop = self.gen3node.getProperty("fragment_minimum_length")
                property = row.get("fragment_minimum_length")
                agdr_fragment_minimum_length = AGDRProperty(property, g3prop)

                # fragment_standard_deviation_length
                g3prop = self.gen3node.getProperty("fragment_standard_deviation_length")
                property = row.get("fragment_standard_deviation_length")
                agdr_fragment_standard_deviation_length = AGDRProperty(property, g3prop)

                # multiplex_barcode
                g3prop = self.gen3node.getProperty("multiplex_barcode")
                property = row.get("multiplex_barcode")
                agdr_multiplex_barcode = AGDRProperty(property, g3prop)

                count += 1

                row_data = [
                    agdr_submitter_id,
                    agdr_sample,
                    agdr_adapter_name,
                    agdr_adapter_sequence,
                    agdr_barcoding_applied,
                    agdr_base_caller_name,
                    agdr_base_caller_version,
                    agdr_flow_cell_barcode,
                    agdr_fragment_maximum_length,
                    agdr_fragment_mean_length,
                    agdr_fragment_minimum_length,
                    agdr_fragment_standard_deviation_length,
                    agdr_includes_spike_ins,
                    agdr_instrument_model,
                    agdr_is_paired_end,
                    agdr_library_name,
                    agdr_library_preparation_kit_catalog_number,
                    agdr_library_preparation_kit_name,
                    agdr_library_preparation_kit_vendor,
                    agdr_library_preparation_kit_version,
                    agdr_library_selection,
                    agdr_library_strand,
                    agdr_library_strategy,
                    agdr_multiplex_barcode,
                    agdr_platform,
                    agdr_read_group_name,
                    agdr_read_length,
                    agdr_sequencing_center,
                    agdr_sequencing_date,
                    agdr_size_selection_range,
                    agdr_spike_ins_concentration,
                    agdr_spike_ins_fasta,
                    agdr_target_capture_kit,
                    agdr_target_capture_kit_catalog_number,
                    agdr_target_capture_kit_name,
                    agdr_target_capture_kit_target_region,
                    agdr_target_capture_kit_vendor,
                    agdr_target_capture_kit_version,
                    agdr_to_trim_adapter_sequence,
                    agdr_type
                ]
                nodes.append(AGDRRow(row_data, self.gen3node, sheet_name))
            return nodes

        def populate_supplementary_file(data_category="supplementary file"):
            # TODO: Q for Claire:
            # previously, we could have half as many instruments as files, 
            # in the case of having 2 read groups per instrument
            # currently, we have 1 instrument per file, because of how 
            # the data is structured in the spreadsheet
            #
            # is that fine?
            nodes = []
            sheet_name = None
            try:
                sheet_name = self._extract_spreadsheet_name(data)
            except Exception:
                # no data for this entry, no worries
                return []

            # actually want to generate a validation error, but scream
            # for now instead
            if data_category != "supplementary file" and data_category != "raw read file" and data_category != "processed file":
                raise Exception("Invalid data category for supplementary file: " + data_category)

            agdr_type = self._generate_property("type", self.gen3name, self.gen3node.getProperty("type"))
            count = 0
            for row in data:
                # only populate rows that match the data category, 
                # there will be different node types in the same table
                if row.get("data_category").data.lower() != data_category.lower():
                    continue

                # doi
                #g3prop = self.gen3node.getProperty("doi")
                #property = row.get("doi")
                #agdr_doi = AGDRProperty(property, g3prop)

                # md5sum
                g3prop = self.gen3node.getProperty("md5sum")
                property = row.get("md5sum")
                agdr_md5sum = AGDRProperty(property, g3prop)

                # file_size
                g3prop = self.gen3node.getProperty("file_size")
                property = row.get("file_size")
                agdr_file_size = AGDRProperty(property, g3prop)

                # file_name
                g3prop = self.gen3node.getProperty("file_name")
                property = row.get("file_name")
                agdr_file_name = AGDRProperty(property, g3prop)

                # experimental_strategy -- if file is not supplementary
                g3prop = self.gen3node.getProperty("experimental_strategy")
                property = row.get("experimental_strategy")
                agdr_experimental_strategy = AGDRProperty(property, g3prop)

                # data_type
                g3prop = self.gen3node.getProperty("data_type")
                property = row.get("data_type")
                agdr_data_type = AGDRProperty(property, g3prop)

                # data_format
                g3prop = self.gen3node.getProperty("data_format")
                property = row.get("data_format")
                agdr_data_format = AGDRProperty(property, g3prop)

                # data_category
                g3prop = self.gen3node.getProperty("data_category")
                property = row.get("data_category")
                agdr_data_category = AGDRProperty(property, g3prop)

                # genomics_assay
                # sample_id -- generate parent genomics_assay.submitter_id
                g3prop = self.gen3node.getProperty("submitter_id")
                property = row.get("sample_id")
                submitter_id = property.data + "_" + "GENOMICS_ASSAY_" + str(count)
                property = self._generate_property("genomics_assay.submitter_id", submitter_id, g3prop)
                agdr_genomics_assay = AGDRProperty(property, g3prop)
                agdr_genomics_assay.gen3_name = "genomics_assay.submitter_id" # override name

                # submitter_id
                # for files, submitter_id is the file_name
                g3prop = self.gen3node.getProperty("submitter_id")
                property = row.get("file_name")
                agdr_submitter_id = AGDRProperty(property, g3prop)
                agdr_submitter_id.gen3_name = "submitter_id" # override name

                # cmc -- don't need to populate
                # read_pair_number -- raw file only
                g3prop = self.gen3node.getProperty("read_pair_number")
                property = row.get("read_pair_number")
                agdr_read_pair_number = AGDRProperty(property, g3prop)

                # processed file -- aligned reads index -- no good way to extract this yet

                count += 1

                row_data = [
                    agdr_md5sum,
                    agdr_file_size,
                    agdr_file_name,
                    #agdr_experimental_strategy, # not for supplementary files
                    agdr_data_type,
                    agdr_data_format,
                    agdr_data_category,
                    agdr_genomics_assay,
                    agdr_submitter_id,
                    #agdr_read_pair_number # raw file only
                    agdr_type
                ]
                if data_category.lower() != "supplementary file":
                    row_data.append(agdr_experimental_strategy)
                if data_category.lower() == "raw read file":
                    row_data.append(agdr_read_pair_number)
                nodes.append(AGDRRow(row_data, self.gen3node, sheet_name))
            return nodes

        def populate_raw():
            return populate_supplementary_file(data_category="raw read file")

        def populate_processed_file():
            return populate_supplementary_file(data_category="processed file")




        if self.name.lower() ==               "project": return populate_project_node()
        if self.name.lower() ==               "dataset": return populate_dataset_node()
        if self.name.lower() ==      "external_dataset": return populate_external_dataset_node()
        if self.name.lower() ==           "contributor": return populate_contributors()
        if self.name.lower() ==            "experiment": return populate_experiment()
        if self.name.lower() ==                "genome": return populate_genome()
        if self.name.lower() ==            "metagenome": return populate_metagenome()
        if self.name.lower() ==                "sample": return populate_sample()
        if self.name.lower() ==           "publication": return populate_publication()
        #if self.name.lower() == "indigenous_governance": return populate_indigenous_governance()
        #if self.name.lower() ==                   "iwi": return populate_iwi()
        if self.name.lower() ==        "genomics_assay": return populate_genomics_assay()
        if self.name.lower() ==    "supplementary_file": return populate_supplementary_file()
        if self.name.lower() ==                   "raw": return populate_raw()
        if self.name.lower() ==        "processed_file": return populate_processed_file()
        # above are good

        # create an AGDRRow object for each row of data
        # each AGDRRow must have the correct properties 
        # associated with it

        # TODO: generate validation errors if there are any missing fields


    def addProperty(self, property):
        #'''
        #add a property to the node
        #'''
        #self.data.append(property)
        pass