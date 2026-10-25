import logging

from omniport.celery import celery_app
from categories.redisdb import Subscription
from notifications.redisdb import PushEndpoint, UserNotification
from notifications.utils.fcm import (
    DEAD_TOKEN_ERRORS,
    fcm_push,
    fcm_push_multicast,
)
from notifications.constants import FCM_PUSH_LIMIT

logger = logging.getLogger('notifications')


def execute_topic_push(notification):
    """
    Topic push notification trigger function
    :param notification: notification to send
    :return: success/failure
    """

    category = notification.category.slug

    users = Subscription.fetch_people(
        category_slug=category,
        action='notifications'
    )

    # Register in (redis)database
    UserNotification.push_multiple(
        persons=users,
        notification_id=notification.id
    )

    return fcm_push(notification.id)


def execute_users_set_push(notification_id, persons):
    """
    Mass push notification trigger function
    :param notification_id: Notification id
    :param persons: List of user ids
    :return: success/failure
    """
    # A list of endpoints, independent of type
    endpoints = list()

    # Register in database
    UserNotification.push_multiple(
        persons=persons,
        notification_id=notification_id
    )
    for person in persons:
        endpoints += endpoints_of(person)

    res = list()
    for chunk in _divide_chunks(endpoints):
        res.append(subset_push.delay(notification_id, chunk))
    return all(res)


def endpoints_of(person_id):
    """
    List the person's endpoints, each with the person and field it is
    registered under so that it can be deleted if it turns out to be dead
    :param person_id: Person's db id
    :return: list of (person id, field, token)
    """

    return [
        (person_id, field, token)
        for field, token in PushEndpoint.fetch_fields(person_id).items()
    ]


def push_to_endpoints(notification_id, endpoints):
    """
    Push to the given endpoints and delete the tokens that FCM reports will
    never receive a push again
    :param notification_id: Notification id
    :param endpoints: List of (person id, field, token)
    :return: success/failure
    """

    # Tasks queued before endpoints carried their owner hold bare tokens
    endpoints = [
        endpoint if isinstance(endpoint, (list, tuple))
        else (None, None, endpoint)
        for endpoint in endpoints
    ]
    if not endpoints:
        return True

    response = fcm_push_multicast(
        notification_id=notification_id,
        tokens=[token for _, _, token in endpoints],
    )
    if response is None:
        return False

    # Any other error is not the token's fault: an invalid message, for
    # one, fails every token in the batch
    for (person_id, field, token), result in zip(
            endpoints, response.responses
    ):
        if (
            person_id is not None
            and isinstance(result.exception, DEAD_TOKEN_ERRORS)
        ):
            try:
                PushEndpoint.remove(person_id, field, token)
            except Exception:
                logger.exception(
                    f'Could not delete a dead token of person {person_id}'
                )

    return True


def _divide_chunks(endpoints):
    length = len(endpoints)
    for i in range(0, length, FCM_PUSH_LIMIT):
        yield endpoints[i:i + FCM_PUSH_LIMIT]


celery_app.control.add_consumer('notifications', reply=True) # Create separate queue for notifications task

# Queue
@celery_app.task(
    queue='notifications',
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 5}
)
def subset_push(notification_id, endpoints):
    """
    Batchwise pushing notifications using message-broker
    :param notification_id: Notification id
    :param endpoints: List of (person id, field, token) less than push limit
    :return: success/failure
    """
    return push_to_endpoints(
        notification_id=notification_id,
        endpoints=endpoints,
    )
