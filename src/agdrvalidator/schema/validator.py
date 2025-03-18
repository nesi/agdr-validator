import pprint
from enum import Enum

import numpy as np
from alive_progress import alive_bar

from agdrvalidator import *
from agdrvalidator.schema.agdrschema import AGDR as AGDRSchema
from agdrvalidator.schema.base import Schema as Schema
from agdrvalidator.schema.gen3schema import Gen3 as Gen3Schema
from agdrvalidator.schema.node.gen3node import RequiredType as RequiredType
from agdrvalidator.utils import logger

logger = logger.setUp(__name__)

def getParentUniqueIdProperties(node_name):
    # TODO: I may have misunderstood what UniqueId is -- maybe it's not the same as submitter_id value
    #print(f"node_name: {node_name}")
    props = ["project_id"] # just some default
    if node_name == "publication":
        props = ["project_id"]
    if node_name == "external_dataset":
        props = ["projects.code"]
    if node_name == "core_metadata_collection":
        props = ["projects.code"]
    if node_name == "dataset":
        props = ["projects.code"]
    if node_name == "contributor":
        props = ["dataset.submitter_id"] # TBD: add external_dataset.submitter_id
    if node_name == "experiment":
        props = ["dataset.submitter_id"]
    if node_name == "metagenome":
        props = ["experiment.submitter_id"]
    if node_name == "genome":
        props = ["experiment.submitter_id"]
    if node_name == "sample":
        props = ["genomes.submitter_id", "metagenomes.submitter_id"]
    if node_name == "genomics_assay":
        props = ["sample.submitter_id"]
    if node_name == "processed_file":
        props = ["genomics_assay.submitter_id"]
    if node_name == "raw":
        props = ["genomics_assay.submitter_id"]
    if node_name == "supplementary_file":
        props = ["experiment.submitter_id"]
    return props


ValidationError = Enum('ValidationError',
    [
        "INFO",
        "WARNING",
        "ERROR"
    ])

class ValidationEntry(object):
    def __init__(self, v_type, message):
        self.validation_error_type = v_type # ValidationError
        self.message = message # string describing the error


class Dataset(object):
    '''
    this is intended to be a recursive data structure
    i.e. each child is a dataset, each parent is a dataset

    Note this is not a "Dataset" in the custom AGDR dictionary, but 
    a collection of nodes that are related to each other in the
    Gen3 schema. 

    the structure means lookup is O(n) for each node, because 
    each node type will be represented as a list of datasets
    inside the AGDRValidator class.

    As of Python 3.7, regular dicts are guaranteed to be ordered, so 
    the order of the children and parents lists is guaranteed to be
    in the same order as nodes in Gen3Schema.walk(), i.e. the correct 
    order for a sensible validation report. See the AGDRValidation class 
    implementation for more details.
    '''
    def __init__(self, key, value):
        self.name = key 
        self.metadata = value 
        self.children = []
        self.parents = []


    def addChild(self, child):
        logger.debug(f"adding child {child.name} to {self.name}")
        for c in self.children:
            if c.metadata.uniqueId() == child.metadata.uniqueId():
                return
        self.children.append(child)


    def addParent(self, parent):
        logger.debug(f"adding parent {parent.name} to {self.name}")
        for p in self.parents:
            if p.metadata.uniqueId() == parent.metadata.uniqueId():
                return
        self.parents.append(parent)
        parent.addChild(self)

    def __repr__(self):
        result = {}
        result["name"] = self.name
        result["metadata"] = self.metadata.uniqueId()
        result["children"] = [(x.name, x.metadata.uniqueId()) for x in self.children]
        result["parents"] = [(x.name, x.metadata.uniqueId()) for x in self.parents]
        return str(result)
    

