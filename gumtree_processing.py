import os
import shutil
import subprocess

from ecoprocessings.data_threading import ThreadedDataManager

suff = lambda s: s + ".java"

def linear_processing(gumtreebin, logfile, blobspath, outpath):
    log = open(logfile)
    log.readline() # skipping first
    while True:
        line = log.readline()
        if not line: break
        proceed_diff(line, gumtreebin, blobspath, outpath)

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

def skip_diff(logline, outpath):
    l = logline.split("; ")
    commit_hash = l[0]
    blobnames = l[4:6]
    status = l[2]
    filename = l[3]
    outfile = os.path.join(outpath,
                           "{0}-{1}-{2}.json".format(commit_hash, *blobnames))
    if os.path.exists(outfile):
        print("Skipping, already processed")
        return True
    if status != "M":
        print("Skipping, bad type")
        return True
    if not filename.endswith(suff("")):
        print("Skipping, not a java source file")
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

if __name__ == "__main__":
    args = ("~/gumtree-2.1.3-SNAPSHOT/bin/gumtree", "~/gcm_aurora_full.log", "~/aurora_blobs", "~/aurora_diff_new")
    args_with_corrected_path = map(os.path.expanduser, args)
    threaded_processing(*args_with_corrected_path)
