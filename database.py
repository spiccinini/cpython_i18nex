import os
import re
import sys
import glob
import pickle
from collections import defaultdict, namedtuple

import polib


class ParseError(Exception):
    pass


ExceptionObj = namedtuple("ExceptionObj", ['name', 'text', 'language_code'])


class ExceptionDatabase(object):

    def __init__(self, exceptions=None):
        self.exceptions = set()

    def all(self):
        return self.exceptions

    def filter(self, name=None, lang=None):
        def cond(val, name, lang):
            result = True
            if name is not None:
                result = result and val.name == name
            if lang is not None:
                result = result and val.language_code == lang
            return result
        return {exc for exc in self.exceptions if cond(exc, name, lang)}

    def filter_by_name_and_lang(self, name, lang):
        return {exc for exc in self.exceptions if \
                 exc.name == name and exc.language_code == lang}

    def add(self, exception):
        self.exceptions.add(exception)

    def dump(self, fobj):
        pickle.dump(self.exceptions, fobj)

    @classmethod
    def load_from_pickle(cls, file_obj):
        return ExceptionDatabase(pickle.load(file_obj))

    def export_as_po(self):
        po = polib.POFile()
        for exception in exceptions:
            entry = polib.POEntry(
                msgid=exception.text, msgstr='',
                occurrences=[(exception.name, '')]
            )
            po.append(entry)
        po.save('./messages.po')


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
        return ExceptionObj(exc_type, text_error, 'en')

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
                         "name '%.200s' is not defined", "en"),
            ExceptionObj("NameError",
                         "global name '%.200s' is not defined", "en"),
            ExceptionObj("NameError",
                         "local variable '%.200s' referenced " \
                         "before assignment", "en"),
            ExceptionObj("NameError",
                         "free variable '%.200s' referenced " \
                         "before assignment in enclosing scope", "en"),
        }
