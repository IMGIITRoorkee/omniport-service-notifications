import datetime
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from discovery.available import available_apps
from categories.models import UserSubscription, Category
from categories.serializers import SubscriptionTreeSerializer
from notifications.models import Notification
from notifications.serializers import NotificationSerializer
from notifications.redisdb import UserNotification
from notifications.constants import NOTIFICATION_AGE_LIMIT


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
        TODO
        :return:
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
        :return:
        """

        person_id = self.request.person.id
        data = UserNotification.fetch(
            person_id=person_id
        )

        available = available_apps(
            request=self.request,
        )
        apps = [
            app
            for (app, app_configuration)
            in available
        ]

        all_notification_ids = data['all']

        app_filter = Q(pk=None)
        for app in apps:
            app_filter |= Q(category__slug__startswith=app)

        notifications_list = Notification.objects.filter(
            datetime_created__gt=self._time_threshold
        ).filter(
            id__in=all_notification_ids
        ).filter(app_filter)

        return notifications_list


class MarkRead(APIView):
    """
    TODO
    """

    permission_classes = [IsAuthenticated, ]

    def post(self, request, *args, **kwargs):
        """
        TODO
        :param request:
        :param args:
        :param kwargs:
        :return:
        """

        try:
            notification_ids = request.data['ids']
            print('\n#### ', type(notification_ids), notification_ids)
        except KeyError as e:
            print('\n#### ', e, request.data, '\n')
            # TODO Log
            return Response(
                data={
                    'success': False,
                    'error': 'Invalid payload'
                },
                status=400
            )

        unread_left = UserNotification.mark_read(
            request.person.id,
            notification_ids
        )

        return Response(
            data={
                'success': True,
                'unread': unread_left
            },
            status=200
        )


class Subscription(APIView):
    """
    TODO
    """

    permission_classes = [IsAuthenticated, ]

    def get(self, request, *args, **kwargs):
        """

        :param request:
        :param args:
        :param kwargs:
        :return:
        """

        roots = Category.objects.root_nodes()
        serializer = SubscriptionTreeSerializer(roots, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        """

        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            new_subscriptions = request.data['save']
            new_unsubscription = request.data['delete']
        except KeyError:
            # TODO Log
            return Response(
                data={
                    'success': False,
                    'error': 'Invalid payload'
                },
                status=400
            )

        for category in new_subscriptions:
            _ = UserSubscription(
                person=request.person,
                category=category,
                action='notifications',
            ).subscribe()

        for category in new_unsubscription:
            _ = UserSubscription(
                person=request.person,
                category=category,
                action='notifications',
            ).unsubscribe()

        return Response(
            data={
                'success': True,
            },
            status=200
        )


class FCMToken(APIView):
    """
    TODO
    """

    permission_classes = [IsAuthenticated, ]

    def post(self, request, *args, **kwargs):
        """
        TODO
        :param request:
        :param args:
        :param kwargs:
        :return:
        """

        print('\n#### ', request.data, '\n')

        return Response(
            data={
                'success': True,
            },
            status=200
        )
