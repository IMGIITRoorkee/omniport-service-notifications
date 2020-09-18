import swapper
from django.dispatch import receiver
from django.db.models.signals import (
    post_save
)

from rest_framework import status
from rest_framework.response import Response

from categories.models import (
    UserSubscription,
    Category
)

@receiver(post_save, sender = Category)
def subscription_all_persons(sender, instance, **kwargs):    
    """ 
    Database signal receiver for the notification subscription of all Persons
    to every new Category created.
    :param sender: Category Model Class
    :param instance: new Category object created
    :param kwargs:
    """
    
    persons_list = swapper.load_model('kernel', 'Person').objects.all()
    persons_list = list(persons_list)
    
    for person in persons_list:
        _ = UserSubscription(
            person = person,
            category = instance,
            action = 'notifications'
        ).subscribe()
