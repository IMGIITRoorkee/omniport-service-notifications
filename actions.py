import logging

from notifications.models import Notification
from notifications.tasks import (
    execute_topic_push,
    execute_users_set_push,
)
from notifications.utils.fcm import fcm_push
from notifications.redisdb import (
    PushEndpoint,
    UserNotification,
)

logger = logging.getLogger('notifications')


def push_notification(
        template,
        category,
        web_onclick_url='',
        android_onclick_activity='',
        ios_onclick_action='',
        is_personalised=False,
        person=None,
        has_custom_users_target=False,
        persons=None
):
    """
    Unified method to generate notification object and execute pushing
    :param template: Template string or Body string of the notification
    :param category: Category object to which the notification belongs to
    :param web_onclick_url: Onclick url for web push notification as well as at frontend
    :param android_onclick_activity: Name of android activity to open on clicking the notification
    :param ios_onclick_action: # TODO
    :param is_personalised: Flag for a personalised notification
    :param person: Person corresponding to the personalised notification
    :param has_custom_users_target: Flag for a notification with a custom users target
    :param persons: Custom users target
    :return: Notification object
    """

    try:
        app_base_url = category.app_config.base_urls.http
    except AttributeError:
        app_base_url = ''

    notification = Notification(
        template=template,
        category=category,
        web_onclick_url=web_onclick_url or app_base_url,
        android_onclick_activity=android_onclick_activity,
        ios_onclick_action=ios_onclick_action,
        is_personalised=is_personalised,
        has_custom_users_target=has_custom_users_target,
    )

    # Exception handling
    if is_personalised and has_custom_users_target:
        raise ValueError(
            '\'is_personalised\' and \'has_custom_users_target\' cannot be '
            'True at the same time '
        )

    if is_personalised:
        if person is None:
            logger.error(
                f'Incorrect argument for notification #{notification.id}: '
                '\'person\' cannot be None for a personalised notification'
            )
            raise ValueError(
                '\'person\' cannot be None for a personalised notification'
            )
        else:
            notification.save()
            all_endpoints = PushEndpoint.fetch(person)
            UserNotification(
                person_id=person,
                notification_id=notification.id
            ).push()
            if all_endpoints:
                _ = fcm_push(
                    notification_id=notification.id,
                    tokens=all_endpoints,
                )
            logger.info(
                f'Personal notification #{notification.id} successfully sent'
            )
            return notification

    if has_custom_users_target:
        if persons is None:
            logger.error(
                'Incorrect argument for notification #{notification.id}: '
                '\'persons\' cannot be None while \'has_custom_users_target\' '
                'is True '
            )
            raise ValueError(
                '\'persons\' cannot be None while \'has_custom_users_target\' '
                'is True '
            )
        else:
            notification.save()
            _ = execute_users_set_push(
                notification_id=notification.id,
                persons=persons
            )
            logger.info(
                f'Mass notification #{notification.id} successfully sent'
            )
            return notification

    if not (is_personalised and has_custom_users_target):
        notification.save()
        _ = execute_topic_push(notification)
        logger.info(
            f'Topic notification #{notification.id} successfully sent'
        )

    return notification
