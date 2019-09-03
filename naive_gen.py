'''
Generates naive commit messages
'''

import diff
from gumtree_processing import skip_diff

import os
import csv
import json

cf = lambda s: s[0].upper()+s[1:] if s else s

def new_methods_msg(method_list, classname):
    if len(method_list) == 1:
        return 'added new method ' + classname+ '.' + method_list[0]
    elif len(method_list) < 4:
        return 'added new methods ' + ', '.join(method_list) + ' to class ' + classname
    else:
        return 'a lot of new methods added to class ' + classname

def updated_methods_msg(method_list, classname):
    if len(method_list) == 1:
        return 'changed method ' + classname+ '.' + method_list[0]
    elif len(method_list) < 4:
        return 'some changes in methods ' + ', '.join(method_list) + ' in class ' + classname
    else:
        return 'massive update of class ' + classname

def removed_methods_msg(method_list, classname):
    if len(method_list) == 1:
        return 'deleted method ' + classname+ '.' + method_list[0]
    elif len(method_list) < 4:
        return 'methods ' + ', '.join(method_list) + ' had been removed from ' + classname
    else:
        return 'cleanup in class ' + classname

def tree_on_methodlist(method_list):
    t = dict()
    for m in method_list:
        parname = diff.name_of(m.parent_class)
        if parname not in t.keys():
            t[parname] = [diff.name_of(m)]
        else:
            t[parname].append(diff.name_of(m))
    return t

def generate_msg_on_tree(msgfunc, method_tree):
    totalmsg = list()
    for cn, ml in method_tree.items():
        msg = msgfunc(ml, cn)
        totalmsg.append(msg)
    return '; '.join(totalmsg)

def generate_msg_on_ml(msgfunc, method_list):
    return generate_msg_on_tree(msgfunc, tree_on_methodlist(method_list))

def generate_msg_on_funcname(astdiff, funcname):
    msgfunc = globals()[funcname+'_msg']
    method_list = getattr(astdiff, funcname).values()
    return generate_msg_on_ml(msgfunc, method_list)

def naive_msg(astdiff):
    msg = list()
    for fn in ['new_methods', 'updated_methods', 'removed_methods']:
        msg.append(generate_msg_on_funcname(astdiff, fn))
    return '[' + '; '.join(filter(lambda s: s, msg)) + ']'

def linear_process(logfile, outfile, astpath):
    log = open(logfile)
    log.readline() # skipping first
    out = open(outfile, 'w')
    wr = csv.writer(out, delimiter='|', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    lastch = None
    ca = list()
    skipping = False
    while True:
        line = log.readline()
        if not line: break
        # skip or process
        if skip_diff(line):
            res = parseline(line) + ['<skip>']
        else:
            res = process_line(line, astpath)
        # summarizing several commits
        curch = res[0]
        if not lastch or lastch == curch:
            ca.append(res)
        else:
            wr.writerow(flatcl(ca))
            ca = [res]
        lastch = curch

fn_st_msg = lambda r: (r[4], r[3], r[5])
cor_msg = lambda r: r[2] != '<skip>' and r[2] != '<error>'
compose_fn = lambda r: r[0]+' ['+r[1]+']'
compose_msg = lambda r: r[0].split('/')[-1]+' '+r[2]

def flatcl(commit_array):
    c = commit_array[0]
    fsm = list(map(fn_st_msg, commit_array))
    fsm.sort()
    fn = ', '.join(map(compose_fn, fsm))
    #msg = ', '.join(map(compose_msg, filter(cor_msg, fsm)))
    msg = '; '.join(map(lambda c: c[-1], commit_array))
    print(msg)
    return c[:3]+[fn, msg]

def parseline(line):
    l = line.split("; ")
    rl = l[:4]
    rl.insert(2, l[6])
    return rl

def process_line(line, astpath):
    l = line.split("; ")
    commit_hash = l[0]
    author = l[1]
    blobnames = l[4:6]
    status = l[2]
    filename = l[3]
    omsg = l[6]
    a_b_fn = map(lambda n: astpath+n+'.ast', blobnames)
    d_fn = astpath+'{0}-{1}-{2}.json'.format(commit_hash, *blobnames)
    d = diff.ASTDiff()
    try:
        d.load_all_files(*a_b_fn, d_fn)
    except Exception as e:
        print('Some error', e)
        return parseline(line) + ['<error>']
    #msg = naive_msg(d)
    msg  = jsonmsg(d)
    return [commit_hash, author, omsg, status, filename, msg]

def jsonmsg(astdiff):
    d = dict()
    d['cls'] = list(map(diff.name_of, astdiff.updated_classes.values()))
    d['new'] = list(map(diff.name_of_method, astdiff.new_methods.values()))
    d['upd'] = list(map(diff.name_of_method, astdiff.updated_methods.values()))
    d['rmv'] = list(map(diff.name_of_method, astdiff.removed_methods.values()))
    d['rnm'] = list(astdiff.renames.values())
    d['ext'] = list(map(diff.name_of_method, astdiff.method_extractions))
    d['size'] = astdiff.size
    return json.dumps(d)

def main(logfile, outfile, astpath):
    logfile = os.path.expanduser(logfile)
    outfile = os.path.expanduser(outfile)
    astpath = os.path.join(os.path.expanduser(astpath), '')
    linear_process(logfile, outfile, astpath)

if __name__ == '__main__':
    main('~/gcm_aurora_full.log',
         '~/aurora_json.csv',
         '~/aurora_diff_new/')
