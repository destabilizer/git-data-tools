import sys
import csv
import json

import rename_analysis

csv.field_size_limit(sys.maxsize)

check_diffdump = lambda s: s and not s.startswith('<')

def main(astdiff_jsondump, outcsv):
    out = open(outcsv, 'w')
    w = csv.writer(out, delimiter='|',  quotechar='"')
    with open(astdiff_jsondump) as dmp:
        dmpr = csv.reader(dmp, delimiter='|', quotechar='"')
        for r in dmpr:
            diff_dumps = list(map(json.loads, filter(check_diffdump, r[-1].split('; '))))
            msg, cfd = generate_simple_commit(diff_dumps)
            print('\n====')
            print('\nSOURCE\n')
            print(diff_dumps)
            print('\nMESSAGE\n')
            print(msg)
            print('\nCONFIDENCE\n')
            print(cfd)
            w.writerow(r[:-1]+[msg, cfd])
    out.close()

def flatten_and_range(seq):
    D = dict()
    for s in seq:
        if s in D.keys():
            D[s] += 1
        else:
            D[s] = 1
    L = list(map(lambda p: (p[1], p[0]), D.items()))
    L.sort()
    return list(map(lambda p: p[1], L))

def merge_dict_seq(dictseq):
    dsi = iter(dictseq)
    dt = next(dsi)
    for d in dsi:
        for k in dt.keys():
            dt[k] += d[k]
    return dt

def generate_simple_commit(diff_seq):
    if not diff_seq:
        return ('', 
                1.)
    diff_merge = merge_dict_seq(diff_seq)
    diff_merge['rnm'] = list(map(tuple, diff_merge['rnm']))   # hack cause we need hashable renames
    major_changes = list(filter(lambda d: d['size'] > 4, diff_seq))
    in_test = 'test' in diff_merge['cls'][0].lower() if diff_merge['cls'] else False
    add_in_test = ' in test' if in_test else ''
    if not major_changes:
        minor_confidence =  0.9 - 0.05*diff_merge['size']
        if diff_merge['rnm']: # detect renames and typos
            return (', '.join(map(rename_analysis.genmsg, flatten_and_range(diff_merge['rnm']))),
                    0.95)
        elif diff_merge['ext']:
            return ('extract code snippet to method ' +
                    flatten_and_range(diff_merge['ext'])[0].split('.')[-1] +
                    add_in_test,
                    0.9)
        elif diff_merge['rmv']:
            return ('cleanup' + add_in_test, 
                    minor_confidence+0.05)
        elif diff_merge['new']:
            return ('minor update' + add_in_test,
                    minor_confidence)
        else:
            return ('minor fix' + add_in_test, 
                    minor_confidence-0.2)
    elif diff_merge['ext'] and len(diff_merge['upd']) <= 1 and \
                               len(diff_merge['new']) <= 1 and \
                               len(diff_merge['rmv']) <= 1:
        ext = flatten_and_range(diff_merge['ext'])
        return ('extract logic to method' + ('s' if len(ext) > 1 else '') +\
                ' ' + ', '.join(ext)
               , 0.5)
    elif diff_merge['rmv'] and len(diff_merge['upd']) <= 1 and \
                               len(diff_merge['new']) <= 1:
        rmv = flatten_and_range(diff_merge['rmv'])
        if 1 <= len(diff_merge['rmv']) <= 2:
            return ('cleanup: ' + ', '.join(map(lambda s: 'removed '+ s.split('.')[-1], 
                                                rmv)),
                    0.6)
        elif len(diff_merge['rmv']) > 2:
            return ('large cleanup', 
                    0.5)
    else:
        return ('massive update', 0.3)
    

if __name__ == '__main__':
    main('/Users/Balaram.Usov/aurora_json.csv',
         '/Users/Balaram.Usov/aurora_easy.csv')

