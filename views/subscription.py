from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from categories.models import UserSubscription, Category
from categories.serializers import SubscriptionTreeSerializer


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
            return Response(
                data={
                    'success': False,
                    'error': 'Invalid payload'
                },
                status=status.HTTP_400_BAD_REQUEST
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
            status=status.HTTP_201_CREATED
        )
