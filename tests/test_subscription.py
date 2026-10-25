"""
Tests for reading the notification settings tree

Run from the repository folder, in an environment with Django and
firebase_admin installed, with
    python -m unittest discover --start-directory tests
"""

import types
import unittest

import stubs
from stubs import Category, Roots, subscription_view


def get(app=None, person='person'):
    request = types.SimpleNamespace(
        person=person,
        query_params={'app': app} if app is not None else {},
    )
    return subscription_view.Subscription().get(request)


class SubscriptionReadTestCase(unittest.TestCase):
    """
    The tree is read for the person asking, and for one app when asked
    """

    def setUp(self):
        stubs.reset()
        Roots.rows = [
            Category('noticeboard'),
            Category('placement_and_internship'),
        ]

    def test_the_tree_is_read_for_the_person_and_notifications(self):
        response = get(person='student')

        for root in response.data:
            self.assertEqual(
                root['context'],
                {'person': 'student', 'action': 'notifications'},
            )

    def test_an_app_returns_only_its_root(self):
        response = get(app='placement_and_internship')

        self.assertEqual(
            [root['slug'] for root in response.data],
            ['placement_and_internship'],
        )

    def test_without_an_app_every_root_is_returned(self):
        response = get()

        self.assertEqual(
            [root['slug'] for root in response.data],
            ['noticeboard', 'placement_and_internship'],
        )

    def test_an_unknown_app_returns_nothing(self):
        self.assertEqual(get(app='unknown').data, [])


if __name__ == '__main__':
    unittest.main()
