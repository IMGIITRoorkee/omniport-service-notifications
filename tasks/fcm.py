from omniport.celery import celery_app
from categories.redisdb import Subscription
from notifications.redisdb import PushEndpoint, UserNotification
from notifications.utils.fcm import fcm_push
from notifications.constants import FCM_PUSH_LIMIT


def execute_topic_push(notification):
    """
    TODO
    :param notification: notification to send
    :return: None
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
    TODO
    :param notification_id: Notification id
    :param persons: List of user ids
    :return:
    """
    # TODO
    # A list of endpoints, independent of type
    endpoints = list()

    # Register in database
    UserNotification.push_multiple(
        persons=persons,
        notification_id=notification_id
    )
    for person in persons:
        endpoints += PushEndpoint.fetch(person)

    res = list()
    for chunk in _divide_chunks(endpoints):
        res.append(subset_push.delay(notification_id, chunk))
    return all(res)


def _divide_chunks(endpoints):
    length = len(endpoints)
    if length <= FCM_PUSH_LIMIT:
        yield endpoints
    for i in range(0, length, FCM_PUSH_LIMIT):
        yield endpoints[i:i + FCM_PUSH_LIMIT]


# Queue
@celery_app.task(
    queue='celery',
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 5}
)
def subset_push(notification_id, endpoints):
    """
    TODO
    :param notification_id: Notification id
    :param endpoints: List of endpoints less than push limit
    :return:
    """
    return fcm_push(
        notification_id=notification_id,
        tokens=endpoints,
    )
