'''
@Author: Eirian Perkins

This file contains the Gen3 node class, which is used as a component 
of the Gen3 schema, which is used to represent an arbitrary Gen3 metadata 
structure. A Node is a component of a schema, which are linked together 
in a directed acyclic graph. A node is composed of properties.
'''
from agdrvalidator.utils import logger 
from agdrvalidator.schema.node.base import Node as Node
import agdrvalidator.schema.node.property.gen3property as Property
from agdrvalidator import AgdrFormatException


from enum import Enum

logger = logger.setUp(__name__)

Multiplicity = Enum('Multiplicity', 
    [
        'ONE_TO_ONE', 
        'ONE_TO_MANY', 
        'MANY_TO_ONE', 
        'MANY_TO_MANY'
    ])

LinkType = Enum("LinkType",
    [
        "PARENT",
        "CHILD"
    ])

RequiredType = Enum("RequiredType",
    [
        "REQUIRED",
        "OPTIONAL"
    ])

class Link():
    def __init__(self, node_id, multiplicity, linktype, requiredtype):
        self.node_id = node_id
        self.multiplicity = multiplicity
        self.linktype = linktype
        self.requiredtype = requiredtype
        self.isComplex = False


class ComplexLink(Link):
    # for complex links
    def __init__(self, node_id, multiplicity, linktype, requiredtype, nodes_in_subgroup, requiredtype_subgroup, exclusive_subgroup):
        super().__init__(node_id, multiplicity, linktype, requiredtype)

        self.isComplex = True
        self.nodes_in_subgroup = nodes_in_subgroup
        self.requiredtype_subgroup = requiredtype_subgroup
        self.exclusive_subgroup = exclusive_subgroup


