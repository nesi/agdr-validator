import os
from agdrvalidator.parser.dictionary.gen3parser import Gen3 as Gen3Dictionary
from agdrvalidator.schema.node.gen3node import Gen3 as Gen3Node

DATADIR = "test/data"
DICTIONARY = "gen3.nesi_2022_09_23.json"

def test_reading_dictionary_children_set_properly():
    d = os.path.join(DATADIR, DICTIONARY)
    print("dictionary: ", d)
    g3d = Gen3Dictionary(d)
    schema = g3d.parse()
    #print("received nodes:")
    #print(schema.nodes.keys())
    #print("Children of Program:")
    #for child in schema.nodes["program"].getChildren():
    #    print(f"\t{child.name}")

    #print("Children of Project:")
    #for child in schema.nodes["project"].getChildren():
    #    print(f"\t{child.name}")

    #print("parents of Project:")
    #for parent in schema.nodes["project"].getParents():
    #    # this returns links, not nodes
    #    # inconsistent with getChildren()
    #    #print(f"\t{parent.node_id}")
    #    print(f"\t{parent.name}")

    #print("Children of Experiment:")
    #for child in schema.nodes["experiment"].getChildren():
    #    print(f"\t{child.name}")

    assert set([ x.name for x in schema.nodes["program"].getChildren()]) == set(["project"])
    assert set([ x.name for x in schema.nodes["project"].getChildren() ]) == set(["experiment","indigenous_governance", "publication", "keyword", "acknowledgement", "bc_tk", "core_metadata_collection"])

    assert set([ x.name for x in schema.nodes["bc_tk"].getChildren()]) == set([])
    assert set([ x.name for x in schema.nodes["acknowledgement"].getChildren()]) == set([])
    assert set([ x.name for x in schema.nodes["keyword"].getChildren()]) == set([])
    assert set([ x.name for x in schema.nodes["publication"].getChildren()]) == set(["acknowledgement", "keyword"])
    
    assert set([ x.name for x in schema.nodes["indigenous_governance"].getChildren()]) == set([])
    assert set([ x.name for x in schema.nodes["experiment"].getChildren()]) == set(["publication", "metagenome", "organism", "population_genomics", "sample", "experimental_metadata"])

    assert set([ x.name for x in schema.nodes["metagenome"].getChildren()]) == set(["sample"])
    assert set([ x.name for x in schema.nodes["organism"].getChildren()]) == set(["sample"])
    assert set([ x.name for x in schema.nodes["population_genomics"].getChildren()]) == set(["sample"])


    assert set([ x.name for x in schema.nodes["sample"].getChildren()]) == set(["aliquot"])
    assert set([ x.name for x in schema.nodes["aliquot"].getChildren()]) == set(["read_group"])
    assert set([ x.name for x in schema.nodes["read_group"].getChildren()]) == set(["processed_file", "raw", "read_group_qc"])

    assert set([ x.name for x in schema.nodes["processed_file"].getChildren()]) == set(["aligned_reads_index", "read_group_qc"])
    assert set([ x.name for x in schema.nodes["raw"].getChildren()]) == set(["read_group_qc"])

    assert set([ x.name for x in schema.nodes["core_metadata_collection"].getChildren()]) == set(["raw", "analysis", "analysis_method", "experimental_metadata", "processed_file", "aligned_reads_index"])
    assert set([ x.name for x in schema.nodes["analysis"].getChildren()]) == set([])
    assert set([ x.name for x in schema.nodes["analysis_method"].getChildren()]) == set([])
    assert set([ x.name for x in schema.nodes["experimental_metadata"].getChildren()]) == set([])
    assert set([ x.name for x in schema.nodes["aligned_reads_index"].getChildren()]) == set([])
    #qc

