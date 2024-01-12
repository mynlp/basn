#!/usr/bin/env python
import os, sys
import json, glob

from graphviz import Digraph

COLORS = ["red", "blue", "green", "orange", "darkgreen", "purple", "lightgreen", "cyan", "magenta", "navy"]

def create_graph(data: dict):
    g = Digraph()
    for n in data["nodes"]:
        g.node(n["id"], make_node_label(n))
    for e in data["edges"]:
        label = None
        if e["id"] in data["default_inferences"]:
            label = "DI"
        g.edge(e["from"], e["to"], label=label)
    colors = COLORS[:]
    for i in data["instances"]:
        with g.subgraph(name="cluster_%s" % i["id"]) as c:
            c.attr(color=colors.pop(0))
            for n in i["node_map"].values():
                c.node(n)
    return g

def make_node_label(n: dict):
    return "%s(%s)" % (n["predicate"], ",".join(n["args"]))

def read_idioms(idioms_dir: str):
    idioms = {}
    for file_path in glob.glob(os.path.join(idioms_dir, "*.json")):
        d = json.load(open(file_path))
        idioms[d["id"]] = d
    return idioms

def make_caption(data: dict, idioms: dict):
    variables, instances = [], []
    for k, v in data["variables"].items():
        variables.append("%s %s: %s" % (v["type"], k, v["text"]))
    for index, i in enumerate(data["instances"]):
        idiom = idioms[i["idiom_id"]]
        instances.append("%s: %s %s" % (COLORS[index], idiom["id"], idiom["name"]))
    return "\n".join(["[variables]"] + variables + ["[instances]"] + instances)

if __name__ == "__main__":
    input_path = sys.argv[1]
    output_path = os.path.join("image", os.path.basename(input_path).replace(".json", ""))

    data = json.load(open(input_path))
    g = create_graph(data)
    #g.view()
    g.render(output_path)

    idioms = read_idioms("idiom")
    caption = make_caption(data, idioms)
    with open("%s.txt" % output_path, "wt") as f:
        f.write(caption)
