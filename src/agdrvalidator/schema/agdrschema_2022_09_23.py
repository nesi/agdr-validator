'''
@Author: Eirian Perkins

A schema (collection of nodes) that holds the data read in from an 
excel spreadsheet. It is compatible with the AGDR dictionary 
version 2022-09-23 only.

An AGDR schema object defined here "has-a" Gen3 schema object, but 
it would be better to keep those separate and have a Validator 
object that "has-a" Gen3 schema and "has-a" AGDR schema. 

This improved implementation should be done for the new AGDR dictionary.
'''
from agdrvalidator.utils import logger
import agdrvalidator.utils as utils
from agdrvalidator.utils.helpers import *
#from agdrvalidator.schema.gen3schema import Gen3 as Gen3SchemaBase
from agdrvalidator.schema.base import *
from agdrvalidator.schema.node.agdrnode_2022_09_23 import AGDR as AGDRNode
from agdrvalidator.schema.node.property.agdrproperty_2022_09_23 import AGDR as AGDRProperty
from agdrvalidator.schema.node.property.gen3property import Gen3 as Gen3Property
from agdrvalidator.utils.tabular import * # Table()
from agdrvalidator.transformer.agdrtsv_2022_09_23 import AGDRTSVTransformer
import datetime


logger = logger.setUp(__name__)


class TerminologyConverter:

    def header_lookup(self, column_name):
        # input: a column name from spreadsheet template 
        # output: property name from schema
        pass


