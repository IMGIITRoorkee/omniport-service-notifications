from django.core.management.base import BaseCommand

from notifications.redisdb import PushEndpoint
from notifications.utils.fcm import (
    DEAD_TOKEN_ERRORS,
    fcm_validate,
)

# Most tokens that FCM accepts in one multicast message
VALIDATE_BATCH_SIZE = 500


class Command(BaseCommand):
    """
    This class describes the command to be executed
    """

    help = """Delete the push tokens that FCM reports will never receive a
    push again, found by sending every token a dry run message, which delivers
    nothing. Direct sends already delete the dead tokens they hit, so this
    catches the ones that only ever get topic pushes. Meant to be run weekly.
    Usage: django-admin prunepushendpoints [--dry-run]
    """

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verb = 'Would delete' if dry_run else 'Deleted'

        endpoints = [
            (person_id, field, token)
            for person_id in PushEndpoint.persons()
            for field, token in PushEndpoint.fetch_fields(person_id).items()
        ]

        dead = unchecked = 0
        for i in range(0, len(endpoints), VALIDATE_BATCH_SIZE):
            batch = endpoints[i:i + VALIDATE_BATCH_SIZE]
            response = fcm_validate([token for _, _, token in batch])
            if response is None:
                unchecked += len(batch)
                continue

            for (person_id, field, token), result in zip(
                    batch, response.responses
            ):
                if isinstance(result.exception, DEAD_TOKEN_ERRORS):
                    dead += 1
                    self.stdout.write(
                        f'{verb} the dead token of person {person_id} '
                        f'under {field}'
                    )
                    if not dry_run:
                        PushEndpoint.remove(person_id, field, token)

        self.stdout.write(
            f'{verb} {dead} dead tokens out of {len(endpoints)}'
        )
        if unchecked:
            self.stderr.write(
                f'{unchecked} tokens could not be checked with FCM'
            )
