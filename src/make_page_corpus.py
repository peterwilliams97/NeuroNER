"""
    PDF to text conversion
"""
import os
from glob import glob
from collections import defaultdict
import hashlib
from subprocess import CalledProcessError, Popen, PIPE
import re
from utils_peter import save_json
from html_to_text import update_summary

KBYTE = 1024
MBYTE = 1024 * 1024

# Settings
min_size = 1 * KBYTE
max_size = 10 * MBYTE


permission_errors = [
    'You do not have permission to extract text',
    'Permission Error'
]


def run_command(cmd, raise_on_error=True):
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


def pdf_to_pages(pdf_path):
    """Extract pages from PDF file `pdf_path` using PdfBox
        Returns: ok, text, pages
            ok: Analysis succeeded. PDF is valid
            text: Text of PDF in html format
            pages: Pages of PDF in html format
    """
    cmd = ['java', '-jar', 'pdfbox-app-2.0.7.jar', 'ExtractText',
           '-html', '-console', pdf_path]
    retcode, stdout, stderr = run_command(cmd, raise_on_error=False)
    ok = retcode == 0
    if not ok:
        print('FAILURE: retcode=%d stderr=<%s>' % (retcode, stderr))
        return ok, '', []
    text = stdout.decode('utf-8')
    sep = '<div style="page-break-before:always; page-break-after:always">'
    return ok, text, text.split(sep)[1:]


# Num Pages: 1
RE_NUMPAGES = re.compile(b'Num Pages:\s+(\d+)')


def pdf_num_pages(pdf_path):
    """Use Unidoc to count pages in PDF file `pdf_path`"""
    cmd = ['./pdf_info', pdf_path]
    retcode, stdout, stderr = run_command(cmd, raise_on_error=False)
    ok = retcode == 0
    if not ok:
        return ok, 0
    m = RE_NUMPAGES.search(stdout)
    return ok, int(m.group(1))


def save_pdf_summary(pdf_path, summary_path):
    """Extract text from `pdf`, break it into pages and write the summary to 'summary_path
    """
    ok, text, pages_html = pdf_to_pages(pdf_path)
    if not ok:
        return
    print('save_pdf_summary: %s->%s' % (pdf_path, summary_path))

    summary = {
        'name': os.path.basename(pdf_path),
        'n_pages': len(pages_html),
        'n_chars': sum(len(page) for page in pages_html),
        'pages': pages_html,
        'text': text,
    }
    update_summary(summary)

    outpath = os.path.abspath('%s.json' % summary_path)
    save_json(outpath, summary)


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


def corpus_to_text(pdf_dir, summary_dir):
    """Convert the unique PDF files in `pdf_dir` to file with the same name in `summary_dir`
    """
    keepers = corpus_to_keepers(pdf_dir)

    os.makedirs(summary_dir, exist_ok=True)

    for i, pdf_path in enumerate(keepers):

        size = os.path.getsize(pdf_path)
        print('%3d: %s [%.1f]' % (i, pdf_path, size / MBYTE), end=' -> ')
        assert os.path.abspath(pdf_path) == pdf_path

        if min_size <= size <= max_size:
            name = extract_name(pdf_path)
            summary_path = os.path.join(summary_dir, '%s.json' % name)
            print(summary_path, end=' ')
            save_pdf_summary(pdf_path, summary_path)
        print(flush=True)


pdf_dir = '~/testdata'
summary_dir = '~/testdata.pages0'
pdf_dir = os.path.expanduser(pdf_dir)
summary_dir = os.path.expanduser(summary_dir)
print('pdf_dir=%s' % pdf_dir)
print('summary_dir=%s' % summary_dir)


if __name__ == '__main__':
    corpus_to_text(pdf_dir, summary_dir)
