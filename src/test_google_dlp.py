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
# from google.cloud import datastore
import requests
from subprocess import CalledProcessError, Popen, PIPE
import json
from pprint import pprint
# from oauth2client.client import GoogleCredentials



# # Google Cloud Project ID. This can be found on the 'Overview' page at
# # https://console.developers.google.com
# PROJECT_ID = 'pc-doc-class'


# def get_client():
#     return datastore.Client(PROJECT_ID)


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


access_token = get_access_token()
print("access_token=%r" % access_token)

headers = {
    'Authorization': 'Bearer %s' % access_token,
    'Content-Type': 'application/json',
}

ehr = '''
Har is a 43 year old 6' 214 pound gentleman who is referred for
consultation by Dr. Harlan Oneil.  About a week ago he slipped on
the driveway at home and sustained an injury to his left ankle.
He was seen at Tri-City Hospital and was told he had a
fracture.  He was placed in an air splint and advised to be
partial weight bearing, and he is using a cane.  He is here for
routine follow-up.
Past medical history is notable for no ankle injuries previously.
He has a history of diabetes and sleep apnea.  He takes Prozac,
Cardizem, Glucophage and Amaryl.  He is also followed by Dr. Harold
Nutter for an arrhythmia.  He does not smoke.  He drinks
minimally.  He is a set designer at Columbia Pictures.

On examination today he has slight tenderness of the left ankle
about four fingerbreadths above the malleolus.  The malleolus is
non-tender medially or laterally with no ligamentous tenderness
either.  Dorsal flexion and plantar flexion is without pain.
There is no significant swelling.  There are no some skin changes
with some small abrasions proximally.  There is no fibular
tenderness proximally.  No anterior pain is noted.  No hindfoot,
midfoot or forefoot tenderness is noted.
I would like him to use a tube sock with his air cast.  He is
using a cane for ambulation.  His x-rays do not show a notable
fracture pattern today, and we will await the Radiology opinion.
I would like him to stay in the air splint with the sock.  I will
see him back in six weeks for review at the Boxborough office.
'''

ehr = '''



Record date: 2108-03-14

                     CAMPBELL EMERGENCY DEPT VISIT



VALDEZ,HARLAN,JR.   845-41-54-4                VISIT DATE: 03/14/08

The patient was seen and examined in the emergency department.  The

patient was seen by the Emergency Medicine resident.  I have

discussed the management with the resident.  I have also seen the

patient primarily and reviewed the medical record.  This is a brief

addendum to the medical record.

HISTORY OF PRESENTING COMPLAINT:  Briefly, this is a 45-year-old

male who complains of several days of nausea, vomiting, and left

lower quadrant discomfort.  He also describes intermittent chest

pain, which he has had for a number of months without significant

change.  He was sent in from his primary care doctor today with

this pain and was also noted to have some EKG changes.  The patient

has no chest pain at the time of evaluation in the emergency

department and no shortness of breath.

REVIEW OF SYSTEMS:  As indicated and otherwise negative.

PAST MEDICAL HISTORY:  As indicated in the chart.

SOCIAL HISTORY AND FAMILY HISTORY:  As indicated in the chart.

PHYSICAL EXAMINATION:  On physical examination, the patient is very

well-appearing, a smiling, very pleasant gentleman in no acute

distress.  The blood pressure is 119/90, the pulse 82, and the

temperature 97.9 degrees.  Normocephalic and atraumatic.  The chest

is clear to auscultation.  The heart has a regular rate and rhythm.

The abdomen is soft.  He has left lower quadrant tenderness.  He

also, of note on cardiovascular examination, has a soft murmur

which he says he has had since childhood.  The extremities are

normal.  The neurologic examination is non-focal.

THERAPY RENDERED/COURSE IN ED:  This is a gentleman with abdominal

pain who will receive a CAT scan to rule out diverticulitis.  He

has also had some non-specific ST changes on his EKG.  He is

pain-free at this time.  He does not describe a classic exertional

pattern for his chest pain, but given that he is a diabetic and

with EKG changes, he will also be admitted for rule out MI.  A CT

is pending at the time of this dictation.

DISPOSITION (including condition upon discharge):  As above.  The

patient's condition is currently stable.

___________________________________                    CK498/89095

JAY CARROLL, M.D.  JC72                                 D:03/14/08

                                                       T:03/14/08

Dictated by:  JAY CARROLL, M.D.  JC72
'''

ehr = '''
    Peter Williams is 25 years old.
    His SSN is 321-67-2114.
    He lives in 1 Burke Rd, Camberwell
    His phone number is 0566 223 999
    Peter's Australian tax file number is 213 824 911

'''
text = '''{
    "items": [
        {
            "type": "text/plain",
            "value": "%s",
        },
    ],
    "inspectConfig": {
        "infoTypes": [],
        "minLikelihood": "LIKELIHOOD_UNSPECIFIED",
         "maxFindings": 100,
        "includeQuote": true
    }
}''' % ehr

text_deidentify = '''{
    "items": [
        {
            "type": "text/plain",
            "value": "%s",
        },
    ]

}''' % ehr.replace('\n', ' ')

#  0         1         2
#  0123456789012345678901234567890123
#                      |19          |33
# "My phone number is (555) 253-0000.",

result = '''{
  "results": [
    {
      "findings": [
        {
          "quote": "(555) 253-0000",
          "infoType": {
            "name": "PHONE_NUMBER"
          },
          "likelihood": "VERY_LIKELY",
          "location": {
            "byteRange": {
              "start": "19",
              "end": "33"
            },
            "codepointRange": {
              "start": "19",
              "end": "33"
            }
          },
          "createTime": "2017-10-09T04:31:03.534Z"
        }
      ]
    }
  ]
}'''


# data = open('inspect-request.json')
api_base = 'https://dlp.googleapis.com/v2beta1/content:'
api_inspect = api_base + 'inspect'
api_deidentify = api_base + 'deidentify'


def inspect(text):
    infoTypes = set()
    r = requests.post('https://dlp.googleapis.com/v2beta1/content:inspect', headers=headers, data=text)
    # r = requests.post(api_deidentify, headers=headers, data=text_deidentify)
    # print(r)
    # print(r.text)
    # print(r.ok)

    d = json.loads(r.text)
    # print('d=%s' % type(d))
    # pprint(d)
    results = d['results']
    # print('results=%s' % type(results))
    # pprint(results)
    for i, r in enumerate(results):
        # print('results[%d]=%s %d' % (i, type(r), len(r)))
        # pprint(r)
        findings = r['findings']
        # print('findings=%s %d' % (type(findings), len(findings)))
        # pprint(findings)
        for j, f in enumerate(findings):
            print('findings[%d]=%s %d' % (j, type(f), len(f)))
            pprint(f)

            print(i, j, f['infoType'])
            infoTypes.add(f['infoType']['name'])

    return infoTypes


infoTypes = set()
it = inspect(text)
infoTypes |= it
print(sorted(infoTypes))


# if __name__ == '__main__':
#     client = get_client()
#     print('client=%s' % client)
