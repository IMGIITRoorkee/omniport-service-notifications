from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from categories.models import UserSubscription, Category
from categories.serializers import SubscriptionTreeSerializer


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

        for category_slug in new_subscriptions:
            category = Category.objects.get(slug=category_slug)
            try:
                UserSubscription.objects.get(
                    person=request.person,
                    category=category,
                    action='notifications')
            except UserSubscription.DoesNotExist:
                _ = UserSubscription(
                    person=request.person,
                    category=category,
                    action='notifications',
                ).subscribe()
                    
            

        for category in new_unsubscription:
            _ = UserSubscription(
                person=request.person,
                category=Category.objects.get(slug=category),
                action='notifications',
            ).unsubscribe()

        return Response(
            data={
                'success': True,
            },
            status=status.HTTP_201_CREATED
        )
