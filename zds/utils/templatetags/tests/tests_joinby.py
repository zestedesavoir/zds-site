from django.test import TestCase
from zds.utils.templatetags.joinby import joinby


class JoinByTest(TestCase):
    def test_main(self):
        self.assertEqual(joinby(()), '')

        l = ['apple', 'banana', 'orange', 'clementine']
        self.assertEqual(
            joinby(l, final_separator=', '),
            'apple, banana, orange, clementine'
        )

        l = ['apple', 'banana', 'orange', 'clementine']
        self.assertEqual(
            joinby(l, final_separator=' and '),
            'apple, banana, orange and clementine'
        )

        l = ['apple', 'banana', 'orange', 'clementine']
        self.assertEqual(
            joinby(l, separator=';', final_separator=';'),
            'apple;banana;orange;clementine'
        )

        l = [1, 2, 3, 4]
        self.assertEqual(
            joinby(l, separator=';', final_separator=';'),
            '1;2;3;4'
        )

        l = ['Clem']
        self.assertEqual(
            joinby(l, final_separator=' and '),
            'Clem'
        )

        l = ['Clem', 'Chuck Norris']
        self.assertEqual(
            joinby(l, final_separator=' and '),
            'Clem and Chuck Norris'
        )

        l = ['Clem', 'Chuck Norris', 'Arnold Schwarzenegger']
        self.assertEqual(
            joinby(l, final_separator=' and '),
            'Clem, Chuck Norris and Arnold Schwarzenegger'
        )
