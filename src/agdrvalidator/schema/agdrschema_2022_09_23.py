from agdrvalidator.utils import logger
import agdrvalidator.utils as utils
#from agdrvalidator.schema.gen3schema import Gen3 as Gen3SchemaBase
from agdrvalidator.schema import Schema
from agdrvalidator.schema.node.agdrnode_2022_09_23 import AGDR as AGDRNode
from agdrvalidator.schema.node.property.agdrproperty_2022_09_23 import AGDR as AGDRProperty
from agdrvalidator.schema.node.property.gen3property import Gen3 as Gen3Property
from agdrvalidator.utils.tabular import * # Table()
from agdrvalidator.transformer.agdrtsv_2022_09_23 import AGDRTSVTransformer


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
    def __init__(self, g3schema, exceldata, report=None, project=None):
        self.gen3schema = g3schema
        self.raw_data = exceldata

        self.report_output = report
        if not report:
            self.report_output = "report.txt"

        self.project_code = project
        if not self.project_code:
            self.project_code = "AGDR99999"

        self.graph_data = None
        # set self.graph_data

        self._root = None
        self._nodes = {}
        self._graphify()

        # set root node 
        # self._root
        # TODO


    def _addProperties(self, node, table):
        allNodes = []

        logger.debug(f"adding property to node {node._input_name}")
        # iterate over a Table defined in parser.excel.agdrspreadhseet

        # FIRST: test this with project (/done)
        # THEN: do rule application (/done)
        # FINALLY: come back and do other tables (/done)
        # STRETCH: TSV generator (in progress)
        logger.debug(f"table header:\t{table.header}")
        header = table.header
        if len(table.header) == 1:
            header = table.header[0]
        logger.debug(f"table header: {header}")
        for node_count, row in enumerate(table.data):
            # a new node should be created here, instead of
            # continuously adding new properties
            agdrNode = AGDRNode(node._input_name, node._gen3_node)
            #logger.debug(f"row: {row}")
            #logger.debug(f"row length: {len(row)}")
            #logger.debug(f"header length: {len(header)}")
            assert len(row) == len(header)
            property_names = set()
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
                    if gen3prop_name:
                        property_names.add(gen3prop_name)
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
                        raise Exception(f"unhandled case: property {column_name} does not exist in Gen3 node {agdrNode._output_name}")
            # check if `submitter_id` was a property, not guaranteed 
            # for all node types from spreadsheet-based input
            if "submitter_id" not in property_names:
                sid = None
                if agdrNode._output_name == "project":
                    sid = self.project_code.upper()
                else:
                    sid = self.project_code.upper() + "_" + agdrNode._output_name.upper() + "_" + str(node_count)
                prop = AGDRProperty("submitter_id", sid, self.gen3schema.nodes[agdrNode._output_name].getProperty("submitter_id"))
                agdrNode.addProperty(prop)
            allNodes.append(agdrNode)
        return allNodes

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


        # there should be one project only
        project = AGDRNode('project', self.gen3schema._root)
        # TODO add properties
        # (do it here)
        project = self._addProperties(project, self.raw_data.Project)[0]
        logger.debug(f"___adding ROOT node: [{project._output_name}]")
        logger.info(f"Project properties:\n\n{self.raw_data.Project.header}\n\n{self.raw_data.Project.data}")
        self._root = project
        self._nodes[project._output_name] = [project] # assume single project

        #logger.debug(f"Experiment data: \n\t{self.raw_data.Experiments.data}")
        # list of lists, 1 list per row


        experiments = AGDRNode('experiment', self.gen3schema.nodes["experiment"])
        name = experiments._output_name
        logger.info(f"Experiment properties:\n\n{self.raw_data.Experiments.header}\n\n{self.raw_data.Experiments.data}")
        # this here returns a list of nodes
        experiments = self._addProperties(experiments, self.raw_data.Experiments)
        logger.debug(f"___adding node: [{name}]")
        self._nodes[name] = experiments

        # add organism nodes
        organisms = AGDRNode('organism', self.gen3schema.nodes["organism"])
        name = organisms._output_name
        logger.info(f"Organism properties:\n\n{self.raw_data.Organism.header}\n\n{self.raw_data.Organism.data}")
        organisms = self._addProperties(organisms, self.raw_data.Organism)
        logger.debug(f"___adding node: [{name}]")
        self._nodes[name] = organisms

        # add metagenome nodes
        environmentals = AGDRNode('metagenome', self.gen3schema.nodes["metagenome"])
        name = environmentals._output_name
        logger.info(f"Environmental properties:\n\n{self.raw_data.Environmental.header}\n\n{self.raw_data.Environmental.data}")
        environmentals = self._addProperties(environmentals, self.raw_data.Environmental)
        logger.debug(f"___adding node: [{name}]")
        self._nodes[name] = environmentals


        # add raw and processed file nodes
        # must first determine whether it's a raw or processed file 
        #
        # extract raw files
        type_idx = self.raw_data.Files.getIndexOf("data_category")
        raw_files = [row for row in self.raw_data.Files.data if "Raw" in row[type_idx] ]
        rfiles = Table()
        rfiles.header = self.raw_data.Files.header
        rfiles.required = self.raw_data.Files.required
        rfiles.data = raw_files

        # add raw files
        files = AGDRNode('raw', self.gen3schema.nodes["raw"])
        name = files._output_name
        #files = self._addProperties(files, self.raw_data.Files)
        files = self._addProperties(files, rfiles)
        logger.debug(f"___adding node: [{name}]")
        self._nodes[name] = files


        # extract processed files
        processed_files = [row for row in self.raw_data.Files.data if "Raw" not in row[type_idx] ]
        pfiles = Table()
        pfiles.header = self.raw_data.Files.header
        pfiles.required = self.raw_data.Files.required
        pfiles.data = processed_files

        # add processed files
        files = AGDRNode('processed_file', self.gen3schema.nodes["processed_file"])
        name = files._output_name
        #files = self._addProperties(files, self.raw_data.Files)
        files = self._addProperties(files, pfiles)
        logger.debug(f"___adding node: [{name}]")
        self._nodes[name] = files

        # add read group nodes
        instruments = AGDRNode('read_group', self.gen3schema.nodes["read_group"])
        name = instruments._output_name
        instruments = self._addProperties(instruments, self.raw_data.InstrumentMetadata)
        logger.debug(f"___adding node: [{name}]")
        self._nodes[name] = instruments

        # TODO TODO TODO 
        # TODO loop back and add missing nodes, e.g. for associated references
        # TODO TODO TODO 


        ########################
        # some post processing 
        ########################

        # add required fields to project
        # dbgap_accession_number
        g3prop = Gen3Property("dbgap_accession_number", self.project_code, required="dbgap_accession_number")
        agdrprop = AGDRProperty("dbgap_accession_number", self.project_code, g3prop)
        project.addProperty(agdrprop)
        # project code
        g3prop = Gen3Property("code", self.project_code, required="code")
        agdrprop = AGDRProperty("code", self.project_code, g3prop)
        project.addProperty(agdrprop)
        self._nodes["project"] = [project]

        # determine number of samples per experimental group, for experiment nodes
        samples_per_exp_group = self._count_samples_per_experimental_group()
        logger.debug(f"samples per exp group: {samples_per_exp_group}")

        for exp in experiments:
            # add in missing number_samples_per_experimental_group 
            logger.debug(f"experiment: {exp.getProperty('submitter_id')._value}")
            exp_sub_id = exp.getProperty("submitter_id")._value
            ct = samples_per_exp_group.get(exp_sub_id, 0)
            g3prop = Gen3Property("number_samples_per_experimental_group", ct, required="number_samples_per_experimental_group")
            agdrprop = AGDRProperty("number_samples_per_experimental_group", ct, g3prop)
            exp.addProperty(agdrprop)

            # add in projects.code
            g3prop = Gen3Property("projects.code", self.project_code, required="projects.code")
            agdrprop = AGDRProperty("projects.code", self.project_code, g3prop)
            exp.addProperty(agdrprop)
        self._nodes["experiment"] = experiments


        for org in organisms:
            g3prop = Gen3Property("projects.code", self.project_code, required="projects.code")
            agdrprop = AGDRProperty("projects.code", self.project_code, g3prop)
            org.addProperty(agdrprop)
        self._nodes["organism"] = organisms

        for env in environmentals:
            g3prop = Gen3Property("projects.code", self.project_code, required="projects.code")
            agdrprop = AGDRProperty("projects.code", self.project_code, g3prop)
            env.addProperty(agdrprop)
        self._nodes["metagenome"] = environmentals

        for rg in instruments:
            g3prop = Gen3Property("projects.code", self.project_code, required="projects.code")
            agdrprop = AGDRProperty("projects.code", self.project_code, g3prop)
            rg.addProperty(agdrprop)
        self._nodes["read_group"] = instruments

        for raw in self._nodes["raw"]:
            g3prop = Gen3Property("projects.code", self.project_code, required="projects.code")
            agdrprop = AGDRProperty("projects.code", self.project_code, g3prop)
            raw.addProperty(agdrprop)

        for pfile in self._nodes["processed_file"]:
            g3prop = Gen3Property("projects.code", self.project_code, required="projects.code")
            agdrprop = AGDRProperty("projects.code", self.project_code, g3prop)
            pfile.addProperty(agdrprop)



    def _count_samples_per_experimental_group(self, counts=None):
        counts = {}
        # it would be better if this were a proper graph structure with 
        # connection between parent and child nodes, then would not have 
        # to iterate over the entire graph
        #
        # need to fix schema implementation to make this possible
        # ok for now
        for nodelist in self.walk():
            for node in nodelist:
                if node._output_name == "organism" or node._output_name == "metagenome":
                    experiment_name = node.getProperty("experiments")._value
                    logger.debug(f"experiment name: {experiment_name}")
                    counts[experiment_name] = counts.get(experiment_name, 0) + 1
        return counts


    def report(self, isValid, node, reasons):
        with open(self.report_output, 'a') as f:
            #f.write(f"Node {name} is invalid: \n\t{reasons}\n")
            if isValid:
                f.write(f"{node._input_name}: {node._unique_id} \t... OK!\n")
            else:
                f.write(f"{node._input_name} \t... INVALID!\n")
                for reason in reasons:
                    f.write(f"\t{reason}:\t{reasons[reason]}\n")
                f.write("\n")

    def validate(self):
        # walk nodes
        # for each node, call validate
        for nodelist in self.walk():
            submitter_ids = set()
            for node in nodelist:
                logger.debug(f"validating node: {node}")
                isValid, reasons = node.validate()

                # need to check for duplicate submitter_id
                for property in node._properties:
                    if property._output_name == "submitter_id":
                        if property._value in submitter_ids:
                            isValid = False
                            reasons[property._output_name] = f"Duplicate {property._input_name} (submitter_id): {property._value}"
                            logger.debug(f"________duplicate submitter id: {property._value}")
                        submitter_ids.add(property._value)

                self.report(isValid, node, reasons)


    def toTSV(self, outputDirectory=None):
        # TODO: configure output dir with argparse
        for nodelist in self.walk():
            if not nodelist:
                # not sure why this is happening, TBD: investigate
                continue
            logger.debug(f"nodelist: {nodelist}")
            tt = None
            for node in nodelist:
                # check if "type" property exists
                # this is a one-off problem for Environmental nodes
                # (bug in spreadsheet template)
                node.addProperty(AGDRProperty("type", node._input_name, None))
                if not tt:
                    tt = AGDRTSVTransformer(node)
                tt.addRow(node)
            tt.toTSV(outputDirectory)

    def walk(self):
        for node in self._nodes:
            yield self._nodes[node]