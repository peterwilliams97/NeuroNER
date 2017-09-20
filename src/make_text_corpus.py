'''
    Miscellaneous utility functions
'''
import os
from glob import glob
from collections import defaultdict
import hashlib
# from shutil import copyfile
from subprocess import check_output, STDOUT, CalledProcessError, Popen, PIPE


def run_command(cmd):
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    return p.returncode, stdout, stderr


def pdftotext(pdf, txt):
    cmd = ['pdftotext', pdf, txt]
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


pdf_dir = '~/testdata'
text_dir = '~/testdata.txt/deploy'

pdf_dir = os.path.expanduser(pdf_dir)
text_dir = os.path.expanduser(text_dir)
print('pdf_dir=%s' % pdf_dir)
print('text_dir=%s' % text_dir)

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
directories = sorted({os.path.dirname(os.path.join(text_dir, extract_name(path, start=pdf_dir, whole=True)))
                     for path in keepers})

os.makedirs(text_dir, exist_ok=True)
# for i, path in enumerate(directories):
#     print('Making directory %d: %s' % (i, path))
#     os.makedirs(path, exist_ok=True)


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
    print()
