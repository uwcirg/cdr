import datetime
from flask import url_for

from ..extensions import db


class ClinicalDoc(db.Document):
    """Mongo object to hold metadata and path to Clinical Documents"""
    mrn = db.StringField(max_length=255, primary_key=True, unique=True)
    receipt_time = db.DateTimeField(default=datetime.datetime.now,
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


class Unparsed(db.Document):
    """Mongo object to hold minimal data and path to Clinical Documents"""
    mrn = db.StringField(max_length=255, primary_key=True, unique=True)
    receipt_time = db.DateTimeField(default=datetime.datetime.now,
                                    required=True)
    filepath = db.StringField(max_length=512, required=True, unique=True)

    def __unicode__(self):
        return u"<{0}: {1}@{2}>".format(self.__class__.__name__,
                                       self.mrn,self.filepath)

    meta = {
        'allow_inheritance': True,
        'indexes': [{'fields': ['-filepath'], 'unique': True},
                    '-receipt_time'],
        'ordering': ['-receipt_time'],
    }
