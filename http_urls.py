from django.urls import path, include
from rest_framework import routers

from notifications.views import (
    UserNotificationViewSet,
    Subscription,
    MarkRead,
    FCMToken,
)

app_name = 'notifications'

router = routers.SimpleRouter()
router.register(
    r'user_notifications',
    UserNotificationViewSet,
    basename='user_notifications'
)

urlpatterns = [
    path('', include(router.urls)),
    path('subscription/', Subscription.as_view()),
    path('read/', MarkRead.as_view()),
    path('token/', FCMToken.as_view())
]
