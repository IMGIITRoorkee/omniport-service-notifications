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
            return notification

    if has_custom_users_target:
        if not persons:
            raise ValueError(
                '\'persons\' cannot be falsy while'
                ' \'has_custom_users_target\' is True '
            )
        else:
            notification.save()
            _ = execute_users_set_push(
                notification_id=notification.id,
                persons=persons
            )
            return notification

    if not (is_personalised and has_custom_users_target):
        notification.save()
        res = execute_topic_push(notification)
        if not res:
            notification.delete()
            pass  # TODO Log and raise error

    return notification
