"""
Load the service's modules without a Django project

The service imports the categories service, the kernel's Person model, a
celery app and a Redis connection, none of which exist outside a running
omniport. This module puts small stand-ins for those in sys.modules and loads
the real modules of this service on top of them. firebase_admin is the real
library, with its network calls patched by the tests.
"""

import fnmatch
import importlib
import logging
import pathlib
import sys
import types

import django.conf

ROOT = pathlib.Path(__file__).resolve().parent.parent

if not django.conf.settings.configured:
    django.conf.settings.configure(STATIC_URL='/static/')

# The failures that the tests cause on purpose are logged with tracebacks
logging.getLogger('notifications').addHandler(logging.NullHandler())
logging.getLogger('notifications').propagate = False


class FakeRedis:
    """
    The subset of a Redis client that the service uses, storing bytes the way
    Redis returns them
    """

    def __init__(self):
        self.data = {}

    @staticmethod
    def _bytes(value):
        return value if isinstance(value, bytes) else str(value).encode()

    def flushall(self):
        self.data.clear()

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value):
        self.data[key] = self._bytes(value)
        return True

    def delete(self, *keys):
        return sum(self.data.pop(key, None) is not None for key in keys)

    def hset(self, key, field, value):
        hash_ = self.data.setdefault(key, {})
        is_new = self._bytes(field) not in hash_
        hash_[self._bytes(field)] = self._bytes(value)
        return int(is_new)

    def hget(self, key, field):
        return self.data.get(key, {}).get(self._bytes(field))

    def hdel(self, key, *fields):
        hash_ = self.data.get(key, {})
        removed = sum(
            hash_.pop(self._bytes(field), None) is not None
            for field in fields
        )
        if key in self.data and not hash_:
            del self.data[key]
        return removed

    def hgetall(self, key):
        return dict(self.data.get(key, {}))

    def hvals(self, key):
        return list(self.data.get(key, {}).values())

    def lpush(self, key, *values):
        list_ = self.data.setdefault(key, [])
        for value in values:
            list_.insert(0, self._bytes(value))
        return len(list_)

    def scan_iter(self, match='*'):
        for key in list(self.data):
            if fnmatch.fnmatchcase(key, match):
                yield key.encode()

    def pipeline(self, transaction=True):
        return FakePipeline(self)


class FakePipeline:
    """
    Queue calls and run them in order on execute, as a Redis pipeline does
    """

    def __init__(self, client):
        self.client = client
        self.calls = []

    def __getattr__(self, name):
        def queue(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            return self
        return queue

    def execute(self):
        results = [
            getattr(self.client, name)(*args, **kwargs)
            for name, args, kwargs in self.calls
        ]
        self.calls = []
        return results


redis = FakeRedis()


class Category:
    def __init__(self, slug, meta=None, name='Category'):
        self.slug = slug
        self.meta = meta
        self.name = name


class Subscriptions:
    """
    The UserSubscription rows, kept as a list of (person id, category, action)
    """

    rows = []

    def filter(self, person_id, action):
        return QuerySet(
            types.SimpleNamespace(person_id=row_person, category=category)
            for row_person, category, row_action in self.rows
            if row_person == person_id and row_action == action
        )


class QuerySet(list):
    def select_related(self, *fields):
        return self


class Roots:
    """
    The root Category rows, which are the apps and services
    """

    rows = []

    def root_nodes(self):
        return RootQuerySet(self.rows)


class RootQuerySet(list):
    def filter(self, slug):
        return RootQuerySet(root for root in self if root.slug == slug)


class SubscriptionTreeSerializer:
    """
    Record what the view asks the categories service to serialize
    """

    def __init__(self, instance, many=False, context=None):
        self.data = [
            {'slug': root.slug, 'context': context} for root in instance
        ]


class Notifications:
    """
    The Notification rows by id
    """

    rows = {}

    class DoesNotExist(Exception):
        pass

    def get(self, id):
        try:
            return self.rows[id]
        except KeyError:
            raise self.DoesNotExist


def _module(name, path=None, **attributes):
    module = types.ModuleType(name)
    if path is not None:
        module.__path__ = [str(path)]
    module.__dict__.update(attributes)
    sys.modules[name] = module
    return module


def _task(*args, **kwargs):
    def decorate(function):
        function.delay = function
        return function
    return decorate


_module('django_redis', get_redis_connection=lambda name: redis)
_module('swapper', load_model=lambda app, model: type(model, (), {}))
_module('omniport')
_module('omniport.celery', celery_app=types.SimpleNamespace(
    task=_task,
    control=types.SimpleNamespace(add_consumer=lambda *args, **kwargs: None),
))
_module('categories')
_module(
    'categories.models',
    UserSubscription=types.SimpleNamespace(objects=Subscriptions()),
    Category=types.SimpleNamespace(objects=Roots()),
)
_module('categories.utils')
_module('categories.utils.get_subscription', GetSubscription=None)
_module('rest_framework')
_module(
    'rest_framework.status',
    HTTP_201_CREATED=201,
    HTTP_400_BAD_REQUEST=400,
    HTTP_500_INTERNAL_SERVER_ERROR=500,
)
_module('rest_framework.permissions', IsAuthenticated=object)
_module('rest_framework.response', Response=lambda data=None, status=200: (
    types.SimpleNamespace(data=data, status_code=status)
))
_module('rest_framework.views', APIView=object)
_module('categories.redisdb', Subscription=types.SimpleNamespace(
    fetch_people=lambda category_slug, action: [],
))


class ModelSerializer:
    """
    Serialize the fields that the notification serializer reads back, the way
    the real nested category serializer would
    """

    def __init__(self, instance=None, context=None, **kwargs):
        self.instance = instance
        self.context = context or {}

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'template': instance.template,
            'category': {
                'name': instance.category.name,
                'slug': instance.category.slug,
            },
            'data': instance.data,
        }


