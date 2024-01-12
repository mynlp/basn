#!/usr/bin/env python
import json
import copy

def main(category, topic_ids):
    data = {id: json.load(open("graph/%s%s.json" % (category, id))) for id in topic_ids}
    check_variable_duplication(data)
    nodeid_mapping = make_nodeid_mapping(data)
    converted = {
        "nodes": [],
        "edges": [],
        "variables": {},
        "instances": [],
        "non_idiom": {}
    }
    for topic_id, d in sorted(data.items()):
        append_graph(converted, topic_id, d, nodeid_mapping)
    with open("graph/%s.json" % category, mode="wt") as f:
        f.write(json.dumps(converted, indent=4))

def check_variable_duplication(data):
    seen = {}
    for id, d in data.items():
        for k, v in d["variables"].items():
            if not k in seen:
                seen[k] = v
            else:
                if seen[k]["type"] != v["type"] or seen[k]["text"] != v["text"]:
                    raise Exception("%s is duplicated" % k)

def make_nodeid_mapping(data):
    nodeid_mapping = {}
    seen = {}
    for topic_id, d in sorted(data.items()):
        for n in d["nodes"]:
            key = (n["predicate"],) + tuple(n["args"])
            if n["id"][0] == "z":
                nodeid_mapping[topic_id + n["id"]] = topic_id + n["id"]
            elif not key in seen:
                nodeid_mapping[topic_id + n["id"]] = topic_id + n["id"]
                seen[key] = topic_id + n["id"]
            else:
                nodeid_mapping[topic_id + n["id"]] = seen[key]
    return nodeid_mapping

def append_graph(converted, topic_id, d, nodeid_mapping):
    for n in d["nodes"]:
        mapped_id = nodeid_mapping[topic_id + n["id"]]
        if mapped_id != topic_id + n["id"]:
            continue
        n = copy.deepcopy(n)
        n["id"] = mapped_id
        converted["nodes"].append(n)
    for e in d["edges"]:
        converted["edges"].append({
            "id": topic_id + e["id"],
            "from": nodeid_mapping[topic_id + e["from"]],
            "to": nodeid_mapping[topic_id + e["to"]]
        })
    for k, v in d["variables"].items():
        converted["variables"][k] = v
    for i in d["instances"]:
        converted["instances"].append({
            "id": topic_id + i["id"],
            "idiom_id": i["idiom_id"],
            "node_map": {idiom_nid:nodeid_mapping[topic_id + nid] for idiom_nid, nid in i["node_map"].items()}
        })
    for eid, v in d["non_idiom"].items():
        converted["non_idiom"][topic_id + eid] = v
    return converted


if __name__ == "__main__":
    main("DP", ["01", "04", "06", "08"])
