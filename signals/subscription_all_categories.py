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

Person = swapper.get_model_name('kernel', 'Person')
@receiver(post_save, sender = Person)
def subscription_all_categories(sender, instance, **kwargs):
    """ 
    Database signal receiver for notification subscription to all Categories
    whenever a new Person is created.
    :param sender: Person model class
    :param instance: new Person object created
    :param kwargs:
    """
    
    category_list = Category.objects.filter(level=0)
    category_list = list(category_list)
    
    for category in category_list:        
        _ = UserSubscription(
            person = instance,
            category = category,
            action = 'notifications'
        ).subscribe()
