'''
Generates naive commit messages
'''

import diff
from gumtree_processing import skip_diff

import os

cf = lambda s: s[0].upper()+s[1:] if s else s

def new_methods_msg(method_list):
    if len(method_list) == 1:
        return 'added new method ' + method_list[0]
    elif len(method_list) < 4:
        return 'added new methods ' + ', '.join(method_list)
    else:
        return 'a lot of new methods added'

def updated_methods_msg(method_list):
    if len(method_list) == 1:
        return 'changed method ' + method_list[0]
    elif len(method_list) < 4:
        return 'some changes in methods ' + ', '.join(method_list)
    else:
        return 'massive update'

def removed_methods_msg(method_list):
    if len(method_list) == 1:
        return 'deleted method ' + method_list[0]
    elif len(method_list) < 4:
        return 'methods ' + ', '.join(method_list) + ' had been removed'
    else:
        return 'cleanup'

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
        msg = msgfunc(ml) + ' in class ' + cn
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
    while True:
        line = log.readline()
        if not line: break
        if skip_diff(line): continue
        p = process_line(line, astpath)
        if p:
            out.write(line.strip('\n')+' '+p+'\n')

def process_line(line, astpath):
    l = line.split("; ")
    commit_hash = l[0]
    blobnames = l[4:6]
    status = l[2]
    filename = l[3]
    a_b_fn = map(lambda n: astpath+n+'.ast', blobnames)
    d_fn = astpath+'{0}-{1}-{2}.json'.format(commit_hash, *blobnames)
    d = diff.ASTDiff()
    try:
        d.load_all_files(*a_b_fn, d_fn)
    except Exception as e:
        print('Some error', e)
        return ''
    return naive_msg(d)

def main(logfile, outfile, astpath):
    logfile = os.path.expanduser(logfile)
    outfile = os.path.expanduser(outfile)
    astpath = os.path.join(os.path.expanduser(astpath), '')
    linear_process(logfile, outfile, astpath)

if __name__ == '__main__':
    main('~/gcm_aurora_full.log',
         '~/aurora_naive_fullnames.log',
         '~/aurora_diff_new/')
