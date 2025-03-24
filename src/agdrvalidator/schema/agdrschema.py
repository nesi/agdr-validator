'''
A schema (collection of nodes) that holds the data read in from an
excel spreadsheet. It is compatible with the latest AGDR dictionary
'''

import datetime as dt
from typing import Dict

from alive_progress import alive_bar

import agdrvalidator.utils as utils
from agdrvalidator import *  # import AGDR exception types
from agdrvalidator.schema.agdrspreadsheet_validator import \
    AGDRSpreadsheetValidator
from agdrvalidator.schema.base import *
from agdrvalidator.schema.node.agdrnode import AGDR as AGDRNode
from agdrvalidator.schema.node.property.agdrproperty import \
    AGDR as AGDRProperty
from agdrvalidator.schema.node.property.gen3property import \
    Gen3 as Gen3Property
from agdrvalidator.transformer.agdrtsv import AGDRTSVTransformer
from agdrvalidator.utils import logger
from agdrvalidator.utils.helpers import *
from agdrvalidator.utils.rich_tabular import *

logger = logger.setUp(__name__)

class AGDR(Schema):
    def __init__(self, gen3_dictionary, spreadsheet_metadata: Dict[str, AGDRNode], report=None, project="AGDR99999", program="NZ"):
        self._gen3_dictionary = gen3_dictionary
        self.project_code = project
        self.program_name = program

        # check that all expected fields 
        # are still present in the metadata
        # (researcher did not delete them)
        self.bad_spreadsheet_validation_errors = []
        # check that all required fields are present
        self.bad_required_validation_errors = []
        # look for duplicate submitter IDs
        self.bad_submitter_validation_errors = []

        self.project_code = project
        if not self.project_code:
            self.project_code = "99999"

        self.report_output = report
        if not report:
            self.report_output = f"{self.project_code}_validation_report_{dt.datetime.now().strftime('%Y-%m-%d')}.txt"

        self.spreadsheet_report_output = f"{self.project_code}_spreadsheet_validation_report_{dt.datetime.now().strftime('%Y-%m-%d')}.txt"
        
        self.program_name = program
        if not self.program_name:
            self.program_name = "NZ"

        self.graph_data = None

        self._root = None
        self._nodes = {}
        self._metadata = self._consolidate(spreadsheet_metadata)

    def __iter__(self):
        return iter(self._nodes.items())

    def walk(self):
        for node in self._nodes:
            yield self._nodes[node]

    def walkDictStructure(self):
        for node in self._gen3_dictionary.walk():
            if node.name in self._nodes:
                yield self._nodes[node.name]

    def toTSV(self, outputDirectory=None):
        num_files_to_write = 0
        for nodelist in self.walkDictStructure():
            if not nodelist:
                continue
            num_files_to_write += len(nodelist)
        nodecount = 0
        with alive_bar(num_files_to_write, title="\tWriting metadata to TSVs") as bar:
            for nodelist in self.walkDictStructure():
                if not nodelist:
                    continue
                logger.debug(f"nodelist: {nodelist}")
                tt = None
                for node in nodelist:
                    if not tt:
                        tt = AGDRTSVTransformer(node)
                    tt.addRow(node)
                    bar()
                logger.debug(f"{nodecount}: {node.gen3_name}")
                tt.toTSV(outputDirectory, nodecount)
                nodecount += 1

    def project_id(self):
        return self.program_name + "-" + self.project_code

    def _consolidate(self, raw_metadata):
        '''
        the purpose of this function is to consolidate excel spreadsheet
        metadata and the Gen3 dictionary schema. So for all properties, 
        create a new AGDRProperty object and a new Gen3Property object, 
        for all nodes, create a new AGDRNode object and a new Gen3Node object,
        which will build up the AGDR schema.
        The validator class will build the graph structure from the schema
        created by this class.
        '''

        g3schema = self._gen3_dictionary # shorter name

        # most nodes have a 1-1 mapping with the Gen3 schema and
        # the tables from in the metadata spreadsheet
        node = "project"
        logger.debug(f"type of g3schema: {type(g3schema)}")
        logger.debug(f"type of g3schema.nodes: {type(g3schema.nodes)}")
        self._nodes[node] = AGDRNode(node, raw_metadata[node], g3schema.nodes[node], project=self.project_code, program=self.program_name, outputfile=self.report_output)
        self._root = self._nodes[node] # set root to project node

        node = "dataset"
        self._nodes[node] = AGDRNode(node, raw_metadata[node], g3schema.nodes[node], project=self.project_code, program=self.program_name, outputfile=self.report_output)
        node = "external_dataset"
        self._nodes[node] = AGDRNode(node, raw_metadata[node], g3schema.nodes[node], project=self.project_code, program=self.program_name, outputfile=self.report_output)
        node = "contributor"
        self._nodes[node] = AGDRNode(node, raw_metadata[node], g3schema.nodes[node], project=self.project_code, program=self.program_name, outputfile=self.report_output)
        node = "experiment"
        self._nodes[node] = AGDRNode(node, raw_metadata[node], g3schema.nodes[node], project=self.project_code, program=self.program_name, outputfile=self.report_output)
        node = "genome"
        self._nodes[node] = AGDRNode(node, raw_metadata[node], g3schema.nodes[node], project=self.project_code, program=self.program_name, outputfile=self.report_output)
        node = "metagenome"
        self._nodes[node] = AGDRNode(node, raw_metadata[node], g3schema.nodes[node], project=self.project_code, program=self.program_name, outputfile=self.report_output)

        # need to pass in the submitter_id from the genome and metagenome tables
        # specifically for the sample table
        sample_parents = {}
        sample_parents["genome"] = [prop.data for prop in self._nodes["genome"].getProperties("submitter_id")]
        sample_parents["metagenome"] = [prop.data for prop in self._nodes["metagenome"].getProperties("submitter_id")]

        node = "sample"
        self._nodes[node] = AGDRNode(node, raw_metadata[node], g3schema.nodes[node], project=self.project_code, program=self.program_name, parents=sample_parents, outputfile=self.report_output)

        # some nodes are mushed into a single table in the metadata
        # so, split data out from "file" table from excel
        node = "publication"
        dataset_pubs = AGDRNode(node, raw_metadata["dataset"], g3schema.nodes[node], project=self.project_code, program=self.program_name, outputfile=self.report_output)
        external_dataset_pubs = (AGDRNode(node, raw_metadata["external_dataset"], g3schema.nodes[node], project=self.project_code, program=self.program_name, outputfile=self.report_output))
        if dataset_pubs and dataset_pubs.data and external_dataset_pubs and external_dataset_pubs.data:
            dataset_pubs.data.extend(external_dataset_pubs.data)
            self._nodes[node] = dataset_pubs
        elif dataset_pubs and dataset_pubs.data:
            self._nodes[node] = dataset_pubs
        elif external_dataset_pubs and external_dataset_pubs.data:
            self._nodes[node] = external_dataset_pubs

        # TODO: indigenous_governance
        # TODO: iwi

        node = "genomics_assay"
        self._nodes[node] = AGDRNode(node, raw_metadata["file"], g3schema.nodes[node], project=self.project_code, program=self.program_name, outputfile=self.report_output)
        node = "aligned_reads_index"
        self._nodes[node] = AGDRNode(node, raw_metadata["file"], g3schema.nodes[node], project=self.project_code, program=self.program_name, outputfile=self.report_output)
        node = "raw"
        self._nodes[node] = AGDRNode(node, raw_metadata["file"], g3schema.nodes[node], project=self.project_code, program=self.program_name, outputfile=self.report_output)
        node = "processed_file"
        self._nodes[node] = AGDRNode(node, raw_metadata["file"], g3schema.nodes[node], project=self.project_code, program=self.program_name, outputfile=self.report_output)
        node = "supplementary_file"
        self._nodes[node] = AGDRNode(node, raw_metadata[node], g3schema.nodes[node], project=self.project_code, program=self.program_name, outputfile=self.report_output)


        # next, validate the spreadsheet itself
        #asv = AGDRSpreadsheetValidator()
        #asv.add(self._nodes)
        #asv.validate(self.spreadsheet_report_output)

    def getNodeCount(self):
        count = 0
        for node in self._nodes:
            logger.debug("counting node", node, len(self._nodes[node]))
            logger.debug(f"details: \n\t{self._nodes[node]}")
            count += len(self._nodes[node])
        logger.debug("total nodes", count)
        return count


    def findNode(self, name):
        if name in self._nodes:
            return self._nodes[name]
        raise AgdrNotFoundException(f"node {name} not found in AGDR schema")

    def getRootNode(self):
        return self._root
