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
            'data',
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

        # The bell's header is the category name, which for a season row is
        # only the season, so the title sent with the push takes its place
        title = (instance.data or {}).get('title')
        if title and representation.get('category'):
            representation['category']['name'] = title

        unread = self.context.get('unread') or set()
        representation['unread'] = instance.id in unread
        return representation
