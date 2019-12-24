from formula_one.serializers.base import ModelSerializer

from notifications.models import Notification
from categories.serializers import CategorySerializer


class NotificationSerializer(ModelSerializer):
    """
    Serializer for notification object
    """
    category = CategorySerializer(
        many=False,
        read_only=True
    )

    class Meta:
        """
        Meta class for NotificationSerializer
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
        Extend to_representation of model serializer to include data
        from context
        :param instance:
        :return:
        """

        representation = super().to_representation(instance)

        unread = self.context.get('unread') or set()
        representation['unread'] = instance.id in unread
        return representation
