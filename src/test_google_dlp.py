"""
    gcloud auth print-access-token
    ya29.El_eBGZK0Fp81PLhX69b0b2rZc00B7iMV-FVzEZK-qpTcRb8ayzU1hhZx5WaTXFiYYrvt2YwVKPtwDZ9gIFQtsmHjiXDg46x-7Poxlo7Fgf2sIpmdT4ZqZ20u99KySl0Sg

curl -s \
  -H "Authorization: ya29.El_eBGZK0Fp81PLhX69b0b2rZc00B7iMV-FVzEZK-qpTcRb8ayzU1hhZx5WaTXFiYYrvt2YwVKPtwDZ9gIFQtsmHjiXDg46x-7Poxlo7Fgf2sIpmdT4ZqZ20u99KySl0Sg" \
  -H "Content-Type: application/json" \
  https://dlp.googleapis.com/v2beta1/content:inspect -d @inspect-request.json
"""
from google.cloud import datastore
import requests


# Google Cloud Project ID. This can be found on the 'Overview' page at
# https://console.developers.google.com
PROJECT_ID = 'pc-doc-class'


def get_client():
    return datastore.Client(PROJECT_ID)


access_token = 'ya29.El_eBGZK0Fp81PLhX69b0b2rZc00B7iMV-FVzEZK-qpTcRb8ayzU1hhZx5WaTXFiYYrvt2YwVKPtwDZ9gIFQtsmHjiXDg46x-7Poxlo7Fgf2sIpmdT4ZqZ20u99KySl0Sg'
access_token = 'ya29.El_eBDwN46e6E2dEBisB3DfFVcCWjI2cKTBUd9lj7MkDyEpWn4czG64WGP3D3M32h041jLBaeXdkCt0Deu4izhXerK5v5RTmfDZm4eILbOJQT7pTlinIH4hcAqBiZAfa0Q'

headers = {
    'Authorization': access_token,
    'Content-Type': 'application/json',
}

data = open('inspect-request.json')
r = requests.post('https://dlp.googleapis.com/v2beta1/content:inspect', headers=headers, data=data)
print(r)
print(r.text)


# if __name__ == '__main__':
#     client = get_client()
#     print('client=%s' % client)
