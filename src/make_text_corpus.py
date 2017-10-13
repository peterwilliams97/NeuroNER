'''
    Miscellaneous utility functions
'''
import os
from glob import glob
from collections import defaultdict
import hashlib
import string
from subprocess import CalledProcessError, Popen, PIPE
import utils
import re
from ngrams import Pw

# Settings
MAX_DOC_SIZE = 10000
CONVERT_PDF = True
CLEAN_TEXT = True


def quote(s):
    if not RE_SPACE.search(s):
        return s
    s = s.replace('"', '\\"')
    s = '"%s"' % s
    print('$$$', s)
    return s


def run_command(cmd):
    # cmd = [quote(s) for s in cmd]
    print('cmd=%s' % cmd)

    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()

    if p.returncode != 0:
        if stdout:
            print('~' * 80)
            print(stdout.decode("utf-8"))
        if stderr:
            print('^' * 80)
            print(stderr.decode("utf-8"))
        if 'Permission Error' not in str(stderr):
            print('-' * 80)
            print(' '.join(cmd))
            raise CalledProcessError(p.returncode, cmd)

    return p.returncode, stdout, stderr


# pdfminer = '~/pdf/pdfminer/tools/pdf2txt.py'
# pdfminer = os.path.expanduser(pdfminer)
pdfminer = '/anaconda/bin/pdf2txt.py'
# assert os.path.exists(pdfminer), pdfminer
# assert shutil.which('pdftotext')
# # assert shutil.which('pdfbox-app-2.0.7.jar')
# assert shutil.which('pdf2txt.py')


def pdftotext(pdf, txt, method=1):
    """pdfbox works best"""
    if method == 0:
        cmd = ['pdftotext', pdf, txt]
    elif method == 1:
        cmd = ['java', '-jar', 'pdfbox-app-2.0.7.jar', 'ExtractText', pdf, txt]
    elif method == 2:
        cmd = ['python', pdfminer, '-o', txt, pdf]
    return run_command(cmd)


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
    """Return the 1 file in of the identical files in `paths` that we will use"""
    paths = sorted(paths, key=lambda x: (-len(x), x))
    for path in paths:
        other_paths = [p for p in paths if p != path]
        if 'xarc' in path and not any('xarc' in p for p in other_paths):
            print('1 %s -> %s' % (other_paths, path))
            return {path}
        name = extract_name(path)
        other_names = [extract_name(p) for p in other_paths]

        if all(name in p for p in other_names):
            print('2 %s -> %s' % (other_paths, path))
            return {path}

        for limit in 255, 127:
            if ascii_count(path, limit) < min(ascii_count(p, limit) for p in other_paths):
                print('3 %s -> %s' % (other_paths, path))
                return {path}

        if punc_count(path) < min(punc_count(p) for p in other_paths):
            print('4 %s -> %s' % (other_paths, path))
            return {path}

    print('5 %s -> %s' % (paths[1:], path[0]))
    return {paths[0]}


def corpus_to_keepers(pdf_dir):
    """Return the unique files in `pdf_dir` that we will use"""
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


def corpus_to_text(pdf_dir, text_dir, method=1, keep_dirs=False):
    """Convert the unique PDF files in `pdf_dir` to file with the same name in `text_dir` using converter
        specified by `method`. Use method=1
    """
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

        print('%3d: %s' % (i, path), end=' -> ')
        assert os.path.abspath(path) == path

        name = extract_name(path)
        path_txt = os.path.join(text_dir, '%s.txt' % name)
        print(path_txt, end=' ')
        pdftotext(path, path_txt, method)
        print(flush=True)


RE_SPACE = re.compile(r'[\t ]+', re.MULTILINE | re.DOTALL)
punctuation = string.punctuation
punctuation = punctuation.replace("-", "")  # don't remove hyphens
RE_BREAK = re.compile(r'(\w+)-([\n\f\r]+)(\w+)([%s]*)\s*' % punctuation,
                      re.MULTILINE | re.DOTALL)

hyphenated = set()


def unbreak(m):
    global hyphenated

    w00 = m.group(0)
    w0 = m.group(1) + '-' + m.group(2) + m.group(3)
    w1 = m.group(1) + '-' + m.group(3)
    w2 = m.group(1) + m.group(3)
    w1n = w1 + m.group(4) + '\n'
    w2n = w2 + m.group(4) + '\n'
    p0 = Pw(w0)
    p1 = Pw(w1)
    p2 = Pw(w1)
    if p1 < 1e-32 and p2 < 1e-34:
        p1a = Pw(m.group(1)) * Pw(m.group(3))
        if p1a > 1e-27:
            p1 = p1a
    probs = [(p, i) for i, p in enumerate([p0, p1, p2])]
    words = [w00, w1n, w2n]
    _, best = max(probs)

    if best != 2:
        hyphenated.add((w1, w2))
    return words[best]


def dehyphenate(text):
    """
        The businesses around newspapers, books, and mag-
        azines are changing on a daily basis; even still, global electronic com-
        munication over the Internet
     =>
        The businesses around newspapers, books, and magazines
        are changing on a daily basis; even still, global electronic communication
        over the Internet
    """
    assert isinstance(text, str), type(text)
    print([type(x) for x in (text, RE_BREAK, unbreak)])
    unbroke = RE_BREAK.sub(unbreak, text)
    return unbroke


def clean_file(path, path_cln, min_len=100):
    """Clean up text file `path` and write the resulting text to `path_cln`
        NOTE: This function also trims the text to length `MAX_DOC_SIZE`
    """
    assert path != path_cln
    text = text0 = utils.read_file(path)

    text = dehyphenate(text)

    text = text[:MAX_DOC_SIZE]
    if len(text) >= min_len:
        print('-' * 80)
        print(text[:200])
        print('-' * 80)
        utils.write_file(path_cln, text)
        return True, len(text0), len(text)
    return False, 0, 0


def clean_text_corpus(text_dir, clean_dir):
    """Clean up text files in `text_dir` and write the resulting text to `clean_dir`
        NOTE: This function also trims the text to length `MAX_DOC_SIZE`
    """
    os.makedirs(clean_dir, exist_ok=True)
    n = 0
    for path in glob(os.path.join(text_dir, "*.txt")):
        name = extract_name(path, whole=True)
        name = RE_SPACE.sub('_', name)
        assert ' ' not in name, name
        path_cln = os.path.join(clean_dir, name)
        ok, l0, ll = clean_file(path, path_cln)
        if ok:
            print('%3d: %-30s %4d->%4d' % (n, path_cln, l0, ll))
            n += 1

    print('-' * 80)
    for i, (w1, w2) in enumerate(sorted(hyphenated)):
        print('%4d: %-40s: %s' % (i, w1, w2))


pdf_dir = '~/testdata'
text_dir = '~/testdata.txt/deploy'
clean_dir = '~/testdata.clean/deploy'
pdf_dir = os.path.expanduser(pdf_dir)
text_dir = os.path.expanduser(text_dir)
clean_dir = os.path.expanduser(clean_dir)
print('pdf_dir=%s' % pdf_dir)
print('text_dir=%s' % text_dir)
print('clean_dir=%s' % clean_dir)


if __name__ == '__main__':
    if CONVERT_PDF:
        corpus_to_text(pdf_dir, text_dir)
    if CLEAN_TEXT:
        clean_text_corpus(text_dir, clean_dir)