_module('formula_one')
_module('formula_one.serializers')
_module('formula_one.serializers.base', ModelSerializer=ModelSerializer)
_module(
    'categories.serializers',
    CategorySerializer=ModelSerializer,
    SubscriptionTreeSerializer=SubscriptionTreeSerializer,
)

# The package itself is the repository, loaded under the name it has in
# omniport. The FCM package is replaced because its __init__ reads the
# service account certificate, and the views package because its __init__
# loads every view.
_module('notifications', path=ROOT)
_module('notifications.models', Notification=type('Notification', (), {
    'objects': Notifications(),
    'DoesNotExist': Notifications.DoesNotExist,
}))
fcm_package = _module('notifications.utils.fcm', path=ROOT / 'utils' / 'fcm')
_module('notifications.views', path=ROOT / 'views')

fcm = importlib.import_module('notifications.utils.fcm.fcm')
for name in (
        'DEAD_TOKEN_ERRORS', 'fcm_push', 'fcm_push_multicast',
        'fcm_subscribe', 'fcm_unsubscribe', 'fcm_validate',
):
    setattr(fcm_package, name, getattr(fcm, name))

push_endpoint = importlib.import_module('notifications.redisdb.push_endpoint')
push_endpoints = importlib.import_module('notifications.utils.push_endpoints')
tasks = importlib.import_module('notifications.tasks.fcm')
actions = importlib.import_module('notifications.actions')
prune = importlib.import_module(
    'notifications.management.commands.prunepushendpoints'
)
serializers = importlib.import_module('notifications.serializers.notification')
subscription_view = importlib.import_module('notifications.views.subscription')

PushEndpoint = push_endpoint.PushEndpoint


def notification(id, data=None, category=None):
    """
    Store and return a notification that fcm_push can load
    """

    row = types.SimpleNamespace(
        id=id,
        template='Body',
        data=data,
        category=category or Category('placement_and_internship__results__pla'),
        android_onclick_activity='',
        web_onclick_url='https://channeli.in/',
    )
    row.category.app_config = types.SimpleNamespace(
        assets=types.SimpleNamespace(logo='logo.svg'),
        base_urls=types.SimpleNamespace(static='placement/'),
    )
    Notifications.rows[id] = row
    return row


def reset():
    redis.flushall()
    Roots.rows = []
    Subscriptions.rows = []
    Notifications.rows = {}
