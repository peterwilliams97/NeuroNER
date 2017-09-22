'''
    Miscellaneous utility functions
'''
import os
from glob import glob
from collections import defaultdict
import hashlib
# from shutil import copyfile
from subprocess import CalledProcessError, Popen, PIPE


def run_command(cmd):
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    return p.returncode, stdout, stderr


def pdftotext(pdf, txt):
    cmd = ['pdftotext', pdf, txt]
    cmd = ['java', '-jar', 'pdfbox-app-2.0.7.jar', 'ExtractText', pdf, txt]
    rc, stdout, stderr = run_command(cmd)
    if rc == 0:
        return ''
    if stderr:
        print(stderr)
    if 'Permission Error' not in str(stderr):
        raise CalledProcessError(rc, cmd)


if False:
    rc, stdout, stderr = run_command(['pdftotext', '/Users/pcadmin/testdata/Forerunner_230_OM_EN.pdf', 'blah.txt'])
    print(rc)
    print(stdout)
    print(stderr)
    pdftotext('/Users/pcadmin/testdata/Forerunner_230_OM_EN.pdf', 'blah.txt')
    pdftotext('blah.pdf', 'blah.txt')

    assert False


def sha1_digest(path):
    sha1 = hashlib.sha1()
    with open(path, 'rb') as f:
        while True:
            data = f.read(50000)
            if not data:
                break
            sha1.update(data)
    return sha1.hexdigest()


def extract_name(path, start=None, whole=False):
    if start is None:
        name = os.path.basename(path)
    else:
        name = os.path.relpath(path, start=start)
    if whole:
        return name
    return os.path.splitext(name)[0]


def ascii_count(s, limit):
    return len([c for c in s if ord(c) > limit])


def punc_count(s):
    return len([c for c in s if not ((ord('A') <= ord(c) <= ord('Z')) or
                                     (ord('a') <= ord(c) <= ord('z')))])


def find_keeper(paths):
    # print('**', sorted(paths))
    paths = sorted(paths, key=lambda x: (-len(x), x))
    for path in paths:
        other_paths = [p for p in paths if p != path]
        if 'xarc' in path and not any('xarc' in p for p in other_paths):
            print('1 %s -> %s' % (other_paths, path))
            # assert False
            return {path}
        name = extract_name(path)
        other_names = [extract_name(p) for p in other_paths]
        # print('!!', name, other_names)
        if all(name in p for p in other_names):
            print('2 %s -> %s' % (other_paths, path))
            # assert False
            return {path}
        for limit in 255, 127:
            if ascii_count(path, limit) < min(ascii_count(p, limit) for p in other_paths):
                print('3 %s -> %s' % (other_paths, path))
                # print('$$$', limit, ascii_count(path, limit), min(ascii_count(p, limit) for p in other_paths))
                # assert False
                return {path}
        if punc_count(path) < min(punc_count(p) for p in other_paths):
            print('4 %s -> %s' % (other_paths, path))
            # print('$##', limit, ascii_count(path, limit), min(ascii_count(p, limit) for p in other_paths))
            # assert False
            return {path}

    print('5 %s -> %s' % (paths[1:], path[0]))
    return {paths[0]}


def corpus_to_keepers(pdf_dir):
    sha1_paths = defaultdict(set)
    xarc = []
    for i, path in enumerate(glob(os.path.join(pdf_dir, '**'), recursive=True)):
        # print('%4d: %s' % (i, fn))
        if not os.path.isfile(path):
            continue
        _, ext = os.path.splitext(path)
        if ext != '.pdf':
            continue
        assert os.path.abspath(path) == path, (os.path.abspath(path), path)
        sha1 = sha1_digest(path)
        sha1_paths[sha1].add(path)
        if 'xarc' in path:
            xarc.append(path)
    assert xarc
    print('%d xarc files' % len(xarc))

    for sha1 in sha1_paths:
        paths = sha1_paths[sha1]
        if len(paths) > 1:
            sha1_paths[sha1] = find_keeper(paths)

    keepers = []
    for paths in sha1_paths.values():
        assert len(paths) == 1, (len(paths), paths)
        keepers.append(list(paths)[0])
    keepers.sort()
    return keepers


