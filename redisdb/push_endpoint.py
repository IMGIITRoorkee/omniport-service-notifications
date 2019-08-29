from django_redis import get_redis_connection

from notifications.constants import REDIS_CONNECTION_NAME

client = get_redis_connection(REDIS_CONNECTION_NAME)


class PushEndpoint:
    """
    This class defines the web, android and ios push notification endpoints
    """

    key_prefix = 'notifications:push_endpoint:person'

    def __init__(self, person_id, session_id, endpoint):
        """
        Constructor for class `PushEndpoint`
        :param person_id: logged-in person's Db id
        :param endpoint: endpoint value
        """

        self.person_id = person_id
        self.session_id = session_id
        self.endpoint = endpoint

    def save(self):
        """
        Save endpoint to redis database
        :return: success True/False
        """

        _ = client.hset(
            f'{self.key_prefix}:{self.person_id}',
            self.session_id,
            self.endpoint
        )
        return True

    @classmethod
    def delete(cls, person_id, session_id):
        """
        Delete endpoint from redis database
        :param person_id: Person's db id
        :param session_id:
        :return:
        """
        # delete from redis
        _ = client.hdel(
            f'{cls.key_prefix}:{person_id}',
            session_id
        )
        return True

    @classmethod
    def fetch(cls, person_id):
        """
        TODO
        :param cls:
        :param person_id:
        :return: return an array of array of endpoints
        """

        results = client.hvals(
            f'{cls.key_prefix}:{person_id}',
        )
        print(f'{person_id} {results}')
        if results:
            return [s.decode('utf-8') for s in results]
        else:
            return []
