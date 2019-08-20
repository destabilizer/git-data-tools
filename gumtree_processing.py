import os
import shutil
import subprocess

from data_threading import ThreadedDataManager

suff = lambda s: s + ".java"

def linear_processing(gumtreebin, logfile, blobspath, outpath):
    log = open(logfile)
    log.readline() # skipping first
    allc = 0
    truc = 0
    while True:
        print(allc, '/', truc)
        line = log.readline()
        if not line: break
        allc += 1
        if skip_diff(line, outpath): continue
        truc += 1
        #proceed_diff(line, gumtreebin, blobspath, outpath)

def threaded_processing(gumtreebin, logfile, blobspath, outpath,
                        thread_amount=16):
    pd = lambda l: proceed_diff(l, gumtreebin, blobspath, outpath)
    ad = lambda l: not skip_diff(l, outpath)
    tdm = ThreadedDataManager(thread_amount=thread_amount, update_period=0.25)
    tdm.setDataProcess(pd)
    tdm.setApplyCondition(ad)
    tdm.setTimeout(100)
    tdm.setOnSuccess(lambda s: print("yay finished", s))
    # adding data
    log = open(logfile)
    log.readline()
    tdm.setData(log.readlines())
    tdm.start()

def skip_diff(logline):
    l = logline.split("; ")
    commit_hash = l[0]
    blobnames = l[4:6]
    status = l[2]
    filename = l[3]
    #outfile = os.path.join(outpath,
    #                       "{0}-{1}-{2}.json".format(commit_hash, *blobnames))
    #if os.path.exists(outfile):
    #    print("Skipping, already processed")
    #    return True
    if status != "M":
        #print("Skipping, bad type")
        return True
    if not filename.endswith(suff("")):
        #print("Skipping, not a java source file")
        return True
    return False
    
def proceed_diff(logline, gumtreebin, blobspath, outpath):
        l = logline.split("; ")
        commit_hash = l[0]
        blobnames = l[4:6]
        status = l[2]
        filename = l[3]

        print("\n\n====\n\n")
        print("commit:", commit_hash)

        suffpaths = []
        for blobname in blobnames:
            blobpath = os.path.join(blobspath, blobname)
            suffpath = suff(blobpath)
            if not os.path.exists(suffpath):
                shutil.copyfile(blobpath, suffpath)
                print("copied:", suffpath)
            suffpaths.append(suffpath)

        outdir = os.path.join(outpath, "")
        frmt = lambda s: s.format(gumtreebin, *suffpaths, outdir,
                                  commit_hash, *blobnames)
        print(frmt(" | ".join(map(lambda n: "{"+str(n)+"}", range(6)))))
        for i in range(2):
              filepath = frmt("{3}{"+str(i+5)+"}.ast")
              if not os.path.exists(filepath):
                  subprocess.run(frmt("{0} parse {"+str(i+1)+"} > " + filepath),
                                      shell=True)
                  print(frmt("generated ast for {"+str(i+5)+"}"))
        subprocess.run(frmt("{0} jsondiff {1} {2} > {3}{4}-{5}-{6}.json"),
                       shell=True)
        print("calculated diff beetween {1} {2}")
        #subprocess.run(frmt("{0} axmldiff {1} {2} > {3}.xml"), shell=True)
        #subprocess.run(frmt("{0} cluster {1} {2} > {3}.cluster"), shell=True)
        print("processed")

def process_diff(gumtreebin, blobspath, blobnames, outpath):
    bn = list(blobnames)
    gumbin = os.path.expanduser(gumtreebin)
    op = os.path.join(outpath, '')
    bp = os.path.join(blobspath, '')
    parse_cmd = "{0} parse {1}{3}"
    parse_fn = "{2}{3}.ast"
    diff_cmd = "{0} jsondiff {1}{3} {1}{4}"
    diff_fn = "{2}{3}-{4}-diff.json"
    filenames = list()
    for n in bn:
        pc = parse_cmd.format(gumbin, op, bp, n)
        pf = parse_fn.format(gumbin, op, bp, n)
        subprocess.run(pc + " > " + pf, shell=True)
        filenames.append(pf)
    dc = diff_cmd.format(gumbin, op, bp, *bn)
    df = diff_fn.format(gumbin, op, bp, *bn)
    subprocess.run(dc + " > " + df, shell=True)
    filenames.append(df)
    return filenames

if __name__ == "__main__":
    args = ("~/gumtree-2.1.3-SNAPSHOT/bin/gumtree", "~/gcm_aurora_full.log", "~/intellij_blobs", "~/intellij_diff")
    args_with_corrected_path = map(os.path.expanduser, args)
    linear_processing(*args_with_corrected_path)
