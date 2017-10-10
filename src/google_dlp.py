"""
    Lots of documentantion on how GCP authentication is supposed to work
    https://developers.google.com/identity/protocols/application-default-credentials
    https://google-cloud-python.readthedocs.io/en/latest/core/auth.html#overview

    but we just do
        gcloud auth print-access-token
    and stick the result in an Authorization Bearer token

 'PHONE_NUMBER' 'UNLIKELY', '321-67-2114'}
 'US_SOCIAL_SECURITY_NUMBER'}, '321-67-2114'

 'CANADA_BC_PHN'},'0566 223 999'

f'PHONE_NUMBER'},'VERY_LIKELY','0566 223 999'
 'PHONE_NUMBER'}, 'UNLIKELY', '213 824 911'


"""
import requests
from subprocess import CalledProcessError, Popen, PIPE
import json
from collections import defaultdict
import glob
import os
from utils import read_file, write_file
# from pprint import pprint


def run_command(cmd):
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    return p.returncode, stdout, stderr


def get_access_token():
    cmd = ['gcloud', 'auth', 'print-access-token']
    rc, stdout, stderr = run_command(cmd)
    if rc != 0:
        print('-' * 80)
        print(stderr)
        raise CalledProcessError(rc, cmd)
    # print(type(stdout))
    # print(stdout)
    # print(str(stdout, 'utf-8'))
    access_token = str(stdout, 'utf-8').strip('\n').strip()
    return access_token


access_token = None


def get_headers():
    global access_token
    if not access_token:
        access_token = get_access_token()
        print("access_token=%r" % access_token)
    headers = {
        'Authorization': 'Bearer %s' % access_token,
        'Content-Type': 'application/json',
    }
    return headers


# json_req = '''{
#     "items": [
#         {
#             "type": "text/plain",
#             "value": "%s",
#         },
#     ],
#     "inspectConfig": {
#         "infoTypes": [],
#         "minLikelihood": "LIKELIHOOD_UNSPECIFIED",
#          "maxFindings": 0,
#         "includeQuote": true
#     }
# }'''

dict_req = {
    "items": [
        {
            "type": "text/plain",
            "value": "%s",
        },
    ],
    "inspectConfig": {
        "infoTypes": [],
        "minLikelihood": "LIKELIHOOD_UNSPECIFIED",
        "maxFindings": 0,
        "includeQuote": True
    }
}


api_base = 'https://dlp.googleapis.com/v2beta1/content:'
api_inspect = api_base + 'inspect'
api_deidentify = api_base + 'deidentify'


def inspect(text):
    headers = get_headers()

    text = text[:100000]
    text = text.replace('"', '\\"')
    # text = text.encode('utf-8')

    d = dict_req.copy()
    d["items"][0]["value"] = text
    data = json.dumps(d)

    r = requests.post('https://dlp.googleapis.com/v2beta1/content:inspect', headers=headers, data=data)
    if not r.ok:
        print('=' * 80)
        print(text)
        print(type(text), len(text))
        print('-' * 80)
        print(data)
        print('=' * 80)
        print(r.text)
        print('^' * 80)
        print(type(text), len(text))
    assert r.ok, (r, r.text)
    return r.text


def process_file(path, path_out):
    text = read_file(path)
    result = inspect(text)
    write_file(path_out, result)


def process_dir(data_dir, results_dir):
    assert os.path.exists(data_dir), data_dir
    os.makedirs(results_dir, exist_ok=True)

    text_filepaths = sorted(glob.glob(os.path.join(data_dir, '*.txt')))
    for path in text_filepaths:
        print(path, end='->')
        name = os.path.splitext(os.path.basename(path))[0]
        path_out = os.path.join(results_dir, '%s.json' % name)
        process_file(path, path_out)
        print(os.path.abspath(path_out))


def inspect_result(path):
    infoTypes = defaultdict(list)

    with open(path, 'r') as ff:
        d = json.load(ff)
    # print('d=%s' % type(d))
    # pprint(d)
    results = d['results']
    # print('results=%s' % type(results))
    # pprint(results)
    for i, r in enumerate(results):
        # print('results[%d]=%s %d' % (i, type(r), len(r)))
        # pprint(r)
        if 'findings' not in r:
            continue
        findings = r['findings']
        # print('findings=%s %d' % (type(findings), len(findings)))
        # pprint(findings)
        for j, f in enumerate(findings):
            print('findings[%d]=%s %d' % (j, type(f), len(f)))
            # pprint(f)

            # print(i, j, f['infoType'])
            t = f['infoType']['name']
            quote = f['quote']
            infoTypes[t].append(quote)

    return infoTypes


def list2freq(quotes):
    freq = defaultdict(int)
    for q in quotes:
        freq[q] += 1
    return sorted(freq, key=lambda x: (-freq[x], x))


def analyze_results(results_dir):
    json_filepaths = sorted(glob.glob(os.path.join(results_dir, '*.json')))
    typeQuotes = defaultdict(list)
    for path in json_filepaths:
        tq = inspect_result(path)
        for t, q in tq.items():
            typeQuotes[t].extend(q)
    for i, t in enumerate(sorted(typeQuotes)):
        quotes = list2freq(typeQuotes[t])
        print('%2d: %-25s %4d %s' % (i, t, len(quotes), quotes[:5]))


data_dir = '/Users/pcadmin/testdata.clean/deploy'
results_dir = '../output/google.dlp/testdata.clean/deploy'

data_dir = '../data/i2b2_2014_deid/test'
results_dir = '../output/google.dlp/i2b2_2014_deid/test'


if True:
    process_dir(data_dir, results_dir)
if True:
    analyze_results(results_dir)
