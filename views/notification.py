import datetime

from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from discovery.available import available_apps
from omniport.settings import DISCOVERY
from notifications.models import Notification
from notifications.serializers import NotificationSerializer
from notifications.constants import NOTIFICATION_AGE_LIMIT
from notifications.redisdb import UserNotification


class UserNotificationViewSet(ModelViewSet):
    """
    The view for fetching user notifications
    """
    _time_threshold = datetime.date.today() - datetime.timedelta(
        NOTIFICATION_AGE_LIMIT)

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated, ]
    http_method_names = ['get', ]

    def get_serializer_context(self):
        """
        Pass context to the serializer
        :return: the context data
        """

        person_id = self.request.person.id
        data = UserNotification.fetch(
            person_id=person_id
        )
        unread_notification_ids = data['unread']
        return {'unread': unread_notification_ids}

    def get_queryset(self):
        """
        Queryset for fetching user notifications
        :return: the queryset of user notifications
        """

        person_id = self.request.person.id
        data = UserNotification.fetch(
            person_id=person_id
        )

        specific_app = self.request.query_params.get('app', False)
        available_services = set(service for service, _ in DISCOVERY.services)
        available = set(app for app, _ in available_apps(
            request=self.request,
        )) | available_services
        if specific_app:
            if specific_app in available:
                available = [specific_app]
            else:
                available = []

        all_notification_ids = data['all']

        app_filter = Q(pk=None)
        for app in available:
            app_filter |= Q(category__slug__startswith=app)

        notifications_list = Notification.objects.filter(
            datetime_created__gt=self._time_threshold
        ).filter(
            id__in=all_notification_ids
        ).filter(app_filter)
        return notifications_list
