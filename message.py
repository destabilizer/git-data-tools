import Levenshtein
import diff
from gumtree_processing import skip_diff
import os


def match_word_in_text(w, txt, bound=2):
    matches = []
    cur_word = ''
    pos = 0
    for t in txt+'.':
        if cur_word and not t.isalpha():
            d = Levenshtein.distance(w, cur_word)
            if d <= bound: matches.append((d, pos, cur_word))
            cur_word = ''
        pos += 1
        if t.isalpha(): cur_word += t
    return matches


def process_message(logline, outpath):
    l = logline.split(";")
    commit_hash = l[0]
    blobnames = l[4:6]
    status = l[2]
    filename = l[3]
    commit_message = l[-1]
    ast_files = map(lambda s: os.path.join(outpath, s+".ast"), blobnames)
    diff_file = os.path.join(outpath,
                           "{0}-{1}-{2}.json".format(commit_hash, *blobnames))

    d = diff.ASTDiff()
    d.load_all_files(*ast_files, diff_file)

    # names = lambda md: map(diff.name_of, md.values())
    # all_names = dict(map(lambda a: [a[0], names(getattr(d, a))],
    #                      ['new_methods', 'removed_methods', 'updated_methods']))

    # matches = dict([[m, list()] for m in all_names.keys()])
    # for marker, method_names in all_names.items():
    #     for mn in method_names:
    #         method_matches = match_word_in_text(mn, commit_message)
    #         matches[marker].extend(method_matches)
    
    # for marker, matchlist in matches.items():
    #     if matchlist:
    #         print('====')
    #         print('Matches in commit {0} of type {1}'.format(commit_hash, marker))
    #         print('Commit message:', commit_message)
    #         print('Matchlist:', matchlist)
    #         print('====')

def process_messages(logfile, outpath):
    with open(os.path.expanduser(logfile)) as log:
        for logline in log.readlines():
            if skip_diff(logline, outpath): continue
            process_message(logline, outpath)

#print(sorted(match_word_in_text("meow", "woof meow woof meww")))
process_messages('~/gcm_intellij_full.log', '~/intellij_diff')
