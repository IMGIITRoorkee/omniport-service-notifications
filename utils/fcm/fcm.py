import os

from firebase_admin import messaging
from django.conf import settings

from notifications.models import Notification


def fcm_push(notification_id, tokens=None):
    """
    FCM message push, either to all users subscribed to the
    topic(category slug), or to a specific user targeted by the specified token.
    :param notification_id: Notification id.
    :param tokens: Specific tokens of clients to push the notification to.
    :return: None
    """

    try:
        notification = Notification.objects.get(id=notification_id)
        app_config = notification.category.app_config

    except Notification.DoesNotExist:
        return False

    base_notification = messaging.Notification(
        title=notification.category.name,
        body=notification.template,
    )
    android_conf = messaging.AndroidConfig(
        notification=messaging.AndroidNotification(
            click_action=notification.android_onclick_activity
        )
    )
    webpush_conf = messaging.WebpushConfig(
        notification=messaging.WebpushNotification(
            icon=os.path.join(
                settings.STATIC_URL,
                app_config.base_urls.static,
                'assets',
                app_config.assets.logo,
            ),
            actions=[
                messaging.WebpushNotificationAction(
                    action=notification.web_onclick_url,
                    title=f'Open {notification.web_onclick_url}'
                )
            ]
        )
    )

    # If tokens are provided, make a multicast message
    # else it is assumed that it is a topic based broadcast
    if tokens:
        message = messaging.MulticastMessage(
            notification=base_notification,
            android=android_conf,
            webpush=webpush_conf,
            tokens=tokens
        )
    else:
        message = messaging.Message(
            notification=base_notification,
            android=android_conf,
            webpush=webpush_conf,
            topic=notification.category.slug
        )

    try:
        # use dry_run = True for testing purpose
        if tokens:
            _ = messaging.send_multicast(message, dry_run=False)
        else:
            _ = messaging.send(message, dry_run=False)
    except messaging.ApiCallError as e:
        return False
    except ValueError as e:
        return False

    return True


def fcm_subscribe(tokens, topic):
    """
    Subscribe the given tokens to a specific FCM topic.
    :param tokens: list of FCM tokens
    :param topic: FCM topic/category slug
    :return: success True/False
    """

    try:
        _ = messaging.subscribe_to_topic(tokens, topic)
    except messaging.ApiCallError as e:
        return False
    except ValueError as e:
        return False

    return True


def fcm_unsubscribe(tokens, topic):
    """
    Unsubscribe the given tokens from a specific FCM topic.
    :param tokens: list of FCM tokens
    :param topic: FCM topic/category slug
    :return: success True/False
    :return:
    """

    try:
        _ = messaging.unsubscribe_from_topic(tokens, topic)
    except messaging.ApiCallError as e:
        return False
    except ValueError as e:
        return False

    return True