class AGDR(Schema):
    def __init__(self, g3schema, exceldata, report=None, project=None, program=None):
        self.gen3schema = g3schema
        self.raw_data = exceldata

        self.project_code = project
        if not self.project_code:
            self.project_code = "AGDR99999"

        self.report_output = report
        if not report:
            self.report_output = f"{self.project_code}_validation_report_{datetime.datetime.now().strftime('%Y-%m-%d')}.txt"


        self.program_name = program
        if not self.program_name:
            self.program_name = "TAONGA"

        self.graph_data = None
        # set self.graph_data

        self._root = None
        self._nodes = {}
        self._graphify()


    def getRootNode(self):
        return self._root


    def _addProperties(self, node, table):
        allNodes = []

        logger.debug(f"adding property to node {node._input_name}")
        # iterate over a Table defined in parser.excel.agdrspreadhseet

        logger.debug(f"table header:\t{table.header}")
        header = table.header
        if len(table.header) == 1:
            header = table.header[0]
        logger.debug(f"table header: {header}")
        for node_count, row in enumerate(table.data):
            # a new node should be created here, instead of
            # continuously adding new properties
            agdrNode = AGDRNode(node._input_name, node._gen3_node)
            assert len(row) == len(header)
            property_names = set()
            for i, column_name in enumerate(header):

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

            # this block below should now be "dead code"
            # next time maintenance is performed here, remove it and test
            if "submitter_id" not in property_names:
                sid = None
                if agdrNode._output_name == "project":
                    sid = self.project_code.upper()
                else:
                    sid = self.project_code.upper() + "_" + agdrNode._output_name.upper() + "_" + str(node_count)
                    #sid = agdrNode.generateSubmitterId()
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

        # first, determine project_id, as it will be injected to most nodes
        proj_id = self.program_name + "-" + self.project_code


        # there should be one project only
        project = AGDRNode('project', self.gen3schema._root)
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
        for file in files:
            oldprop = file.removeProperty("submitter_id")
            sid = file.generateSubmitterId()
            newprop = AGDRProperty("submitter_id", sid, oldprop._rule)
            file.addProperty(newprop)
        logger.debug(f"___adding node: [{name}]")
        self._nodes[name] = files


        # extract processed files
        processed_files = [row for row in self.raw_data.Files.data if "Raw" not in row[type_idx] and "experimental" not in row[type_idx] ]
        pfiles = Table()
        pfiles.header = self.raw_data.Files.header
        pfiles.required = self.raw_data.Files.required
        pfiles.data = processed_files

        # add processed files
        files = AGDRNode('processed_file', self.gen3schema.nodes["processed_file"])
        name = files._output_name
        files = self._addProperties(files, pfiles)
        for file in files:
            oldprop = file.removeProperty("submitter_id")
            sid = file.generateSubmitterId()
            newprop = AGDRProperty("submitter_id", sid, oldprop._rule)
            file.addProperty(newprop)
        logger.debug(f"___adding node: [{name}]")
        self._nodes[name] = files

        # extract experimental metadata files 
        exp_metadata_files = [row for row in self.raw_data.Files.data if "experimental" in row[type_idx].lower() ]
        efiles = Table()
        efiles.header = self.raw_data.Files.header
        efiles.required = self.raw_data.Files.required
        efiles.data = exp_metadata_files

        # add experimental metadata files
        files = AGDRNode('experimental_metadata', self.gen3schema.nodes["experimental_metadata"])
        name = files._output_name
        files = self._addProperties(files, efiles)
        for file in files:
            oldprop = file.removeProperty("submitter_id")
            sid = file.generateSubmitterId()
            newprop = AGDRProperty("submitter_id", sid, oldprop._rule)
            file.addProperty(newprop)
        logger.debug(f"___adding node: [{name}]")
        self._nodes[name] = files

        # add read group nodes
        instruments = AGDRNode('read_group', self.gen3schema.nodes["read_group"])
        name = instruments._output_name
        instruments = self._addProperties(instruments, self.raw_data.InstrumentMetadata)
        logger.debug(f"___adding node: [{name}]")
        self._nodes[name] = instruments

        ########################
        # add in "missing" nodes
        ########################
        logger.debug(f"generating missing nodes")

        logger.debug(f"core metadata collection")
        # core metadata collection
        g3cmc = self.gen3schema.nodes["core_metadata_collection"]
        cmcNode = AGDRNode("core_metadata_collection", g3cmc)
        g3prop = Gen3Property("type", "core_metadata_collection", required="type")
        agdrprop = AGDRProperty("type", "core_metadata_collection", g3prop)
        cmcNode.addProperty(agdrprop)
        g3prop = Gen3Property("projects.code", self.project_code, required="projects.code")
        agdrprop = AGDRProperty("projects.code", self.project_code, g3prop)
        cmcNode.addProperty(agdrprop)
        subid = cmcNode.generateSubmitterId()
        g3prop = Gen3Property("submitter_id", subid, required="submitter_id")
        agdrprop = AGDRProperty("submitter_id", subid, g3prop)
        cmcNode.addProperty(agdrprop)
        self._nodes["core_metadata_collection"] = [cmcNode]

        logger.debug(f"sample")
        # parent is experiment and also either metagenome, organism or environmental
        # don't actually need to loop through experiments because of how 
        # the metadata template is structured -- experiment submitter_id is included 
        # in the metagenome, organism and environmental tables

        ###############################################################
        # TODO TODO TODO TODO TODO
        # The developer (Eirian so far) has only seen examples of 
        # spreadsheets with metagenome nodes
        # probably code should be duplicated from metagenome to organism
        #
        # test with organism and make appropriate changes
        # TODO TODO TODO TODO TODO
        ###############################################################
        g3sample = self.gen3schema.nodes["sample"]
        samples = []
        for node in self._nodes["metagenome"]:
            sampleNode = AGDRNode("sample", g3sample)

            g3prop = Gen3Property("project_id", proj_id, required="project_id")
            agdrprop = AGDRProperty("project_id", proj_id, g3prop)
            sampleNode.addProperty(agdrprop)

            g3prop = Gen3Property("type", "sample", required="type")
            agdrprop = AGDRProperty("type", "sample", g3prop)
            sampleNode.addProperty(agdrprop)

            g3prop = Gen3Property("experiments.submitter_id", node.getProperty("experiments")._value, required="experiments.submitter_id")
            agdrprop = AGDRProperty("experiments.submitter_id", node.getProperty("experiments")._value, g3prop)
            sampleNode.addProperty(agdrprop)

            g3prop = Gen3Property("metagenomes.submitter_id", node.getProperty("submitter_id")._value, required="")
            agdrprop = AGDRProperty("metagenomes.submitter_id", node.getProperty("submitter_id")._value, g3prop)
            sampleNode.addProperty(agdrprop)

            g3prop = Gen3Property("organisms.submitter_id", "", required="")
            agdrprop = AGDRProperty("organisms.submitter_id", "", g3prop)
            sampleNode.addProperty(agdrprop)

            subid = sampleNode.generateSubmitterId(node.getProperty("submitter_id")._value)
            g3prop = Gen3Property("submitter_id", subid, required="submitter_id")
            agdrprop = AGDRProperty("submitter_id", subid, g3prop)
            sampleNode.addProperty(agdrprop)

            samples.append(sampleNode)
        self._nodes["sample"] = samples

        samples = []
        for node in self._nodes["organism"]:
            sampleNode = AGDRNode("sample", g3sample)

            g3prop = Gen3Property("project_id", proj_id, required="project_id")
            agdrprop = AGDRProperty("project_id", proj_id, g3prop)
            sampleNode.addProperty(agdrprop)

            g3prop = Gen3Property("type", "sample", required="type")
            agdrprop = AGDRProperty("type", "sample", g3prop)
            sampleNode.addProperty(agdrprop)

            g3prop = Gen3Property("experiments.submitter_id", node.getProperty("experiments")._value, required="experiments.submitter_id")
            agdrprop = AGDRProperty("experiments.submitter_id", node.getProperty("experiments")._value, g3prop)
            sampleNode.addProperty(agdrprop)

            g3prop = Gen3Property("metagenomes.submitter_id", "", required="")
            agdrprop = AGDRProperty("metagenomes.submitter_id", "", g3prop)
            sampleNode.addProperty(agdrprop)

            g3prop = Gen3Property("organisms.submitter_id", node.getProperty("submitter_id")._value, required="")
            agdrprop = AGDRProperty("organisms.submitter_id", node.getProperty("submitter_id")._value, g3prop)
            sampleNode.addProperty(agdrprop)

            subid = sampleNode.generateSubmitterId(node.getProperty("submitter_id")._value)
            g3prop = Gen3Property("submitter_id", subid, required="submitter_id")
            agdrprop = AGDRProperty("submitter_id", subid, g3prop)
            sampleNode.addProperty(agdrprop)

            samples.append(sampleNode)
        self._nodes["sample"].extend(samples)

        g3aliquot = self.gen3schema.nodes["aliquot"]
        aliquots = []
        for node in self._nodes["sample"]:
            aliquotNode = AGDRNode("aliquot", g3aliquot)

            g3prop = Gen3Property("project_id", proj_id, required="project_id")
            agdrprop = AGDRProperty("project_id", proj_id, g3prop)
            aliquotNode.addProperty(agdrprop)

            g3prop = Gen3Property("type", "aliquot", required="type")
            agdrprop = AGDRProperty("type", "aliquot", g3prop)
            aliquotNode.addProperty(agdrprop)

            g3prop = Gen3Property("samples.submitter_id", node.getProperty("submitter_id")._value, required="samples.submitter_id")
            agdrprop = AGDRProperty("samples.submitter_id", node.getProperty("submitter_id")._value, g3prop)
            aliquotNode.addProperty(agdrprop)

            subid = aliquotNode.generateSubmitterId(node.getProperty("submitter_id")._value.split("_SAMPLE")[0])
            g3prop = Gen3Property("submitter_id", subid, required="submitter_id")
            agdrprop = AGDRProperty("submitter_id", subid, g3prop)
            aliquotNode.addProperty(agdrprop)

            aliquots.append(aliquotNode)
        self._nodes["aliquot"] = aliquots
 

        # TBD - implement this when we have an example for ingest
        #for node in self._nodes["population"]:
        #    pass
        # TODO
        # ditto for organism


        ########################
        # Create publication nodes
        # (extract reference property from Experiment nodes)
        ########################
        experiments = self._nodes["experiment"]
        publications = []
        for exp in experiments:
            pubNode = AGDRNode("publication", self.gen3schema.nodes["publication"])

            g3prop = Gen3Property("type", "publication", required="type")
            agdrprop = AGDRProperty("type", "publication", g3prop)
            pubNode.addProperty(agdrprop)

            subid = pubNode.generateSubmitterId(exp.getProperty("submitter_id")._value)
            g3prop = Gen3Property("submitter_id", subid, required="submitter_id")
            agdrprop = AGDRProperty("submitter_id", subid, g3prop)
            pubNode.addProperty(agdrprop)

            refprop = exp.removeProperty("associated_references")
            value = ""
            if refprop:
                value = refprop._value
                g3prop = Gen3Property("citation_placeholder", value, required="")
                agdrprop = AGDRProperty("citation_placeholder", value, g3prop)
                pubNode.addProperty(agdrprop)

                #g3prop = Gen3Property("submitter_id", node.getProperty("submitter_id")._value, required="submitter_id")
                #agdrprop = AGDRProperty("submitter_id", f'{node.getProperty("submitter_id")._value}_PUB', g3prop)
                #pubNode.addProperty(agdrprop)

                g3prop = Gen3Property("project_id", proj_id, required="project_id")
                agdrprop = AGDRProperty("project_id", proj_id, g3prop)
                pubNode.addProperty(agdrprop)

                publications.append(pubNode)
        if publications:
            self._nodes["publication"] = publications

        ########################
        # Correct experimental_metadata nodes -- hack because of dictionary structure
        ########################
        experimental_metadata = self._nodes["experimental_metadata"]
        for em in experimental_metadata:
            experiment_id = em.removeProperty("corresponding_sample_id")._value
            g3prop = Gen3Property("experiments.submitter_id", experiment_id, required="")
            agdrprop = AGDRProperty("experiments.submitter_id", experiment_id, g3prop)
            em.addProperty(agdrprop)
        


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
            # TODO: expand code out as in environmentals below
            # need a spreadsheet example to verify code correctness
            g3prop = Gen3Property("project_id", proj_id, required="project_id")
            agdrprop = AGDRProperty("project_id", proj_id, g3prop)
            #g3prop = Gen3Property("projects.code", self.project_code, required="projects.code")
            #agdrprop = AGDRProperty("projects.code", self.project_code, g3prop)
            org.addProperty(agdrprop)

            latlon = org.removeProperty("lat_lon")
            lat, lon = latlonify(latlon._value)
            g3prop = Gen3Property("latitude_decimal_degrees", lat, required="")
            agdrprop = AGDRProperty("latitude_decimal_degrees", lat, g3prop)
            org.addProperty(agdrprop)

            g3prop = Gen3Property("longitude_decimal_degrees", lon, required="")
            agdrprop = AGDRProperty("longitude_decimal_degrees", lon, g3prop)
            org.addProperty(agdrprop)

            submitted_to_insdc = org.getProperty("submitted_to_insdc")
            agdrprop = False
            # TODO: this is a bug
            newval = False
            if submitted_to_insdc:
                newval = boolify(submitted_to_insdc._value)
            g3prop = Gen3Property("submitted_to_insdc", newval, required="")
            agdrprop = AGDRProperty("submitted_to_insdc", newval, g3prop)
            org.addProperty(agdrprop)

            # correct date format
            collection_date = org.getProperty("collection_date")._value
            newval = dateify(collection_date)
            g3prop = Gen3Property("collection_date", newval, required="")
            agdrprop = AGDRProperty("collection_date", newval, g3prop)
            org.addProperty(agdrprop)
        self._nodes["organism"] = organisms

        for env in environmentals:
            g3prop = Gen3Property("project_id", proj_id, required="project_id")
            agdrprop = AGDRProperty("project_id", proj_id, g3prop)
            #g3prop = Gen3Property("projects.code", self.project_code, required="projects.code")
            #agdrprop = AGDRProperty("projects.code", self.project_code, g3prop)
            env.addProperty(agdrprop)

            #logger.debug("all properties: "+ "\n".join([str(x) for x in env.getProperties()]))
            latlon = env.removeProperty("lat_lon")
            lat, lon = latlonify(latlon._value)
            g3prop = Gen3Property("latitude_decimal_degrees", lat, required="")
            agdrprop = AGDRProperty("latitude_decimal_degrees", lat, g3prop)
            env.addProperty(agdrprop)

            g3prop = Gen3Property("longitude_decimal_degrees", lon, required="")
            agdrprop = AGDRProperty("longitude_decimal_degrees", lon, g3prop)
            env.addProperty(agdrprop)

            submitted_to_insdc = env.getProperty("submitted_to_insdc")
            newval = boolify(submitted_to_insdc._value)
            g3prop = Gen3Property("submitted_to_insdc", newval, required="")
            agdrprop = AGDRProperty("submitted_to_insdc", newval, g3prop)
            env.addProperty(agdrprop)

            # correct date format
            collection_date = env.getProperty("collection_date")._value
            newval = dateify(collection_date)
            g3prop = Gen3Property("collection_date", newval, required="")
            agdrprop = AGDRProperty("collection_date", newval, g3prop)
            env.addProperty(agdrprop)

            # remove properties that spreadsheet asks for, 
            # that are not part of metagenome node in gen3 model
            env.removeProperty("sample_type")
            env.removeProperty("organism")
            env.removeProperty("isolation_source")
            env.removeProperty("temperature")
            env.removeProperty("ph")
        self._nodes["metagenome"] = environmentals

        gen_rg_sub_id = []
        for rg in instruments:
            g3prop = Gen3Property("project_id", proj_id, required="project_id")
            agdrprop = AGDRProperty("project_id", proj_id, g3prop)
            rg.addProperty(agdrprop)

            sample_id = rg.removeProperty("corresponding_sample_id")

            subid = rg.generateSubmitterId(sample_id._value)
            if subid not in gen_rg_sub_id:
                gen_rg_sub_id.append(subid)
                subid = subid + "_R1"
            else:
                subid = subid + "_R2"
            g3prop = Gen3Property("submitter_id", subid, required="submitter_id")
            agdrprop = AGDRProperty("submitter_id", subid, g3prop)
            rg.addProperty(agdrprop)

            # this is missing from the spreadsheet, so this is 
            # a bug in the template
            # uncomment these lines when spreadsheet is updated
            #print("corr samp id: " + rg.getProperty("corresponding_sample_id"))
            alq_id = sample_id._value + "_ALQ"
            g3prop = Gen3Property("aliquots.submitter_id", alq_id, required="aliquots.submitter_id")
            agdrprop = AGDRProperty("aliquots.submitter_id", alq_id, g3prop)
            rg.addProperty(agdrprop)

            is_paired_end = rg.getProperty("is_paired_end")
            newval = boolify(is_paired_end._value)
            g3prop = Gen3Property("is_paired_end", newval, required="")
            agdrprop = AGDRProperty("is_paired_end", newval, g3prop)
            rg.addProperty(agdrprop)

        self._nodes["read_group"] = instruments

        rg_sub_id = []
        for raw in self._nodes["raw"]:
            g3prop = Gen3Property("project_id", proj_id, required="project_id")
            agdrprop = AGDRProperty("project_id", proj_id, g3prop)
            raw.addProperty(agdrprop)

            sample_id = raw.removeProperty("corresponding_sample_id")._value
            rg_id = sample_id + "_RG"
            if rg_id not in gen_rg_sub_id:
                if rg_id not in rg_sub_id:
                    rg_sub_id.append(rg_id)
                    rg_id = rg_id + "_R1"
                else:
                    rg_id = rg_id + "_R2"
            else:
                rg_id = rg_id + "_R1"
            g3prop = Gen3Property("read_groups.submitter_id", rg_id, required="read_groups.submitter_id")
            agdrprop = AGDRProperty("read_groups.submitter_id", rg_id, g3prop)
            raw.addProperty(agdrprop)

        rg_sub_id = []
        for pfile in self._nodes["processed_file"]:
            g3prop = Gen3Property("project_id", proj_id, required="project_id")
            agdrprop = AGDRProperty("project_id", proj_id, g3prop)
            pfile.addProperty(agdrprop)

            sample_id = pfile.removeProperty("corresponding_sample_id")._value
            rg_id = sample_id + "_RG"
            if rg_id not in gen_rg_sub_id:
                if rg_id not in rg_sub_id:
                    rg_sub_id.append(rg_id)
                    rg_id = rg_id + "_R1"
                else:
                    rg_id = rg_id + "_R2"
            else:
                rg_id = rg_id + "_R1"
            g3prop = Gen3Property("read_groups.submitter_id", rg_id, required="read_groups.submitter_id")
            agdrprop = AGDRProperty("read_groups.submitter_id", rg_id, g3prop)
            pfile.addProperty(agdrprop)

            g3prop = Gen3Property("data_type", "Processed File", required="")
            agdrprop = AGDRProperty("data_type", "Processed File", g3prop)
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
        logger.debug("output order:")
        # TODO: configure output dir with argparse
        nodecount = 0
        #for nodelist in self.walk():
        for nodelist in self.walkDictStructure():
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
            logger.debug(f"{nodecount}: {node._output_name}")
            tt.toTSV(outputDirectory, nodecount)
            nodecount += 1

    def walk(self):
        # TBD: walk in the expected order (root to leaves)
        for node in self._nodes:
            yield self._nodes[node]

    def walkDictStructure(self):
        for node in self.gen3schema.walk():
            if node.name in self._nodes:
                yield self._nodes[node.name]