'''
this file contains data container classes used to represent 
metadata from excel workbook input.
'''
import sys

import pandas as pd
from alive_progress import alive_bar

from agdrvalidator import *  # import AGDR exception types
from agdrvalidator.schema.node.gen3node import Gen3 as Gen3Node
from agdrvalidator.schema.node.property.agdrproperty import \
    AGDR as AGDRProperty
from agdrvalidator.schema.node.property.gen3property import \
    Gen3 as Gen3Property
from agdrvalidator.utils import logger
from agdrvalidator.utils.rich_tabular import (CellLocation, SpreadsheetNode,
                                              SpreadsheetProperty,
                                              SpreadsheetRow)


class AllDatasets:
    def __init__(self):
        self.datasets = []  # Define an empty list

    def add_dataset(self, name, value):
        dataset_entry = {"name": name, "value": value}
        self.datasets.append(dataset_entry)  # Add the dictionary to the list

    def get_value_by_name(self, dataset_name_in_experiment):
        for dataset in self.datasets:
            if str(dataset["name"]).strip().lower() == str(dataset_name_in_experiment).strip().lower():
                return dataset["value"]
        else:
            print(f"In Experiments or Contributor, there is one or more dataset name {dataset_name_in_experiment} \n" 
                f"that we cannot match to any dataset names in the project tab.\n "
                f"Make sure that there is 1 row per entry. e.g if a contributor is connected to more than 1 dataset, please enter 2 rows, 1 for each dataset.\n ")
            sys.exit(1)
            return None  # Return None if no match is found
        
    def get_first(self):
        if self.datasets:
            return self.datasets[0]["value"]
        else:
            print(f"Have you defined datasets?\n ")
            return None  # Return None if the list is empty
    
logger = logger.setUp(__name__)
all_datasets = AllDatasets()

class AGDRRow(SpreadsheetRow):
    '''
    This class represents an entire row of data from a 
    table in the spreadsheet input

    The implementation is the same as the base class, except the 
    properties are AGDRProperty objects instead of SpreadsheetProperty objects, 
    which combine the data from the spreadsheet with the 2024_09_10 AGDR 
    metadata dictionary
    '''
    @classmethod
    def convertProperties(cls, md_node:list[AGDRProperty], gen3_node: Gen3Node):

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

    def __init__(self, data: list[AGDRProperty], gen3node: Gen3Node, sheet_name):
        self.data = data
        self.sheet_name = sheet_name    # the sheet where the data was entered
        self.gen3_name = gen3node.name  # what the dictionary calls the table
        self.gen3node = gen3node

    def __getitem__(self, index):
        return self.data[index]

    def __str__(self):
        return f"AGDRRow(data=[\n\t" + ",\n\t".join(str(prop) for prop in self.data) + f"\n])\n\tALL PROPERTIES: \n\t{self.gen3node}"

    def __repr__(self):
        return self.__str__()

    def getProperty(self, name):
        for prop in self.data:
            if prop.name == name or prop.gen3_name == name:
                return prop
        return None

    def uniqueId(self):
        node_name = self.gen3node.name
        if node_name == "project":
            return str(self.getProperty("code").data)
        return str(self.getProperty("submitter_id").data)


    def validate(self):
        is_valid = True
        reasons = []
        
        for property in self.data:
            # Skip validation if there's no cell location
            if not property.location:
                continue

            location_info = f"sheet [{self.sheet_name}] - [{property.location}]"

            # Check if required properties are populated
            if property.required and not property.data:
                reasons.append(f"Missing required field: {property.name} at {location_info}")
                is_valid = False
            
            # Validate the property itself and collect any issues
            prop_valid, prop_reasons = property.validate()
            if not prop_valid:
                is_valid = False
                reasons.append(f"{prop_reasons} at {location_info}")
        
        return is_valid, reasons