class AGDRValidator(Schema):
    def __init__(self, gen3schema, agdrschema, outputfile=None):
        self._gen3schema = gen3schema # contains dictionary structure
        self._agdrschema = agdrschema # contains metadata
        self._root = agdrschema.getRootNode() # only one project node
        self._outputfile = outputfile # where to write the report, None for stdout

        self._metadata_graph = {} # "list" of Dataset objects

        # node type -> submitter_id -> list of ValidationEntry objects
        # dictionary -> dictionary -> list
        # there will be no duplicated submitter IDs in this collection;
        # if there were any, it is recorded as a validation error 
        # for a single entry only
        self._node_validation_errors = {} 
        self._validation_errors_detected = False

        self._schemasRelated = False
        self._relateSchemas() # build graph structure


    def showMetadataGraph(self):
        '''
        print out all node instances and their children
        (data here are represented tabularly, rather than in a graph,
        where there is an entry for each node type from the metadata 
        input, along with its direct children. Some entries
        may be duplicated across different tables, represented as 
        dictionary values).
        '''
        # this code explodes and I'm not sure why 
        # just don't call it for now
        #
        # it also prints by alphabetic order of dictionary keys,
        # which is not the most helpful
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(self._metadata_graph)

    def _addNodeToGraphData(self, node):
        '''
        used to populate the metadata graph, which internally is 
        implemented as a dictionary relating node names to lists of
        instances, together with each node's children

        this is a semi-recursive data structure and may duplicate data.
        this representation is not a requirement, and may be represented
        in whichever way is most convenient for a subsequent validator
        implementation.
        '''
        logger.debug(f"___adding node {node.name} to metadata graph___")
        # TODO: currently, not clear if I want to use
        # node.name or node.gen3name
        if node.name not in self._metadata_graph:
            # add the node to the graph for the first time
            logger.debug(f"adding node {node.name} to metadata graph")
            self._metadata_graph[node.name] = [node]
        else:
            # check if the node is already in the list
            node_id = node.metadata.getProperty("submitter_id")
            logger.debug(f"checking if node {node.name} is already in metadata graph")
            exists_already = False
            for n in self._metadata_graph[node.name]:
                n_id = n.metadata.getProperty("submitter_id")
                if n_id == node_id:
                    exists_already = True
            else:
                if not exists_already:
                    self._metadata_graph[node.name].append(node)

    def _bulkAddNodesToGraphData(self, node_type, nodes):
        '''
        add multiple nodes to the metadata graph at once
        '''
        self._metadata_graph[node_type] = nodes

    def _addChildToNodeInGraphData(self, node, child):
        '''
        not actually needed
        '''
        pass

    def _bulkAddParentsToNodesInGraphData(self, node_list, node_type, progress_bar, progress_count, progress_total):
        '''
        This function does most of the work to validate a schema. In order 
        to connect a node to its parent, it must first find the parent
        in the metadata graph. It does this by looking for a match between
        the uniqueId of the parent and the uniqueId of the node. If a match
        is found, the node is connected to the parent. If no match is found,
        validation errors are generated and collected, and the 
        node connection algorithm continues until all instances of nodes
        provided by the spreadsheet input are visited.

        This function does bulk operations for all nodes of a specific 
        node type. It was rewritten for bulk operation in order to 
        alleviate performance issues for large datasets.
        '''
        connected_node_names = set()
        for parent_type in node_type.getParents():
            if parent_type.name.lower() == "program":
                continue
            # get list of all nodes of parent_type that have been iterated over
            # these are actual metadata values
            key = parent_type.name
            potential_parents = []
            #print(f"key: {key}")
            if key in self._metadata_graph:
                potential_parents = self._metadata_graph[key]
            lookup_props = [] 
            #print(f"all potential parents: {potential_parents}")
            if len(node_list) > 0:
                lookup_props = getParentUniqueIdProperties(node_list[0].name)
                #print(f"lookup_props: {lookup_props}")
            else:
                logger.debug(f"no nodes of type {node_type.name} found in metadata graph")
            for pp in potential_parents:
                #print(f"potential parent: {pp.metadata.uniqueId()}")
                # check if parent's primary key matches any of the children 
                # (this way, we loop through the parents only once)
                for lookup_prop in lookup_props:
                    for node in node_list:
                        if not node.metadata.getProperty(lookup_prop):
                            logger.info(f"no property {lookup_prop} found in node {node.name}")
                            continue
                        if node.metadata.getProperty(lookup_prop).get_value() == np.nan:
                            print(f"property {lookup_prop} is nan in node {node.name}")
                            continue
                        #print(f"node: {node.metadata.uniqueId()}")
                        #print(f"lookup_prop: {lookup_prop}")
                        #print(f"node metadata: {node.metadata.getProperty(lookup_prop)}")
                        #print(f"node metadata value: {node.metadata.getProperty(lookup_prop).get_value()}")
                        #print(f"uniqueId: {pp.metadata.uniqueId().lower()} == {node.metadata.getProperty(lookup_prop).get_value().lower()}")
                        if pp.metadata.uniqueId().lower().strip() == str(node.metadata.getProperty(lookup_prop).get_value()).lower().strip():
                            node.addParent(pp)
                            pp.addChild(node)
                            node_id = node.metadata.getProperty('submitter_id').get_value() 
                            progress_bar(( progress_count + len(connected_node_names) )/ progress_total)
                            connected_node_names.add(node_id)
                    #for node_type in node_list: # AGDRNode - could have multiple rows
                    #    for node in node_type:  # AGDRRow - represents an instance of a node
                    #        if pp.metadata.uniqueId().lower() == node.metadata.getProperty(lookup_prop).get_value().lower():
                    #            node.addParent(pp)
                    #            pp.addChild(node)
                    #            node_id = node.metadata.getProperty('submitter_id').get_value() 
                    #            progress_bar(( progress_count + len(connected_node_names) )/ progress_total)
                    #            connected_node_names.add(node_id)
        else:
            orphans = []
            for node in node_list:
                if node.name.lower() == "project":
                    continue
                if node.metadata.getProperty('submitter_id').get_value() not in connected_node_names:
                    orphans.append(node)

            orphan_count = 0
            reported_errors = set()
            for node in orphans:
                for plink in node.metadata.gen3node.getParentLinks():
                    node_id = node.metadata.getProperty('submitter_id').get_value()
                    entry = None
                    msg = None
                    if plink.requiredtype == RequiredType.OPTIONAL:
                        msg = f"INFO:\tno optional link found connecting parent [{plink.node_id}] link to child [{node.name}:{node_id}]"
                        logger.debug(msg)
                        entry = ValidationEntry(ValidationError.INFO, msg)

                        validationError = False
                        # TODO: check if verbose validation is enabled, and if so, warn about optional links
                    else:
                        msg = f"ERROR:\tno REQUIRED link found connecting parent [{plink.node_id}] link to child [{node.name}:{node_id}]"
                        logger.info(msg)
                        entry = ValidationEntry(ValidationError.ERROR, msg)

                    # self._node_validation_errors:
                    # node type -> submitter_id -> list of ValidationEntry objects
                    if node.name not in self._node_validation_errors:
                        self._node_validation_errors[node.name] = {}
                    if node_id not in self._node_validation_errors[node.name]:
                        self._node_validation_errors[node.name][node_id] = []
                    if msg not in reported_errors:
                        self._node_validation_errors[node.name][node_id].append(entry)
                    reported_errors.add(msg)

                orphan_count += 1
                progress_bar(( orphan_count + progress_count + len(connected_node_names) )/ progress_total)

        return progress_count + len(node_list)


