# -*- coding: utf-8 -*-

import unittest
import exc_i18n

error_templates = {
    "SyntaxError": {"EOL while scanning string literal"},
    "NameError": {"name %s is not defined", "name %s is not defined. Neither is %s"},
    "TypeError": {"argument should be %s, not %.200s"},
    }


class ErrorSearcher(unittest.TestCase):

    def test_no_match(self):
        template, values = exc_i18n.search_template(error_templates, "ZeroDivisionError",
                                            "division by zero")
        self.assertEqual((template, values), (None, None))
        
    def test_match_equal(self):
        template, values = exc_i18n.search_template(error_templates, "SyntaxError",
                                            "EOL while scanning string literal")
        self.assertEqual(template, "EOL while scanning string literal")

    def test_match_with_one_simple_format(self):
        template, values = exc_i18n.search_template(error_templates, "NameError",
                                              "name 'a' is not defined")
        self.assertEqual(template, "name %s is not defined")

    def test_match_with_two_simple_formats(self):
        template, values = exc_i18n.search_template(error_templates, "NameError",
                                              "name 'a' is not defined. Neither is 'b'")
        self.assertEqual(template, "name %s is not defined. Neither is %s")
        
    def test_match_with_complex_format(self):
        template, values = exc_i18n.search_template(error_templates, "TypeError",
                                              "argument should be 748.ble, not bla132.41jvv vnslvn")
        self.assertEqual(template, "argument should be %s, not %.200s")

    def test_extract_values_from_error(self):
        template, values = exc_i18n.search_template(error_templates, "TypeError",
                                              "argument should be 748.ble, not bla132.41jvv vnslvn")
        self.assertEqual(values, ('748.ble', 'bla132.41jvv vnslvn'))
        
        
if __name__ == "__main__":
    unittest.main()
