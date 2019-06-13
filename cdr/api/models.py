import datetime
from flask import current_app

from ..extensions import db
from ..time_util import parse_datetime


class ClinicalDoc(db.Document):
    """Mongo object representing Clinical Documents"""
    mrn = db.StringField(max_length=255, primary_key=True)
    receipt_time = db.DateTimeField(default=datetime.datetime.utcnow,
                                    required=True)
    generation_time = db.DateTimeField(required=False)
    lastvisit_time = db.DateTimeField(required=False)
    filepath = db.StringField(max_length=512, required=True)

    def __unicode__(self):
        return u"<{0}: {1}@{2}>".format(self.__class__.__name__,
                                       self.mrn,self.filepath)

    meta = {
        'allow_inheritance': True,
        'indexes': ['mrn', '-receipt_time'],
        'ordering': ['-receipt_time'],
    }


class Code(db.Document):
    """Mongo object representing an observation code"""
    code = db.StringField(max_length=80, required=True)
    code_system = db.StringField(max_length=80, required=True)
    code_system_name = db.StringField(max_length=80, required=True)
    display = db.StringField(required=True)

    @classmethod
    def from_json(cls, json):
        return cls(code=json['_code'], code_system=json['_codeSystem'],
                   code_system_name=json['_codeSystemName'],
                   display=json['_displayName'])


    def to_json(self):
        return {'code': self.code, 'code_system': self.code_system,
                'code_system_name': self.code_system_name,
                'display': self.display}

    def save(self, *args, **kwargs):
        """Avoiding tons of duplicates - check for existing or save"""
        existing = Code.objects(code=self.code, code_system=self.code_system,
                                code_system_name=self.code_system_name)
        if existing:
            assert len(existing) == 1
            self.id = existing[0].id
        else:
            super(type(self), self).save(*args, **kwargs)


class Status(db.Document):
    """Mongo object representing status code et al"""
    status_code = db.StringField(max_length=80, required=True)
    code = db.ReferenceField(Code)
    value = db.ReferenceField(Code)

    @classmethod
    def from_json(cls, json):
        code, value = None, None
        if 'code' in json:
            code = Code.from_json(json['code'])
            code.save()
        if 'value' in json:
            value = Code.from_json(json['value'])
            value.save()
        return cls(status_code=json['statusCode']['_code'],
                   code=code,
                   value=value)

    def to_json(self):
        d = {}
        if self.status_code:
            d['status_code'] = self.status_code
        if self.code:
            d['code'] = self.code.to_json()
        if self.value:
            d['value'] = self.value.to_json()
        return d

    def save(self, *args, **kwargs):
        """Avoiding tons of duplicates - check for existing or save"""
        existing = Status.objects(
            status_code=self.status_code, code=self.code, value=self.value)
        if existing:
            assert len(existing) == 1
            self.id = existing[0].id
        else:
            super(type(self), self).save(*args, **kwargs)


class Observation(db.Document):
    """Mongo object representing an observation"""
    owner = db.ReferenceField(ClinicalDoc)
    code = db.ReferenceField(Code)
    icd9 = db.ReferenceField(Code)
    icd10 = db.ReferenceField(Code)
    entry_date = db.DateTimeField(required=False)
    onset_date = db.DateTimeField(required=False)
    status = db.ReferenceField(Status)


class ParseException(Exception):
    pass


def parse_effective_time(effectiveTime):
    """Given an effectiveTime, pull best value from high/low and return

    Frequently we get only a high or low value.  Only sometimes does
    it include timezone info.  Prefer low if both defined.  Assume local
    time zone if not defined.

    Returns a datetime instance with timezone info (or None if not found)

    """
    value = effectiveTime['low'].get('_value')
    if not value:
       value = effectiveTime['high'].get('_value')
    if not value:
        return None
    return parse_datetime(value)


def parse_icds(translation):
    """Given a translation, return icd9 and icd10 if found"""
    icd9, icd10 = None, None

    # occasionally, we get a single translation - make it list like
    if isinstance(translation, dict):
        translation = [translation,]

    for t in translation:
        code = Code.from_json(t)
        if code.code_system_name.startswith('ICD-9'):
            assert icd9 is None
            icd9 = code
            icd9.save()
        if code.code_system_name.startswith('ICD-10'):
            assert icd10 is None
            icd10 = code
            icd10.save()

    return icd9, icd10


def parse_observation(observation_json):
    """Parse observation portion of json - returns an Observation"""
    try:
        code = Code.from_json(observation_json['value'])
    except KeyError:
        code = None  # we don't always get a meaningful code, just translations

    try:
        onset_date = parse_effective_time(observation_json['effectiveTime'])
    except KeyError:
        onset_date = None # occasionally the effectiveTime is missing

    entry_date = parse_datetime(observation_json['author']['time']['_value'])
    if 'translation' in observation_json['value']['_']:
        icd9, icd10 = parse_icds(observation_json['value']['_']['translation'])
    else:
        icd9, icd10 = None, None

    # in the event of a "no problems" situation, there is no associated
    # status.  without a status, there's no value in keeping the observation
    if 'entryRelationship' not in observation_json:
        return None

    # occasionally we get multiple status entries - preserve only the last
    try:
        s_json = observation_json['entryRelationship']['_']['observation']['_']
    except TypeError:
        s_json = observation_json['entryRelationship'][-1]['_']['observation']['_']
    status = Status.from_json(s_json)
    return Observation(code=code, entry_date=entry_date,
                       onset_date=onset_date,
                       icd9=icd9, icd10=icd10, status=status)


def parse_problem_list(problem_list, clinical_doc, replace=False):
    """Pull the relevant data from the problem list

    Expecting a structure generated in the Mirth channel by converting
    the "Problem List" from its CCDA XML to JSON.  The mirth conversion
    includes strange structure - any element containing attributes gets a '_'
    attribute and all attributes pick up a leading '_'.

    We generate Observations from the data found.

    If 'replace' is set true, don't mess with matching duplicates, given the
    nature of CCDAs, just blow away any existing problems for the clinical_doc
    and add in the ones parsed.

    """
    if not problem_list:
        return

    if replace:
        current_app.logger.info("deleting problems from {} in favor of new".\
                                format(clinical_doc.mrn))
        Observation.objects(owner=clinical_doc).delete()

    if problem_list['section']['code']['_displayName'] != u'Problem List':
        raise ParseException("Requires section/code -> Problem List")
    for entry in problem_list['section']['entry']:
        try:
            obs = entry['act']['_']['entryRelationship']['_']\
                    ['observation']['_']
        except TypeError:
            # When there's a single entry, only the act key comes through
            # pull up this one obs directly from the problem list
            assert(entry == 'act')  
            obs = problem_list['section']['entry']['act']['_']\
                    ['entryRelationship']['_']['observation']['_']
        observation = parse_observation(obs)
        if observation:
            observation.owner = clinical_doc
            observation.cascade_save()
            observation.save()
        else:
            current_app.logger.debug(
                "Tossing observation w/o status for {}".format(
                    clinical_doc.mrn))
