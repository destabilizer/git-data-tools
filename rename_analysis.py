import Levenshtein as lev

import json

find_renames = lambda jd: filter(
    lambda d: d["action"] == "update-node" and d["tree"].startswith("SimpleName"), 
    jd["actions"])

parse_rename = lambda d: (d["tree"].split(":")[1].lstrip(" ").split("[")[0].rstrip(" "), d["label"])

istypo = lambda pd: lev.distance(*pd) <= 2

def genmsg(d):
    pd = parse_rename(d)
    if istypo(pd):
        msg = "fix typo of {1}"
    else:
        msg = "rename {0} to {1}"
    return msg.format(*pd)

def renames_in_json(fn):
    with open(fn) as f:
        return map(genmsg, find_renames(json.load(f)))
