from flask import current_app
from sqlalchemy import UniqueConstraint
from sqlalchemy.ext.hybrid import hybrid_property

from ..extensions import sdb
from ..time_util import datetime_w_tz, parse_datetime, utc_now


class ClinicalDoc(sdb.Model):
    """SQL object representing Clinical Documents"""
    __tablename__ = 'clinical_doc'
    mrn = sdb.Column(sdb.VARCHAR(length=255), primary_key=True)
    _receipt_time = sdb.Column(
        "receipt_time", sdb.DateTime(timezone=True),
        default=utc_now, nullable=False)
    _generation_time = sdb.Column(
        "generation_time", sdb.DateTime(timezone=True))
    _lastvisit_time = sdb.Column(sdb.DateTime(timezone=True))
    filepath = sdb.Column(sdb.VARCHAR(length=512), nullable=False)

    @hybrid_property
    def generation_time(self):
        return datetime_w_tz(self._generation_time)

    @generation_time.setter
    def generation_time(self, value):
        self._generation_time = parse_datetime(value)

    @hybrid_property
    def lastvisit_time(self):
        return datetime_w_tz(self._lastvisit_time)

    @lastvisit_time.setter
    def lastvisit_time(self, value):
        self._lastvisit_time = parse_datetime(value)

    @hybrid_property
    def receipt_time(self):
        return datetime_w_tz(self._receipt_time)

    @receipt_time.setter
    def receipt_time(self, value):
        self._receipt_time = parse_datetime(value)

    def __str__(self):
        return u"<{0}: {1}@{2}>".format(
            self.__class__.__name__, self.mrn, self.filepath)

    def save(self):
        """Only save the most recent - return existing, replace or add"""
        existing = ClinicalDoc.query.get(self.mrn)
        if existing:
            if existing.generation_time > self.generation_time:
                return existing
            else:
                # delete existing to replace
                sdb.session.delete(existing)
        sdb.session.add(self)
        return self


class Code(sdb.Model):
    """SQL object representing an observation code"""
    __tablename__ = 'code'
    id = sdb.Column(sdb.Integer, primary_key=True)
    code = sdb.Column(sdb.String(80), index=True, nullable=False)
    code_system = sdb.Column(sdb.String(80), index=True, nullable=False)
    code_system_name = sdb.Column(sdb.String(80), nullable=False)
    display = sdb.Column(sdb.Text, nullable=False)

    __table_args__ = (UniqueConstraint(
        'code', 'code_system', name='_code_code_system'),)

    @classmethod
    def from_json(cls, json):
        return cls(code=json['_code'], code_system=json['_codeSystem'],
                   code_system_name=json['_codeSystemName'],
                   display=json['_displayName'])

    def to_json(self):
        return {'code': self.code, 'code_system': self.code_system,
                'code_system_name': self.code_system_name,
                'display': self.display}

    def save(self):
        """Avoid duplicates - return existing or add new"""
        existing = Code.query.filter_by(
            code=self.code, code_system=self.code_system,
            code_system_name=self.code_system_name)
        if existing.count():
            self = existing.one()
        else:
            sdb.session.add(self)
        return sdb.session.merge(self)


