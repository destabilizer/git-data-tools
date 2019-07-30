import Levenshtein
import diff
from gumtree_processing import skip_diff
import os
import time


def match_word_in_text(w, txt, bound=2):
    wl = w.lower()
    matches = []
    cur_word = ''
    pos = 0
    for t in txt+'.':
        if cur_word and not t.isalpha():
            d = Levenshtein.distance(wl, cur_word.lower())
            if d <= bound: matches.append((d, pos, cur_word))
            cur_word = ''
        pos += 1
        if t.isalpha(): cur_word += t
    return matches


def process_logline(logline, outpath, r):
    l = logline.split(";")
    commit_hash = l[0]
    blobnames = l[4:6]
    status = l[2]
    filename = l[3]
    commit_message = l[-1]
    ast_files = map(lambda s: os.path.join(outpath, s+".ast"), blobnames)
    diff_file = os.path.join(outpath,
                           "{0}-{1}-{2}.json".format(commit_hash, *blobnames))

    astdiff = diff.ASTDiff()
    astdiff.load_all_files(*ast_files, diff_file)

    matches = find_methods_in_commit_message(commit_message, astdiff)

    for marker, matchlist in matches.items():
        if matchlist:
            print('====')
            print('Matches in commit {0} of type {1}'.format(commit_hash, marker))
            print('Commit message:', commit_message)
            print('Matchlist:', matchlist)
            print('====')
    
    r.update(matches)

def find_methods_in_commit_message(commit_message, astdiff):
    names = lambda md: map(diff.name_of, md.values())
    all_names = dict(map(lambda a: [a[0], names(getattr(astdiff, a))],
                         ['new_methods', 'removed_methods', 'updated_methods']))
    matches = dict([[m, dict()] for m in all_names.keys()])
    for marker, method_names in all_names.items():
        for mn in method_names:
            method_matches = match_word_in_text(mn, commit_message)
            matches[marker][mn] = method_matches
    return matches

def process_messages_linear(logfile, outpath, outfile):
    with open(os.path.expanduser(logfile)) as log:
        for logline in log.readlines():
            if skip_diff(logline, outpath): continue
            process_logline(logline, outpath)

def process_messages_threaded(logfile, outpath, matchfile, allmatchfile):
    from data_threading import ThreadedDataManager
    pm = lambda l, r: process_message(l, outpath, r)
    am = lambda l: not skip_diff(l, outpath)
    tdm = ThreadedDataManager(thread_amount=16, update_period=0.005)
    tdm.set_data_process(pm)
    tdm.set_apply_condition(am)
    tdm.set_timeout(20)
    tdm.set_on_success(lambda s, r: print('<=\n', s, r, '\n=>'))
    log = open(os.path.expanduser(logfile))
    log.readline()
    tdm.set_data(log.readlines())
    tdm.start()
    
    def check_result(r):
        for md in r.values():
            for ml in md.values():
                if ml: return True
        return False
    
    while not tdm.is_finished():
        time.sleep(20)
        print('====\n\n\n\n\nSaving results\n\n\n\n\n====')
        matchf = open(os.path.expanduser(matchfile), 'w')
        allmatchf = open(os.path.expanduser(allmatchfile), 'w')
        for i in range(tdm.total):
            d, r = tdm.get_data_res(i)
            outstring = d.strip('\n')+';'+str(r)+'\n'
            if r:
                allmatchf.write(outstring)
            if check_result(r):
                matchf.write(outstring)
        matchf.close()
        allmatchf.close()
    
if __name__ == '__main__':
    #print(sorted(match_word_in_text("meow", "woof meow woof meww")))
    process_messages_threaded('~/gcm_intellij_full.log', '~/intellij_diff',
                              '~/intellij_matches.txt', '~/intellij_all_matches.txt')
