#!/usr/bin/env python
"""
Very simple HTTP server in python.

Usage::
    ./dummy-web-server.py [<port>]

Send a GET request::
    curl http://localhost

Send a HEAD request::
    curl -I http://localhost

Send a POST request::
    curl -d "foo=bar&bin=baz" http://localhost

"""
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import unquote
import os
from glob import glob
from time import clock
from collections import defaultdict
import shutil
from neuroner import NeuroNER
from make_text_corpus import pdftotext
from brat_to_conll import get_entities_from_brat
from utils import write_file, read_file


dataset_root = '/Users/pcadmin/phi.data'
dataset_text_folder = os.path.join(dataset_root, 'deploy')
dataset_text_folder_pdf = '/Users/pcadmin/phi.data.pdf'
output_folder = '/Users/pcadmin/phi.output'
path_txt = os.path.join(dataset_text_folder, 'text.txt')
parameters_filepath = 'parameters_phi_data.ini'

shutil.rmtree(dataset_root)
os.makedirs(dataset_text_folder, exist_ok=True)


def abridge(text, maxlen=200):
    if len(text) <= 2 * maxlen:
        return text
    return '%s<br>...<br>%s' % (text[:maxlen], text[-maxlen:])


def markup(text_path, ann_path):
    text, ann = get_entities_from_brat(text_path, ann_path)
    print('&' * 80)
    print(len(ann))
    for i, a in enumerate(ann[:5]):
        s = text[a['start']:a['end']]
        print('%3d: %10s %s %s' % (i, a['type'], a['text'], s))
    gaps = [text[a['end']:b['start']] for a, b in zip(ann[:-1], ann[1:])]
    gaps = [text[:ann[0]['start']]] + gaps + [text[ann[-1]['end']:]]
    gaps = [abridge(g) for g in gaps]
    words = ['<b>%s</b> [%s] ' % (a['text'], a['type']) for a in ann]
    for i, (g, w) in enumerate(list(zip(gaps, words))[:5]):
        print('%3d: "%s" -- "%s"' % (i, g, w))
    print(text[:ann[5]['end']])

    gw = [g + w for g, w in zip(gaps, words)]
    gw.append(gaps[-1])
    marked = '<html><body>%s</body></html>' % ''.join(gw)

    write_file('blah.html', marked)


def sort_texts(texts):
    text_count = defaultdict(int)
    text_unique = []
    for text in texts:
        if text not in text_count:
            text_unique.append(text)
        text_count[text] += 1

    def key(text):
        return -text_count[text], text_unique.index(text)

    return sorted(text_count, key=key)


if False:
    texts = ['a', 'b', 'b', 'c']
    print(sort_texts(texts))
    assert False


def summarize(entities, max_texts=20):
    summary = defaultdict(list)
    for e in entities:
        summary[e['type']].append(e['text'])

    def key(tp):
        return len(summary[tp]), tp

    print('-' * 80)
    for i, tp in enumerate(sorted(summary)):
        texts = summary[tp]
        print('%2d: %20s: %4d %s' % (i, tp, len(texts), sort_texts(texts)[:max_texts]))


def predict(path):
    """ NeuroNER main method
    Args:
        parameters_filepath the path to the parameters file
        output_folder the path to the output folder
    """
    t0 = clock()
    pdftotext(path, path_txt)
    t1 = clock()
    files = list(glob(os.path.join(dataset_text_folder, '*')))
    print('files=%d %s' % (len(files), files))
    assert files

    nn = NeuroNER(parameters_filepath=parameters_filepath)
    text = read_file(path_txt)
    entities = nn.predict(text)
    # nn.fit()
    nn.close()
    t2 = clock()
    print('*' * 80)
    print(path, len(text))
    print('pdftotext=%4.1f sec' % (t1 - t0))
    print('  predict=%4.1f sec' % (t2 - t1))
    print('    total=%4.1f sec' % (t2 - t0))
    summarize(entities)
    print(nn.stats_graph_folder_)


# predict('/Users/pcadmin/testdata/LIDS_TO_.pdf')
# predict('/Users/pcadmin/testdata/PaperCutMF-Top-10-Reasons.pdf')
# predict('/Users/pcadmin/testdata/Spatial Transformer Networks.pdf')
predict('/Users/pcadmin/testdata/cover_and_thesis.pdf')


markup('/Users/pcadmin/phi.output/phi_2017-10-13_17-20-11-176572/brat/deploy/text.txt',
       '/Users/pcadmin/phi.output/phi_2017-10-13_17-20-11-176572/brat/deploy/text.ann')
assert False

# gets = '\n'.join(['<h%d>GET! %d</h%d>' % (i, i, i) for i in range(1, 7)])
# print(gets)
# text = '<html><body>%s</body></html>' % gets
# print(text)
# btext = bytearray(text, 'utf-8')
# print(btext)

template = '''{
    "pdf": "%s",
    "id": %d
}'''


class S(BaseHTTPRequestHandler):
    def _set_headers(self):
        print('_set_headers')
        self.send_response(200)
        # self.send_header('Content-type', 'text/html')
        self.send_header("Content-type", "application/json")
        self.end_headers()

    def do_GET(self):
        print('do_GET', self.path)
        self._set_headers()
        self.wfile.write(bytes('\r\n', 'utf-8'))

        s = template % (unquote(self.path), 1234)

        output = bytearray(s, 'utf-8')
        self.wfile.write(output)

        # self.wfile.write(btext)

    def do_HEAD(self):
        print('do_HEAD')
        self._set_headers()

    def do_POST(self):
        # Doesn't do anything with posted data
        print('do_POST')
        self._set_headers()
        self.wfile.write(b'<html><body><h1>POST!</h1></body></html>')


def run(port=9999):
    server_address = ('', port)
    httpd = HTTPServer(server_address, S)
    print('Starting httpd...')
    httpd.serve_forever()


if __name__ == "__main__":
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()