#!/usr/bin/env python
import os, sys
import json, glob
from collections import Counter

PREDICATES_ARGNUMS = {
    "bring_about": 1,# "not_bring_about": 1,
    "acceptable": 1, "unacceptable": 1,
    "lead_to": 2, "means_to": 2, "have_higher_priority_for": 2,
    "honest": 1, "assert": 2, "familiar_with": 2, "authority_over": 2,
    "follow": 2, "violate": 2,
    "mean": 2, "reason_enough": 2, "reason_enough_not": 2,
    "fact": 1, "evidence": 2, "example": 2,
    "either": 2, "contradict": 2, "consistent": 2, "better_than": 2,
    "is": 2, "have": 2, "key_property_of": 2, "positive": 1, "negative": 1,
    "correlate": 2, "equivalent": 0
}
VARIABLE_TYPES = ["Person(s)", "Thing(s)", "Action", "Case", "Proposition", "Concept", "Property"]

def read_idioms(idioms_dir: str):
    idioms = {}
    for file_path in glob.glob(os.path.join(idioms_dir, "*.json")):
        d = json.load(open(file_path))
        idioms[d["id"]] = d
    return idioms

def should_id_be_unique(values: list):
    ids = set()
    for v in values:
        assert v["id"] not in ids, "duplicated id %s" % v["id"]
        ids.add(v["id"])

def should_predicate_be_reserved(data):
    for n in data["nodes"]:
        assert n["predicate"] in PREDICATES_ARGNUMS,\
            "[%s] undefined predicate %s" % (n["id"], n["predicate"])

def check_num_of_predicate_args(data):
    for n in data["nodes"]:
        if n["predicate"] in ["contradict", "consistent"] and len(n.get("args", [])) == 0:
            continue
        elif n["predicate"] in ["either"] and len(n.get("args", [])) == 1:
            continue
        assert len(n.get("args", [])) == PREDICATES_ARGNUMS[n["predicate"]],\
            "[%s] invalid num of args %d, expexted to %d" % (n["id"], len(n["args"]), PREDICATES_ARGNUMS[n["predicate"]])

def should_args_be_defined(data):
    for n in data["nodes"]:
        for arg in n["args"]:
            assert arg in data["variables"], "[%s] undefined variable %s" % (n["id"], arg)

def should_edge_connect_existing_nodes(data):
    node_ids = [n["id"] for n in data["nodes"]]
    for e in data["edges"]:
        assert e["from"] in node_ids, "[%s] unknown node %s" % (e["id"], e["from"])
        assert e["to"]   in node_ids, "[%s] unknown node %s" % (e["id"], e["to"])

def should_edge_be_unique(data):
    edges = [(e["from"], e["to"]) for e in data["edges"]]
    c = Counter(edges)
    for k, v in c.items():
        assert v == 1, "duplicate edge %s to %s" % (k[0], k[1])

def should_edge_not_be_bidirected(data):
    edges = [(e["from"], e["to"]) for e in data["edges"]]
    for e in edges:
        assert (e[1], e[0]) not in edges, "bidirected edge %s to %s" % (e[0], e[1])

def should_variable_type_be_reserved(data):
    for k, v in data["variables"].items():
        assert v["type"] in VARIABLE_TYPES, "undefined variable type %s for %s" % (v["type"], k)

def check_idiom_exist(data, idioms):
    for i in data["instances"]:
        assert i["idiom_id"] in idioms, "[%s] unknown idiom id %s" % (i["id"], i["idiom_id"])

def should_predicate_be_same_as_idiom(data, idioms):
    instance_node_predicate = {n["id"]:n["predicate"] for n in data["nodes"] if "predicate" in n}
    for i in data["instances"]:
        idiom = idioms[i["idiom_id"]]
        idiom_node_predicate = {n["id"]:n["predicate"] for n in idiom["nodes"]}
        for idiom_node, instance_node in i["node_map"].items():
            assert instance_node_predicate[instance_node] == idiom_node_predicate[idiom_node],\
                "[%s] wrong predicate %s, expected to be %s" % (i["id"], instance_node_predicate[instance_node], idiom_node_predicate[idiom_node])

def should_edge_be_same_as_idiom(data, idioms):
    edges = [(e["from"], e["to"]) for e in data["edges"]]
    for i in data["instances"]:
        idiom = idioms[i["idiom_id"]]
        for idiom_edge in idiom["edges"]:
            e = (i["node_map"][idiom_edge["from"]], i["node_map"][idiom_edge["to"]])
            assert e in edges, "[%s] edge %s to %s should exist" % (i["id"], e[0], e[1])

def find_edge(data, edge_id: str):
    for e in data["edges"]:
        if e["id"] == edge_id:
            return (e["from"], e["to"])
    raise Exception("undefined edge %s" % edge_id)

def should_edge_be_either_from_idiom_or_others(data, idioms):
    non_idiom_edges = [find_edge(data, eid) for eid in data["non_idiom"].keys()]
    idiom_edges = set()
    for i in data["instances"]:
        idiom = idioms[i["idiom_id"]]
        for idiom_edge in idiom["edges"]:
            e = (i["node_map"][idiom_edge["from"]], i["node_map"][idiom_edge["to"]])
            idiom_edges.add(e)

    for edge in data["edges"]:
        e = (edge["from"], edge["to"])
        edge_in_di = e in non_idiom_edges
        edge_in_idiom = e in idiom_edges
        assert edge_in_di != edge_in_idiom, "[%s] strange edge %s to %s" % (edge["id"], e[0], e[1])

if __name__ == "__main__":
    input_path = sys.argv[1]
    data = json.load(open(input_path))
    print("checking %s" % input_path)

    should_id_be_unique(data["nodes"])
    should_predicate_be_reserved(data)
    check_num_of_predicate_args(data)
    should_args_be_defined(data)

    should_id_be_unique(data["edges"])
    should_edge_connect_existing_nodes(data)
    should_edge_be_unique(data)
    should_edge_not_be_bidirected(data)
    should_variable_type_be_reserved(data)

    idioms = read_idioms("./idiom")
    should_id_be_unique(data["instances"])
    check_idiom_exist(data, idioms)
    should_predicate_be_same_as_idiom(data, idioms)
    should_edge_be_same_as_idiom(data, idioms)
    should_edge_be_either_from_idiom_or_others(data, idioms)

    print("done")
