# -*- coding: utf-8 -*-

import unittest
import exc_i18n
from database import ExceptionDatabase, ExceptionObj, TranslationDatabase, TranslationObj

exc_db = ExceptionDatabase()
exc_db.add(ExceptionObj(name="SyntaxError", text="EOL while scanning string literal"))
exc_db.add(ExceptionObj(name="NameError", text="name %s is not defined"))
exc_db.add(ExceptionObj(name="NameError", text="name %s is not defined. Neither is %s"))
exc_db.add(ExceptionObj(name="TypeError", text="argument should be %s, not %.200s"))

trans_db = TranslationDatabase()
trans_db.add(TranslationObj(exc_name="SyntaxError", exc_text="EOL while scanning string literal", language_code="es", translation="te olvidaste una comilla pelandrún"))
trans_db.add(TranslationObj(exc_name="NameError", exc_text="name %s is not defined", language_code="es", translation="el nombre %s no ha sido definido"))
trans_db.add(TranslationObj(exc_name="NameError", exc_text="name %s is not defined. Neither is %s", language_code="es", translation="el nombre %s no ha sido definido y %s tampoco"))
trans_db.add(TranslationObj(exc_name="TypeError", exc_text="argument should be %s, not %.200s", language_code="es", translation="argumento debe ser %s, no %.200s"))

translator = exc_i18n.ExceptionTranslator(exc_db, trans_db)

class ExceptionTranslatorSearchTests(unittest.TestCase):

    def test_no_match(self):
        exc = translator.search_exception("ZeroDivisionError",
                                            "division by zero")
        self.assertEqual(exc, None)
        
    def test_match_equal(self):
        exc = translator.search_exception("SyntaxError",
                                            "EOL while scanning string literal")
        self.assertEqual(exc.text, "EOL while scanning string literal")

    def test_match_with_one_simple_format(self):
        exc = translator.search_exception("NameError",
                                              "name 'a' is not defined")
        self.assertEqual(exc.text, "name %s is not defined")

    def test_match_with_two_simple_formats(self):
        exc = translator.search_exception("NameError",
                                              "name 'a' is not defined. Neither is 'b'")
        self.assertEqual(exc.text, "name %s is not defined. Neither is %s")
        
    def test_match_with_complex_format(self):
        exc = translator.search_exception("TypeError",
                                              "argument should be 748.ble, not bla132.41jvv vnslvn")
        self.assertEqual(exc.text, "argument should be %s, not %.200s")

    def test_extract_values_from_error(self):
        exc_name = "TypeError"
        formatted_msg = "argument should be 748.ble, not bla132.41jvv vnslvn"
        exc = ExceptionObj(name=exc_name, text="argument should be %s, not %.200s")
        values = translator.extract_values(exc, formatted_msg)
        self.assertEqual(values, ('748.ble', 'bla132.41jvv vnslvn'))

class ExceptionTranslatorTranslationTests(unittest.TestCase):

    def test_search_translation(self):
        translator.set_language_code('es')
        exc = ExceptionObj(name="SyntaxError", text="EOL while scanning string literal")
        trans = translator.search_translation(exc)
        self.assertEqual(trans.translation, "te olvidaste una comilla pelandrún")

    def test_translate_simple(self):
        exc_name = "TypeError"
        formatted_msg = "argument should be 748.ble, not bla132.41jvv vnslvn"
        translated_msg = translator.translate(exc_name, formatted_msg)
        self.assertEqual(translated_msg, "argumento debe ser 748.ble, no bla132.41jvv vnslvn")

if __name__ == "__main__":
    unittest.main()
