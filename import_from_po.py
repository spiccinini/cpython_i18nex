import os
from database import TranslationDatabase

description = 'Imports from a .po file to a TranslationDatabase'

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("db",
                        help='db filename. The file is created if not exists')
    parser.add_argument("infile",
                        help='input po file')
    parser.add_argument("language_code",
                        help='the language code. Eg: es')
    args = parser.parse_args()

    if not os.path.exists(args.db):
        db = TranslationDatabase()
    else:
        with open(args.db, 'rb') as f:
            db = TranslationDatabase.load_from_pickle(f)

    db.import_from_po(args.infile, args.language_code)

    with open(args.db, 'wb') as fout:
        db.dump(fout)