class AGDR(SpreadsheetNode):
    '''
    This class represents all rows of data for a particular 
    node type, such as Project, Dataset, or File metadata.

    self.name represents the table name
    '''
    @classmethod
    def convertName(cls, name):
        '''
        helper function to convert the name of the node to the
        Gen3 node name
        '''
        name = str(name).lower().strip()
        lookup = {
            "instrument": "genomics_assay"
        }
        if name in lookup:
            return lookup[name]
        return name

    def __init__(self, name, data, gen3node:Gen3Node, project="AGDR999999", program="NZ", parents={}, outputfile=None):
        self.name = name
        self.gen3name = AGDR.convertName(name)
        self.gen3node = gen3node
        self.project_name = project
        self.program_name = program
        self.outputfile = outputfile
        self.messagestodisplay = []

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
        #the_data = self._populate_node(data)
        self.data = self._populate_node(data)

        self._unique_id = None

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
        print(f"uniqueId called from AGDRNode")
        return str(self._unique_id)

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

    ############################################################################
    ### validation logic
    ############################################################################

    def validate(self, verbose=False):
        is_valid = True
        reasons = []
        
        for row in self.data:
            # Validate each row and collect row-level errors
            row_valid, row_reasons = row.validate()
            if not row_valid:
                is_valid = False
                reasons.extend(row_reasons)
                
                if verbose:
                    row_info = f"Row [{row.get('submitter_id').data if row.get('submitter_id') else 'Unknown'}]"
                    reasons.append(f"{row_info}: {', '.join(row_reasons)}")
        
        return is_valid, reasons
        
    def report_spreadsheet_issues(self, reasons):
        if self.outputfile:
            with open(self.outputfile, "a", encoding="utf-8") as f:
                # Write the node header line
                f.write(f"Spreadsheet information\n")

                # Iterate through each reason in the list and write it
                for message in reasons:
                    if message:  # Only write non-empty messages
                        f.write(f"\t{message}\n")
        else:
            print(f"Issue with the spreadsheet")
            for message in reasons:
                if message:
                    print(f"\t{message}")

    def add_missing_field_message(self, field, prop, messages, sheet_name, node_name):
        if field.get_value() is None or pd.isna(field.get_value()):
            if prop:
                message = f'{field.gen3_name} is missing in {sheet_name} for node {node_name} in cell {prop.location} \n'
            else: 
                message = f'{field.gen3_name} is missing in {sheet_name} for node {node_name} \n'
            messages.append(message)
        return messages
    
    def add_missing_message(self, msg, messages, sheet_name):
        message = f'{msg} in {sheet_name} \n'
        messages.append(message)
        return messages

    ############################################################################
    ### Code for populating the AGDRNode with metadata from the spreadsheet
    ############################################################################
    
    def _extract_spreadsheet_name(self, data:SpreadsheetNode):
        sheet_name = set()
        for row in data.data:
            sheet_name.add(row.sheet_name)
        if len(sheet_name) > 1:
            # TODO: add to validation errors, something wrong with the data
            #raise AGDRValidationError("Multiple sheets found for Project node")
            raise Exception(f"spreadsheet parsing error; multiple sheets listed for {data.name} node")
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
            prop_name = "dbgap_accession_number"
            agdr_dbgap = self._generate_property(prop_name, self.project_name, self.gen3node.getProperty(prop_name))
            prop_name = "code"
            agdr_code = self._generate_property(prop_name, self.project_name, self.gen3node.getProperty(prop_name))

            nodes = []
            sheet_name = self._extract_spreadsheet_name(data)
            for row in data:
                g3_property = self.gen3node.getProperty("detailed_description")
                property = row.get("project_description")
                agdr_description = AGDRProperty(property, g3_property)
                self.messagestodisplay = self.add_missing_field_message(agdr_description, property, self.messagestodisplay, sheet_name, "project")
                
                property = row.get("name")
                agdr_name = AGDRProperty(property, g3_property)
                self.messagestodisplay = self.add_missing_field_message(agdr_name, property, self.messagestodisplay, sheet_name, "project")
                # need to create a property list
                row_data = [
                    agdr_dbgap, 
                    agdr_code,
                    agdr_description,
                    agdr_name
                    ]
                nodes.append(AGDRRow(row_data, self.gen3node, sheet_name))
                
            if self.messagestodisplay:
                self.report_spreadsheet_issues(self.messagestodisplay)
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

            agdr_projects = self._generate_property("project_id", f"{self.program_name}-{self.project_name}", self.gen3node.getProperty("project_id"))
            agdr_project_code = self._generate_property("projects.code", f"{self.project_name}", self.gen3node.getProperty("project_id"))
            agdr_project_code.gen3_name = "projects.code" # override name

            agdr_type = self._generate_property("type", self.gen3name, self.gen3node.getProperty("type"))
            
            count = 0
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
                self.messagestodisplay = self.add_missing_field_message(agdr_name, property, self.messagestodisplay, sheet_name, "dataset")

                # date_collected is collection_date in the dictionary
                g3prop = self.gen3node.getProperty("collection_date") 
                property = row.get("date_collected")
                agdr_date_collected = AGDRProperty(property, g3prop)
                agdr_date_collected.gen3_name = "collection_date"
                self.messagestodisplay = self.add_missing_field_message(agdr_date_collected, property, self.messagestodisplay, sheet_name, "dataset")

                # detailed_description
                g3prop = self.gen3node.getProperty("detailed_description")
                property = row.get("dataset_description")
                if property is None:
                    property = row.get("datatset_description") #spelling mistake in the template we had at one point - need to remove in the future
                agdr_detailed_description = AGDRProperty(property, g3prop)
                self.messagestodisplay = self.add_missing_field_message(agdr_detailed_description, property, self.messagestodisplay, sheet_name, "dataset")

                # investigator_affiliation
                g3prop = self.gen3node.getProperty("investigator_affiliation")
                property = row.get("investigator_affiliation")
                agdr_investigator_affiliation = AGDRProperty(property, g3prop)
                self.messagestodisplay = self.add_missing_field_message(agdr_investigator_affiliation, property, self.messagestodisplay, sheet_name, "dataset")

                # investigator_name
                g3prop = self.gen3node.getProperty("investigator_name")
                property = row.get("investigator_name")
                agdr_investigator_name = AGDRProperty(property, g3prop)
                self.messagestodisplay = self.add_missing_field_message(agdr_investigator_name, property, self.messagestodisplay, sheet_name, "dataset")

                # contact
                g3prop = self.gen3node.getProperty("contact")
                property = row.get("contact") 
                agdr_contact = AGDRProperty(property, g3prop)
                self.messagestodisplay = self.add_missing_field_message(agdr_contact, property, self.messagestodisplay, sheet_name, "dataset")

                # support_source
                g3prop = self.gen3node.getProperty("support_source")
                property = row.get("support_source")
                agdr_support_source = AGDRProperty(property, g3prop)

                # data_availability
                g3prop = self.gen3node.getProperty("data_availability")
                property = row.get("data_availability")
                agdr_data_availability = AGDRProperty(property, g3prop)

                # agdr_doi
                g3prop = self.gen3node.getProperty("agdr_doi")
                property = row.get("agdr_doi")
                agdr_doi = AGDRProperty(property, g3prop)

                # application_form
                g3prop = self.gen3node.getProperty("application_form")
                property = row.get("access_request_form_link")
                agdr_application_form = AGDRProperty(property, g3prop)

                # submitter_id -- in red at the end
                g3prop = self.gen3node.getProperty("submitter_id")
                property = row.get("dataset_id")
                self._unique_id = property.data
                agdr_submitter_id = AGDRProperty(property, g3prop)
                
                #adding the dataset in the list - used by the experiment to change the name into the id
                all_datasets.add_dataset(agdr_name.get_value(), agdr_submitter_id.get_value())
                
                count += 1
                # properties ordered by order displayed in the portal
                # (not a requirement, a preference)
                row_data = [
                    agdr_submitter_id,
                    agdr_projects,
                    agdr_project_code,
                    agdr_date_collected,
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
                
            if self.messagestodisplay:
                self.report_spreadsheet_issues(self.messagestodisplay)
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
            
            agdr_projects = self._generate_property("project_id", f"{self.program_name}-{self.project_name}", self.gen3node.getProperty("project_id"))
            agdr_project_code = self._generate_property("projects.code", f"{self.project_name}", self.gen3node.getProperty("project_id"))
            agdr_project_code.gen3_name = "projects.code" # override name           
            agdr_type = self._generate_property("type", self.gen3name, self.gen3node.getProperty("type"))
            for row in data:
                # properties ordered by order displayed in spreadsheet
                # (not a requirement, a preference)

                # submitter_id
                g3prop = self.gen3node.getProperty("submitter_id")
                property = row.get("dataset_name")
                agdr_submitter_id = AGDRProperty(property, g3prop)
                self._unique_id = property.data

                # date collected 764
                # Not yet in the dictionary - future work AGDR-
                g3prop = None #self.gen3node.getProperty("date_collected")
                property = row.get("date_collected")
                agdr_date_collected = AGDRProperty(property, g3prop)

                # detailed_description
                g3prop = self.gen3node.getProperty("detailed_description")
                property = row.get("dataset_description")
                if property is None:
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

                properties = [
                    agdr_submitter_id,
                    agdr_date_collected,
                    agdr_bioproject_accession,
                    agdr_biosample_accession,
                    agdr_contact,
                    agdr_dataset_accession,
                    agdr_detailed_description,
                    agdr_external_doi,
                    agdr_investigator_affiliation,
                    agdr_investigator_name,
                    agdr_name,
                    agdr_submitted_to_insdc,
                    agdr_support_source
                ]
                properties_mandatory = [
                    agdr_detailed_description,
                    agdr_investigator_affiliation,
                    agdr_investigator_name,
                    agdr_name
                ]
                if any(pd.notna(prop.get_value()) and prop.get_value() for prop in properties):
                    if any( not pd.notna(prop.get_value()) or not prop.get_value() for prop in properties_mandatory):
                        self.messagestodisplay = self.add_missing_message('External dataset has some cells filled but not enough for an external dataset to be populated, either delete or complete', self.messagestodisplay, sheet_name)
                
                # properties ordered by order displayed in the portal
                # (not a requirement, a preference)
                row_data = [
                    agdr_submitter_id,
                    agdr_projects,
                    agdr_project_code,
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
                
            if self.messagestodisplay:
                self.report_spreadsheet_issues(self.messagestodisplay)
            return nodes

        def populate_contributors():
            nodes = []
            sheet_name = None
            try:
                sheet_name = self._extract_spreadsheet_name(data)
            except Exception:
                # no data for this entry
                # (ok, Contributors optional)
                return []
            agdr_type = self._generate_property("type", self.gen3name, self.gen3node.getProperty("type"))
            agdr_project_id = self._generate_property("project_id", f"{self.program_name}-{self.project_name}", self.gen3node.getProperty("project_id"))
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
                property = row.get("dataset_name")
                agdr_dataset_name = AGDRProperty(property, g3prop)
                agdr_dataset = self._generate_property("dataset.submitter_id", all_datasets.get_value_by_name(agdr_dataset_name.get_value()), g3prop)
                agdr_dataset.gen3_name = "dataset.submitter_id" # override name

                g3prop = self.gen3node.getProperty("submitter_id")
                submitter_id = agdr_dataset_name.data + "_" + "CONTACT_" + str(count)
                property = self._generate_property("submitter_id", submitter_id, g3prop)
                agdr_submitter_id = AGDRProperty(property, g3prop)
                self._unique_id = property.data

                count += 1

                properties = [
                    agdr_dataset,
                    agdr_institution,
                    agdr_name
                ]
                properties_mandatory = [
                    agdr_dataset,
                    agdr_institution,
                    agdr_name
                ]
                if any(pd.notna(prop.get_value()) and prop.get_value() for prop in properties):
                    if any( not pd.notna(prop.get_value()) or not prop.get_value() for prop in properties_mandatory):
                        self.messagestodisplay = self.add_missing_message('Contributors table has some cells filled but not enough for a contributor to be populated, either delete or complete', self.messagestodisplay, sheet_name)

                # properties ordered by order displayed in the portal
                # (not a requirement, a preference)
                row_data = [
                    agdr_submitter_id,
                    agdr_dataset,
                    agdr_institution,
                    agdr_name,
                    agdr_type,
                    agdr_project_id
                ]
                nodes.append(AGDRRow(row_data, self.gen3node, sheet_name))
                
            if self.messagestodisplay:
                self.report_spreadsheet_issues(self.messagestodisplay)
            return nodes

        def populate_experiment():
            nodes = []
            # Experiment can be in multiple sheets, so we'll just call it "Experiment" for now
            sheet_name = "Experiment" 
            agdr_type = self._generate_property("type", self.gen3name, self.gen3node.getProperty("type"))
            agdr_project_id = self._generate_property("project_id", f"{self.program_name}-{self.project_name}", self.gen3node.getProperty("project_id"))
            for row in data:
                # properties ordered by order displayed in spreadsheet
                # (not a requirement, a preference)

                # submitter_id
                g3prop = self.gen3node.getProperty("submitter_id")
                property = row.get("experiment_name")
                agdr_submitter_id = AGDRProperty(property, g3prop)
                self._unique_id = property.data
                self.messagestodisplay = self.add_missing_field_message(agdr_submitter_id, property, self.messagestodisplay, sheet_name, "experiment")

                # dataset_name
                # create a dataset.submitter_id property
                g3prop = self.gen3node.getProperty("dataset") 
                property = row.get("dataset_name")
                agdr_dataset_name = AGDRProperty(property, g3prop)
                agdr_dataset = self._generate_property("dataset.submitter_id", all_datasets.get_value_by_name(agdr_dataset_name.get_value()), g3prop)
                agdr_dataset.gen3_name = "dataset.submitter_id" # override name
                self.messagestodisplay = self.add_missing_field_message(agdr_dataset_name, property, self.messagestodisplay, sheet_name, "experiment")

                # data_description
                g3prop = self.gen3node.getProperty("data_description")
                property = row.get("data_description")
                agdr_data_description = AGDRProperty(property, g3prop)

                row_data = [
                    agdr_submitter_id,
                    agdr_dataset,
                    agdr_data_description,
                    agdr_type,
                    agdr_project_id
                ]
                nodes.append(AGDRRow(row_data, self.gen3node, sheet_name))
                
            if self.messagestodisplay:
                self.report_spreadsheet_issues(self.messagestodisplay)
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
                self._unique_id = property.data

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

                # ** age
                g3prop = self.gen3node.getProperty("age")
                property = row.get("** age")
                agdr_age = AGDRProperty(property, g3prop)

                # ** age_unit
                g3prop = self.gen3node.getProperty("age_unit")
                property = row.get("age_unit")
                agdr_age_unit = AGDRProperty(property, g3prop)

                # ** dev_stage
                g3prop = self.gen3node.getProperty("developmental_stage")
                property = row.get("** dev_stage")
                agdr_developmental_stage = AGDRProperty(property, g3prop)

                # birth_date
                g3prop = self.gen3node.getProperty("birth_date")
                property = row.get("birth_date")
                agdr_birth_date = AGDRProperty(property, g3prop)
                # due to limitation in the parser, gen3 properties with 
                # $ref may not be currently extracted
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

                properties = [
                    agdr_submitter_id,
                    agdr_geo_loc_name,
                    agdr_experiment,
                    agdr_age,
                    agdr_age_unit,
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
                    agdr_specimen_collect_device,
                    agdr_specimen_common_name,
                    agdr_specimen_maori_name,
                    agdr_specimen_scientific_name,
                    agdr_specimen_voucher,
                    agdr_store_cond,
                    agdr_strain
                ]
                properties_mandatory = [
                    agdr_submitter_id,
                    agdr_experiment
                ]
                if any(pd.notna(prop.get_value()) and prop.get_value() for prop in properties):
                    if any( not pd.notna(prop.get_value()) or not prop.get_value() for prop in properties_mandatory):
                        self.messagestodisplay = self.add_missing_message('Genome has some cells filled but not enough for a genome to be populated, either delete or complete', self.messagestodisplay, sheet_name)

                row_data = [
                    agdr_submitter_id,
                    agdr_geo_loc_name,
                    agdr_experiment,
                    agdr_age,
                    agdr_age_unit,
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
                    #agdr_source_material_id, # not in template, combined with the secondary_identifier field
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
                
            if self.messagestodisplay:
                self.report_spreadsheet_issues(self.messagestodisplay)
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

                # similar to specimen_id
                g3prop = self.gen3node.getProperty("submitter_id")
                property = row.get("metagenomic_id")
                if property is None:
                    property = row.get("sample_id") #old name in the spreadsheet
                agdr_submitter_id = AGDRProperty(property, g3prop)
                self._unique_id = property.data

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

                properties = [
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
                    agdr_specimen_collect_device,
                    agdr_store_cond
                ]
                properties_mandatory = [
                    agdr_submitter_id,
                    agdr_habitat,
                    agdr_geo_loc_name,
                    agdr_experiment,
                    agdr_environmental_medium,
                    agdr_basis_of_record,
                    agdr_collection_date
                ]

                if any(pd.notna(prop.get_value()) and prop.get_value() for prop in properties):
                    if any( not pd.notna(prop.get_value()) or not prop.get_value() for prop in properties_mandatory):
                        self.messagestodisplay = self.add_missing_message('Metagenome has some cells filled but not enough for a metagenome to be populated, either delete or complete', self.messagestodisplay, sheet_name)

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
                    #agdr_source_material_id,      # not in template, combined with the secondary_identifier field
                    agdr_specimen_collect_device,
                    agdr_store_cond,
                    agdr_type
                ]
                nodes.append(AGDRRow(row_data, self.gen3node, sheet_name))
                
            if self.messagestodisplay:
                self.report_spreadsheet_issues(self.messagestodisplay)
            return nodes

        def populate_sample():
            nodes = []
            sheet_name = self._extract_spreadsheet_name(data)
            agdr_projects = self._generate_property("project_id", f"{self.program_name}-{self.project_name}", self.gen3node.getProperty("project_id"))
            agdr_type = self._generate_property("type", self.gen3name, self.gen3node.getProperty("type"))
            
            for row in data:
                # sample_id
                g3prop = self.gen3node.getProperty("submitter_id")
                property = row.get("sample_id")
                agdr_submitter_id = AGDRProperty(property, g3prop)
                if property:
                    self._unique_id = property.data
                else:
                    self.messagestodisplay = self.add_missing_message('Sample table has sample_id missing', self.messagestodisplay, sheet_name)

                property = row.get("genomic_specimen_ID or metagenomic_sample_ID")
                if property:
                    parent_id = property.data
                else:
                    parent_id = self.gen3node.getProperty("type")#filling it with something not to crash
                    self.messagestodisplay = self.add_missing_message('Sample table has genomic_specimen_ID or metagenomic_sample_ID missing', self.messagestodisplay, sheet_name)

                    
                property_name = None
                if "genome" in self._potential_parents and self._potential_parents["genome"]:
                    if parent_id in self._potential_parents["genome"]:
                        property_name = "genomes.submitter_id"
                elif "metagenome" in self._potential_parents and self._potential_parents["metagenome"]:
                    if parent_id in self._potential_parents["metagenome"]:
                        property_name = "metagenomes.submitter_id"
                if not property_name:
                    # assume whichever one was populated
                    # there will be a validation error
                    if "genome" in self._potential_parents and self._potential_parents["genome"]:
                        property_name = "genomes.submitter_id"
                    elif "metagenome" in self._potential_parents and self._potential_parents["metagenome"]:
                        property_name = "metagenomes.submitter_id"
                g3prop = self.gen3node.getProperty(property_name) 
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

                properties = [
                    agdr_submitter_id,
                    agdr_collected_by,
                    agdr_collection_date,
                    agdr_coordinate_uncertainty_in_meters,
                    agdr_developmental_stage,
                    agdr_environmental_medium,
                    agdr_geo_loc_name,
                    agdr_habitat,
                    agdr_latitude_decimal_degrees,
                    agdr_longitude_decimal_degrees,
                    agdr_sample_collect_device,
                    agdr_sample_mat_process,
                    agdr_sample_size_unit,
                    agdr_sample_size_value,
                    agdr_sample_title,
                    agdr_secondary_identifier,
                    agdr_specimen_voucher,
                    agdr_store_cond,
                    agdr_tissue,
                    agdr_parent
                ]
                properties_mandatory = [
                    agdr_submitter_id,
                    agdr_collection_date,
                    agdr_parent
                ]
                if any(pd.notna(prop.get_value()) and prop.get_value() for prop in properties) :
                    if any( not pd.notna(prop.get_value()) or not prop.get_value() for prop in properties_mandatory):
                        names = []
                        for prop in properties:
                            value = prop.get_value()    
                            if value and pd.notna(prop.get_value()):  # Check if the value is not empty
                                names.append((prop.gen3_name, prop.get_value(), prop.location))
                        self.messagestodisplay = self.add_missing_message(f'Sample has some cells filled but not enough for a sample to be populated, either delete or complete {names}', self.messagestodisplay, sheet_name)

                row_data = [
                    agdr_submitter_id,
                    agdr_projects,
                    #agdr_biomaterial_provider, # not in template - correct, in the experiments_genomic tab
                    agdr_collected_by,
                    agdr_collection_date,
                    agdr_coordinate_uncertainty_in_meters,
                    agdr_developmental_stage,
                    agdr_environmental_medium,
                    #agdr_genomes, # cannot be determined here
                    agdr_geo_loc_name,
                    agdr_habitat,
                    #agdr_host, # not in template correct, only in the experiments_metagenomic tab
                    agdr_latitude_decimal_degrees,
                    agdr_longitude_decimal_degrees,
                    #agdr_metagenomes, # cannot be determined here
                    agdr_sample_collect_device,
                    agdr_sample_mat_process,
                    agdr_sample_size_unit,
                    agdr_sample_size_value,
                    agdr_sample_title,
                    agdr_secondary_identifier,
                    #agdr_source_material_id, # not in template combined with the secondary_identifier field
                    #agdr_specimen_collect_device, # not in template, correct, it is unused
                    agdr_specimen_voucher,
                    agdr_store_cond,
                    agdr_tissue,
                    agdr_parent, # either genome or metagenome submitter_id
                    agdr_type
                ]
                nodes.append(AGDRRow(row_data, self.gen3node, sheet_name))
                
            if self.messagestodisplay:
                self.report_spreadsheet_issues(self.messagestodisplay)
            return nodes

        def populate_publication():
            # need to determine whether this comes from dataset or external_dataset
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
                # create real g3prop object
                parent = ""
                if is_external_dataset:
                    parent = "external_dataset.submitter_id"
                    g3prop = self.gen3node.getProperty(parent)
                    dataset = row.get("dataset_name")
                    agdr_dataset_external = AGDRProperty(dataset, g3prop)
                    agdr_dataset_external = self._generate_property("external_dataset.submitter_id", agdr_dataset_external.get_value(), g3prop)
                    agdr_dataset_external.gen3_name = parent # override name
                    agdr_dataset = self._generate_property("dataset.submitter_id", all_datasets.get_first(), g3prop)
                    agdr_dataset.gen3_name = "dataset.submitter_id" 
                else:
                    parent = "dataset.submitter_id"
                    g3prop = self.gen3node.getProperty(parent)
                    dataset = row.get("dataset_name")
                    agdr_dataset = AGDRProperty(dataset, g3prop)
                    agdr_dataset = self._generate_property(parent, all_datasets.get_value_by_name(agdr_dataset.get_value()), g3prop)
                    agdr_dataset.gen3_name = parent # override name
                    agdr_dataset_external = self._generate_property("external_dataset.submitter_id", 'nan', g3prop)
                    agdr_dataset_external.gen3_name = "external_dataset.submitter_id"
                # submitter_id
                g3prop = self.gen3node.getProperty("submitter_id")
                property = row.get("dataset_name")
                submitter_id = dataset.data + "_" + "PUBLICATION_" + str(count)
                property = self._generate_property("submitter_id", submitter_id, g3prop)
                agdr_submitter_id = AGDRProperty(property, g3prop)
                self._unique_id = property.data
                count += 1

                row_data = [
                    agdr_doi,
                    #agdr_citation_string # not in template
                    agdr_dataset,
                    agdr_dataset_external,
                    agdr_submitter_id,
                    agdr_type
                ]
                if agdr_doi.get_value() and pd.notna(agdr_doi.get_value()):
                    nodes.append(AGDRRow(row_data, self.gen3node, sheet_name))
                    
            if self.messagestodisplay:
                self.report_spreadsheet_issues(self.messagestodisplay)
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
                submitter_id = str(property.data) + "_" + "GENOMICS_ASSAY_" + str(count)
                property = self._generate_property("submitter_id", submitter_id, g3prop)
                agdr_submitter_id = AGDRProperty(property, g3prop)
                self._unique_id = property.data

                # sample
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

                # sequencing_date - Note the validator is not able yet to get the props of the sequencing date 
                g3prop = self.gen3node.getProperty("sequencing_date")
                property = row.get("sequencing_date")
                agdr_sequencing_date = AGDRProperty(property, g3prop)
                agdr_sequencing_date.gen3_name = "sequencing_date"

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

                # target_capture_kit this does not exist in the spreadsheet at this stage but it is normal
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
                
                properties = [
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
                    agdr_target_capture_kit_catalog_number,
                    agdr_target_capture_kit_name,
                    agdr_target_capture_kit_target_region,
                    agdr_target_capture_kit_vendor,
                    agdr_target_capture_kit_version,
                    agdr_to_trim_adapter_sequence
                ]
                properties_mandatory = [
                    agdr_sample,
                    agdr_platform
                ]
                if any(pd.notna(prop.get_value()) and prop.get_value() for prop in properties) :
                    if any( not pd.notna(prop.get_value()) or not prop.get_value() for prop in properties_mandatory) :
                        names = []
                        for prop in properties:   
                            if prop.get_value() and pd.notna(prop.get_value()):  # Check if the value is not empty
                                names.append((prop.gen3_name, prop.get_value(), prop.location))
                        self.messagestodisplay = self.add_missing_message(f'Files has some cells filled but not enough for a genomic assay to be populated, either delete or complete {names}', self.messagestodisplay, sheet_name)
                
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
                    agdr_target_capture_kit, # this is not in the spreadsheet
                    agdr_target_capture_kit_catalog_number,
                    agdr_target_capture_kit_name,
                    agdr_target_capture_kit_target_region,
                    agdr_target_capture_kit_vendor,
                    agdr_target_capture_kit_version,
                    agdr_to_trim_adapter_sequence,
                    agdr_type
                ]
                nodes.append(AGDRRow(row_data, self.gen3node, sheet_name))
                
            if self.messagestodisplay:
                self.report_spreadsheet_issues(self.messagestodisplay)
            return nodes

        def populate_file(data_category="Raw Read File"):
            nodes = []
            sheet_name = None
            try:
                sheet_name = self._extract_spreadsheet_name(data)
            except Exception:
                # no data for this entry, no worries
                return []

            agdr_type = self._generate_property("type", self.gen3name, self.gen3node.getProperty("type"))
            count = 0
            for row in data:
                
                # only populate rows that match the data category, 
                # there will be different node types in the same table
                # data_category
                g3prop = self.gen3node.getProperty("data_category")
                property = row.get("data_category")
                agdr_data_category = AGDRProperty(property, g3prop)

                if str(agdr_data_category.get_value()).lower() == data_category.lower():
                    agdr_data_category = self._generate_property("data_category", data_category, g3prop)
                elif str(agdr_data_category.get_value()).lower() not in ('raw read file','processed file', 'aligned reads file', 'aligned read index') and data_category.lower() == 'raw read file': #this is to do only once
                    self.messagestodisplay = self.add_missing_message(f'Invalid data category: {agdr_data_category.get_value()} in location {property.location}', self.messagestodisplay, sheet_name)
                    count += 1
                    continue
                else: 
                    count += 1
                    continue
                
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

                # experimental_strategy
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

                # genomics_assay
                # sample_id -- generate parent genomics_assay.submitter_id
                g3prop = self.gen3node.getProperty("submitter_id")
                property = row.get("sample_id")
                submitter_id = str(property.data) + "_" + "GENOMICS_ASSAY_" + str(count)
                property = self._generate_property("genomics_assay.submitter_id", submitter_id, g3prop)
                agdr_genomics_assay = AGDRProperty(property, g3prop)
                agdr_genomics_assay.gen3_name = "genomics_assay.submitter_id" # override name

                # submitter_id
                # for files, submitter_id is the file_name
                g3prop = self.gen3node.getProperty("submitter_id")
                property = row.get("file_name")
                agdr_submitter_id = AGDRProperty(property, g3prop)
                agdr_submitter_id.gen3_name = "submitter_id" # override name
                self._unique_id = property.data

                # read_pair_number -- raw file only
                g3prop = self.gen3node.getProperty("read_pair_number")
                property = row.get("read_pair_number")
                agdr_read_pair_number = AGDRProperty(property, g3prop)
                
                properties = [
                    agdr_md5sum,
                    agdr_file_size,
                    agdr_file_name,
                    agdr_experimental_strategy,
                    agdr_data_type,
                    agdr_data_format,
                    agdr_data_category,
                    agdr_genomics_assay,
                    agdr_read_pair_number
                ]
                properties_mandatory = [
                    agdr_md5sum,
                    agdr_file_size,
                    agdr_file_name,
                    agdr_experimental_strategy,
                    agdr_data_type,
                    agdr_data_format,
                    agdr_data_category,
                    agdr_genomics_assay,
                ]

                if any(pd.notna(prop.get_value()) and prop.get_value() for prop in properties) :
                    if any( not pd.notna(prop.get_value()) or not prop.get_value() for prop in properties_mandatory) :
                        names = []
                        for prop in properties:
                            if prop.get_value() and pd.notna(prop.get_value()):  # Check if the value is not empty
                                names.append((prop.gen3_name, prop.get_value(), prop.location))
                        self.messagestodisplay = self.add_missing_message(f'Files has some cells filled but not enough for a file to be populated, either delete or complete {names}', self.messagestodisplay, sheet_name)

                count += 1

                row_data = [
                    agdr_md5sum,
                    agdr_file_size,
                    agdr_file_name,
                    agdr_experimental_strategy,
                    agdr_data_type,
                    agdr_data_format,
                    agdr_data_category,
                    agdr_genomics_assay,
                    agdr_submitter_id,
                    #agdr_read_pair_number # raw file only see below
                    agdr_type
                ]
                
                if data_category.lower() == "raw read file":
                    row_data.append(agdr_read_pair_number)
                nodes.append(AGDRRow(row_data, self.gen3node, sheet_name))
                
            if self.messagestodisplay:
                self.report_spreadsheet_issues(self.messagestodisplay)
            return nodes

        def populate_raw():
            return populate_file(data_category="Raw Read File")

        def populate_processed_file():
            return populate_file(data_category="Processed File")

        def populate_aligned_read_index():
            return populate_file(data_category="Aligned Reads File")
        
        def populate_supplementary_file():
            nodes = []
            sheet_name = None
            try:
                sheet_name = self._extract_spreadsheet_name(data)
            except Exception:
                # no data for this entry, no worries
                return []

            agdr_type = self._generate_property("type", self.gen3name, self.gen3node.getProperty("type"))
            agdr_data_category = self._generate_property("data_category", "Supplementary File", self.gen3node.getProperty("data_category"))

            count = 0
            for row in data:
 
                # md5sum
                g3prop = self.gen3node.getProperty("md5sum")
                property = row.get("md5sum")
                agdr_md5sum = AGDRProperty(property, g3prop)
                agdr_md5sum = self._generate_property("md5sum", agdr_md5sum.get_value().replace(" ", ""), g3prop)
    
                # file_size
                g3prop = self.gen3node.getProperty("file_size")
                property = row.get("file_size")
                agdr_file_size = AGDRProperty(property, g3prop)

                # file_name
                g3prop = self.gen3node.getProperty("file_name")
                property = row.get("file_name")
                agdr_file_name = AGDRProperty(property, g3prop)

                # data_type
                g3prop = self.gen3node.getProperty("data_type")
                property = row.get("data_type")
                agdr_data_type = AGDRProperty(property, g3prop)

                # data_format
                g3prop = self.gen3node.getProperty("data_format")
                property = row.get("data_format")
                agdr_data_format = AGDRProperty(property, g3prop)

                # experiment name -- generate parent
                g3prop = self.gen3node.getProperty("experiment")
                property = row.get("experiment_name")
                agdr_experiment = AGDRProperty(property, g3prop)
                agdr_experiment.gen3_name = "experiment.submitter_id" # override name

                # submitter_id
                # for files, submitter_id is the file_name
                g3prop = self.gen3node.getProperty("submitter_id")
                property = row.get("file_name")
                agdr_submitter_id = AGDRProperty(property, g3prop)
                agdr_submitter_id.gen3_name = "submitter_id" # override name
                self._unique_id = property.data
                
                properties = [
                    agdr_md5sum,
                    agdr_file_size,
                    agdr_file_name,
                    agdr_data_type,
                    agdr_data_format,
                    agdr_data_category,
                    agdr_experiment,
                ]
                properties_mandatory = [
                    agdr_md5sum,
                    agdr_file_size,
                    agdr_file_name,
                    agdr_data_type,
                    agdr_data_format,
                    agdr_data_category,
                    agdr_experiment,
                ]

                if any(pd.notna(prop.get_value()) and prop.get_value() for prop in properties) :
                    if any( not pd.notna(prop.get_value()) or not prop.get_value() for prop in properties_mandatory) :
                        names = []
                        for prop in properties:
                            if prop.get_value() and pd.notna(prop.get_value()):  # Check if the value is not empty
                                names.append((prop.gen3_name, prop.get_value(), prop.location))
                        self.messagestodisplay = self.add_missing_message(f'Supplementary files has some cells filled but not enough for a supplementary file to be populated, either delete or complete {names}', self.messagestodisplay, sheet_name)

                count += 1

                row_data = [
                    agdr_md5sum,
                    agdr_file_size,
                    agdr_file_name,
                    agdr_data_type,
                    agdr_data_format,
                    agdr_data_category,
                    agdr_experiment,
                    agdr_submitter_id,
                    agdr_type
                ]
                nodes.append(AGDRRow(row_data, self.gen3node, sheet_name))
                
            if self.messagestodisplay:
                self.report_spreadsheet_issues(self.messagestodisplay)
            return nodes

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
        if self.name.lower() ==        "aligned_reads_index": return populate_aligned_read_index()
