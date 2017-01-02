import unittest
from utils import test_connect_user
from tutorialv2 import test_add_author, test_remove_author,
test_create_tutorial, test_delete_tutorial, test_edit_tutorial,
test_validate_tutorial
from selenium import selenium


class suite(unittest.TestCase):
    def setUp(self):
        self.verificationErrors = []
        self.selenium = selenium("localhost", 4444, "*firefox", "http://127.0.0.1:8000/")
        self.selenium.start()

    def test_suite(self):
        sel = self.selenium
        test_connect_user.test_connect_user(sel)
        test_create_tutorial.test_create_tutorial(sel)
        test_edit_tutorial.test_edit_tutorial(sel)
        test_add_author.test_add_author(sel)
        test_remove_author.test_remove_author(sel)
        test_validate_tutorial.test_validate_tutorial(sel)
        test_delete_tutorial.test_delete_tutorial(sel)

    def tearDown(self):
        self.selenium.stop()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
