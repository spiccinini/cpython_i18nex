import re
import os
import sys
import glob
import pickle
from database import ExceptionDatabase, ExceptionObj

description = 'Builds a database of exceptions from CPython source'


class ParseError(Exception):
    pass

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

if __name__ == "__main__":
    import pprint
    import argparse

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("path",
                        help='path to CPython source eg: /home/foo/Python-3.3.2')
    args = parser.parse_args()


    cpyimporter = CPythonExceptionImporter(args.path)
    exceptions = cpyimporter.do_import()
    db = ExceptionDatabase(exceptions)

    print("%d Exceptions imported" % len(exceptions))
    out_filename = './db.pickle'
    with open(out_filename, 'wb') as f:
        db.dump(f)
        print('Database written to %s' % out_filename)
