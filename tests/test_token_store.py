"""
Tests for registering push tokens and moving them between topics

Run from the repository folder, in an environment with Django and
firebase_admin installed, with
    python -m unittest discover --start-directory tests
"""

import unittest
from unittest import mock

from firebase_admin import messaging

import stubs
from stubs import Category, PushEndpoint, Subscriptions, push_endpoints
from notifications.utils.topics import joins_topic

ANNOUNCEMENT_PLA = Category(
    'placement_and_internship__profile_announcement__pla', {'fcmTopic': True}
)
RESULTS_INT = Category(
    'placement_and_internship__results__int', {'fcmTopic': True}
)
APP_STATUS = Category(
    'placement_and_internship__app_status_update', {'fcmTopic': False}
)
NOTICEBOARD = Category('noticeboard')


def topic_response(tokens, topic):
    return messaging.TopicManagementResponse(
        {'results': [{} for _ in tokens]}
    )


class TopicTestCase(unittest.TestCase):
    """
    Patch the FCM topic calls and record which topics each token moved to
    """

    def setUp(self):
        stubs.reset()
        self.subscribe = self._patch('subscribe_to_topic')
        self.unsubscribe = self._patch('unsubscribe_from_topic')

    def _patch(self, name):
        patcher = mock.patch.object(
            messaging, name, side_effect=topic_response
        )
        self.addCleanup(patcher.stop)
        return patcher.start()

    @staticmethod
    def moves(fcm_call):
        return sorted(
            (tuple(call.args[0]), call.args[1])
            for call in fcm_call.call_args_list
        )

    def reset_calls(self):
        self.subscribe.reset_mock()
        self.unsubscribe.reset_mock()


class JoinsTopicTestCase(unittest.TestCase):
    """
    Only categories that opt out stay out of their topic
    """

    def test_a_category_marked_false_does_not_join(self):
        self.assertFalse(joins_topic(APP_STATUS))

    def test_a_category_marked_true_joins(self):
        self.assertTrue(joins_topic(ANNOUNCEMENT_PLA))

    def test_a_category_without_meta_joins_as_before(self):
        self.assertTrue(joins_topic(NOTICEBOARD))


