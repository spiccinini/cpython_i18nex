import os
import sys
import pickle
from collections import defaultdict, namedtuple

import polib

ExceptionObj = namedtuple("ExceptionObj", ['name', 'text'])
TranslationObj = namedtuple("TranslationObj", ['exc_name', 'exc_text', 'language_code', 'translation'])

class Database(object):
    def __init__(self, data=None):
        self.data = data if data else set()

    def all(self):
        return self.data

    def add(self, item):
        self.data.add(item)

    def dump(self, fobj):
        pickle.dump(self.data, fobj)

    @classmethod
    def load_from_pickle(cls, file_obj):
        return cls(pickle.load(file_obj))

    def pprint(self):
        pprint.pprint(self.data)


class ExceptionDatabase(Database):
    def __init__(self, exceptions=None):
        super(ExceptionDatabase, self).__init__(exceptions)

    def filter(self, name=None):
        def cond(val, name):
            result = True
            if name is not None:
                result = result and val.name == name
            return result
        return {exc for exc in self.exceptions if cond(exc, name)}

    def export_as_po(self, path):
        po = polib.POFile()
        po.metadata = {
            'MIME-Version': '1.0',
            'Content-Type': 'text/plain; charset=utf-8',
            'Content-Transfer-Encoding': '8bit',
        }

        for exception in self.all():
             entry = polib.POEntry(
                 msgid=exception.text, msgstr='',
                 occurrences=[(exception.name, '')]
             )
             po.append(entry)
        po.save('./messages.po')
        po.save(path)

    @property
    def exceptions(self):
        return self.data


class TranslationDatabase(Database):
    def __init__(self, translations=None):
        super().__init__(translations)


    def filter(self, exc_name=None, lang=None):
        def cond(val, exc_name, lang):
            result = True
            if exc_name is not None:
                result = result and val.exc_name == exc_name
            if lang is not None:
                result = result and val.language_code == lang
            return result
        return {trans for trans in self.translations if cond(trans, exc_name, lang)}

    @property
    def translations(self):
        return self.data

    def import_from_po(self, path, language_code):
        po = polib.pofile(path)
        valid_entries = [e for e in po if not e.obsolete]
        for entry in valid_entries:
            self.add(TranslationObj(exc_name=entry.occurrences[0],
                                    exc_text=entry.msgid,
                                    language_code=language_code,
                                    translation=entry.msgstr))

if __name__ == "__main__":
    import pprint
    with open('./db.pickle', 'rb') as f:
        db = ExceptionDatabase.load_from_pickle(f)

    print("%d Exceptions" % len(db.all()))
    db.pprint()