#######

#not called anywhere for the moment ???
    # def _addParentToNodeInGraphData(self, node, parent):
    #     '''
    #     This function does most of the work to validate a schema. In order 
    #     to connect a node to its parent, it must first find the parent
    #     in the metadata graph. It does this by looking for a match between
    #     the uniqueId of the parent and the uniqueId of the node. If a match
    #     is found, the node is connected to the parent. If no match is found,
    #     validation errors are generated and collected, and the 
    #     node connection algorithm continues until all instances of nodes
    #     provided by the spreadsheet input are visited.
    #     '''
    #     # node is a Dataset type
    #     # parent is a Gen3Node type
    #     logger.debug("\n\n...")
    #     logger.debug(f"adding parent __{parent.name}__ to node ___{node.name}___")
    #     key = parent.name
    #     if key not in self._metadata_graph:
    #         # this is OK, example if node is sample, and it could have one of 
    #         # several parents (metagenome, organism, population genomics)
    #         #
    #         # When this function is called for a particular node, it is known
    #         # that all of its parents have been visited, and therefore
    #         # will have been added to the metadata graph. If a parent is not
    #         # found, it is either because the parent is not required, or 
    #         # there is invalid metadata provided as input to the program.
    #         #
    #         # If there is an error, it will be detected when an orphaned node
    #         # tries to find its parents in the graph.
    #         logger.info(f"parent {key} not found in metadata graph for child {node.name}")
    #         return
    #     potential_parents = self._metadata_graph[key]
    #     logger.debug(f"number of potential parents: {len(potential_parents)}")
    #     logger.debug("------------------------------------------------------")
    #     logger.debug(f"current properties of {node.name}:")
    #     logger.debug("------------------------------------------------------")
    #     logger.debug("\t---------------gen3-----------------")
    #     for prop in node.metadata.getGen3Node()._properties:
    #         logger.debug(f"\t{prop._name}: \t {node.metadata.getProperty(prop._name)}")
    #     logger.debug("\t---------------excel----------------")
    #     for prop in node.metadata._properties:
    #         logger.debug(f"\t{prop._name}: \t {node.metadata.getProperty(prop._name)}")
    #     logger.debug("------------------------------------------------------\n\n")
    #     lookup_props = getParentUniqueIdProperties(node.name)
    #     matchFound = False
    #     pp = None # define here so it's in scope later for disconnected nodes
    #     for pp in potential_parents:
    #         logger.debug(f"parent: {node.name} {node.metadata.getProperty(lookup_props[0])}")
    #         logger.debug(f"potential parent: {pp.name} {pp.metadata.getProperty('submitter_id')}")
    #         logger.debug(f"+_+_+_+_____lookup prop: {lookup_props[0]}")
    #         logger.debug(f"all properties of {key}:")
    #         # from the data dictionary input
    #         logger.debug("\t---------------gen3-----------------")
    #         for prop in pp.metadata.getGen3Node()._properties:
    #             logger.debug(f"\t{prop._name}")
    #             logger.debug(f"\t{pp.metadata.getProperty(prop._name)}\n\n")
    #         # from the spreadsheet input
    #         #for prop in pp.metadata._properties:
    #         #    print(f"\t{prop._name}")
    #         #    print(f"\t{pp.metadata.getProperty(prop._name)}")
    #         #    print()
    #         for lookup_prop in lookup_props:
    #             if pp.metadata.uniqueId().lower().strip() == node.metadata.getProperty(lookup_prop).get_value().lower().strip():
    #                 logger.debug(f"______setting parent...______")
    #                 node.addParent(pp)
    #                 pp.addChild(node)
    #                 matchFound = True
    #                 break
    #             else:
    #                 logger.debug(f"no match: {pp.metadata.uniqueId()} != {node.metadata.getProperty(lookup_prop).get_value()}")
    #     else:
    #         if not matchFound:
    #             # TODO: I can start adding validation error objects from here
    #             # rather than iterating through again, I am trying to link up the graph 
    #             # and it fails here, so no need to iterate through again
    #             #
    #             # actually, I want to distinguish between optional and required links
    #             # I can do that here though
    #             #
    #             # note also that gen3 doesn't really model child links
    #             # so, just need to look at parent links, and bob's your uncle

    #             validationError = True
    #             for plink in node.metadata.getGen3Node().getParentLinks():
    #                 if pp and str(plink.node_id).lower().strip() == str(pp.name).lower().strip():
    #                     node_id = node.metadata.getProperty('submitter_id').get_value()
    #                     entry = None
    #                     if plink.requiredtype == RequiredType.OPTIONAL:
    #                         msg = f"INFO:\tno optional link found connecting parent [{plink.node_id}] link to child [{node.name}:{node_id}]"
    #                         logger.debug(msg)
    #                         entry = ValidationEntry(ValidationError.INFO, msg)

    #                         validationError = False
    #                     else:
                            
    #                         msg = f"ERROR:\tno REQUIRED link found connecting parent [{plink.node_id}] link to child [{node.name}:{node_id}]"
    #                         logger.error(msg)
    #                         entry = ValidationEntry(ValidationError.ERROR, msg)

    #                     # self._node_validation_errors:
    #                     # node type -> submitter_id -> list of ValidationEntry objects
    #                     if node.name not in self._node_validation_errors:
    #                         self._node_validation_errors[node.name] = {}
    #                     if node_id not in self._node_validation_errors[node.name]:
    #                         self._node_validation_errors[node.name][node_id] = []
    #                     self._node_validation_errors[node.name][node_id].append(entry)

    #                     break


    def findNode(self, node_name, submitter_id):
        '''
        find parent node in self._metadata_graph by 
        doing a search for (node_name, submitter_id) pair

        we could set up a graph structure, but linear search 
        should be fine for individual datasets (single 
        project / excel file input))
        '''

        logger.debug("looking for nodes in metadata graph")
        for node in self._metadata_graph:
            logger.debug(f"node: {node.name}")
            if node.name == node_name and node.metadata.submitter_id == submitter_id:
                return node 
        raise AgdrNotFoundException(f"Node {node_name} with submitter_id {submitter_id} not found in metadata graph.")


    def _findParents(self, child):
        '''
        ??? not used
        '''
        parents = []
        node_name = child.getGen3NodeName()
        submitter_id = child.getProperty("submitter_id")
        for node in self._metadata_graph:
            for child in node.children:
                if child.name == node_name and child.metadata.submitter_id == submitter_id:
                    parents.append(node)
        return parents


    def _relateSchemas(self):
        '''
        connect nodes from the agdrschema, e.g. nodes to their 
        parents and children

        it's not only about the dictionary structure, but also 
        matching the correct parent/child submitter ids
        '''
        if self._schemasRelated:
            return
        self._schemasRelated = True

        logger.debug(f"root: {self._root.getGen3NodeName()}")
        logger.debug("parents:")
        logger.debug(f"\t {[x.name for x in self._root.getGen3Node().getParents()]}")
        logger.debug("children:")
        logger.debug(f"\t {[x.name for x in self._root.getGen3Node().getChildren()]}")

        nodeCount = self._agdrschema.getNodeCount() 
        progressCount = 0
        # use manual mode because we have a slight overcount and go over 100% with auto mode
        #with alive_bar(title="Building node graph", stats=False, manual=True) as bar:
        with alive_bar(title="\tBuilding metadata graph ", stats=True, manual=True) as bar:
            # node order is tightly coupled to walk() being implemented 
            # correctly in the self._gen3schema. 
            # Correctly means walking from the root to the leaves such 
            # that all parents are visited before their children 
            # (nontrivial when there are multiple parents).
            for node_type in self._gen3schema.walk():
                logger.info(f"walking.... node type: {node_type.name}")
                metadata = None
                try:
                    metadata = self._agdrschema.findNode(node_type.name)
                except Exception as e:
                    # program node not modelled
                    # also, not all nodes will be represented in a dataset (excel input)
                    logger.debug(e)
                    logger.debug(f"no metadata found for node {node_type.name}")
                    continue
                metadata_to_add = []
                for md in metadata:
                    ds = Dataset(node_type.name, md)
                    #self._addNodeToGraphData(ds) # avoid this due to performance hit
                    metadata_to_add.append(ds)
                else:
                    logger.debug("____bulk adding nodes to graph data____")
                    self._bulkAddNodesToGraphData(node_type.name, metadata_to_add)
                    progressCount = self._bulkAddParentsToNodesInGraphData(metadata_to_add, node_type, bar, progressCount, nodeCount)
            bar(1.00)

    def getRootNode(self):
        '''
        return the root node of the agdr schema. This is the 
        metadata-containing schema
        '''
        return self._root

    def walk(self):
        '''
        walk the graph structure, for only nodes containing metadata

        ideally generating TSVs would happen at the validator level,
        but due to an earlier implementation flaw, this was implemented
        inside the AGDRSchema class. walk() would then be used to 
        generate TSVs for each node in the graph structure.

        As of Python 3.7, regular dicts are guaranteed to be ordered, so 
        iterating over self._metadata_graph will return nodes in the
        same order they were visited by walking the Gen3Schema, i.e.
        something reasonably cogent to the researcher or support staff 
        working on metadata ingest.
        '''
        #for node_type in self._metadata_graph:
        #    print("node type:")
        #    print(node_type)
        #    return node_type
        #self.showMetadataGraph()
        #print(self._metadata_graph.keys())
        for node_type in self._metadata_graph:
            yield(node_type)

    def validate(self, verbosity=1):
        '''
        - schema level   -- check if the graph structure is valid 
          (each node has expected nodes and children)
        - node   level   -- check that each node has required properties 
        - property level -- check that each property is valid
        '''
        if verbosity <= 0:
            print("NO VALIDATION PERFORMED. \tDid you forget the -v option?")
            return
        verbose = verbosity > 1
        print("PERFORMING VALIDATION...")
        if self._outputfile:
            print(f"\tFILE:\t\t{self._outputfile}")
        self._validateSchema(verbose)
        print("...VALIDATION COMPLETE")


    def _report_complete(self):
        msg = ""
        if not self._validation_errors_detected:
            msg = "\tNO ERRORS DETECTED"
        if self._outputfile:
            with open(self._outputfile, "a", encoding="utf-8") as f:
                f.write(f"{msg}\n")
        else:
            print(msg)


    
    def _report_header(self, node_type):
        msg = f"\t{node_type.upper()}"
        if self._outputfile:
            with open(self._outputfile, "a", encoding="utf-8") as f:
                f.write(node_type.upper())
                f.write("\n")
        else:
            print(msg)

    
    def _report_node(self, validation_entry):
        if self._outputfile:
            with open(self._outputfile, "a", encoding="utf-8") as f:
                f.write(f"\t{validation_entry.message}")
                f.write("\n")
        else:
            print(f"\t\t{validation_entry.message}")
            pass

    #def _report_node_properties(self, node_type, node, verbose):
    #    #isValid, reasons = node.metadata.validate(verbose)
    #    isValid, reasons = node.metadata.validate()
    #    if not isValid:
    #        self._validation_errors_detected = True
    #        if self._outputfile:
    #            with open(self._outputfile, "a", encoding="utf-8") as f:
    #                f.write(f"{node_type} [{node.metadata.getProperty('submitter_id').get_value()}]\n")
    #                for reason in reasons:
    #                    f.write(f"\t{reason}\n")
    #                    f.write(f"\t\t{reasons[reason]}\n")
    #        else:
    #            print(f"{node_type} [{node.metadata.getProperty('submitter_id').get_value()}]")
    #            for reason in reasons:
    #                print(f"\t{reason}")
    #                print(f"\t\t{reasons[reason]}")
    #        # will in turn call property-based validation

    ## does not work
    #def _report_node_properties(self, node_type, node, verbose):
    #    #isValid, reasons = node.metadata.validate(verbose)
    #    isValid, reasons = node.metadata.validate()
    #    if not isValid:
    #        self._validation_errors_detected = True
    #        if self._outputfile:
    #            with open(self._outputfile, "a", encoding="utf-8") as f:
    #                # Write the node header line once
    #                f.write(f"{node_type} [{node.metadata.getProperty('submitter_id').get_value()}]\n")
    #                
    #                # Iterate through each reason and write it as a complete message
    #                for message in reasons:
    #                    if message:
    #                        f.write(f"\t{message} - Location: {node.metadata.location}\n")  # Adjusting to include location info
    #        else:
    #            print(f"{node_type} [{node.metadata.getProperty('submitter_id').get_value()}]")
    #            for message in reasons:
    #                if message:
    #                    print(f"\t{message} - Location: {node.metadata.location}")
        
    # issue with multiple lines
    def _report_node_properties(self, node_type, node, verbose):
        #isValid, reasons = node.metadata.validate(verbose)
        isValid, reasons = node.metadata.validate()
        if not isValid:
            self._validation_errors_detected = True
            if self._outputfile:
                with open(self._outputfile, "a", encoding="utf-8") as f:
                    # Write the node header line
                    f.write(f"{node_type} [{node.metadata.getProperty('submitter_id').get_value()}]\n")

                    # Iterate through each reason in the list and write it
                    for message in reasons:
                        if message:  # Only write non-empty messages
                            f.write(f"\t{message}\n")
            else:
                print(f"{node_type} [{node.metadata.getProperty('submitter_id').get_value()}]")
                for message in reasons:
                    if message:
                        print(f"\t{message}")
        

    
    def _validateSchema(self, verbose, outputfile=None):
        '''
        This is a schema level validation, checking that the graph
        structure is valid. 

        self._relateSchemas() builds a graph structure of the metadata
        by relating instances of nodes, provided by researchers, to 
        their corresponding nodes in the Gen3 Schema (data dictionary).
        self._relateSchemas() connects nodes to their parents, which is
        how it is represented in an arbitrary data dictionary structure. 
        (It is not necessary to connect nodes to their children).

        self._addParentToNodeInGraphData() is the method that connects
        nodes to their parents, and it is here that validation errors
        are collected. It leverages the walk() implementation in the 
        Gen3 Schema, which is implemented generically, to visit all 
        parents, including optional parents, before visiting their
        children. Because validation of a schema can be done by checking
        each node's parent links, validation can be done in a single
        pass through the graph structure.

        This method has a minimal implementation, and is defined here 
        largely to make the validation algorithm more clear where this 
        function is called.
        '''
        #print("called _validateSchema")
        #print(f"metadata graph: {self._metadata_graph}")

        with alive_bar(len(self._metadata_graph), title="\tValidating schema       ") as bar:
            for node_type in self.walk():
                submitter_ids = set()
                for node in self._metadata_graph[node_type]:
                    #print(f"node: {node}")
                    submitter_id = None
                    if node.name == "project":
                        submitter_id = node.metadata.getProperty("code").get_value()
                    else:
                        submitter_id = node.metadata.getProperty("submitter_id").get_value()
                    if submitter_id in submitter_ids:
                        node_id = submitter_id
                        msg = f"ERROR: duplicate submitter_id found for {node_type} node: {submitter_id}"
                        entry = ValidationEntry(ValidationError.ERROR, msg)
                        self._validation_errors_detected = True

                        if node.name not in self._node_validation_errors:
                            self._node_validation_errors[node.name] = {}
                        if node_id not in self._node_validation_errors[node.name]:
                            self._node_validation_errors[node.name][node_id] = []
                        self._node_validation_errors[node.name][node_id].append(entry)
                    submitter_ids.add(submitter_id)


                header_reported = False

                # report validation errors
                for node in self._metadata_graph[node_type]:
                    # schema-based validation (node connectivity)
                    #node_id = node.metadata.getProperty('submitter_id').get_value()
                    node_id = None
                    if node.name == "project":
                        node_id = node.metadata.getProperty("code").get_value()
                    else:
                        node_id = node.metadata.getProperty("submitter_id").get_value()
                    if node_type in self._node_validation_errors:
                        if node_id in self._node_validation_errors[node_type]:
                            # report any connectivity errors, like missing links or duplicate submitter ID
                            for entry in self._node_validation_errors[node_type][node_id]:
                                report = False
                                if (entry.validation_error_type == ValidationError.INFO or entry.validation_error_type == ValidationError.WARNING) and verbose:
                                    report = True
                                if entry.validation_error_type == ValidationError.ERROR or report:
                                    if not header_reported:
                                        self._report_header(node_type)
                                        header_reported = True
                                    self._validation_errors_detected = True
                                    self._report_node(entry)


                    # node-based validation (all required properties are present)
                    self._report_node_properties(node_type, node, verbose)
                bar()
            else:
                self._report_complete()