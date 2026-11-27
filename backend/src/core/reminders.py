"""Session reminders (SPEC-0004), sent by `manage.py send_reminders` on a loop.

Same path as the sign-in code: Kavenegar for real numbers; a staging test number gets no SMS
and a log line instead (SPEC-0002). The SMS carries a weekday and a time, nothing else.
"""

import logging
from datetime import timedelta
from datetime import timezone as tz

from django.conf import settings
from django.utils import timezone

from core import sms
from core.access import authorize, read_phone
from core.errors import SmsUnavailableError
from core.models import Booking, BookingStatus, Purpose

AHEAD = timedelta(hours=24)
# shortcut: fixed offset, the slim image has no tz database; Iran has no DST since 2022.
TEHRAN = tz(timedelta(hours=3, minutes=30))
WEEKDAYS = ("دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه", "شنبه", "یکشنبه")  # Monday first
log = logging.getLogger(__name__)


def send_due() -> int:
    """Remind every client whose session starts within a day and who was not reminded yet.
    A failed SMS is left for the next run, which stops once the session starts."""
    now = timezone.now()
    due = Booking.objects.filter(
        status=BookingStatus.BOOKED,
        reminded_at=None,
        slot__start_at__gt=now,
        slot__start_at__lte=now + AHEAD,
        client__phone_ct__isnull=False,
    ).select_related("slot", "client")
    sent = 0
    for booking in due:
        client = booking.client
        # The system acts for the client on their own number: logged as their own read.
        phone = read_phone(authorize(client, client, Purpose.REMINDER), client)
        start = booking.slot.start_at.astimezone(TEHRAN)
        if phone in settings.TEST_PHONES:
            log.warning("staging test reminder, no SMS booking=%s", booking.pk)
        else:
            try:
                sms.send_reminder(phone, WEEKDAYS[start.weekday()], start.strftime("%H:%M"))
            except SmsUnavailableError:
                continue
        booking.reminded_at = now
        booking.save(update_fields=["reminded_at"])
        sent += 1
    return sent
