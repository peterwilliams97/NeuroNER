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
from neuroner import NeuroNER
from make_text_corpus import pdftotext


dataset_text_folder = '/Users/pcadmin/phi.data/deploy'
dataset_text_folder_pdf = '/Users/pcadmin/phi.data.pdf'
output_folder = '/Users/pcadmin/phi.output'
path_txt = os.path.join(dataset_text_folder, 'text.txt')
parameters_filepath = 'parameters_phi_data.ini'

os.makedirs(dataset_text_folder, exist_ok=True)


def predict(path):
    """ NeuroNER main method
    Args:
        parameters_filepath the path to the parameters file
        output_folder the path to the output folder
    """
    pdftotext(path, path_txt)
    files = list(glob(os.path.join(dataset_text_folder, '*')))
    print('files=%d %s' % (len(files), files))
    assert files

    nn = NeuroNER(parameters_filepath=parameters_filepath)
    nn.fit()
    nn.close()


predict('/Users/pcadmin/testdata/Sluice networks.pdf')

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
