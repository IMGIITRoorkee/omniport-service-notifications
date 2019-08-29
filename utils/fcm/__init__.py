import os
import firebase_admin
from firebase_admin import credentials
from django.conf import settings

from notifications.utils.fcm.fcm import (
    fcm_push,
    fcm_subscribe,
    fcm_unsubscribe
)

service_account_file = os.path.join(
    settings.CERTIFICATES_DIR,
    'firebase_service_account.json',
)
cred = credentials.Certificate(str(service_account_file))
default_app = firebase_admin.initialize_app(cred)

__all__ = ['fcm_subscribe', 'fcm_push', 'fcm_unsubscribe']
