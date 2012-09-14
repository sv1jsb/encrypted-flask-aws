#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from peewee import *
import mimetypes
import datetime

class File(Model):
    filename = CharField()
    created_date = DateTimeField(default=datetime.datetime.now)
    encrypted = BooleanField(default=False)

    def get_mimetype(self):
        return mimetypes.guess_type(self.filename)[0]
