"""Make an existing account an admin: `manage.py grant_admin 0912...` (SPEC-0003).

The only way to an admin account outside staging. Run by an operator on the server.
"""

from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from core.crypto import blind_index, normalise_phone
from core.models import Account, Role


class Command(BaseCommand):
    help = "Grant the admin role to the account signed in with this phone number."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("phone")

    def handle(self, *args: Any, **options: Any) -> None:
        try:
            phone = normalise_phone(options["phone"])
        except ValueError:
            raise CommandError("not an Iranian mobile number") from None
        updated = Account.objects.filter(phone_index=blind_index(phone), is_active=True).update(
            role=Role.ADMIN
        )
        if not updated:
            raise CommandError("no account: sign in with this number first")
        self.stdout.write("granted")
