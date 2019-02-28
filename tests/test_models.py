from datetime import datetime, timedelta
from dateutil.parser import parse as dateutilparse
import json
import os
from tzlocal import get_localzone

from cdr.api.models import ClinicalDoc, Code, Observation, Status
from cdr.api.models import parse_icds, parse_effective_time, parse_observation
from cdr.api.models import parse_problem_list
from tests import client


def test_code_parse(client):
    as_json = {
        "_type": "CD",
        "_displayName": "Headache",
        "_codeSystem": "2.16.840.1.113883.6.96",
        "_code": "25064002",
        "_codeSystemName": "SNOMED CT"}
    code = Code.from_json(as_json)
    assert code.code == as_json['_code']
    assert code.code_system == as_json['_codeSystem']
    assert code.code_system_name == as_json['_codeSystemName']
    assert code.display == as_json['_displayName']

    # Confirm a second run doesn't produce a duplicate record
    c2 = Code.from_json(as_json)
    code.save()
    c2.save()
    assert code == c2


def test_status_code_parse():
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
    assert status.status_code == "completed"
    assert status.code.code == as_json['code']['_code']
    assert status.value.code == as_json['value']['_code']
    assert status.value.display == as_json['value']\
                      ['_displayName']


def test_parse_effective_time():
    with_tz = {"high": {"_value": "20150312000000-0400"},
               "low": {"_value": "20121011000000-0400"}}
    without_tz = {"high": {"_value": "20150312000000"},
               "low": {"_value": "20121011000000"}}
    without_low = {"high": {"_nullFlavor": "UNK"},
                   "low": {"_value": "20130326000000-0400"}}
    et = parse_effective_time(with_tz)
    assert et == dateutilparse("20121011000000-0400")
    et = parse_effective_time(without_tz)
    assert et.isoformat() == dateutilparse(
        "20121011000000-0700").isoformat()
    et = parse_effective_time(without_low)
    assert et == dateutilparse("20130326000000-0400")


def test_parse_icds():
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
    assert icd9.display == "Urinary frequency"
    assert icd10.display == "Frequency of micturition"


def test_parse_observation():
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

    assert obs.code.code == "66344007"
    assert obs.code.display == "Recurrent major depression"
    assert obs.icd9.code == "296.30"
    assert obs.icd9.display == (
        "Major depressive disorder, recurrent episode, unspecified degree")
    assert obs.icd10.code == "F33.9"
    assert obs.icd10.display == (
        "Major depressive disorder, recurrent, unspecified")

    tz = get_localzone()
    entry_date = tz.localize(dateutilparse("20031112130139"), is_dst=None)
    assert obs.entry_date == entry_date
    assert obs.onset_date == dateutilparse("20031111000000-0500")

    assert obs.status.status_code == "completed"
    assert obs.status.value.code == '55561003'


def test_parse_problem_list(client):
    here = os.path.dirname(__file__)
    with open(os.path.join(here, 'prob_list.json'), 'r') as json_file:
        data = json.load(json_file)
    doc = ClinicalDoc(mrn='abc123', filepath='/var/foo')
    doc.save()
    parse_problem_list(data['problem_list'], doc)
    observations = Observation.objects(owner=doc)
    assert len(observations) == 51


def test_parse_problem_list_of_one(client):
    here = os.path.dirname(__file__)
    with open(os.path.join(here, 'one_prob.json'), 'r') as json_file:
        data = json.load(json_file)
    doc = ClinicalDoc(mrn='abc927', filepath='/var/food')
    doc.save()
    parse_problem_list(data, doc)
    observations = Observation.objects(owner=doc)
    assert len(observations) == 1
    assert observations[0].icd10.code == 'D69.2'


def test_parse_no_problem_list(client):
    here = os.path.dirname(__file__)
    with open(os.path.join(here, 'no_problems.json'), 'r') as json_file:
        data = json.load(json_file)
    doc = ClinicalDoc(mrn='abc927', filepath='/var/food')
    doc.save()
    parse_problem_list(data, doc)
    observations = Observation.objects(owner=doc)
    assert len(observations) == 0


def test_update_problem_list(client):
    here = os.path.dirname(__file__)
    with open(os.path.join(here, 'prob_list.json'), 'r') as json_file:
        data = json.load(json_file)
    doc = ClinicalDoc(mrn='abc123', filepath='/var/foo')
    doc.save()
    doc2 = ClinicalDoc(mrn='123abc123', filepath='/var/food')
    doc2.save()
    dup = Code(code='678', code_system='fake', code_system_name='test',
               display="should get removed")
    dup.save()
    keep = Code(code='876', code_system='fake', code_system_name='test',
                display="should persist")
    keep.save()
    ob = Observation(code=dup, owner=doc)
    ob.save()
    ob2 = Observation(code=keep, owner=doc2)
    ob2.save()

    parse_problem_list(data['problem_list'], doc, replace=True)
    observations = Observation.objects(owner=doc)
    assert len(observations) == 51

    assert len(Observation.objects(owner=doc2)) == 1
    assert len(Observation.objects(code=dup)) == 0


def test_clinical_repr():
    u = ClinicalDoc(mrn='111', filepath='/a/b/c')
    s = '<ClinicalDoc: 111@/a/b/c>'
    assert str(u) == s


def test_duplicate_clinical(client):
    """ClinicalDoc is unique by MRN"""
    now = datetime.utcnow().replace(microsecond=0)
    u1 = ClinicalDoc(
        mrn='123456', receipt_time=now, filepath='/some/path')
    u1.save()

    found = ClinicalDoc.objects.get(mrn='123456')
    assert found.mrn == '123456'

    # Update by storing object with same mrn
    tomorrow = now + timedelta(days=1)
    u2 = ClinicalDoc(
        mrn='123456', receipt_time=tomorrow, filepath='/some/other/path')
    u2.save()
    found = ClinicalDoc.objects.get(mrn='123456')
    assert found.filepath == '/some/other/path'
    assert found.receipt_time, tomorrow
