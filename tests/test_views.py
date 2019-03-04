import datetime
from dateutil.parser import parse as dateutilparse
import json
import os
import pytest
import pytz
import time
import urllib.parse

from cdr.api.models import ClinicalDoc
from cdr.api.models import parse_problem_list
from tests import client


def utc_now():
    """ datetime does have a utcnow method, but it doesn't contain tz """
    utc = pytz.timezone('UTC')
    n = datetime.datetime.now(utc)
    return n


def test_upload(client):
    fp = "/tmp/whatever"

    j = {'filepath': fp, 'effectiveTime': '20151023101908-0400'}
    resp = client.put('/patients/123abc/ccda', json=j)
    assert resp.status_code == 200

    record = ClinicalDoc.objects.get(mrn='123abc')
    et = record.generation_time
    # mongo stores in UTC, but doesn't mark tz by default
    if et.tzinfo is None:
        et = et.replace(tzinfo=pytz.UTC)
    assert et.tzinfo

    # convert effectiveTime to UTC for comparison
    given = dateutilparse(j['effectiveTime']).astimezone(pytz.UTC)

    assert et == given
    assert record.filepath == fp


def test_duplicate_upload(client):
    fp = "/tmp/whatever"
    mrn = '123abc'
    pre_existing = ClinicalDoc(
        mrn=mrn, filepath=fp+'/before',
        generation_time=datetime.datetime.utcnow())
    pre_existing.save()

    j = {'filepath': fp, 'effectiveTime': '20151023101908-0400'}
    resp = client.put('/patients/{}/ccda'.format(mrn), json=j)
    assert resp.status_code == 200

    record = ClinicalDoc.objects.get(mrn=mrn)
    assert record.filepath.endswith('before')


def test_get_mrn(client):
    now = utc_now()
    fp = '/tmp/abc123'
    c = ClinicalDoc(mrn='abc123', filepath=fp)
    c.save()

    resp = client.get('/patients/abc123/ccda/file_info')
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert c.mrn == data['mrn']
    assert c.filepath == data['filepath']
    assert time.mktime(now.timetuple()) == pytest.approx(
        time.mktime(dateutilparse(data['receipt_time']).timetuple()))


def test_get_problem_list(client):
    now = utc_now()
    fp = "/tmp/whatever"
    c = ClinicalDoc(mrn='abc123', filepath=fp)
    c.save()

    here = os.path.dirname(__file__)
    with open(os.path.join(here, 'prob_list.json'), 'r') as json_file:
        data = json.load(json_file)

    parse_problem_list(data['problem_list'], c)

    resp = client.get('/patients/abc123/problem_list')
    assert resp.status_code == 200
    data = resp.json
    assert c.mrn == data['mrn']
    assert 51 == len(data['problem_list'])
    assert time.mktime(now.timetuple()) == pytest.approx(
        time.mktime(dateutilparse(data['receipt_time']).timetuple()))


def test_get_problem_list_filter(client):
    fp = "/tmp/whatever"
    c = ClinicalDoc(mrn='abc123', filepath=fp)
    c.save()

    here = os.path.dirname(__file__)
    with open(os.path.join(here, 'prob_list.json'), 'r') as json_file:
        data = json.load(json_file)

    parse_problem_list(data['problem_list'], c)

    filter_by = {
        'filter':
            {
                'icd9': {
                    'code': ['133.0', '296.2*', '296.3*', '300.4', '311.*']
                },
                'icd10': {
                    'code': ['E78.*', 'H21.239']}},
        'status': {
            'value': {
                'code': '55561003', 'code_system': '2.16.840.1.113883.6.96'}
        }
    }

    encrypted = urllib.parse.quote(json.dumps(filter_by))
    #print('/patients/abc123/problem_list?filter={}'.format(encrypted))
    resp = client.get(
        '/patients/abc123/problem_list?filter={}'.format(encrypted))
    assert resp.status_code == 200
    data = resp.json
    assert c.mrn == data['mrn']
    assert 3 == len(data['problem_list'])
    for prob in data['problem_list']:
        assert 'Active' == prob['status']['value']['display']
