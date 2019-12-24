from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from notifications.redisdb import UserNotification


class MarkRead(APIView):
    """
    Mark notification read for the user
    """

    permission_classes = [IsAuthenticated, ]
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        try:
            notification_ids = request.data['ids']
        except KeyError:
            return Response(
                data={
                    'success': False,
                    'error': 'Invalid payload'
                },
                status=status.HTTP_400_BAD_REQUEST
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
            status=status.HTTP_201_CREATED
        )
