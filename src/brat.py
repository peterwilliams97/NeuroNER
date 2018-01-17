"""
    path_list=1304
     0:            DATE: 12482 ['04/07/69', '04/15/69', '2069-04-07', '2075-01-07', 'November']
     1:          DOCTOR:  4797 ['Gilbert P. Perez', 'Hobbs', 'XGT', 'Xzavian G. Tavares', 'holmes']
     2:        HOSPITAL:  2312 ['BCH', 'EHMS', 'SILVER RIDGE', 'Silver Ridge', 'Southwest Texas Medical Center']
     3:         PATIENT:  2195 ['OROZCO, KYLE', 'OROZCO,KYLE', 'Villegas', 'Villegas, Yosef', 'Yosef Villegas']
     4:             AGE:  1997 ['58', '61', '65', '70', '71']
     5:   MEDICALRECORD:  1033 ['560-40-78-5', '56040785', '643-65-59-5', '64365595', '8249813']
     6:            CITY:   654 ['Bangdung', 'Mansfield', 'OLNEY', 'Olney', 'Pinehurst']
     7:           PHONE:   524 ['(215)579-9664', '(680) 317-3494', '207-155-2827', '5-4228', '84710']
     8:           STATE:   504 ['AL', 'NV', 'OH', 'VA', 'Virginia']
     9:           IDNUM:   456 ['1-1277442', '7-9617124 SJZvdbs', 'NE270/9072', 'VF918/05141', 'XW277/90683']
    10:      PROFESSION:   413 ['Customs Broker', 'Personnel Officer', 'journalist', 'news writer', 'political journalist']
    11:        USERNAME:   356 ['FB59', 'HO97', 'KT40', 'PU38', 'VB07']
    12:          STREET:   352 ['3 Eaton Place', '494 Fairhaven Road', '803 FAIRHAVEN ROAD', '86 Cote Avenue', '870 Newburgh Street']
    13:             ZIP:   352 ['19792', '23751', '29473', '35594', '54854']
    14:    ORGANIZATION:   206 ["Amy's Baking Company", 'Casco Bay Shipping', "Pilgrim's Pride", 'Prudential', 'Vassar']
    15:         COUNTRY:   183 ['Algeria', 'Columbia', 'Columbian', 'Finland', 'Paraguay']
    16:  LOCATION-OTHER:    17 ['Cape Cod', 'Central Park', 'Rockefeller Centre', 'Storting', 'global']
    17:          DEVICE:    15 ['4712198', '5167DH/20', '5435', 'CTE 226', 'QQ 626']
    18:             FAX:    10 ['(251)628-xxxx', '(385) 031-7905', '595-442-5450', '664-577-0339', '966-221-9723']
    19:           EMAIL:     5 ['gmichael@KCM.ORG', 'iparedes@oachosp.org', 'vmeadows@sbhnc.org', 'yfcooley@wsh.org']
    20:             URL:     2 ['Valley Hospital Web Services', 'Web Services']
    21:           BIOID:     1 ['L5317YR']
    22:      HEALTHPLAN:     1 ['state insurance']

    ['DATE', 'DOCTOR', 'HOSPITAL', 'PATIENT', 'AGE', 'MEDICALRECORD', 'CITY', 'PHONE', 'STATE', 'IDNUM', 'PROFESSION',
     'USERNAME', 'STREET', 'ZIP', 'ORGANIZATION', 'COUNTRY', 'LOCATION-OTHER', 'DEVICE', 'FAX', 'EMAIL', 'URL', 'BIOID',
     'HEALTHPLAN']

"""
import os
from glob import glob
from collections import defaultdict
import re


RE_SPACE = re.compile('\s+')


def text_path(ann):
    name = os.path.splitext(ann)[0]
    return '%.txt' % name


nn = os.path.expanduser('~/code/NeuroNER/data/i2b2_2014_deid')
assert os.path.exists(nn), nn

path_list = [p for p in glob(os.path.join(nn, '**'), recursive=True)
             if os.path.splitext(p)[-1] == '.ann']
print('%d files' % len(path_list))
size_list = [os.path.getsize(p) for p in path_list]
total_size = sum(size_list)
print('total: %d bytes' % total_size)
print('min : %7.2f bytes' % min(size_list))
print('mean: %7.2f bytes' % (total_size / len(path_list)))
print('max : %7.2f bytes' % max(size_list))

entities = defaultdict(int)
entity_vals = defaultdict(set)

for path in path_list:
    # print(path)
    with open(path, 'rt') as f:
        for line in f:
            line = line.rstrip('\n')
            parts = RE_SPACE.split(line)
            # print(line, list(enumerate(parts)))
            entity = parts[1]
            value = ' '.join(parts[4:])
            entities[entity] += 1
            if entity not in entity_vals or len(entity_vals[entity]) < 5:
                entity_vals[entity].add(value)


def entity_key(entity):
    return -entities[entity], entity


print('path_list=%d' % len(path_list))
entity_list = sorted(entities, key=entity_key)
for i, entity in enumerate(sorted(entities, key=entity_key)):
    n = entities[entity]
    vals = sorted(entity_vals[entity])
    print('%2d: %15s: %5d %s' % (i, entity, n, vals))
print(entity_list)
