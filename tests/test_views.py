import datetime
from dateutil.parser import parse as dateutilparse
import json
import os
import pytz
from tests import TestCase
import time
import urllib

from cdr.extensions import db
from cdr.api.models import ClinicalDoc
from cdr.api.models import parse_problem_list

def utc_now():
    """ datetime does have a utcnow method, but it doesn't contain tz """
    utc = pytz.timezone('UTC')
    n = datetime.datetime.now(utc)
    return n

class TestAPI(TestCase):

    def test_upload(self):
        fp = "/tmp/whatever"
        with open(fp, 'w') as f:
            f.write("test file")

        j = { 'filepath': fp,
             'effectiveTime': '20151023101908-0400'}
        resp = self.client.put('/patients/123abc/ccda', data=json.dumps(j),
                content_type='application/json')
        self.assert_200(resp)

        record = ClinicalDoc.objects.get(mrn='123abc')
        et = record.generation_time
        # mongo stores in UTC, but doesn't mark tz by default
        if et.tzinfo is None:
            et = et.replace(tzinfo=pytz.UTC)
        self.assertTrue(et.tzinfo)

        # convert effectiveTime to UTC for comparison
        given = dateutilparse(j['effectiveTime']).astimezone(pytz.UTC)

        self.assertEquals(et, given)
        self.assertEquals(record.filepath, '/tmp/archive/abc/123abc')
        self.assertFalse(os.path.exists(fp))

    def test_get_mrn(self):
        now = utc_now()
        fp = '/tmp/abc123'
        c = ClinicalDoc(mrn='abc123', filepath=fp)
        c.save()

        resp = self.client.get('/patients/abc123/ccda/file_info')
        self.assert_200(resp)
        data = json.loads(resp.data)
        self.assertEqual(c.mrn, data['mrn'])
        self.assertEqual(c.filepath, data['filepath'])
        self.assertAlmostEqual(time.mktime(now.timetuple()),
            time.mktime(dateutilparse(data['receipt_time']).timetuple()))

    def test_get_problem_list(self):
        now = utc_now()
        fp = "/tmp/whatever"
        c = ClinicalDoc(mrn='abc123', filepath=fp)
        c.save()

        here = os.path.dirname(__file__)
        with open(os.path.join(here, 'prob_list.json'), 'r') as json_file:
            data = json.load(json_file)

        parse_problem_list(data['problem_list'], c)

        resp = self.client.get('/patients/abc123/problem_list')
        self.assert_200(resp)
        data = resp.json
        self.assertEqual(c.mrn, data['mrn'])
        self.assertEqual(51, len(data['problem_list']))
        self.assertAlmostEqual(time.mktime(now.timetuple()),
            time.mktime(dateutilparse(data['receipt_time']).timetuple()))

    def test_get_problem_list_filter(self):
        now = utc_now()
        fp = "/tmp/whatever"
        c = ClinicalDoc(mrn='abc123', filepath=fp)
        c.save()

        here = os.path.dirname(__file__)
        with open(os.path.join(here, 'prob_list.json'), 'r') as json_file:
            data = json.load(json_file)

        parse_problem_list(data['problem_list'], c)

        filter_by = {'filter':
                     {'icd9': {'code': ['296.2*', '296.3*', '300.4', '311.*']},
                      'icd10': {'code': ['F32', 'F33']}
                     },
                     'status': {'value': 
                       {'code': '55561003',
                        'code_system': '2.16.840.1.113883.6.96'}}
                    }
        filter_by = {'filter':
                     {'icd9': {'code': ['133.0', '296.2*', '296.3*', '300.4', '311.*']},
                      'icd10': {'code': ['E78.*', 'H21.239']}
                     },
                     'status': {'value': 
                       {'code': '55561003',
                        'code_system': '2.16.840.1.113883.6.96'}}
                    }
        encrypted = urllib.quote(json.dumps(filter_by))
        print '/patients/abc123/problem_list?filter={}'.format(encrypted)
        resp = self.client.get(
            '/patients/abc123/problem_list?filter={}'.format(encrypted))
        self.assert_200(resp)
        data = resp.json
        self.assertEqual(c.mrn, data['mrn'])
        self.assertEqual(3, len(data['problem_list']))
        for prob in data['problem_list']:
            self.assertEqual('Active', prob['status']['value']['display'])
