import os
import logging

from firebase_admin import messaging
from django.conf import settings

from notifications.models import Notification

logger = logging.getLogger('notifications')

# Errors after which a token will never receive a push again
DEAD_TOKEN_ERRORS = (
    messaging.UnregisteredError,
    messaging.SenderIdMismatchError,
)


def fcm_push(notification_id, tokens=None):
    """
    FCM message push, either to all users subscribed to the
    topic(category slug), or to a specific user targeted by the specified token.
    :param notification_id: Notification id.
    :param tokens: Specific tokens of clients to push the notification to.
    :return: success True/False
    """

    return _send(notification_id, tokens) is not None


def fcm_push_multicast(notification_id, tokens):
    """
    FCM message push to specific tokens, reporting the result for each token
    :param notification_id: Notification id.
    :param tokens: Specific tokens of clients to push the notification to.
    :return: BatchResponse in the order of the tokens, or None if nothing
    could be sent
    """

    # Without tokens the message would go to the whole topic
    if not tokens:
        return None

    return _send(notification_id, tokens)


def _send(notification_id, tokens):
    """
    Build the message for the notification and send it to the tokens, or to
    its topic when there are none
    :param notification_id: Notification id.
    :param tokens: Specific tokens of clients to push the notification to.
    :return: response from FCM, or None if nothing could be sent
    """

    try:
        notification = Notification.objects.get(id=notification_id)
        app_config = notification.category.app_config

    except Notification.DoesNotExist:
        logger.exception(f'Notification #{notification_id} does not exist')
        return None

    # FCM only accepts string values in the data map
    payload = {
        key: '' if value is None else str(value)
        for key, value in (notification.data or {}).items()
    }

    base_notification = messaging.Notification(
        title=payload.get('title') or notification.category.name,
        body=notification.template,
    )
    android_conf = messaging.AndroidConfig(
        notification=messaging.AndroidNotification(
            click_action=notification.android_onclick_activity or None
        )
    )
    apns_conf = messaging.APNSConfig(
        payload=messaging.APNSPayload(
            aps=messaging.Aps(sound='default')
        )
    )

    if app_config is not None and app_config.assets is not None:
        icon_url = os.path.join(
            settings.STATIC_URL,
            app_config.base_urls.static,
            'assets',
            app_config.assets.logo,
        )
    else:
        icon_url = os.path.join(
                settings.STATIC_URL,
                'notifications',
                settings.DISCOVERY.get_app_configuration(
                    'notifications'
                ).base_urls.static,
                'bell_icon.svg'
        )

    webpush_conf = messaging.WebpushConfig(
        notification=messaging.WebpushNotification(
            icon=icon_url,
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
            data=payload,
            notification=base_notification,
            android=android_conf,
            apns=apns_conf,
            webpush=webpush_conf,
            tokens=tokens
        )
    else:
        message = messaging.Message(
            data=payload,
            notification=base_notification,
            android=android_conf,
            apns=apns_conf,
            webpush=webpush_conf,
            topic=notification.category.slug
        )

    try:
        # use dry_run = True for testing purpose
        if tokens:
            response = messaging.send_multicast(message, dry_run=False)
        else:
            response = messaging.send(message, dry_run=False)
    except Exception:
        logger.exception(f'Could not push notification #{notification_id}')
        return None

    return response


def fcm_validate(tokens):
    """
    Send a dry run message to the tokens, which delivers nothing but reports
    the tokens that FCM no longer accepts
    :param tokens: list of FCM tokens, at most 500
    :return: BatchResponse in the order of the tokens, or None if the check
    could not be made
    """

    message = messaging.MulticastMessage(
        data={'type': 'validate'},
        tokens=tokens,
    )
    try:
        return messaging.send_multicast(message, dry_run=True)
    except Exception:
        logger.exception('Could not validate tokens')
        return None


def fcm_subscribe(tokens, topic):
    """
    Subscribe the given tokens to a specific FCM topic.
    :param tokens: list of FCM tokens
    :param topic: FCM topic/category slug
    :return: success True/False
    """

    try:
        response = messaging.subscribe_to_topic(tokens, topic)
    except Exception:
        logger.exception(f'Could not subscribe tokens to the topic {topic}')
        return False

    return _check_topic_response(response, 'subscribe to', topic)


def fcm_unsubscribe(tokens, topic):
    """
    Unsubscribe the given tokens from a specific FCM topic.
    :param tokens: list of FCM tokens
    :param topic: FCM topic/category slug
    :return: success True/False
    :return:
    """

    try:
        response = messaging.unsubscribe_from_topic(tokens, topic)
    except Exception:
        logger.exception(
            f'Could not unsubscribe tokens from the topic {topic}'
        )
        return False

    return _check_topic_response(response, 'unsubscribe from', topic)


def _check_topic_response(response, operation, topic):
    """
    Log the tokens that FCM refused to move, which it reports in the response
    rather than by raising
    :param response: TopicManagementResponse from FCM
    :param operation: Description of the operation, for the log
    :param topic: FCM topic/category slug
    :return: success True/False
    """

    if response.failure_count:
        reasons = ', '.join(error.reason for error in response.errors)
        logger.warning(
            f'{response.failure_count} tokens could not {operation} the topic '
            f'{topic}: {reasons}'
        )
        return False

    return True