class Gen3(Node):
    def __init__(self, structure, name):
        '''
        structure is a dictionary representing a Gen3 node ingested from JSON
        '''
        super().__init__()
        self._parentLinks = []
        self.name = name
        logger.debug(f"created node: {name}")
        self._parse_structure(structure)

        self._last_lookup_table = None
        self._properties = []

    def getProperty(self, name):
        for prop in self._properties:
            if name == prop._name:
                return prop
        return None

    def getParents(self):
        return self._parents

    def getParentLinks(self):
        return self._parentLinks

    def isParent(self, node_id):
        #raise NotImplementedError
        if self.name in [x.name for x in self._children]:
            return True
        return False

    def isChildOf(self, node):
        for parent in self._parentLinks:
            logger.debug(f"parent: {parent.node_id}")
            logger.debug(f"checking potential parent: {node.name}")
            if parent.node_id == node.name:
                return True
        return False

    def walk(self):
        for child in self.getChildren():
            yield child

    
    def getChildren(self):
        return self._children
    
    def addParent(self, parent):
        # input: Node object (parent)
        self._parents.append(parent)
        self._parents = list(set(self._parents))
    

    def addChild(self, child):
        # input: Node object (child)
        #
        # self's parents are already set 
        # addChild is called as the dictionary is parsed
        self._children.append(child)
        self._children = list(set(self._children))


    def _parse_simple(self, structure):
        multiplicity = Multiplicity[structure["multiplicity"].upper()]
        requiredtype = RequiredType.OPTIONAL
        if structure["required"]:
            requiredtype = RequiredType.REQUIRED
        linktype = LinkType.PARENT
        return Link(structure["target_type"], multiplicity, linktype, requiredtype)


    def _parse_complex(self, structure):
        is_exclusive = structure["exclusive"]
        subgroup_required = structure["required"]
        nodes_in_subgroup = [ x["target_type"] for x in structure["subgroup"] ]
        nodes = []
        for group in structure["subgroup"]:
            link = self._parse_simple(group)
            complex = ComplexLink(link.node_id, link.multiplicity, link.linktype, link.requiredtype, nodes_in_subgroup, subgroup_required, is_exclusive)
            nodes.append(complex)
        return nodes


    def _parse_structure(self, structure):
        '''
        determine parent/child relationships
        '''
        self.name = structure["id"]
        if not "links" in structure:
            raise AgdrFormatException(f"Gen3 node {self.name} does not have a parent node, and is not a root node")
        # simple case: no subgroups 
        for link in structure["links"]:
            if "target_type" in link:
                self._parentLinks.append(self._parse_simple(link))
            elif link == []:
                # program node, no parent
                pass
            else:
                # complex case: subgroups
                for node in self._parse_complex(link):
                    self._parentLinks.append(node)

    def _extract_definition_from_ref(self, lookup, ref):
        # for now: assume no recursion needed
        ref = ref.split("#")
        category = ref[0]
        key = ref[1].split("/")[-1]
        if category in lookup:
            return lookup[category][key]
        else:
            raise AgdrFormatException(f"could not find definition for {ref}")


    def _extract_definition_from_ref(self, lookup, ref):
        # for now: assume no recursion needed
        ref = ref.split("#")
        category = ref[0]
        key = ref[1].split("/")[-1]
        if category in lookup:
            return {key: lookup[category][key]}
        else:
            raise AgdrFormatException(f"could not find definition for {ref}")

    def _extract_properties_from_ref(self, ref, terms, definitions, settings, isTopLevel=True):
        '''
        extract all the referenced properties

        if any of the refs point to other definitions, 
        substitute them in
        '''
        lookup = {
            "_terms.yaml": terms,
            "_definitions.yaml": definitions,
            "_settings.yaml": settings
        }
        raw_properties = {}
        ref = ref.split("#")
        category = ref[0]
        key = ref[1].split("/")[-1]
        if category:
            self._last_lookup_table = category 
        else:
            logger.debug(f"_____________________________recursive definition: {key}_____________________________")
            category = self._last_lookup_table
        if category in lookup:
            for property in lookup[category][key]:
                logger.debug(property)
                logger.debug(key)
                if "$ref" in lookup[category][key][property]:
                    # paste in property 
                    # add it to the list of properties
                    subkey = lookup[category][key][property]["$ref"]
                    if subkey[0] == '#':
                        subkey = category + subkey
                    raw_property = self._extract_definition_from_ref(lookup, subkey)
                    logger.debug("____raw property____", raw_property)
                    if "term" in raw_property and "$ref" in raw_property["term"]:
                        term = self._extract_definition_from_ref(key, raw_property["term"]["$ref"])
                        logger.debug("____Extracted term:", term)
                        del raw_property["term"]
                        for item in term:
                            #####
                            raw_property[item] = term[item]
                    if isTopLevel:
                        raw_properties[property] = raw_property
                    else:
                        raw_properties[key] = {property: raw_property}
                else:
                    if isTopLevel:
                        raw_properties[property] = lookup[category][key][property]
                    else:
                        raw_properties[key] = {property: lookup[category][key][property]}
        else:
            raise AgdrFormatException(f"property {property} has an invalid $ref: {ref}")

        # TODO TODO TODO TODO TODO
        # TODO: extract terms from _terms.yaml
        # TODO TODO TODO TODO TODO

        return raw_properties


    def _extract_property(self, properties, property, terms, definitions, settings):
        # extraction for properties with no nesting at top level
        # there may be some nesting in properties
        key = property
        value = properties[property]
        raw_result = {}
        logger.debug(f"+++---\t:property: {key}\t{value}")

        for item in value:
            if item == "term":
                # TODO create term object
                logger.warning(f"term found in property: {key}.\tSKIPPING" )
            elif item == "$ref":
                logger.debug("~~~~ref")
                extracted = self._extract_properties_from_ref(value[item], terms, definitions, settings, isTopLevel=False)
                for prop in extracted:
                    raw_result[prop] = extracted[prop]
            elif item == "enum":
                # TODO create enum object
                raw_result["type"] = {item: value[item]}
            else:
                raw_result[item] = value[item]

        return raw_result


        
    def add_property(self, property):
        if property not in self._properties:
            self._properties.append(property)
        self._properties = sorted(self._properties, key=lambda p: p.get_name())

    def parse_properties(self, properties, required, terms, definitions, settings):
        nested_properties = []
        unnested_properties = []
        for property in properties:
            logger.debug(property)
            if property == "$ref":
                nested_properties = self._extract_properties_from_ref(properties[property], terms, definitions, settings, isTopLevel=True)
            else:
                p = self._extract_property(properties, property, terms, definitions, settings)
                unnested_properties.append({property: p})
            # still need to extract terms, but it can be skipped for the moment
        logger.debug("[__extracted properties from refs:__]")
        # there are 2 lists of properties here for debugging purposes only
        for property in nested_properties:
            #nest_prop = nested_properties
            prop = None

            # hack for collection_date
            if len(nested_properties[property]) == 1:
                logger.debug("........only one property: " + property)
                prop = list(nested_properties[property].keys())[0]

            logger.debug(f"\t:len of nest_prop: {len(nested_properties[property])}")
            logger.debug(f"\t:property___: {property}\t{nested_properties[property]}")
            if prop:
                logger.debug(f"\t:prop___: {prop}\t{nested_properties[property][prop]}")
            logger.debug("\t\t:is required?__: " + str(property in required))
            if "type" not in nested_properties[property] and "enum" not in nested_properties[property] and not prop: 
                #and prop and "oneOf" not in nested_properties[property][prop]:
                logger.debug(f"\t\t\t:skipping property: {property}")
                # e.g. if property is "id", skip it for now
                # id is system-generated
                continue
            if property == "id":
                # makes pattern application way too complicated,
                # plus gen3 adds the id field anyway
                logger.debug(f"\t\t\t:skipping property: {property}")
                continue
            # TODO TODO TODO TODO TODO
            # need to extract pattern properly
            pat = None
            #if "pattern" in nested_properties[property]:
            #    pat = nested_properties[property]["pattern"]
            #    print(f"pattern: {pat}")
            #else:
            #    #print(nested_properties[property])
            #    pass
            #if 'type' in nested_properties:
            #    pat = self.extractPattern(nested_properties['type'])
            pat = self.extractPattern(nested_properties)
            if "type" in nested_properties[property]:
                p = Property.Gen3(property, value=nested_properties[property], required=required, type=nested_properties[property]["type"], pattern=pat)
                logger.debug(f"\t\t\t:_______CASE 1________")
            elif "oneOf" in nested_properties[property]:
                p = Property.Gen3(property, value=nested_properties[property], required=required, type={"oneOf" : nested_properties[property]["oneOf"]}, pattern=pat)
                logger.debug(f"\t\t\t:_______CASE 2________")
            elif "enum" in nested_properties[property]:
                p = Property.Gen3(property, value=nested_properties[property], required=required, type={"enum" : nested_properties[property]["enum"]}, pattern=pat)
                logger.debug(f"\t\t\t:_______CASE 3________")
            elif prop:
                if "type" in nested_properties[property][prop]:
                    p = Property.Gen3(property, value=nested_properties[property][prop], required=required, type=nested_properties[property][prop]["type"], pattern=pat)
                    logger.debug(f"\t\t\t:_______CASE 4________")
                elif "oneOf" in nested_properties[property][prop]:
                    p = Property.Gen3(property, value=nested_properties[property][prop], required=required, type={"oneOf" : nested_properties[property][prop]["oneOf"]}, pattern=pat)
                    logger.debug(f"\t\t\t:_______CASE 5________")
            # create property object
            self.add_property(p)

        for property in unnested_properties:
            for key in property:
                logger.debug(f"\t:unproperty___: {key}\t{property[key]}")
                logger.debug("\t\t:is required?__: " + str(key in required))
                logger.debug(f"..........property: {property}")
                if "type" not in property[key]:
                    # e.g. if property is "id", skip it for now
                    # id is system-generated
                    continue
                pat = None
                if "pattern" in property[key]:
                    pat = property[key]["pattern"]
                p = Property.Gen3(key, value=property[key], required=required, type=property[key]["type"], pattern=pat)
                # create property object
                self.add_property(p)


    def extractPattern(self, nested_props):
        '''
        recursively search for pattern in property from the input data dictionary
        '''
        logger.debug(nested_props)
        if isinstance(nested_props, dict):
            if "pattern" in nested_props:
                logger.debug("found pattern:")
                logger.debug(nested_props["pattern"])
                return nested_props["pattern"]
            for key in nested_props:
                extraction = self.extractPattern(nested_props[key])
                if extraction:
                    logger.debug(f"found pattern: {extraction}")
                    return extraction
        else:
            return None