class Status(sdb.Model):
    """SQL object representing status code et al"""
    __tablename__ = 'status'
    id = sdb.Column(sdb.Integer, primary_key=True)
    status_code = sdb.Column(sdb.String(80), nullable=False)
    code_id = sdb.Column(
        sdb.ForeignKey('code.id'), nullable=False)
    value_id = sdb.Column(
        sdb.ForeignKey('code.id'), nullable=False)
    code = sdb.relationship('Code', uselist=False, foreign_keys=[code_id])
    value = sdb.relationship('Code', uselist=False, foreign_keys=[value_id])
    __table_args__ = (UniqueConstraint(
        'code_id', 'value_id', name='_status_code_value'),)

    @classmethod
    def from_json(cls, json):
        code, value = None, None
        if 'code' in json:
            code = Code.from_json(json['code']).save()
        if 'value' in json:
            value = Code.from_json(json['value']).save()
        return cls(status_code=json['statusCode']['_code'],
                   code_id=code.id,
                   value_id=value.id)

    def to_json(self):
        d = {}
        if self.status_code:
            d['status_code'] = self.status_code
        if self.code:
            d['code'] = self.code.to_json()
        if self.value:
            d['value'] = self.value.to_json()
        return d

    def save(self):
        """Avoid duplicates - return existing or add new"""

        existing = Status.query.filter_by(
            status_code=self.status_code)
        if self.code_id:
            existing = existing.filter_by(code_id=self.code_id)
        else:
            existing = existing.filter(Status.code_id.is_(None))
        if self.value_id:
            existing = existing.filter_by(value_id=self.value_id)
        else:
            existing = existing.filter(Status.value_id.is_(None))

        if existing.count():
            self = existing.one()
        else:
            sdb.session.add(self)
        return sdb.session.merge(self)


class Observation(sdb.Model):
    """SQL object representing an observation"""
    __tablename__ = 'observation'
    id = sdb.Column(sdb.Integer, primary_key=True)
    doc_id = sdb.Column(  # Previously labeled "owner"
        sdb.ForeignKey('clinical_doc.mrn'), index=True, nullable=False)
    code_id = sdb.Column(sdb.ForeignKey('code.id'))
    icd9_id = sdb.Column(sdb.ForeignKey('code.id'), index=True)
    icd10_id = sdb.Column(sdb.ForeignKey('code.id'), index=True)
    _entry_date = sdb.DateTime(timezone=True)
    _onset_date = sdb.DateTime(timezone=True)
    status_id = sdb.Column(sdb.ForeignKey('status.id'))

    code = sdb.relationship('Code', uselist=False, foreign_keys=[code_id])
    icd9 = sdb.relationship('Code', uselist=False, foreign_keys=[icd9_id])
    icd10 = sdb.relationship('Code', uselist=False, foreign_keys=[icd10_id])
    status = sdb.relationship('Status')

    @hybrid_property
    def entry_date(self):
        return datetime_w_tz(self._entry_date)

    @entry_date.setter
    def entry_date(self, value):
        self._entry_date = parse_datetime(value)

    @hybrid_property
    def onset_date(self):
        return datetime_w_tz(self._onset_date)

    @onset_date.setter
    def onset_date(self, value):
        self._onset_date = parse_datetime(value)


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

    # occasionally, we get a single translation - make it a list
    if isinstance(translation, dict):
        translation = [translation]

    for t in translation:
        code = Code.from_json(t)
        if code.code_system_name.startswith('ICD-9'):
            assert icd9 is None
            icd9 = code.save()
        if code.code_system_name.startswith('ICD-10'):
            assert icd10 is None
            icd10 = code.save()

    return icd9, icd10


def parse_observation(observation_json):
    """Parse observation portion of json - returns an Observation"""
    try:
        code = Code.from_json(observation_json['value']).save()
    except KeyError:
        code = None  # we don't always get a meaningful code, just translations

    try:
        onset_date = parse_effective_time(observation_json['effectiveTime'])
    except KeyError:
        onset_date = None  # occasionally the effectiveTime is missing

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
    status = Status.from_json(s_json).save()
    return Observation(
        code_id=code.id if code else None,
        _entry_date=entry_date,
        _onset_date=onset_date,
        icd9_id=icd9.id if icd9 else None,
        icd10_id=icd10.id if icd10 else None,
        status_id=status.id if status else None)


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
        current_app.logger.info(
            "deleting problems from {} in favor of new".format(
                clinical_doc.mrn))
        for obsolete in Observation.query.filter_by(doc_id=clinical_doc.mrn):
            sdb.session.delete(obsolete)

    if problem_list['section']['code']['_displayName'] != 'Problem List':
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
            observation.doc_id = clinical_doc.mrn
            sdb.session.add(observation)
        else:
            current_app.logger.debug(
                "Tossing observation w/o status for {}".format(
                    clinical_doc.mrn))
