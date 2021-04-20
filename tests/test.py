import xmlparser
import xml.etree.ElementTree as ET

import unittest
from django.db import models
import django
import os

os.environ.setdefault('PYTHONPATH', "/"+"/".join(os.getcwd().split("/")[:-1]))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

django.setup()

def _are_models_equal(m1, m2):
    d1 = m1.__dict__
    d2 = m2.__dict__

    for d in d1, d2:
        d.pop("_state")

    return d1 == d2

class Student(models.Model):
    num = models.PositiveIntegerField(blank=True)
    fullname = models.CharField(max_length=256, blank=True)
    course = models.CharField(max_length=256, blank=True)

    class Meta:
        app_label = 'schoolApp'


class StudentParser(xmlparser.AbstractDjangoParser):
    Model = Student

    data = {"num", "name", "surname", "course", "birthplace"}
    external_data = {"birthplace"}
    internal_attr_data = {"num"}

    # internal_data = {"name", "surname", "course"}

    @staticmethod
    def fullname_from(surname, name):
        if name is None or name == "":
            return surname if surname is not None else ""
        else:
            if surname is None:
                return ""
            else:
                return surname + " " + name

    @staticmethod
    def name_handler(name: str):
        return name.upper() if name is not None else ""

    @staticmethod
    def validate_fullname(fullname: str):
        if fullname[0] == "К":
            raise StudentParser.ValidationFail

    @staticmethod
    def validate(fullname, course):
        if (fullname, course) == ("Гордон МИХАИЛ", "биология"):
            raise StudentParser.ValidationFail()

class StudentParserTest(unittest.TestCase):

    def setUp(self) -> None:

        tree = ET.parse("test.xml")
        self.tree = tree

    def test_unvalid_arguments(self):

        root = self.tree.getroot().find("student[@num='1']")

        unvalid_arguments = [{"root": root, "name":"name", "surname":"surname",
                          "course":'course', "course_id": ("course", "id"), "god": "1123123",
                          "birthplace":"Orel"},
                             {"root": self.tree.getroot(),
                          "course":'course', "course_id": ("course", "id"),
                          "birthplace":"Orel"}]

        for args in unvalid_arguments:
            with self.subTest(args=args):
                self.assertRaises(xmlparser.AbstractParser.OddArguments, StudentParser,
                                  **args)

    def test_parsing(self):

        root = self.tree.getroot().find("student[@num='1']")

        arguments = {"root": root, "name":"name", "surname":"surname",
                          "course":'course', "num": ('', "num"),
                          "birthplace": "Orel"}

        p = StudentParser(**arguments)

        model = Student(num="1", fullname="Енин МИХАИЛ", course="Математика")
        self.assertTrue(_are_models_equal(p.get_model(), model))

    def test_empty_data(self):

        root = self.tree.getroot().find("student[@num='4']")

        arguments = {"root": root, "name":"name", "surname":"surname",
                          "course":'course', "num": ('', "num"),
                          "birthplace": "Orel"}

        p = StudentParser(**arguments)
        model = Student(num="4", fullname="Енин", course="Математика")

        self.assertTrue(_are_models_equal(p.get_model(), model))


    def test_special_validation(self):

        root = self.tree.getroot().find("student[@num='2']")
        args = {"root": root, "num": ("", "num"), "surname": "surname", "name": "name",
							"course":'course',
                        	"birthplace":"Orel"}

        self.assertRaises(xmlparser.AbstractParser.ValidationFail, StudentParser,
                          **args)

    def test_general_validation(self):
        root = self.tree.getroot().find("student[@num='3']")
        args = {"root": root, "num": ("", "num"), "surname": "surname", "name": "name",
                "course": 'course',
                "birthplace": "Orel"}

        self.assertRaises(xmlparser.AbstractParser.ValidationFail, StudentParser, **args)


if __name__ == "__main__":
    unittest.main()