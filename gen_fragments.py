#!/usr/bin/env python
import os, sys
import json, glob

def read_idioms(idioms_dir: str):
    idioms = {}
    for file_path in glob.glob(os.path.join(idioms_dir, "*.json")):
        d = json.load(open(file_path))
        idioms[d["id"]] = d
    return idioms

def make_fragment(source: dict, mapping: dict, idioms: dict):
    instances = list(filter(lambda x: x["id"] in mapping["instances"], source["instances"]))
    default_inferences = list(filter(lambda x: x in mapping["default_inferences"], source["default_inferences"]))
    edges = find_edges(source, instances, default_inferences)
    node_ids = set(sum([[e["from"], e["to"]] for e in edges], []))
    nodes = list(filter(lambda x: x["id"] in node_ids, source["nodes"]))
    variable_keys = set(sum([n["args"] for n in nodes], []))
    variables = {k:source["variables"][k] for k in variable_keys}
    check_whether_node_mapping_consistent(source, mapping, node_ids)
    return {"nodes":nodes, "edges":edges, "variables":variables,
            "instances": instances, "default_inferences": default_inferences}

def find_edges(source: dict, instances: list, default_inferences: list):
    edges = find_edges_from_instances(source, instances) +\
            find_edges_from_default_inferences(source, default_inferences)
    edges.sort(key=lambda x: x["id"])
    return edges

def find_edges_from_instances(source: dict, instances: list):
    edges_from_to = []
    for i in instances:
        idiom = idioms[i["idiom_id"]]
        for idiom_edge in idiom["edges"]:
            edges_from_to.append( (i["node_map"][idiom_edge["from"]], i["node_map"][idiom_edge["to"]]) )
    return list(filter(lambda x: (x["from"], x["to"]) in edges_from_to, source["edges"]))

def find_edges_from_default_inferences(source: dict, default_inferences: list):
    return list(filter(lambda x: x["id"] in default_inferences, source["edges"]))

def check_whether_node_mapping_consistent(source: dict, mapping: dict, node_ids: set):
    if not "nodes" in mapping:
        return
    #nodes = list()
    node_ids_from_mapping = set([n["id"] for n in filter(lambda x: x["id"] in mapping["nodes"], source["nodes"])])
    diff = node_ids ^ node_ids_from_mapping
    if len(diff) > 0:
        raise Exception("incommon nodes found: %s" % ",".join(list(diff)))
    return

if __name__ == "__main__":
    idioms = read_idioms("idiom")
    for mapping_path in glob.glob(os.path.join("graph", "fragment", "mapping", "*.json")):
        mappings = json.load(open(mapping_path))
        sources = {}
        for fragment_id, mapping in mappings.items():
            source_id = fragment_id[:4]
            if not source_id in sources:
                sources[source_id] = json.load(open(os.path.join("graph", "%s.json" % source_id)))
            print("generating %s" % fragment_id)
            fragment = make_fragment(sources[source_id], mapping, idioms)
            with open(os.path.join("graph", "fragment", "%s.json" % fragment_id), "wt") as f:
                json.dump(fragment, f)
