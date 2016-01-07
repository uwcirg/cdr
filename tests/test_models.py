from datetime import datetime, timedelta
from dateutil.parser import parse as dateutilparse
import json
import os
from tests import TestCase
from tzlocal import get_localzone

from cdr.extensions import db
from cdr.api.models import ClinicalDoc, Code, Observation, Status
from cdr.api.models import parse_icds, parse_effective_time, parse_observation
from cdr.api.models import Unparsed, parse_problem_list

class TestAPI(TestCase):

    def test_code_parse(self):
        as_json = {
            "_type": "CD",
            "_displayName": "Headache",
            "_codeSystem": "2.16.840.1.113883.6.96",
            "_code": "25064002",
            "_codeSystemName": "SNOMED CT"}
        code = Code.from_json(as_json)
        self.assertEquals(code.code, as_json['_code'])
        self.assertEquals(code.code_system, as_json['_codeSystem'])
        self.assertEquals(code.code_system_name, as_json['_codeSystemName'])
        self.assertEquals(code.display, as_json['_displayName'])

        # Confirm a second run doesn't produce a duplicate record
        c2 = Code.from_json(as_json)
        code.save()
        c2.save()
        self.assertEquals(code, c2)

    def test_status_code_parse(self):
        as_json = { 
            "statusCode": {
                "_code": "completed"
            },
            "code": {
                "_code": "33999-4",
                "_codeSystem": "2.16.840.1.113883.6.1",
                "_codeSystemName": "LOINC",
                "_displayName": "Status"
            },
            "value": {
                "_code": "55561003",
                "_type": "CD",
                "_codeSystem": "2.16.840.1.113883.6.96",
                "_codeSystemName": "SNOMED CT",
                "_displayName": "Active"
            },
            "templateId": {
                "_root": "2.16.840.1.113883.10.20.22.4.6"
            }
        }
        status = Status.from_json(as_json)
        self.assertEquals(status.status_code, "completed")
        self.assertEquals(status.code.code, as_json['code']['_code'])
        self.assertEquals(status.value.code, as_json['value']['_code'])
        self.assertEquals(status.value.display, as_json['value']\
                          ['_displayName'])

    def test_parse_effective_time(self):
        with_tz = {"high": {"_value": "20150312000000-0400"},
                   "low": {"_value": "20121011000000-0400"}}
        without_tz = {"high": {"_value": "20150312000000"},
                   "low": {"_value": "20121011000000"}}
        without_low = {"high": {"_nullFlavor": "UNK"},
                       "low": {"_value": "20130326000000-0400"}}
        et = parse_effective_time(with_tz)
        self.assertEquals(et, dateutilparse("20121011000000-0400"))
        et = parse_effective_time(without_tz)
        self.assertEquals(et.isoformat(),
                          dateutilparse("20121011000000-0700").isoformat())
        et = parse_effective_time(without_low)
        self.assertEquals(et, dateutilparse("20130326000000-0400"))

    def test_parse_icds(self):
        """parse icd9/10 from the translations"""

        translation = [
          {
            "_code": "R35.0",
            "_codeSystem": "2.16.840.1.113883.6.90",
            "_codeSystemName": "ICD-10-CM",
            "_displayName": "Frequency of micturition"
          },
          {
            "_code": "788.41",
            "_codeSystem": "2.16.840.1.113883.6.103",
            "_codeSystemName": "ICD-9-CM",
            "_displayName": "Urinary frequency"
          }
        ]
        icd9, icd10 = parse_icds(translation)
        self.assertEquals(icd9.display, "Urinary frequency")
        self.assertEquals(icd10.display, "Frequency of micturition")

    def test_parse_observation(self):
        observation = {
            "_classCode": "OBS",
            "_moodCode": "EVN",
            "_": {
              "code": {
                "_code": "282291009",
                "_codeSystem": "2.16.840.1.113883.6.96",
                "_codeSystemName": "SNOMED CT",
                "_displayName": "Diagnosis"
              },
              "author": {
                "assignedAuthor": {
                  "id": {
                    "_nullFlavor": "NI"
                  }
                },
                "time": {
                  "_value": "20031112130139"
                }
              },
              "effectiveTime": {
                "high": {
                  "_nullFlavor": "UNK"
                },
                "low": {
                  "_value": "20031111000000-0500"
                }
              },
              "value": {
                "_type": "CD",
                "_displayName": "Recurrent major depression",
                "_codeSystem": "2.16.840.1.113883.6.96",
                "_code": "66344007",
                "_codeSystemName": "SNOMED CT",
                "_": {
                  "translation": [
                    {
                      "_code": "F33.9",
                      "_codeSystem": "2.16.840.1.113883.6.90",
                      "_codeSystemName": "ICD-10-CM",
                      "_displayName": "Major depressive disorder, recurrent, unspecified"
                    },
                    {
                      "_code": "296.30",
                      "_codeSystem": "2.16.840.1.113883.6.103",
                      "_codeSystemName": "ICD-9-CM",
                      "_displayName": "Major depressive disorder, recurrent episode, unspecified degree"
                    }
                  ],
                  "originalText": {
                    "reference": {
                      "_value": "#Problem49"
                    }
                  }
                }
              },
              "entryRelationship": {
                "_inversionInd": "false",
                "_typeCode": "REFR",
                "_": {
                  "observation": {
                    "_classCode": "OBS",
                    "_moodCode": "EVN",
                    "_": {
                      "statusCode": {
                        "_code": "completed"
                      },
                      "code": {
                        "_code": "33999-4",
                        "_codeSystem": "2.16.840.1.113883.6.1",
                        "_codeSystemName": "LOINC",
                        "_displayName": "Status"
                      },
                      "value": {
                        "_code": "55561003",
                        "_type": "CD",
                        "_codeSystem": "2.16.840.1.113883.6.96",
                        "_codeSystemName": "SNOMED CT",
                        "_displayName": "Active"
                      },
                      "templateId": {
                        "_root": "2.16.840.1.113883.10.20.22.4.6"
                      }
                    }
                  }
                }
              },
              "templateId": {
                "_root": "2.16.840.1.113883.10.20.22.4.4"
              },
              "id": {
                "_root": "1.2.840.113619.21.1.4781327904983107497.3.4",
                "_extension": "1384261299013560"
              },
              "statusCode": {
                "_code": "completed"
              }
            }
        }

        obs = parse_observation(observation['_'])

        self.assertEquals(obs.code.code, "66344007")
        self.assertEquals(obs.code.display, "Recurrent major depression")
        self.assertEquals(obs.icd9.code, "296.30")
        self.assertEquals(obs.icd9.display,
            "Major depressive disorder, recurrent episode, unspecified degree")
        self.assertEquals(obs.icd10.code, "F33.9")
        self.assertEquals(obs.icd10.display,
            "Major depressive disorder, recurrent, unspecified")

        tz = get_localzone()
        entry_date = tz.localize(dateutilparse("20031112130139"), is_dst=None)
        self.assertEquals(obs.entry_date, entry_date)
        self.assertEquals(obs.onset_date, dateutilparse("20031111000000-0500"))

        self.assertEquals(obs.status.status_code, "completed")
        self.assertEquals(obs.status.value.code, '55561003')

    def test_parse_problem_list(self):
        here = os.path.dirname(__file__)
        with open(os.path.join(here, 'prob_list.json'), 'r') as json_file:
            data = json.load(json_file)
        doc = ClinicalDoc(mrn='abc123', filepath='/var/foo')
        doc.save()
        parse_problem_list(data['problem_list'], doc)
        observations = Observation.objects(owner=doc)
        self.assertEquals(len(observations), 51)

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
        now = datetime.utcnow().replace(microsecond=0)
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
        now = datetime.utcnow().replace(microsecond=0)
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
