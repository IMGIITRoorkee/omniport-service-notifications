from urllib.parse import urljoin

from firebase_admin import messaging

from notifications.models import Notification


def fcm_push(notification_id, tokens=None):
    """
    FCM message push, either to all users subscribed to the
    topic(category slug), or to a specific user targeted by the specified token.
    :param notification_id: Notification id.
    :param tokens: Specific tokens of clients to push the notification to.
    :return: None
    """

    BASE_URL = ''

    try:
        notification = Notification.objects.get(id=notification_id)
        app_config = notification.category.app_config

    except Notification.DoesNotExist as e:
        # TODO Log
        print(str(e))
        return False

    print('fcm push')  # TODO remove print

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
            data=dict(
                onlclick_url=notification.web_onclick_url
            )
        )
    extra_data = dict(
        app_icon_url=urljoin(
            app_config.base_urls.static, app_config.assets.logo
        )
    )

    # If tokens are provided, make a multicast message
    # else it is assumed that it is a topic based broadcast
    if tokens:
        message = messaging.MulticastMessage(
            notification=base_notification,
            data=extra_data,
            android=android_conf,
            webpush=webpush_conf,
            tokens=tokens
        )
    else:
        message = messaging.Message(
            notification=base_notification,
            data=extra_data,
            android=android_conf,
            webpush=webpush_conf,
            topic=notification.category.slug
        )

    try:
        # use dry_run = True for testing purpose
        if tokens:
            response = messaging.send_multicast(message, dry_run=False)
        else:
            response = messaging.send(message, dry_run=False)
        print('FCM response', response, type(response))
        # TODO validate for response
    except messaging.ApiCallError as e:
        # TODO Log
        print(1, e)
        return False
    except ValueError as e:
        print(2, e)
        # TODO Log
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
        response = messaging.subscribe_to_topic(tokens, topic)
        print(response.success_count)
        # TODO validate for response
    except messaging.ApiCallError as e:
        print(1, e)
        # TODO Log
        return False
    except ValueError as e:
        print(2, e, type(tokens))
        # TODO Log
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
        response = messaging.unsubscribe_from_topic(tokens, topic)
        print(response.success_count)
        # TODO validate for response
    except messaging.ApiCallError as e:
        print(1, e)
        # TODO Log
        return False
    except ValueError as e:
        print(2, e)
        # TODO Log
        return False

    return True
