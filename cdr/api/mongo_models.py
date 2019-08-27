import datetime

from ..extensions import mdb


class ClinicalDocMDB(mdb.Document):
    """Mongo object representing Clinical Documents"""
    mrn = mdb.StringField(max_length=255, primary_key=True)
    receipt_time = mdb.DateTimeField(default=datetime.datetime.utcnow,
                                     required=True)
    generation_time = mdb.DateTimeField(required=False)
    lastvisit_time = mdb.DateTimeField(required=False)
    filepath = mdb.StringField(max_length=512, required=True)

    def __str__(self):
        return u"<{0}: {1}@{2}>".format(self.__class__.__name__,
                                       self.mrn,self.filepath)

    meta = {
        'allow_inheritance': True,
        'indexes': ['mrn', '-receipt_time'],
        'ordering': ['-receipt_time'],
    }


class CodeMDB(mdb.Document):
    """Mongo object representing an observation code"""
    code = mdb.StringField(max_length=80, required=True)
    code_system = mdb.StringField(max_length=80, required=True)
    code_system_name = mdb.StringField(max_length=80, required=True)
    display = mdb.StringField(required=True)

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
        existing = CodeMDB.objects(code=self.code, code_system=self.code_system,
                                   code_system_name=self.code_system_name)
        if existing:
            assert len(existing) == 1
            self.id = existing[0].id
        else:
            super(type(self), self).save(*args, **kwargs)


class StatusMDB(mdb.Document):
    """Mongo object representing status code et al"""
    status_code = mdb.StringField(max_length=80, required=True)
    code = mdb.ReferenceField(CodeMDB)
    value = mdb.ReferenceField(CodeMDB)

    @classmethod
    def from_json(cls, json):
        code, value = None, None
        if 'code' in json:
            code = CodeMDB.from_json(json['code'])
            code.save()
        if 'value' in json:
            value = CodeMDB.from_json(json['value'])
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
        existing = StatusMDB.objects(
            status_code=self.status_code, code=self.code, value=self.value)
        if existing:
            assert len(existing) == 1
            self.id = existing[0].id
        else:
            super(type(self), self).save(*args, **kwargs)


class ObservationMDB(mdb.Document):
    """Mongo object representing an observation"""
    owner = mdb.ReferenceField(ClinicalDocMDB)
    code = mdb.ReferenceField(CodeMDB)
    icd9 = mdb.ReferenceField(CodeMDB)
    icd10 = mdb.ReferenceField(CodeMDB)
    entry_date = mdb.DateTimeField(required=False)
    onset_date = mdb.DateTimeField(required=False)
    status = mdb.ReferenceField(StatusMDB)