def corpus_to_text(pdf_dir, text_dir, keep_dirs=False):
    keepers = corpus_to_keepers(pdf_dir)

    os.makedirs(text_dir, exist_ok=True)
    if keep_dirs:
        directories = sorted({os.path.dirname(os.path.join(text_dir,
            extract_name(path, start=pdf_dir, whole=True)))
            for path in keepers})
        for i, path in enumerate(directories):
            print('Making directory %d: %s' % (i, path))
            os.makedirs(path, exist_ok=True)

    for i, path in enumerate(keepers):
        # if path != '/Users/pcadmin/testdata/Forerunner_230_OM_EN.pdf': continue
        print('%3d: %s' % (i, path), end=' -> ')

        assert os.path.abspath(path) == path
        name = extract_name(path)
        path_txt = os.path.join(text_dir, '%s.txt' % name)
        # name = extract_name(path, start=pdf_dir, whole=False)
        # path_txt = os.path.join(text_dir, name)
        print(path_txt, end=' ')
        pdftotext(path, path_txt)
        # copyfile(path, path_txt)
        print(flush=True)


import utils
import re
from ngrams import segment2, cPw, segment_cpts, segment_cpts_recursive


RE_WORD = re.compile(r'\w+', re.MULTILINE | re.DOTALL)
RE_NL = re.compile(r'[\n\f\r]+', re.MULTILINE | re.DOTALL)
RE_SPACE = re.compile(r'[\t ]+', re.MULTILINE | re.DOTALL)
RE_SPNL = re.compile(r'[\t ]+[\n\f\r]+', re.MULTILINE | re.DOTALL)
RE_ENDS = re.compile(r'(?:^[\n\f\r]+|[\n\f\r]+$)', re.MULTILINE | re.DOTALL)
RE_SPACEALL = re.compile(r'\s+', re.MULTILINE | re.DOTALL)
cat = ''.join


def best_words(all_words, grp_ids):
    # print('###', all_words[:5])
    grp = [all_words[i] for i in grp_ids]
    words = []
    words.append(grp[0])
    i = 1
    while i < len(grp) - 1:
        prev = words[-1]
        w0 = grp[i]
        w1 = cat([grp[i], grp[i + 1]])
        assert isinstance(prev, str), (i, prev, w0, w1)
        assert isinstance(w0, str), (i, prev, w0, w1)
        assert isinstance(w1, str), (i, prev, w0, w1)
        p0 = cPw(w0, prev)
        p1 = cPw(w1, prev)
        print('>>>>> %12g %12g %5s %10s | %s' % (p0, p1, p0 < p1, w0, w1))
        if p0 >= p1:
            words.append(w0)
            i += 1
        else:
            words.append(w1)
            i += 2
    words.append(grp[-1])
    return ' '.join(words)


# Reducing printing by finding classes of documents that
# Re ducing printingby finding classes of documents that

def rebreak(orig, text):
    "Rebreak `text` to have the breaks in orig"
    continuous_orig = ''.join(orig.split())
    continuous = ''.join(text.split())
    assert continuous_orig == continuous, '\n%\n%s' % (continuous_orig, continuous)
    n = len(continuous)
    i0, i1 = 0, 0
    breaks0 = set()
    breaks1 = set()
    for i, c in enumerate(continuous):
        if orig[i0].isspace():
            breaks0.add(i)
            # print('@', i, i0)
            i0 += 1
        assert c == orig[i0]
        i0 += 1

        if text[i1].isspace():
            breaks1.add(i)
            # print('#', i, i0)
            i1 += 1
        assert c == text[i1]
        i1 += 1

    assert i0 == len(orig) and i1 == len(text), ((i0, len(orig)), (i1, len(text)))
    breaks = sorted(breaks0 & breaks1)
    print(breaks)
    breaks = [0] + breaks + [n]
    boundaries = [(i0, i1) for i0, i1 in zip(breaks[:-1], breaks[1:])]
    print(boundaries)
    parts = [continuous[i0:i1] for i0, i1 in zip(breaks[:-1], breaks[1:])]
    return ' '.join(parts)


