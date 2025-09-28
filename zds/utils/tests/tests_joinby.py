from django.test import TestCase

from zds.utils.templatetags.joinby import joinby


class JoinByTest(TestCase):
    def test_main(self):
        self.assertEqual(joinby(()), "")

        xs = ["apple", "banana", "orange", "clementine"]
        self.assertEqual(joinby(xs, final_separator=", "), "apple, banana, orange, clementine")

        xs = ["apple", "banana", "orange", "clementine"]
        self.assertEqual(joinby(xs, final_separator=" and "), "apple, banana, orange and clementine")

        xs = ["apple", "banana", "orange", "clementine"]
        self.assertEqual(joinby(xs, separator=";", final_separator=";"), "apple;banana;orange;clementine")

        xs = [1, 2, 3, 4]
        self.assertEqual(joinby(xs, separator=";", final_separator=";"), "1;2;3;4")

        xs = ["Clem"]
        self.assertEqual(joinby(xs, final_separator=" and "), "Clem")

        xs = ["Clem", "Chuck Norris"]
        self.assertEqual(joinby(xs, final_separator=" and "), "Clem and Chuck Norris")

        xs = ["Clem", "Chuck Norris", "Arnold Schwarzenegger"]
        self.assertEqual(joinby(xs, final_separator=" and "), "Clem, Chuck Norris and Arnold Schwarzenegger")
