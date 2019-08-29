from django_redis import get_redis_connection

from notifications.constants import (
    REDIS_CONNECTION_NAME,
    USER_NOTIFICATIONS_LIMIT
)

client = get_redis_connection(REDIS_CONNECTION_NAME)


class UserNotification:
    """
    This class maps user with their corresponding notifications
    """

    key_prefix = 'notifications:user_notification:person'

    def __init__(self, person_id, notification_id, unread=True):
        self.person = person_id
        self.notification = notification_id
        self.unread = unread

    def push(self):
        """
        Push a single notification's id corresponding to the person's id
        :return: success True/False
        """

        pipe = client.pipeline(transaction=True)
        pipe.lpush(
            f'{self.key_prefix}:{self.person}:all',
            self.notification
        )
        if self.unread:
            pipe.lpush(
                f'notifications:person:{self.person}:unread',
                self.notification
            )

        res = pipe.execute()
        return all(res)

    @classmethod
    def mark_read(cls, person_id, notification_ids):
        """
        Mark all the notifications 'read' for the person corresponding to
        person_id
        :return: Final number of unread notifications.
        """

        pipe = client.pipeline(transaction=True)
        for notification_id in notification_ids:
            pipe.lrem(
                f'{cls.key_prefix}:{person_id}:unread',
                0,
                notification_id
            )
        pipe.llen(
            f'{cls.key_prefix}:{person_id}:unread'
        )
        results = pipe.execute()
        return results[-1]

    @classmethod
    def clear_all_unread(cls, person_id):
        """
        Mark all notifications 'read' for the corresponding user
        :return: Final number of unread notifications,i.e, 0
        """

        client.delete(f'{cls.key_prefix}:{person_id}:unread')
        return 0

    @classmethod
    def push_multiple(cls, persons, notification_id, unread=True):
        """
        Push a single notification with id as notification_id for
        multiple persons.
        :param persons: list of person ids,
        :param notification_id: notification id to be pushed
        :param unread: mark the notification unread or not
        :return: success True/False
        """

        pipe = client.pipeline(transaction=True)
        for person_id in persons:
            pipe.lpush(
                f'{cls.key_prefix}:{person_id}:all',
                notification_id
            )
            if unread:
                pipe.lpush(
                    f'{cls.key_prefix}:{person_id}:unread',
                    notification_id
                )
        res = pipe.execute()
        return all(res)

    @classmethod
    def fetch(cls, person_id, start=0, end=-1):
        """
        Fetch all ids of user notifications, read and unread separately
        :param person_id: id of person whose notifications are to be fetched
        :param start: starting index of notifications list
        :param end: ending index of notifications list
        :return: dict containing list of ids of 'all' & 'unread' notifications
        """

        # Trim existing list
        cls._trim(person_id)

        pipe = client.pipeline(transaction=True)
        pipe.lrange(
            f'{cls.key_prefix}:{person_id}:all',
            start,
            end
        )
        pipe.lrange(
            f'{cls.key_prefix}:{person_id}:unread',
            0,
            end
        )

        query_data = pipe.execute()

        result = {
            'all': set(
                int(s.decode('utf-8'))
                for s in set(query_data[0])
            ),
            'unread': set(
                int(s.decode('utf-8'))
                for s in (set(query_data[1]) & set(query_data[0]))
            )
        }
        return result

    @classmethod
    def _trim(cls, person_id):
        """
        Trim the list of user notifications :param person_id: person_id
        corresponding to the user whose notifications list is to be trimmed
        """

        all_count = client.llen(
            f'{cls.key_prefix}:{person_id}:all',
        )
        diff = all_count - USER_NOTIFICATIONS_LIMIT

        if diff > 0:
            last_elements = client.lrange(
                f'{cls.key_prefix}:{person_id}:all',
                -diff,
                -1,
            )

            pipe = client.pipeline(transaction=True)
            pipe.ltrim(
                f'{cls.key_prefix}:{person_id}:all',
                0,
                USER_NOTIFICATIONS_LIMIT - 1,
            )
            for element in last_elements:
                pipe.lrem(
                    f'{cls.key_prefix}:{person_id}:unread',
                    0,
                    element,
                )
            pipe.ltrim(
                f'{cls.key_prefix}:{person_id}:unread',
                0,
                USER_NOTIFICATIONS_LIMIT - 1,
            )
            pipe.execute()
