"""Invented data for a pre-launch deployment. Idempotent; does nothing unless PRELAUNCH.

The deploy runs it after every migration, so staging always has something to click through.
Every person here is invented, and the demo therapists have no phone, so nobody signs in as
them.
"""

from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand

from core import seed


class Command(BaseCommand):
    help = "Create invented demo data on a pre-launch deployment (no-op elsewhere)."

    def handle(self, *args: Any, **options: Any) -> None:
        if not settings.PRELAUNCH:
            self.stdout.write("not a pre-launch deployment: nothing seeded")
            return
        seed.run()
        self.stdout.write("seeded")
