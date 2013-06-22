# -*- coding: utf-8 -*-

import sys
import re
import traceback

error_templates = {
    "SyntaxError": {"EOL while scanning string literal"},
    "NameError": {"name %s is not defined", "name %s is not defined. Neither is %s"},
    "TypeError": {"argument should be %s, not %.200s"},
    }

translations = {
    "EOL while scanning string literal": {"ES": "Te falta una comilla papá"},
    "name %s is not defined": {"ES": "el nombre %s no está definido"}
    }

class MissingTranslationError(Exception):
    pass

def search_template(error_templates, error_type, msg):
    "returns the original template and the values passed in the error message"
    if error_type in error_templates:
        for tpl_msg in error_templates[error_type]:
            if msg == tpl_msg:
                return tpl_msg, ()
            else:
                fmt_term_chars = 'sd'
                split_pattern = '%%.*?[%s]' % fmt_term_chars
                # replace every format pattern (eg. %.10s) by .*? so it will match the
                # actual error with values replaced, and group them to obtain the values
                re_pattern = "^"+ '(.*?)'.join(re.split(split_pattern, tpl_msg)) +"$"
                r = re.compile(re_pattern)
                res = re.match(r, msg)
                if res:
                    return tpl_msg, res.groups()
    else:
        return None, None

