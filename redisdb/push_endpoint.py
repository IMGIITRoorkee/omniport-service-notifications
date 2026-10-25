from django_redis import get_redis_connection

from notifications.constants import REDIS_CONNECTION_NAME

client = get_redis_connection(REDIS_CONNECTION_NAME)


class PushEndpoint:
    """
    This class defines the web, android and ios push notification endpoints
    """

    key_prefix = 'notifications:push_endpoint:person'

    # Which person and field a token is registered under, so that a token
    # posted by somebody else can be taken away from its previous owner
    owner_key_prefix = 'notifications:push_endpoint:token'

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

        pipe = client.pipeline(transaction=True)
        pipe.hset(
            f'{self.key_prefix}:{self.person_id}',
            self.session_id,
            self.endpoint
        )
        pipe.set(
            f'{self.owner_key_prefix}:{self.endpoint}',
            f'{self.person_id}|{self.session_id}'
        )
        pipe.execute()
        return True

    @classmethod
    def delete(cls, person_id, session_id):
        """
        Delete endpoint from redis database
        :param person_id: Person's db id
        :param session_id:
        :return:
        """

        endpoint = cls.fetch_one(person_id, session_id)

        pipe = client.pipeline(transaction=True)
        pipe.hdel(
            f'{cls.key_prefix}:{person_id}',
            session_id
        )
        if (
            endpoint is not None
            and cls.owner(endpoint) == (int(person_id), session_id)
        ):
            pipe.delete(f'{cls.owner_key_prefix}:{endpoint}')
        pipe.execute()
        return True

    @classmethod
    def remove(cls, person_id, session_id, endpoint):
        """
        Delete the endpoint only if the field still holds it, so that a token
        found to be dead does not take a newer one posted since with it
        :param person_id: Person's db id
        :param session_id: Field the endpoint was registered under
        :param endpoint: endpoint value
        :return: whether the endpoint was deleted
        """

        if cls.fetch_one(person_id, session_id) != endpoint:
            return False

        return cls.delete(person_id, session_id)

    @classmethod
    def fetch(cls, person_id):
        """
        Fetch the list of registered endpoints
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

    @classmethod
    def fetch_one(cls, person_id, session_id):
        """
        Fetch the endpoint registered under a field
        :param person_id: Person's db id
        :param session_id: Field the endpoint was registered under
        :return: endpoint value, or None
        """

        result = client.hget(
            f'{cls.key_prefix}:{person_id}',
            session_id
        )
        return result.decode('utf-8') if result is not None else None

    @classmethod
    def fetch_fields(cls, person_id):
        """
        Fetch the registered endpoints along with their fields
        :param person_id: Person's db id
        :return: dict of field to endpoint
        """

        results = client.hgetall(
            f'{cls.key_prefix}:{person_id}',
        )
        return {
            field.decode('utf-8'): endpoint.decode('utf-8')
            for field, endpoint in results.items()
        }

    @classmethod
    def owner(cls, endpoint):
        """
        Find who an endpoint is registered under
        :param endpoint: endpoint value
        :return: tuple of person id and field, or None
        """

        result = client.get(f'{cls.owner_key_prefix}:{endpoint}')
        if result is None:
            return None

        person_id, session_id = result.decode('utf-8').split('|', 1)
        return int(person_id), session_id

    @classmethod
    def persons(cls):
        """
        Iterate over the ids of the people with registered endpoints
        :return: generator of person ids
        """

        for key in client.scan_iter(match=f'{cls.key_prefix}:*'):
            yield int(key.decode('utf-8').rsplit(':', 1)[1])