if False:
    print('=' * 80)
    orig = 'Reducing print ing by finding classes of documents that'
    text = 'Re ducing printing by finding classes of documents that'
    broke = rebreak(orig, text)
    print('-' * 80)
    print(orig)
    print(text)
    print(broke)
    print('-' * 80)
    assert False


def retokenize(text):
    matches = [m for m in RE_WORD.finditer(text)]
    words = [m.group(0) for m in matches]
    seps = [text[m0.end():m1.start()] for m0, m1 in zip(matches[:-1], matches[1:])]
    print('-' * 80)
    for i in range(10):
        print('%3d: %-20s -- %s' % (i, words[i], seps[i]))
    n = len(seps)
    groups = []
    grp = []
    for i in range(n):
        if seps[i].isspace():
            grp.append(i)
        elif grp:
            groups.append(grp)
            grp = []
    print('~' * 80)
    out_parts = []
    for i in range(n):
        if i > 0:
            out_parts.append(seps[i - 1])
        # txt = ' '.join(words[i] for i in groups[i])
        wrds = [words[j] for j in groups[i]]
        if len(wrds) == 1:
            out_parts.append(wrds[0])
        else:
            run = ''.join(wrds)
            p2, seg2 = segment2(run)
            seg = segment_cpts_recursive(wrds)
            seg_a = segment_cpts_recursive(wrds, do_mean=True)
            seg_b = segment_cpts_recursive(wrds, L=6)
            seg = ' '.join(seg)
            seg_a = ' '.join(seg_a)
            seg_b = ' '.join(seg_b)
            seg2 = ' '.join(seg2)
            seg2b = rebreak(' '.join(wrds), seg2)
            # wrds = best_words(words, groups[i])
            # p, seg = 0., ''
            if i < 5:
                print('%3d: %s' % (i, groups[i]))
                print('\t%10s -- %s' % ('', seg))
                print('\t%10s -- %s' % ('', seg_a))
                print('\t%10s -- %s' % ('', seg_b))
                print('\t%10g -- %s' % (p2, seg2))
                print('\t%10g -- %s' % (p2, seg2b))
            out_parts.append(seg2b)

    return ''.join(out_parts)


def clean_file(path, path_cln, min_len=100):
    assert path != path_cln
    text = text0 = text00 = utils.read_file(path)
    while True:
        text = RE_NL.sub('\n', text)
        text = RE_SPACE.sub(' ', text)
        text = RE_SPNL.sub('\n', text)
        text = RE_ENDS.sub('', text)
        if text == text0:
            break
        text0 = text
    text += '\n'

    text = retokenize(text)

    # print('=' * 80)
    # print(text00[:100])
    # print('-' * 80)
    # print(text[:100])
    if len(text) >= min_len:
        assert len(text) < len(text00), (len(text), len(text00))
    text = text[:2000]
    if len(text) >= min_len:
        print('-' * 80)
        print(text)
        print('-' * 80)
        utils.write_file(path_cln, text)
        return True, len(text0), len(text)
    assert False, ('yikes', len(text), text[:20])
    return False, 0, 0


def clean_text_corpus(text_dir, clean_dir):
    os.makedirs(clean_dir, exist_ok=True)
    n = 0
    for path in glob(os.path.join(text_dir, "*.txt")):
        name = extract_name(path, whole=True)
        name = RE_SPACE.sub('_', name)
        assert ' ' not in name, name
        path_cln = os.path.join(clean_dir, name)
        ok, l0, l = clean_file(path, path_cln)
        if ok:
            print('%3d: %-30s %4d->%4d' % (n, path_cln, l0, l))
            n += 1


pdf_dir = '~/testdata'
text_dir = '~/testdata.txt/deploy'
clean_dir = '~/testdata.clean/deploy'
pdf_dir = os.path.expanduser(pdf_dir)
text_dir = os.path.expanduser(text_dir)
clean_dir = os.path.expanduser(clean_dir)
print('pdf_dir=%s' % pdf_dir)
print('text_dir=%s' % text_dir)
print('clean_dir=%s' % clean_dir)

if False:
    path = os.path.join(text_dir, '000019.txt')
    assert os.path.exists(path), path
    clean_file(path, 'blah.txt')
    assert False

if True:
    corpus_to_text(pdf_dir, text_dir)
# if True:
#     clean_text_corpus(text_dir, clean_dir)