class RegisterEndpointTestCase(TopicTestCase):
    """
    Posting a token stores it, and moves it and any token it replaces
    """

    def setUp(self):
        super().setUp()
        Subscriptions.rows = [
            (1, ANNOUNCEMENT_PLA, 'notifications'),
            (1, APP_STATUS, 'notifications'),
            (1, NOTICEBOARD, 'notifications'),
            (1, RESULTS_INT, 'emails'),
            (2, RESULTS_INT, 'notifications'),
        ]

    def test_a_new_token_is_stored_with_its_owner(self):
        push_endpoints.register_endpoint(1, 'placement-app:a', 'token')

        self.assertEqual(
            PushEndpoint.fetch_one(1, 'placement-app:a'), 'token'
        )
        self.assertEqual(PushEndpoint.owner('token'), (1, 'placement-app:a'))
        self.assertEqual(sorted(stubs.redis.data), [
            'notifications:push_endpoint:person:1',
            'notifications:push_endpoint:token:token',
        ])

    def test_a_new_token_joins_only_the_topics_marked_true(self):
        push_endpoints.register_endpoint(1, 'placement-app:a', 'token')

        self.assertEqual(
            self.moves(self.subscribe),
            [(('token',), ANNOUNCEMENT_PLA.slug)],
        )
        self.assertEqual(self.moves(self.unsubscribe), [])

    def test_reposting_the_same_token_joins_its_topics_again(self):
        push_endpoints.register_endpoint(1, 'placement-app:a', 'token')
        self.reset_calls()

        push_endpoints.register_endpoint(1, 'placement-app:a', 'token')

        self.assertEqual(
            self.moves(self.subscribe),
            [(('token',), ANNOUNCEMENT_PLA.slug)],
        )
        self.assertEqual(self.moves(self.unsubscribe), [])

    def test_a_reassigned_token_moves_to_the_new_owners_topics(self):
        push_endpoints.register_endpoint(1, 'placement-app:a', 'token')
        self.reset_calls()

        push_endpoints.register_endpoint(2, 'placement-app:b', 'token')

        # It leaves every topic the subscription signal may have joined it
        # to, but not the one that never has a topic
        self.assertEqual(
            self.moves(self.unsubscribe),
            [
                (('token',), NOTICEBOARD.slug),
                (('token',), ANNOUNCEMENT_PLA.slug),
            ],
        )
        self.assertEqual(
            self.moves(self.subscribe),
            [(('token',), RESULTS_INT.slug)],
        )

    def test_a_reassigned_token_is_taken_from_the_previous_owner(self):
        push_endpoints.register_endpoint(1, 'placement-app:a', 'token')

        push_endpoints.register_endpoint(2, 'placement-app:b', 'token')

        self.assertEqual(PushEndpoint.fetch(1), [])
        self.assertEqual(PushEndpoint.fetch(2), ['token'])
        self.assertEqual(PushEndpoint.owner('token'), (2, 'placement-app:b'))

    def test_a_token_moved_to_another_field_leaves_the_first(self):
        push_endpoints.register_endpoint(1, 'placement-app:a', 'token')

        push_endpoints.register_endpoint(1, 'placement-app:b', 'token')

        self.assertEqual(
            PushEndpoint.fetch_fields(1), {'placement-app:b': 'token'}
        )

    def test_a_refreshed_token_takes_the_old_one_out_of_the_topics(self):
        push_endpoints.register_endpoint(1, 'placement-app:a', 'old')
        self.reset_calls()

        push_endpoints.register_endpoint(1, 'placement-app:a', 'new')

        self.assertEqual(
            self.moves(self.unsubscribe),
            [
                (('old',), NOTICEBOARD.slug),
                (('old',), ANNOUNCEMENT_PLA.slug),
            ],
        )
        self.assertEqual(
            self.moves(self.subscribe),
            [(('new',), ANNOUNCEMENT_PLA.slug)],
        )
        self.assertEqual(PushEndpoint.fetch(1), ['new'])
        self.assertIsNone(PushEndpoint.owner('old'))

    def test_a_failed_subscribe_does_not_fail_the_post(self):
        self.subscribe.side_effect = ValueError('FCM is down')

        self.assertTrue(
            push_endpoints.register_endpoint(1, 'placement-app:a', 'token')
        )
        self.assertEqual(PushEndpoint.fetch(1), ['token'])


class UnregisterEndpointTestCase(TopicTestCase):
    """
    Deleting a token takes it out of the topics before forgetting it
    """

    def setUp(self):
        super().setUp()
        Subscriptions.rows = [
            (1, ANNOUNCEMENT_PLA, 'notifications'),
            (1, APP_STATUS, 'notifications'),
        ]
        push_endpoints.register_endpoint(1, 'placement-app:a', 'token')
        push_endpoints.register_endpoint(1, 'placement-app:b', 'other')
        self.reset_calls()

    def test_the_token_leaves_the_topics(self):
        push_endpoints.unregister_endpoint(1, 'placement-app:a')

        self.assertEqual(
            self.moves(self.unsubscribe),
            [(('token',), ANNOUNCEMENT_PLA.slug)],
        )

    def test_the_token_and_its_keys_are_forgotten(self):
        push_endpoints.unregister_endpoint(1, 'placement-app:a')

        self.assertEqual(
            PushEndpoint.fetch_fields(1), {'placement-app:b': 'other'}
        )
        self.assertIsNone(PushEndpoint.owner('token'))
        self.assertEqual(PushEndpoint.owner('other'), (1, 'placement-app:b'))

    def test_an_unknown_field_moves_nothing(self):
        self.assertTrue(
            push_endpoints.unregister_endpoint(1, 'placement-app:c')
        )
        self.assertEqual(self.moves(self.unsubscribe), [])
        self.assertEqual(len(PushEndpoint.fetch(1)), 2)


if __name__ == '__main__':
    unittest.main()
