from django.db import models

from formula_one.models.base import Model


class Notification(Model):
    """
    This model stores information about a notification object
    """

    template = models.CharField(
        max_length=500,
        db_index=True,
    )
    category = models.ForeignKey(
        to='categories.Category',
        on_delete=models.CASCADE
    )
    web_onclick_url = models.URLField(
        max_length=200,
        blank=True,
        null=True,
    )
    android_onclick_activity = models.CharField(
        max_length=200,
        blank=True,
        null=True,
    )
    ios_onclick_action = models.CharField(
        max_length=200,
        blank=True,
        null=True,
    )
    emailed = models.BooleanField(
        default=False,
    )
    is_personalised = models.BooleanField(
        default=False,
    )
    has_custom_users_target = models.BooleanField(
        default=False,
    )
    data = models.JSONField(
        verbose_name='Data',
        help_text='Key value pairs sent to the client along with the push',
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ['-datetime_modified']

    def __str__(self):
        return f'{self.category.slug} : {self.template}'
