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
            # Get a random identifier from the client generated on the basis of person id and current timestamp
            # This identifier can be stored with the client and can be used to remove the token when authentication
            # is not based on session
            if not bool(request.session.session_key):
                client_identifier = request.data['client_identifier']
            else:
                client_identifier = request.session.session_key

            res = PushEndpoint(
                person_id=request.person.id,
                session_id=client_identifier,
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
        try:
            # Delete the endpoint using the client identifier when the authentication used by client
            # is not session based
            if not bool(request.session.session_key):
                client_identifier = request.data['client_identifier']
            else:
                client_identifier = request.session.session_key
            
            res = PushEndpoint.delete(
                person_id=request.person.id,
                session_id=client_identifier
            )
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
            status=status.HTTP_204_NO_CONTENT
            if res else status.HTTP_400_BAD_REQUEST
        )
