def real():
    from categories.models import Category
    from notifications.actions import push_notification
    import datetime

    c = Category.objects.get(slug='noticeboard')
    return push_notification(
            template=f'Test notification @ {str(datetime.datetime.now())}',
            category=c,
            has_custom_users_target=True,
            persons=[1,2,3],
            web_onclick_url='https://fb.com/'
    )

