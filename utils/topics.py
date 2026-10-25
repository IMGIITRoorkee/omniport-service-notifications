from categories.models import UserSubscription


def joins_topic(category):
    """
    Whether a notifications subscription to the category joins its FCM topic.
    A category opts out with "fcmTopic": false in its meta, for rows that are
    only ever pushed to directly, so that their topic never reaches anybody.
    :param category: Category object
    :return: True/False
    """

    return (category.meta or {}).get('fcmTopic') is not False


def joined_topics(person_id):
    """
    Topics that the person's tokens may have joined through the subscription
    signal, which a token has to leave when it stops being theirs
    :param person_id: Person's db id
    :return: list of category slugs
    """

    return [
        subscription.category.slug
        for subscription in _subscriptions(person_id)
        if joins_topic(subscription.category)
    ]


def flagged_topics(person_id):
    """
    Topics of the categories marked "fcmTopic": true that the person is
    subscribed to, which every token posted by them joins
    :param person_id: Person's db id
    :return: list of category slugs
    """

    return [
        subscription.category.slug
        for subscription in _subscriptions(person_id)
        if (subscription.category.meta or {}).get('fcmTopic') is True
    ]


def _subscriptions(person_id):
    return UserSubscription.objects.filter(
        person_id=person_id,
        action='notifications',
    ).select_related('category')