def test_reading_dictionary_parents_set_properly():
    d = os.path.join(DATADIR, DICTIONARY)
    print("dictionary: ", d)
    g3d = Gen3Dictionary(d)
    schema = g3d.parse()

    assert schema.nodes["program"].getParents() == []
    assert set([ x.name for x in schema.nodes["project"].getParents() ]) == set(["program"])

    assert set([ x.name for x in schema.nodes["bc_tk"].getParents()]) == set(["project"])
    assert set([ x.name for x in schema.nodes["acknowledgement"].getParents()]) == set(["project", "publication"])
    assert set([ x.name for x in schema.nodes["keyword"].getParents()]) == set(["project", "publication"])
    assert set([ x.name for x in schema.nodes["publication"].getParents()]) == set(["project", "experiment"])
    
    assert set([ x.name for x in schema.nodes["indigenous_governance"].getParents()]) == set(["project"])
    assert set([ x.name for x in schema.nodes["experiment"].getParents()]) == set(["project"])

    assert set([ x.name for x in schema.nodes["metagenome"].getParents()]) == set(["experiment"])
    assert set([ x.name for x in schema.nodes["organism"].getParents()]) == set(["experiment"])
    assert set([ x.name for x in schema.nodes["population_genomics"].getParents()]) == set(["experiment"])
 
    assert set([ x.name for x in schema.nodes["experimental_metadata"].getParents()]) == set(["core_metadata_collection", "experiment"])

    assert set([ x.name for x in schema.nodes["sample"].getParents()]) == set(["metagenome", "organism", "population_genomics", "experiment"])
    assert set([ x.name for x in schema.nodes["aliquot"].getParents()]) == set(["sample"])
    assert set([ x.name for x in schema.nodes["read_group"].getParents()]) == set(["aliquot"])

    assert set([ x.name for x in schema.nodes["processed_file"].getParents()]) == set(["read_group", "core_metadata_collection"])
    assert set([ x.name for x in schema.nodes["raw"].getParents()]) == set(["read_group", "core_metadata_collection"])

    assert set([ x.name for x in schema.nodes["core_metadata_collection"].getParents() ]) == set(["project"])
    assert set([ x.name for x in schema.nodes["analysis"].getParents()]) == set(["core_metadata_collection"])
    assert set([ x.name for x in schema.nodes["analysis_method"].getParents()]) == set(["core_metadata_collection"])
    assert set([ x.name for x in schema.nodes["experimental_metadata"].getParents()]) == set(["core_metadata_collection", "experiment"])
    assert set([ x.name for x in schema.nodes["aligned_reads_index"].getParents()]) == set(["core_metadata_collection", "processed_file"])


def test_parse_properties_publication():
    d = os.path.join(DATADIR, DICTIONARY)
    print("dictionary: ", d)
    g3d = Gen3Dictionary(d)
    #schema = g3d.parse()
    raw_publication = g3d._gen3Dictionary["publication.yaml"]
    node = Gen3Node(raw_publication, raw_publication["id"])
    required = []
    node.parse_properties(raw_publication["properties"], required, g3d._schema._terms, g3d._schema._definitions, g3d._schema._settings)



def test_parse_some_nodes_visual_inspection():
    # read in dictionary (metadata structure)
    d = os.path.join(DATADIR, DICTIONARY)
    print("dictionary: ", d)
    g3dict = Gen3Dictionary(d)
    schema = g3dict.parse()
    #g3d.pprint()

    # now do example of getting Project out of dictionary
    print("----")
    print("nodes:")
    for node in schema.nodes:
        print(f"\t{node}")
    print("----")
    print("Project properties:")
    for prop in schema.nodes["project"]._properties:
        print(f"\tname: {prop._name}\ttype: {prop._type}\t required: {prop._isRequired}\t pattern: {prop._pattern}")

    print("----")
    print("Experiment properties:")
    for prop in schema.nodes["experiment"]._properties:
        print(f"\tname: {prop._name}\ttype: {prop._type}\t required: {prop._isRequired}\t pattern: {prop._pattern}")

    print("----")
    print("Organism properties:")
    for prop in schema.nodes["organism"]._properties:
        print(f"\tname: {prop._name}\ttype: {prop._type}\t required: {prop._isRequired}\t pattern: {prop._pattern}")

    print("----")
    print("Metagenome properties:")
    for prop in schema.nodes["metagenome"]._properties:
        print(f"\tname: {prop._name}\ttype: {prop._type}\t required: {prop._isRequired}\t pattern: {prop._pattern}")

    print("----")
    print("Processed file properties:")
    for prop in schema.nodes["processed_file"]._properties:
        print(f"\tname: {prop._name}\ttype: {prop._type}\t required: {prop._isRequired}\t pattern: {prop._pattern}")