import os

import message
import diff
import gumtree_processing

import git


def process_git_repo(repo_path, depth, gumtreebin, tmpdir):
    r = git.Repo(os.path.expanduser(repo_path))
    commits = r.iter_commits('master', max_count=depth)
    ac = next(commits)
    for bc in commits:
        commit_message = ac.message
        diffs = ac.diff(bc)
        print('<== Processing commit with message:\n', commit_message)
        for d in diffs:
            if skip_diff(d): continue
            a, b, df = run_gumtree(d, gumtreebin, tmpdir)
            astdiff = diff.ASTDiff()
            astdiff.load_all_files(a, b, df)
            m = message.find_code_mentions_in_commit_message(commit_message, astdiff)
            print(m)
        print('==>\n')
        # print('1st message')
        # print(ac.message)
        # print('2st message')
        # print(bc.message)
        # print('----')
        ac = bc

suff = lambda s: s+'.java'

def run_gumtree(d, gumtreebin, tmpdir):
    names = ['a', 'b']
    for n in names:
        f = open(os.path.join(tmpdir, suff(n)), 'wb')
        f.write(getattr(d, n+'_blob').data_stream.read())
    return gumtree_processing.process_diff(gumtreebin, tmpdir, map(suff, names), tmpdir)

def extract_ast_from_diff(d):
    a = diff.ASTree()
    b = diff.ASTree()
    a.parse_txt(d.a_blob.data_stream.read())
    b.parse_txt(d.b_blob.data_stream.read())

def skip_diff(d):
    if d.change_type != 'M':
        return True
    elif not d.a_path.endswith(suff('')):
        return True
    else:
        return False

if __name__ == '__main__':
    process_git_repo('~/intellij-community', 30, "~/gumtree-2.1.3-SNAPSHOT/bin/gumtree",
    "/Users/balaram.usov/tmp/")
