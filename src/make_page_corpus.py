"""
    PDF to text conversion
"""
import os
from glob import glob
from collections import defaultdict
import hashlib
import string
from subprocess import CalledProcessError, Popen, PIPE
import utils
import re
from ngrams import Pw
# import jsonlines
import json
from html_to_text import update_summary


# Settings
MAX_DOC_SIZE = -1
CONVERT_PDF = True
CLEAN_TEXT = True
MBYTE = 1024 * 1024
min_size = 5 * MBYTE
max_size = 30 * MBYTE


def quote(s):
    if not RE_SPACE.search(s):
        return s
    s = s.replace('"', '\\"')
    s = '"%s"' % s
    print('$$$', s)
    return s


permission_errors = [
    'You do not have permission to extract text',
    'Permission Error'
]


def run_command(cmd, raise_on_error=True):
    # cmd = [quote(s) for s in cmd]
    # print('cmd=%s' % cmd)

    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()

    if p.returncode != 0:
        so = ''
        se = ''
        if stdout:
            print('~' * 80)
            so = stdout.decode("utf-8")
            print(so)
        if stderr:
            print('^' * 80)
            se = stderr.decode("utf-8")
            print(se)

        if not any(pe in s for s in (so, se) for pe in permission_errors):
            print('-' * 80)
            print('run_command real error')
            print(' '.join(cmd))
            if raise_on_error:
                raise CalledProcessError(p.returncode, cmd)

    return p.returncode, stdout, stderr


def pdf_to_pages(pdf):
    """pdfbox works best"""
    # tmp = './aaa.txt'
    cmd = ['java', '-jar', 'pdfbox-app-2.0.7.jar', 'ExtractText',
           '-html', '-console', pdf]
    retcode, stdout, stderr = run_command(cmd, raise_on_error=False)
    # print(' '.join(cmd))
    # assert False
    # assert retcode == 0, 'retcode=%d stderr=<%s>' % (retcode, stderr)
    ok = retcode == 0
    if not ok:
        print('FAILURE: retcode=%d stderr=<%s>' % (retcode, stderr))
        return ok, '', []
    text = stdout.decode('utf-8')
    # <div style="page-break-before:always; page-break-after:always">
    sep = '<div style="page-break-before:always; page-break-after:always">'
    return ok, text, text.split(sep)[1:]
    # with open(tmp, 'rt') as f:
    #     text = f.read()
    # return text


 # Num Pages: 1
RE_NUMPAGES = re.compile(b'Num Pages:\s+(\d+)')


def pdf_num_pages(pdf):
    """pdfbox works best"""
    cmd = ['./pdf_info', pdf]
    retcode, stdout, stderr = run_command(cmd, raise_on_error=False)
    ok = retcode == 0
    if not ok:
        return ok, 0
    m = RE_NUMPAGES.search(stdout)
    return ok, int(m.group(1))


def pdftotext(pdf, output):
    """Extract text from `pdf`, break it into pages and write summary to 'output"""
    # n_pages = pdf_num_pages(pdf)
    ok, text, pages_html = pdf_to_pages(pdf)
    if not ok:
        return
    page_list = []
    print(pdf)
    print(output)
    # print(n_pages)
    for page in pages_html:
        page_list.append(page)
        # print('-' * 80)
        # print(i, len(page))
        # print(page)

    summary = {
        'name': pdf,
        'n_pages': len(pages_html),
        'n_chars': sum(len(page) for page in page_list),
        'pages': page_list,
        'text': text,
    }
    update_summary(summary)

    outpath = os.path.abspath('%s.json' % output)
    with open(outpath, 'w') as f:
        json.dump(summary, f, indent=4, sort_keys=True)
    # with jsonlines.open(outpath, mode='w', sort_keys=True) as f:
    #     f.write(summary)

    # assert len(pages_html) == n_pages, (len(pages_html), n_pages, outpath)


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

        size = os.path.getsize(path)
        print('%3d: %s [%.1f]' % (i, path, size / MBYTE), end=' -> ')
        assert os.path.abspath(path) == path

        if min_size <= size <= max_size:
            name = extract_name(path)
            path_txt = os.path.join(text_dir, name)
            print(path_txt, end=' ')
            pdftotext(path, path_txt)
        print(flush=True)


# RE_SPACE = re.compile(r'[\t ]+', re.MULTILINE | re.DOTALL)
# punctuation = string.punctuation
# punctuation = punctuation.replace("-", "")  # don't remove hyphens
# RE_BREAK = re.compile(r'(\w+)-([\n\f\r]+)(\w+)([%s]*)\s*' % punctuation,
#                       re.MULTILINE | re.DOTALL)

# hyphenated = set()


# def unbreak(m):
#     global hyphenated

#     w00 = m.group(0)
#     w0 = m.group(1) + '-' + m.group(2) + m.group(3)
#     w1 = m.group(1) + '-' + m.group(3)
#     w2 = m.group(1) + m.group(3)
#     w1n = w1 + m.group(4) + '\n'
#     w2n = w2 + m.group(4) + '\n'
#     p0 = Pw(w0)
#     p1 = Pw(w1)
#     p2 = Pw(w1)
#     if p1 < 1e-32 and p2 < 1e-34:
#         p1a = Pw(m.group(1)) * Pw(m.group(3))
#         if p1a > 1e-27:
#             p1 = p1a
#     probs = [(p, i) for i, p in enumerate([p0, p1, p2])]
#     words = [w00, w1n, w2n]
#     _, best = max(probs)

#     # assert m.group(1) != 'indi' or words[best] == 'individual\n', '"%s" %s %s %s "%s"' % (
#     #                        m.group(0), m.groups(), [p0, p1, p2],
#     #                        best, words[best])

#     if best != 2:
#         hyphenated.add((w1, w2))
#     return words[best]


# def dehyphenate(text):
#     """
#         The businesses around newspapers, books, and mag-
#         azines are changing on a daily basis; even still, global electronic com-
#         munication over the Internet
#      =>
#         The businesses around newspapers, books, and magazines
#         are changing on a daily basis; even still, global electronic communication
#         over the Internet
#     """
#     assert isinstance(text, str), type(text)
#     # print([type(x) for x in (text, RE_BREAK, unbreak)])
#     unbroke = RE_BREAK.sub(unbreak, text)
#     return unbroke


def clean_file(path, path_cln, min_len=100):
    """Clean up text file `path` and write the resulting text to `path_cln`
        NOTE: This function also trims the text to length `MAX_DOC_SIZE`
    """
    assert path != path_cln
    text = text0 = utils.read_file(path)

    text = dehyphenate(text)

    if MAX_DOC_SIZE > 0:
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
text_dir = '~/testdata.pages0'
clean_dir = '~/testdata.pages0.clean'
pdf_dir = os.path.expanduser(pdf_dir)
text_dir = os.path.expanduser(text_dir)
clean_dir = os.path.expanduser(clean_dir)
print('pdf_dir=%s' % pdf_dir)
print('text_dir=%s' % text_dir)
print('clean_dir=%s' % clean_dir)


if __name__ == '__main__':
    corpus_to_text(pdf_dir, text_dir)
    clean_text_corpus(text_dir, clean_dir)