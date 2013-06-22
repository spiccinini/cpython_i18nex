import sys
from database import CPythonExceptionImporter, ExceptionDatabase

description = 'Builds a database of exceptions from CPython source'

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
