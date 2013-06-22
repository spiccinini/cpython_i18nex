import os
import re
import sys
import glob
import pickle
from collections import defaultdict, namedtuple

import polib


class ParseError(Exception):
    pass


ExceptionObj = namedtuple("ExceptionObj", ['name', 'text'])
TranslationObj = namedtuple("ExceptionObj", ['exc_name', 'exc_text', 'language_code', 'translation'])

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
        return ExceptionDatabase(pickle.load(file_obj))

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

    def export_as_po(self):
        po = polib.POFile()
        for exception in exceptions:
            entry = polib.POEntry(
                msgid=exception.text, msgstr='',
                occurrences=[(exception.name, '')]
            )
            po.append(entry)
        po.save('./messages.po')

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
   
class CPythonExceptionImporter(object):
    """Extracts exceptions from the CPython sourcecode.
    """

    def __init__(self, path):
        self.path = path

    @staticmethod
    def parse_c_code(text):
        try:
            text_error = ''.join(re.findall(r'"(.*?)"', text))
            exc_type = re.search(r'PyExc_(\w+)', text).groups(1)[0]
        except (AttributeError, ) as e:
            raise ParseError('text: %s' % text)
        return ExceptionObj(exc_type, text_error)

    @staticmethod
    def c_block_finder(text):
        """Splits C code in blocks that contains one Exception
        """
        blocks = re.findall(r'(PyErr_SetString.*?);', text, re.DOTALL)
        blocks.extend(re.findall('(PyErr_Format\(.*?PyExc.*?);', text, re.DOTALL))
        blocks.extend(re.findall('(FORMAT_EXCEPTION\(.*?PyExc.*?);', text, re.DOTALL))

        return set(blocks)

    @staticmethod
    def parse_c_file(filename):
        exceptions = set()
        with open(filename) as f:
            text = f.read()
        blocks = CPythonExceptionImporter.c_block_finder(text)
        for block in blocks:
            try:
                exception_obj = CPythonExceptionImporter.parse_c_code(block)
                exceptions.add(exception_obj)
            except ParseError:
                sys.stderr.write("Warning: Can't parse an exception on file %s\n" % filename)

        return exceptions

    def do_import(self):
        exceptions = set()
        filenames = glob.glob(os.path.join(self.path, 'Python', '*.c'))
        filenames.extend(glob.glob(os.path.join(self.path, 'Objects', '*.c')))
        filenames.extend(glob.glob(os.path.join(self.path, 'Modules', '*.c')))
        filenames.remove(os.path.join(self.path, 'Python', 'errors.c'))
        for filename in filenames:
            exceptions.update(self.parse_c_file(filename))

        exceptions.update(self.fixed_exceptions())
        return exceptions

    def fixed_exceptions(self):
        return {
            ExceptionObj("NameError",
                         "name '%.200s' is not defined"),
            ExceptionObj("NameError",
                         "global name '%.200s' is not defined"),
            ExceptionObj("NameError",
                         "local variable '%.200s' referenced " \
                         "before assignment"),
            ExceptionObj("NameError",
                         "free variable '%.200s' referenced " \
                         "before assignment in enclosing scope"),
        }
