"""
    Code to accompany the chapter "Natural Language Corpus Data"
    from the book "Beautiful Data" (Segaran and Hammerbacher, 2009)
    http://oreilly.com/catalog/9780596157111/

    Code copyright (c) 2008-2009 by Peter Norvig

    You are free to use this code under the MIT licencse:
    http://www.opensource.org/licenses/mit-license.php
"""
import re, string, random, glob, operator, heapq
from collections import defaultdict
from math import log10


def memo(f):
    "Memoize function f."
    table = {}

    def fmemo(*args):
        if args not in table:
            table[args] = f(*args)
        return table[args]
    fmemo.memo = table
    return fmemo


def test(verbose=None):
    """Run some tests, taken from the chapter.
    Since the hillclimbing algorithm is randomized, some tests may fail."""
    import doctest
    print('Running tests...')
    doctest.testfile('ngrams-test.txt', verbose=verbose)

################ Word Segmentation (p. 223)


@memo
def segment(text):
    "Return a list of words that is the best segmentation of text."
    if not text:
        return []
    candidates = ([first]+segment(rem) for first, rem in splits(text))
    return max(candidates, key=Pwords)


def splits(text, L=20):
    "Return a list of all possible (first, rem) pairs, len(first)<=L."
    return [(text[:i+1], text[i+1:])
            for i in range(min(len(text), L))]


def Pwords(words):
    "The Naive Bayes probability of a sequence of words."
    return product(Pw(w) for w in words)


#### Support functions (p. 224)

def product(nums):
    "Return the product of a sequence of numbers."
    return reduce(operator.mul, nums, 1)


class Pdist(dict):
    "A probability distribution estimated from counts in datafile."

    def __init__(self, data=[], N=None, missingfn=None):
        for key, count in data:
            self[key] = self.get(key, 0) + int(count)
        self.N = float(N or sum(self.itervalues()))
        self.missingfn = missingfn or (lambda k, N: 1. / N / N)

    def __call__(self, key):
        if key in self:
            return self[key] / self.N
        else:
            return self.missingfn(key, self.N)


def datafile(name, sep='\t'):
    "Read key,value pairs from file."
    with open(name, 'rt') as f:
        for line in f:
            yield line.split(sep)


def avoid_long_words(key, N):
    "Estimate the probability of an unknown word."
    return 10. / (N * 20**len(key))


N = 1024908267229  # Number of tokens

Pw = Pdist(datafile('count_1w.txt'), N, avoid_long_words)
P2w = Pdist(datafile('count_2w.txt'), N)

#### segment2: second version, with bigram counts, (p. 226-227)


def cPw(word, prev):
    "Conditional probability of word, given previous word."
    # p = ['?', '?']
    try:
        # p = [P2w[prev + ' ' + word], float(Pw[prev])]
        ret = P2w[prev + ' ' + word] / float(Pw[prev])
    except KeyError:
        ret = Pw(word)
    # p.append(Pw(word))
    # print(p, end=' ')
    return ret


@memo
def segment_cpts(cpts, prev='<S>'):
    "Return (log P(words), words), where words is the best segmentation."
    cpts0 = prev + cpts[:1]
    probs = log10(cPw(c1, c0) for c1, c0 in zip(cpts0, cpts))
    return sum(probs)

import itertools


def cpt_joins(cpts):
    """Return a list of all possible (first, rem) pairs, len(first)<=L.
            c1 c2 c3 c4  0 0 0
            c1 c2 c3c4   0 0 1
            c1 c2c3 c4   0 1 0
            c1 c2c3c4    0 1 1
            c1c2 c3 c4   1 0 0
            c1c2 c3c4    1 0 1
            c1c2c3 c4    1 1 0
            c1c2c3c4     1 1 1
    """
    n = len(cpts)

    def J(cpts, b):
        cpts1 = []
        c1 = cpts[0]
        for c, i in zip(cpts[1:], b):
            if i:
                c1 += c
            else:
                assert c1
                cpts1.append(c1)
                c1 = c
        if c1:
            cpts1.append(c1)
        return cpts1

    joins = []
    for i, b in enumerate(itertools.product((False, True), repeat=n - 1)):
        # print(i, b)
        joins.append(J(cpts, b))
    return joins


