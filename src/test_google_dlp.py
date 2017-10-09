"""
    https://developers.google.com/identity/protocols/application-default-credentials

    gcloud auth print-access-token
    ya29.El_eBGZK0Fp81PLhX69b0b2rZc00B7iMV-FVzEZK-qpTcRb8ayzU1hhZx5WaTXFiYYrvt2YwVKPtwDZ9gIFQtsmHjiXDg46x-7Poxlo7Fgf2sIpmdT4ZqZ20u99KySl0Sg

curl -s \
  -H "Authorization: ya29.El_eBGZK0Fp81PLhX69b0b2rZc00B7iMV-FVzEZK-qpTcRb8ayzU1hhZx5WaTXFiYYrvt2YwVKPtwDZ9gIFQtsmHjiXDg46x-7Poxlo7Fgf2sIpmdT4ZqZ20u99KySl0Sg" \
  -H "Content-Type: application/json" \
  https://dlp.googleapis.com/v2beta1/content:inspect -d @inspect-request.json
"""
from google.cloud import datastore
import requests
from subprocess import CalledProcessError, Popen, PIPE
# from oauth2client.client import GoogleCredentials



# Google Cloud Project ID. This can be found on the 'Overview' page at
# https://console.developers.google.com
PROJECT_ID = 'pc-doc-class'


def get_client():
    return datastore.Client(PROJECT_ID)


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
    # assert '\n' not in access_token, access_token
    return access_token


# credentials = GoogleCredentials.get_application_default()


access_token = 'ya29.El_eBGZK0Fp81PLhX69b0b2rZc00B7iMV-FVzEZK-qpTcRb8ayzU1hhZx5WaTXFiYYrvt2YwVKPtwDZ9gIFQtsmHjiXDg46x-7Poxlo7Fgf2sIpmdT4ZqZ20u99KySl0Sg'
# access_token = 'ya29.El_eBDwN46e6E2dEBisB3DfFVcCWjI2cKTBUd9lj7MkDyEpWn4czG64WGP3D3M32h041jLBaeXdkCt0Deu4izhXerK5v5RTmfDZm4eILbOJQT7pTlinIH4hcAqBiZAfa0Q'
# access_token = 'ya29.El_fBE3_8APgZiqJ4T8CyAeR40vZSeuAFLZu-Y-097oXSLbI8r1hHPeJ7hLJRDs4Cr9Jjhz4PYnMe6pIVvRU39RXeCbHYyINSGbOjDhxC_6wiulZq-gqvj3sc5l71RwaNQ'
# access_token = 'ya29.El_fBM32I-n39FZ7AbrWnUrPMHSm3AZmnr8vCfmmMFVsLPK6tirgHJSu9Ml8TgHo8YVN9ga3VSPr40AhNg6dnvcmCgP96BEiN6hFEB7fKn6vSboVJnOfnX82NVbAAm9Qow'
access_token = get_access_token()
print("access_token=%r" % access_token)

headers = {
    'Authorization': 'Bearer %s' % access_token,
    'Content-Type': 'application/json',
}

text = '''{
    "items": [
        {
            "type": "text/plain",
            "value": "My phone number is (555) 253-0000.",
        },
    ],
    "inspectConfig": {
        "infoTypes": [],
        "minLikelihood": "LIKELIHOOD_UNSPECIFIED",
        "maxFindings": 0,
        "includeQuote": true
    }
}'''

# data = open('inspect-request.json')
r = requests.post('https://dlp.googleapis.com/v2beta1/content:inspect', headers=headers, data=text)
print(r)
print(r.text)
print(r.ok)


# if __name__ == '__main__':
#     client = get_client()
#     print('client=%s' % client)
