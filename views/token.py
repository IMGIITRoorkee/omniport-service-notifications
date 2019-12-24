from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from notifications.redisdb import PushEndpoint


class FCMToken(APIView):
    """
    View to handle FCM client tokens
    """

    permission_classes = [IsAuthenticated, ]
    http_method_names = ['post', 'delete']

    def post(self, request):
        """
        Add token to the user's FCM token list
        :param request: API request
        :return: API response
        """

        try:
            res = PushEndpoint(
                person_id=request.person.id,
                session_id=request.session.session_key,
                endpoint=request.data['token']
            ).save()
        except KeyError:
            return Response(
                data={
                    'success': False,
                    'error': 'Invalid payload'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            data={
                'success': res,
            },
            status=status.HTTP_201_CREATED
            if res else status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request):
        """
        Delete token from the user's FCM token list
        :param request: API request
        :return: API response
        """
        res = PushEndpoint.delete(
            person_id=request.person.id,
            session_id=request.session.session_key
        )
        return Response(
            data={
                'success': res,
            },
            status=status.HTTP_201_CREATED
            if res else status.HTTP_400_BAD_REQUEST
        )