def score(cpts, verbose=False):
    probs = [log10(Pw(c)) for c in cpts]
    if verbose:
        print([(l, c) for l, c in zip(probs, cpts)])
    return min(probs), sum(probs)
    # if len(cpts) == 1:
    #     # assert False, cpts
    #     return log10(Pw(cpts[0]))
    # print([(log10(cPw(first, prev)), prev, first) for prev, first in zip(cpts[:-1], cpts[1:])])
    # return sum(log10(cPw(first, prev)) for prev, first in zip(cpts[:-1], cpts[1:]))


def rank_score(ranks):
    return -sum([2** (-i) for i in ranks]) / len(ranks)


def best_cpt_join(cpts):
    # print('best_cpt_join', len(cpts), cpts)

    joins = cpt_joins(cpts)

    # words = {w for cpt in joins for w in cpt}
    # word_prob = {w: log10(Pw(w)) for w in words}
    # probs = set(word_prob.values())
    # prob_rank_pairs = sorted((p, i) for i, p in enumerate(probs))
    # prob_rank = {p: i for p, i in prob_rank_pairs}
    # word_rank = {w: prob_rank[p] for w, p in word_prob.items()}
    # score_joins = [(rank_score([word_rank[w] for w in cpt]), cpt) for cpt in joins]

    score_joins = [(score(cpt), cpt) for cpt in joins]
    # for i, (scr, cpt) in enumerate(sorted(score_joins, reverse=True)):
    #     print('%3d: %10g: %s' % (i, scr, cpt))

    ret = max(score_joins)[1]
    # if 'winstead' in ret:
    #     print('-' * 80)
    #     print(cpts)
    #     for i, (scr, cpt) in enumerate(sorted(score_joins, reverse=True)):
    #         score(cpt, verbose=True)
    #         print('%3d: %10g %10g: %s' % (i, scr[0], scr[1], cpt))
    #     assert False
    return ret


def segment_cpts_recursive(cpts, L=5):
    "Return (log P(words), words), where words is the best segmentation."

    L = min(len(cpts) - 1, L)

    i = 0
    # print('%3d: %10g: %s' % (i, score(cpts), cpts[max(i - L, 0): i + L]))
    cpts_new = []
    while i <= len(cpts) - L:
        n = len(cpts)
        cpts1 = best_cpt_join(cpts[i:i + L])
        cpts = cpts[:i] + cpts1 + cpts[i + L:]
        # print(cpts1)
        # print('%3d: %10g: %s' % (i, score(cpts), cpts[max(i - L, 0): i + L]))
        if n == len(cpts) or True:
            i += 1
    return cpts

    if not cpts:
        return 0.0, []

    candidates = [combine(log10(cPw(first, prev)), first, segment2(rem, first))
                  for first, rem in splits(text)]
    return max(candidates)
    cpts0 = prev + cpts[:1]
    probs = log10(cPw(c1, c0) for c1, c0 in zip(cpts0, cpts))
    return sum(probs)


if True:
    cpts = ['a', 'nd', 'th', 'e', 'm']
    text = ('''Reducing p rinting by finding c lasses of documents t hat should not be p rinted or could be '''
         +  '''printed d ifferently double s ided t wo p ages p er sheet b w i nstead o f colour ''')
    text = text * 10
    cpts = text.split()[:]
    # ret = cpt_joins(cpts)
    # ret = best_cpt_join(cpts)
    for L in range(3, 8):
        ret = segment_cpts_recursive(cpts, L)
        print(L, len(ret), ret[:30])
    assert False






def combine(Pfirst, first, Prem_rem):
    "Combine first and rem results into one (probability, words) pair."
    Prem, rem = Prem_rem
    return Pfirst + Prem, [first] + rem


depth = 0
depth_dict = defaultdict(int)

@memo
def segment2(text, prev='<S>'):
    "Return (log P(words), words), where words is the best segmentation."
    global depth, depth_dict

    if not text:
        return 0.0, []
    depth += 1
    depth_dict[depth] +=1
    candidates = [combine(log10(cPw(first, prev)), first, segment2(rem, first))
                  for first, rem in splits(text)]
    # print('>>>', depth, text, prev, max(candidates))
    depth -= 1
    return max(candidates)


if False:
    text = "p rinting by finding c lasses"
    text = text.replace(' ', '')
    print('text=%d %s' % (len(text), text))
    text = segment2(text)
    print(text)
    for depth in sorted(depth_dict):
        print('%3d: %2d' % (depth, depth_dict[depth]))

