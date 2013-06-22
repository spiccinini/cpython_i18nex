import os
import re
import sys
import glob
from collections import defaultdict, namedtuple


class ParseError(Exception):
    pass

ExceptionObj = namedtuple("ExceptionObj", ['name', 'text'])


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
    import pickle
    cpyimporter = CPythonExceptionImporter("/home/san/Downloads/Python-3.3.2")
    exceptions = cpyimporter.do_import()


    print("Total exception count: %d" % len(exceptions))

    with open('./original_db.pickle', 'wb') as f:
        pickle.dump(exceptions, f)
        print('Database written to original_db.pickle')

