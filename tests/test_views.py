import json
from tests import TestCase

from cdr.extensions import db
from cdr.api.models import Unparsed

class TestAPI(TestCase):

    def test_upload(self):
        fp = "/var/lib/whatever"
        j = { 'filepath': fp,
             'effectiveTime': '20030110'}
        resp = self.client.put('/api/ccda/123abc', data=json.dumps(j),
                content_type='application/json')
        self.assert_200(resp)

        record = Unparsed.objects.get(mrn='123abc')
        self.assertEquals(record.filepath, fp)

    def test_get_unparsed(self):
        u = Unparsed(mrn='abc123', filepath='/tmp/abc123')
        u.save()

        resp = self.client.get('/api/ccda/abc123')
        self.assert_200(resp)
        data = json.loads(resp.data)
        self.assertEqual(u.mrn, data['mrn'])
        self.assertEqual(u.filepath, data['filepath'])
