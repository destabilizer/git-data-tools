import Levenshtein as lev

import json

find_renames = lambda jd: filter(
    lambda d: d["action"] == "update-node" and d["tree"].startswith("SimpleName"), 
    jd["actions"])

parse_rename = lambda d: (d["tree"].split(":")[1].lstrip(" ").split("[")[0].rstrip(" "), d["label"])

def istypo(pd):
    eo = lev.editops(*pd)
    if len(eo) == 1:
        edit = eo[0]
        if edit[0] == 'replace':
            chars = pd[0][edit[1]] + pd[1][edit[2]]
        elif edit[0] == 'insert':
            chars = pd[1][edit[2]]
        elif edit[0] == 'delete':
            chars = pd[0][edit[1]]
        if chars.isalpha():
            return True
    return False

def genmsg(pd):
    if istypo(pd):
        msg = "fix typo of {1}"
    else:
        msg = "rename {0} to {1}"
    return msg.format(*pd)

gen_parse = lambda d: genmsg(parse_rename(d))

def renames_in_json(fn):
    with open(fn) as f:
        return map(gen_parse, find_renames(json.load(f)))
