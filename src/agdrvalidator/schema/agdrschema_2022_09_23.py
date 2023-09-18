from agdrvalidator.utils import logger
import agdrvalidator.utils as utils
#from agdrvalidator.schema.gen3schema import Gen3 as Gen3SchemaBase
from agdrvalidator.schema import Schema
from agdrvalidator.schema.node.agdrnode_2022_09_23 import AGDR as AGDRNode
from agdrvalidator.schema.node.property.agdrproperty_2022_09_23 import AGDR as AGDRProperty


logger = logger.setUp(__name__)


class TerminologyConverter:

    def header_lookup(self, column_name):
        # input: a column name from spreadsheet template 
        # output: property name from schema
        pass


#class Gen3(Gen3SchemaBase):
#    # not sure this should BE a schema
#    # it should HAVE a schema (or several)
#    def __init__(self, g3schema, exceldata):
#        super().__init__(g3schema._root)
#        self._definitions = g3schema._definitions
#        self._settings = g3schema._settings
#        self._terms = g3schema._terms
#        self.nodes = g3schema.nodes
#
#        # tabular data
#        self.raw_data = exceldata
#        self.graph_data = {}
#        # set self.graph_data
#        self._graphify()

class AGDR(Schema):
    # not sure this should BE a schema
    # it should HAVE a schema (or several)
    def __init__(self, g3schema, exceldata, report=None):
        self.gen3schema = g3schema
        self.raw_data = exceldata

        self.report_output = report
        if not report:
            self.report_output = "report.txt"

        self.graph_data = None
        # set self.graph_data

        self._root = None
        self._nodes = {}
        self._graphify()

        # set root node 
        # self._root
        # TODO


    def _addProperties(self, agdrNode, table):
        logger.debug(f"adding property to node {agdrNode._input_name}")
        # iterate over a Table defined in parser.excel.agdrspreadhseet

        #assert len(table.header) == len(table.data)
        #       number of headers        number of nodes
        # I want to check that each row is the same length as headers
        
        # TODO: test this with project
        # THEN: do rule application
        # FINALLY: come back and do other tables
        # STRETCH: TSV generator
        logger.debug(f"table header:\t{table.header}")
        header = table.header
        if len(table.header) == 1:
            header = table.header[0]
        logger.debug(f"table header: {header}")
        for row in table.data:
            #logger.debug(f"row: {row}")
            #logger.debug(f"row length: {len(row)}")
            #logger.debug(f"header length: {len(header)}")
            assert len(row) == len(header)
            for i, column_name in enumerate(header):
                #logger.debug(f"header item: \t\t\t {column_name}")
                #logger.debug(f"row item: \t\t\t {row[i]}")
                #logger.debug(f"nodes: {self.gen3schema.nodes.keys()}")
                #logger.debug(".....")
                #logger.debug(f"output name: {agdrNode._output_name}")

                # column name in excel sheet may not match property name from Gen 3 dictionary
                # or, it may not belong in the current table
                # check that it exists before creating property
                if not utils.is_nan(column_name):
                    gen3prop_name = AGDRProperty.convertName(column_name)
                    #if utils.is_truthy(gen3prop_name):
                    if gen3prop_name:
                        # TODO: I should be storing property by gen3 name 
                        # (output name), but it is the spreadsheet name for now
                        #
                        # investigate why there is some issue, the issue is 
                        # that required fields are tracked by input name, 
                        # but they should be tracked by output name, so that 
                        # the presence/absence can be validated correctly
                        prop = AGDRProperty(column_name, row[i], self.gen3schema.nodes[agdrNode._output_name].getProperty(column_name))
                        agdrNode.addProperty(prop)
                    else:
                        # not yet implemented, definitely need to do this
                        raise Exception(f"unhandled case: property {column_name} does not exist in Gen3 node {agdrNode._output_name}")

    def _graphify(self):
        # convert tabular data from self.exceldata to graph structure

        # Experiments
        #     o associated_references -> create publication nodes
        #     o type -> indicates biosample type, can ignore for now. 
        #               Probably want to remove this column in input
        #            Type generally indicates node type, so want to override
        #            whatever value is populated
        # Files
        #     o there is no submitter_id collected, need to generate one 
        #  
        # Instrument metadata (Read Group)
        #     o corresponding_sample_id -> create sample nodes, this is submitter_id
        #                                  same kind of thing as associated_references

        # to start:
        #   - project node 

        project = AGDRNode('project', self.gen3schema._root)
        # TODO add properties
        # (do it here)
        self._addProperties(project, self.raw_data.Project)
        logger.debug(f"___adding ROOT node: [{project._output_name}]")
        logger.info(f"Project properties:\n\n{self.raw_data.Project.header}\n\n{self.raw_data.Project.data}")
        self._root = project
        self._nodes[project._output_name] = project

        experiments = AGDRNode('experiment', self.gen3schema.nodes["experiment"])
        logger.info(f"Experiment properties:\n\n{self.raw_data.Experiments.header}\n\n{self.raw_data.Experiments.data}")
        self._addProperties(experiments, self.raw_data.Experiments)
        logger.debug(f"___adding node: [{experiments._output_name}]")
        self._nodes[experiments._output_name] = experiments

        # there is some issue with parsing the organism Table for Organism:
        # (it is showing header for both Organism and Environmental)
        # (also, need to remove nan's, shown here as None)
        '''
        >>> header[0]
        ['sample_id', 'experiments', 'submitted_to_insdc', 'individual_identifier', 'secondary_identifier', 'bioproject_accession', 'biosample_accession', 'organism', 'sample_organism_maori_name', 'sample_organism_common_name', 'strain', 'isolate', 'breed', 'cultivar', 'ecotype', 'basis_of_record', 'environmental_medium', 'geo_loc_name', 'lat_lon', '** age', '** dev_stage', 'birth_date', 'birth_location', 'sex', 'tissue', 'biomaterial_provider', 'breeding_history', 'breeding_method', 'cell_line', 'cell_subtype', 'cell_type', 'collected_by', 'collection_date', 'culture_collection', 'death_date', 'disease', 'disease_stage', 'genotype', 'growth_protocol', 'health_state', 'phenotype', 'sample_type', 'store_cond', 'stud_book_number', 'treatment', 'specimen_voucher', 'other_catalogue_numbers']
        >>> header[1]
        ['sample_id', 'experiments', 'submitted_to_insdc', 'bioproject_accession', 'biosample_accession', 'basis_of_record', 'organism', '** host', '**environmental_medium', 'habitat', 'geo_loc_name', 'lat_lon', 'collection_date', 'rel_to_oxygen', 'samp_collect_device', 'collected_by', 'samp_mat_process', 'samp_size', 'source_material_id', 'store_cond ', 'other_catalogue_numbers', 'isolation_source', 'sample_type', 'pH', 'temperature', None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None]
        '''
        organism = AGDRNode('organism', self.gen3schema.nodes["organism"])
        self._addProperties(organism, self.raw_data.Organism)
        logger.debug(f"___adding node: [{organism._output_name}]")
        self._nodes[organism._output_name] = organism

        environmental = AGDRNode('environmental', self.gen3schema.nodes["metagenome"])
        self._addProperties(environmental, self.raw_data.Environmental)
        logger.debug(f"___adding node: [{environmental._output_name}]")
        self._nodes[environmental._output_name] = environmental


        # TODO: determine whether it's a raw or processed file 
        # for now, assume processed file only
        file = AGDRNode('file', self.gen3schema.nodes["processed_file"])
        self._addProperties(environmental, self.raw_data.Files)
        logger.debug(f"___adding node: [{file._output_name}]")
        self._nodes[file._output_name] = file

        instrument = AGDRNode('read_group', self.gen3schema.nodes["read_group"])
        self._addProperties(instrument, self.raw_data.InstrumentMetadata)
        logger.debug(f"___adding node: [{instrument._output_name}]")
        self._nodes[instrument._output_name] = instrument


    def report(self, isValid, name, reasons):
        with open(self.report_output, 'a') as f:
            #f.write(f"Node {name} is invalid: \n\t{reasons}\n")
            if isValid:
                f.write(f"{name} \t... OK!\n")
            else:
                f.write(f"{name} \t... INVALID!\n")
                for reason in reasons:
                    f.write(f"\t{reason}:\t{reasons[reason]}\n")
                f.write("\n")

    def validate(self):
        # walk nodes
        # for each node, call validate
        for node in self.walk():
            logger.debug(f"validating node: {node}")
            isValid, reasons = node.validate()
            self.report(isValid, node._input_name, reasons)


    def walk(self):
        for node in self._nodes:
            yield self._nodes[node]