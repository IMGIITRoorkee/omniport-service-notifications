from notifications.redisdb import PushEndpoint
from notifications.utils.fcm import (
    fcm_subscribe,
    fcm_unsubscribe
)
from notifications.utils.topics import (
    flagged_topics,
    joined_topics
)


def register_endpoint(person_id, field, token):
    """
    Register a token under a field of the person and join it to their topics.
    Safe to call on every launch of a client.
    :param person_id: Person's db id
    :param field: Client identifier the token is registered under
    :param token: FCM token
    :return: success True/False
    """

    # A phone that changed hands after an offline logout still has the
    # previous person's token, which must stop getting their pushes
    owner = PushEndpoint.owner(token)
    if owner is not None and owner != (person_id, field):
        previous_person_id, previous_field = owner
        PushEndpoint.remove(previous_person_id, previous_field, token)
        _leave(token, joined_topics(previous_person_id))

    # A refreshed token replaces the old one, which leaves the topics
    previous_token = PushEndpoint.fetch_one(person_id, field)
    if previous_token is not None and previous_token != token:
        PushEndpoint.remove(person_id, field, previous_token)
        _leave(previous_token, joined_topics(person_id))

    PushEndpoint(
        person_id=person_id,
        session_id=field,
        endpoint=token
    ).save()

    # Rejoining every time repairs a topic that a failed subscribe left out
    for topic in flagged_topics(person_id):
        fcm_subscribe(tokens=[token], topic=topic)

    return True


def unregister_endpoint(person_id, field):
    """
    Take the token under a field of the person out of their topics, then
    forget it
    :param person_id: Person's db id
    :param field: Client identifier the token is registered under
    :return: success True/False
    """

    token = PushEndpoint.fetch_one(person_id, field)
    if token is not None:
        _leave(token, joined_topics(person_id))

    return PushEndpoint.delete(person_id, field)


def _leave(token, topics):
    for topic in topics:
        fcm_unsubscribe(tokens=[token], topic=topic)
