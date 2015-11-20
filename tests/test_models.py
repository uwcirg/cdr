from tests import TestCase
from datetime import datetime, timedelta

from cdr.extensions import db
from cdr.api.models import ClinicalDoc, Unparsed

class TestAPI(TestCase):

    def test_unparsed_repr(self):
        u = Unparsed(mrn='111', filepath='/a/b/c')
        s = '<Unparsed: 111@/a/b/c>'
        self.assertEquals(str(u), s)

    def test_clinical_repr(self):
        u = ClinicalDoc(mrn='111', filepath='/a/b/c')
        s = '<ClinicalDoc: 111@/a/b/c>'
        self.assertEquals(str(u), s)

    def test_duplicate_unparsed(self):
        """Unparsed is unique by MRN"""
        now = datetime.now().replace(microsecond=0)
        u1 = Unparsed(mrn='123456', receipt_time=now, filepath='/some/path')
        u1.save()

        found = Unparsed.objects.get(mrn='123456')
        self.assertTrue(found)

        tomorrow = now + timedelta(days=1)
        u2 = Unparsed(mrn='123456', receipt_time=tomorrow,
                      filepath='/some/updated/path')
        u2.save()
        found = Unparsed.objects.get(mrn='123456')
        self.assertEqual(found.filepath, '/some/updated/path')
        self.assertEqual(found.receipt_time, tomorrow)

    def test_duplicate_clinical(self):
        """ClinicalDoc is unique by MRN"""
        now = datetime.now().replace(microsecond=0)
        u1 = ClinicalDoc(mrn='123456',
                         receipt_time=now,
                         filepath='/some/path')
        u1.save()

        found = ClinicalDoc.objects.get(mrn='123456')
        self.assertTrue(found.mrn == '123456')

        # Update by storing object with same mrn
        tomorrow = now + timedelta(days=1)
        u2 = ClinicalDoc(mrn='123456',
                         receipt_time=tomorrow,
                         filepath='/some/other/path')
        u2.save()
        found = ClinicalDoc.objects.get(mrn='123456')
        self.assertEqual(found.filepath, '/some/other/path')
        self.assertEqual(found.receipt_time, tomorrow)
