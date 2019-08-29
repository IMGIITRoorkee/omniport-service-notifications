from formula_one.serializers.base import ModelSerializer

from notifications.models import Notification
from categories.serializers import CategorySerializer


class NotificationSerializer(ModelSerializer):
    """
    TODO
    """
    category = CategorySerializer(
        many=False,
        read_only=True
    )

    class Meta:
        """
        TODO
        """
        model = Notification
        fields = (
            'id',
            'template',
            'category',
            'web_onclick_url',
            'datetime_modified',
        )

    def to_representation(self, instance):
        """
        TODO
        :param instance:
        :return:
        """

        representation = super().to_representation(instance)

        unread = self.context.get('unread') or set()
        representation['unread'] = instance.id in unread
        return representation
