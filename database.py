import os
import re
import sys
import glob
from collections import defaultdict


class ParseError(Exception):
    pass

class ExceptionObj(object):

    def __init__(self, name, text):
        self.name = name
        self.text = text

class CPythonExceptionImporter(object):
    """
    Extracts exceptions from the CPython sourcecode.
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
        blocks = re.findall(r'(PyErr_SetString.*?);', text, re.DOTALL)
        blocks.extend(re.findall('(PyErr_Format\(.*?PyExc.*?);', text, re.DOTALL))
        blocks.extend(re.findall('(FORMAT_EXCEPTION\(.*?PyExc.*?);', text, re.DOTALL))

        return set(blocks)

    @staticmethod
    def parse_c_file(filename, database):
        with open(filename) as f:
            text = f.read()
        blocks = CPythonExceptionImporter.c_block_finder(text)
        for block in blocks:
            try:
                exception_obj = CPythonExceptionImporter.parse_c_code(block)
                database[exception_obj.name].add(exception_obj.text)
            except ParseError:
                sys.stderr.write("Warning: Can't parse an exception on file %s\n" % filename)

        return database

    def do_import(self):
        database = defaultdict(set)
        filenames = glob.glob(os.path.join(self.path, 'Python', '*.c'))
        filenames.extend(glob.glob(os.path.join(self.path, 'Objects', '*.c')))
        filenames.extend(glob.glob(os.path.join(self.path, 'Modules', '*.c')))
        filenames.remove(os.path.join(self.path, 'Python', 'errors.c'))
        for filename in filenames:
            self.parse_c_file(filename, database)
        add_unhandled_exceptions(database)
        return database

def add_unhandled_exceptions(database):
    database["NameError"].add("name '%.200s' is not defined")
    database["NameError"].add("global name '%.200s' is not defined")
    database["NameError"].add("local variable '%.200s' referenced before assignment")
    database["NameError"].add("free variable '%.200s' referenced before assignment in enclosing scope")


if __name__ == "__main__":
    import pprint
    import pickle
    cpyimporter = CPythonExceptionImporter("/home/san/Downloads/Python-3.3.2")
    database = cpyimporter.do_import()

    exception_type_count = len(database)
    exception_count = 0
    for key in database:
        exception_count += len(database[key])
    #pprint.pprint(database)
    print("Different exception types: %d" % exception_type_count)
    print("Total exception count: %d" % exception_count)

    with open('./original_db.pickle', 'wb') as f:
        pickle.dump(database, f)
        print('Database written to original_db.pickle')

