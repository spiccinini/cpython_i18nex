# -*- coding: utf-8 -*-

import sys
import re
import traceback
from database import ExceptionDatabase, TranslationDatabase

class TranslationMissing(Exception):
    pass

class TranslationNotSupported(Exception):
    pass

translator = None

class ExceptionTranslator(object):
    
    def __init__(self, exc_db, trans_db):
        self.exc_db = exc_db
        self.trans_db = trans_db
        self.language_code = self.detect_language_code()

    def detect_language_code(self):
        #TODO: read actual value from environment
        return 'es'
    
    def set_language_code(self, language_code):
        self.language_code = language_code
        
    def _build_deformating_regex(self, exc):
        fmt_term_chars = 'sdSzcRxUV'
        split_pattern = '%%.*?[%s]' % fmt_term_chars
        # replace every format pattern (eg. %.10s) by .*? so it will match the
        # actual error with values replaced, and group them to obtain the values
        re_pattern = "^"+ '(.*?)'.join(re.split(split_pattern, exc.text)) +"$"
        r = re.compile(re_pattern)
        return r
        
    def search_exception(self, exc_name, formatted_msg):
        "returns the original template and the extracted values from the provided error message"
        exceptions = self.exc_db.filter(name=exc_name)
        if exceptions:
            for exc in exceptions:
                if formatted_msg == exc.text:
                    return exc
                else:
                    r = self._build_deformating_regex(exc)
                    res = re.match(r, formatted_msg)
                    if res:
                        return exc

    def extract_values(self, exc, formatted_msg):
        r = self._build_deformating_regex(exc)
        res = re.match(r, formatted_msg)
        return res.groups()
        
    def search_translation(self, exc):
        translation = self.trans_db.get(exc.name, exc.text, self.language_code)
        return translation
        
    def translate(self, exc_name, formatted_msg):
        exc = self.search_exception(exc_name, formatted_msg)
        if exc:
            trans = self.search_translation(exc)
            if trans:
                values = self.extract_values(exc, formatted_msg)
                return trans.translation % values
            else:
                raise(TranslationMissing('El mensaje de excepción aún no ha sido traducido. Colabora!'))
        else:
            raise(TranslationNotSupported('La excepción no está soportada en el sistema de traducción'))
    
    def show_translation(self):
        pass
    
def i18n_hook(etype, value, tb):
    trans_message = translator.translate(etype.__name__, value.args[0])
    sys.stderr.write("%s: %s\n" % (etype.__name__, trans_message))
    sys.stderr.flush()
    
def activate():
    global translator
    with open('./db.pickle', 'rb') as f:
        exc_db = ExceptionDatabase.load_from_pickle(f)
    with open('./trans.pickle', 'rb') as f:
        trans_db = TranslationDatabase.load_from_pickle(f)
    
    translator = ExceptionTranslator(exc_db, trans_db)
    sys.excepthook = i18n_hook

def set_language_code(language_code):
    activate()
    translator.set_language_code(language_code)
