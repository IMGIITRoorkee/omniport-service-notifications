import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from categories.models import UserSubscription, Category
from categories.serializers import SubscriptionTreeSerializer
from categories.utils.get_subscription import GetSubscription

logger = logging.getLogger('notifications')


class Subscription(APIView):
    """
    Handle notification subscription
    """

    permission_classes = [IsAuthenticated, ]

    def get(self, request, *args, **kwargs):
        """
        Fetch notifications subscription tree of the user
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
        Update notifications subscription tree of the user
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            new_subscriptions = request.data['save']
            new_unsubscription = request.data['drop']
        except KeyError:
            return Response(
                data={
                    'success': False,
                    'error': 'Invalid payload'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        subscribe,unsubscribe = GetSubscription(
                                new_subscriptions,
                                new_unsubscription,
                                request.person,
                                'notifications'
                            ).get_should_subscribe()

        failures = list()

        for category in unsubscribe:
            if not UserSubscription(
                person=request.person,
                category=category,
                action='notifications',
            ).unsubscribe():
                failures.append(category.slug)

        for category in subscribe:
            if not UserSubscription(
                person=request.person,
                category=category,
                action='notifications',
            ).subscribe():
                failures.append(category.slug)

        # Safe for the caller to retry: both calls are idempotent
        if failures:
            logger.error(
                'Failed to update the notification subscriptions of '
                f'{self.request.person} for the categories {failures}'
            )
            return Response(
                data={
                    'success': False,
                    'error': 'Some subscriptions could not be updated',
                    'failed': failures,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        logger.info(
            'Successfully updated the notification subscriptions for '
            f'{self.request.person}'
        )

        return Response(
            data={
                'success': True,
            },
            status=status.HTTP_201_CREATED
        )
