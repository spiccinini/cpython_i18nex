import os
from database import ExceptionDatabase

description = 'Exports a ExceptionDatabase to .po'

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("db",
                        help='path to db filename')
    parser.add_argument("outfile",
                        help='output filename')
    args = parser.parse_args()

    with open(args.db, 'rb') as f:
        db = ExceptionDatabase.load_from_pickle(f)

    db.export_as_po(args.outfile)
