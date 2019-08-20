'''
Generates naive commit messages
'''

import diff
from gumtree_processing import skip_diff

import os

getnames = lambda d: list(map(diff.name_of, d.values()))

_s = lambda a: 's' if len(a) > 1 else ''
cm = lambda a: ', '.join(a)

def naive_msg(astdiff):
    #updc = getnames(astdiff.updated_classes)
    newm = getnames(astdiff.new_methods)
    rmvm = getnames(astdiff.removed_methods)
    updm = getnames(astdiff.updated_methods)
    msg = list()
    if newm:
        msg.append('added new method' + _s(newm) + ' ' + cm(newm))
    if updm:
        msg.append('some changes in method' + _s(updm) + ' ' + cm(updm)) 
    if rmvm:
        msg.append('removed method' + _s(rmvm) + ' ' + cm(rmvm))
    return '; '.join(msg).capitalize()


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
         '~/aurora_naive.log',
         '~/aurora_diff_new/')
