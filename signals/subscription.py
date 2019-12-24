from django.dispatch import receiver
from django.db.models.signals import (
    pre_delete,
    post_save,
)

from categories.models import (
    UserSubscription
)
from notifications.redisdb.push_endpoint import (
    PushEndpoint
)
from notifications.utils.fcm import (
    fcm_subscribe,
    fcm_unsubscribe
)


@receiver(post_save, sender=UserSubscription)
def subscription_handler(sender, instance, **kwargs):
    """
    Database signal receiver for subscription
    :param sender:
    :param instance:
    :param kwargs:
    :return:
    """

    print(f'signal (post_save) {instance}')
    if instance.action == 'notifications':
        tokens = PushEndpoint.fetch(instance.person.id)
        if tokens:
            fcm_subscribe(tokens=tokens, topic=instance.category.slug)


@receiver(pre_delete, sender=UserSubscription)
def unsubscription_handler(sender, instance, **kwargs):
    """
    Database signal receiver for unsubscription
    :param sender:
    :param instance:
    :param kwargs:
    :return:
    """

    print(f'signal (pre_delete) {instance}')
    if instance.action == 'notifications':
        tokens = PushEndpoint.fetch(instance.person.id)
        if tokens:
            fcm_unsubscribe(tokens=tokens, topic=instance.category.slug)
