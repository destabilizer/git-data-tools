import json

from message import match_word_in_text

from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords


lemmatizer = WordNetLemmatizer()
stopWords = set(stopwords.words('english'))


def code_tokenize(txt):
    tokens = list()
    cur_word = str()
    for t in txt:
        if t.isupper() or not t.isalpha():
            if cur_word: tokens.append(cur_word)
            cur_word = t.lower() if t.isalpha() else str()
        else:
            cur_word += t
    else:
        if cur_word: tokens.append(cur_word)
    return tokens


def glue(seq_of_lists):
    g = list()
    for l in seq_of_lists: g += l
    return g


clean_tl = lambda tl: set(map(lemmatizer.lemmatize, glue(map(code_tokenize, tl))))

def token_diff(atl, btl):
    a = clean_tl(atl)
    b = clean_tl(btl)
    return [a.difference(b), b.difference(a)]

# json block

def process_token_json(commit_info):
    a, b = token_diff(commit_info['deletedTokens'], commit_info['addedTokens'])
    commit_info['deletedWordTokens'] = a
    commit_info['addedWordTokens']   = b

def process_commitlist(commitlist):
    for c in commitlist:
        process_token_json(c)

def load_json(filename):
    import json
    with open(filename) as f:
        cl = json.load(f)
        process_commitlist(cl)
        return cl

# linguistic block

def search_for_category(wordcat, commitlist):
    matched = list()
    ws = set(wordcat)
    for c in commitlist:
        mwords = set(word_split(c['message']))
        matches = ws.intersection(mwords)
        if matches: matched.append(c)
    return matched

def check_word(w):
    if len(w) <= 1:
        return False
    elif w in stopWords:
        return False
    else:
        return True

def wordfreq_in_texts(textslist):
    freq = dict()
    for txt in textslist:
        added = list()
        words = code_tokenize(txt)
        for w in words:
            if not check_word(w): continue
            if w in added: continue
            if w in freq.keys():
                freq[w] += 1
            else:
                freq[w] = 1
            added.append(w)
    return list(reversed(sorted(map(lambda wf: tuple(reversed(wf)), freq.items()))))

def wordfreq_of_messages(commitlist):
    messages = list()
    total = 0
    no_message = 0
    for c in commitlist:
        m = c['message']
        if 'no message' in m:
            no_message += 1
        else:
            messages.append(m)
        total += 1
    wfl = wordfreq_in_texts(messages)
    wfl.insert(0, (no_message, 'no message'))
    return list(map(lambda fw: (fw[0]/total, fw[1]), wfl))

token_amount = lambda c: len(c['deletedWordTokens'])+len(c['addedWordTokens'])

def small_changes(commitlist, measure):
    return list(filter(lambda c: token_amount(c) <= measure, commitlist))

def big_changes(commitlist, measure):
    return list(filter(lambda c: token_amount(c) > measure, commitlist))

def print_freq(freqlist):
    for f, w in freqlist:
        print(w, str(round(f*100, 2))+'%')

