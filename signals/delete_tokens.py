from django.dispatch import receiver
from django.db.models.signals import (
    pre_delete,
    post_save
)

from session_auth.models import (
    SessionMap
)
from notifications.redisdb.push_endpoint import (
    PushEndpoint
)

@receiver(pre_delete, sender = SessionMap)
def delete_tokens(sender, instance, **kwargs):
    """
    Signal to delete the token from tokens list when session logged out.
    :param sender: Session Map Model
    :param instance: Session Map object of current User 
    :param kwargs: None
    """
    
    # Delete the endpoint using the client identifier when the client
    # is logged out of session
    client_identifier = instance.session_key

    res = PushEndpoint.delete(
        person_id=instance.user.id,
        session_id=client_identifier
    )
    print(f'signal (pre_delete) {instance}')
