from django_redis import get_redis_connection

from notifications.constants import REDIS_CONNECTION_NAME

client = get_redis_connection(REDIS_CONNECTION_NAME)


class GetTokenType:
    """
    This class defines the token type web or android for the endpoints
    """

    key_prefix = 'notifications:token_type'

    def __init__(self, person_id, token_type, endpoint):
        """
        Constructor for class `PushEndpoint`
        :param person_id: logged-in person's Db id
        :param token_type: token key
        :param endpoint: endpoint value
        """

        self.person_id = person_id
        self.token_type = token_type
        self.endpoint = endpoint

    def save(self):
        """
        Save endpoint to redis database
        :return: success True/False
        """

        _ = client.lpush(
            f'{self.key_prefix}:{self.token_type}:{self.person_id}',
            self.endpoint
        )
        return True

    @classmethod
    def delete(cls, person_id, token_type, endpoint, count=0):
        """
        Delete endpoint from redis database
        :param person_id: Person's db id
        :param token type:
        :return:
        """
        # delete from redis
        _ = client.lrem(
            f'{cls.key_prefix}:{token_type}:{person_id}',
            count,
            endpoint
        )
        return True

    @classmethod
    def fetch(cls, person_id, token_type, start=0, end=-1):
        """
        Fetch the list of registered endpoints of given token type
        :param cls:
        :param person_id:
        :param token_type:
        :return: return an array of array of endpoints
        """

        results = client.lrange(
            f'{cls.key_prefix}:{token_type}:{person_id}',
            start,
            end
        )
        print(f'{person_id} {token_type} {results}')
        if results:
            return [s.decode('utf-8') for s in results]
        else:
            return []
