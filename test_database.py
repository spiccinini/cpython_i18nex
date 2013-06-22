import unittest
from database import ExceptionObj, CPythonExceptionImporter
from collections import defaultdict


class CBlockSearcherTest(unittest.TestCase):
    c_example = 'PyErr_SetString(PyExc_NotImplementedError, "link: src and dst must be the same type");'
    imp = CPythonExceptionImporter

    def test_unformated_exception_type_extraction(self):
        code = self.c_example
        self.assertEqual(self.imp.parse_c_code(code).name, "NotImplementedError")

    def test_unformated_exception_another_error_type_extraction(self):
        code = 'PyErr_SetString(PyExc_OSError, "Load averages are unobtainable");'
        self.assertEqual(self.imp.parse_c_code(code).name, "OSError")

    def test_unformated_exception_error_extraction(self):
        code = self.c_example
        self.assertEqual(self.imp.parse_c_code(code).text, "link: src and dst must be the same type")

    def test_unformated_exception_error_extraction_two_lines(self):
        code = '''
            PyErr_SetString(PyExc_NotImplementedError,
                            "link: src and dst must be the same type");
        '''
        self.assertEqual(self.imp.parse_c_code(code).text, "link: src and dst must be the same type")

    def test_unformated_exception_in_block_of_code(self):
        code = '''
        if ((src.narrow && dst.wide) || (src.wide && dst.narrow)) {
            PyErr_SetString(PyExc_NotImplementedError,
                            "link: src and dst must be the same type");
            goto exit;
        }
        '''
        exception_obj = self.imp.parse_c_code(code)
        self.assertEqual(exception_obj.text, "link: src and dst must be the same type")
        self.assertEqual(exception_obj.name, "NotImplementedError")

    def test_formated_exception_type_extraction(self):
        code = '''
        PyErr_Format(PyExc_ValueError,
                     "%s: src and dst must be the same type", function_name);
        '''
        exception_obj = self.imp.parse_c_code(code)
        self.assertEqual(exception_obj.text, "%s: src and dst must be the same type")
        self.assertEqual(exception_obj.name, "ValueError")

    def test_formated_exception_multiple_line(self):
        code = '''
            PyErr_Format(PyExc_TypeError,
                        "expected an iterator of ints, "
                        "but iterator yielded %R",
                        Py_TYPE(item));
            Py_DECREF(item);
        '''
        exception_obj = self.imp.parse_c_code(code)
        self.assertEqual(exception_obj.text, "expected an iterator of ints, but iterator yielded %R")
        self.assertEqual(exception_obj.name, "TypeError")

    def test_formated_exception_multiple_items_in_format(self):
        code = '''
            PyErr_Format(PyExc_TypeError,
                        "argument should be %s, not %.200s",
                        allowed, Py_TYPE(o)->tp_name);
        return 0;
        '''
        exception_obj = self.imp.parse_c_code(code)
        self.assertEqual(exception_obj.text, "argument should be %s, not %.200s")
        self.assertEqual(exception_obj.name, "TypeError")

    def test_block_finder(self):
        code = '''
            else {
                PyErr_SetString(PyExc_TypeError,
                                "spawnvpe() arg 2 must be a tuple or list");
                goto fail_0;
            }
            if (!PyMapping_Check(env)) {
                PyErr_SetString(PyExc_TypeError,
                                "spawnvpe() arg 3 must be a mapping object");
                goto fail_0;
            }

            argvlist = PyMem_NEW(char *, argc+1);
            if (argvlist == NULL) {
                PyErr_NoMemory();
                goto fail_0;
            }
            '''
        blocks =  self.imp.c_block_finder(code)
        self.assertEqual(len(blocks), 2)

    def test_FORMAT_EXCEPTION(self):
        code = 'FORMAT_EXCEPTION(PyExc_ValueError, "%s too long for Windows");'
        exception_obj = self.imp.parse_c_code(code)
        self.assertEqual(exception_obj.text, "%s too long for Windows")
        self.assertEqual(exception_obj.name, "ValueError")


    def test_parse_posixmodule_file(self):
        exceptions = self.imp.parse_c_file('./test_data/posixmodule.c')
        self.assertTrue(len(exceptions) > 50)


if __name__ == "__main__":
    unittest.main()
