"""Send due session reminders: `manage.py send_reminders` (SPEC-0004).

The deploy runs it every 10 minutes. Safe to run again: a reminded booking is skipped.
"""

from typing import Any

from django.core.management.base import BaseCommand

from core import reminders


class Command(BaseCommand):
    help = "Send SMS reminders for sessions starting within 24 hours."

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write(f"reminders sent: {reminders.send_due()}")
