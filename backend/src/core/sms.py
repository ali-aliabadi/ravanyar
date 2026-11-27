"""Kavenegar Verify Lookup: the only place a phone number leaves the app (SPEC-0001).

The API key sits in Kavenegar's URL path, so nothing here logs a URL, a phone, or a code.
"""

import logging
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings

from core.errors import SmsUnavailableError

log = logging.getLogger(__name__)
URL = "https://api.kavenegar.com/v1/{key}/verify/lookup.json"


def send_code(phone: str, code: str) -> None:
    """Send `code` to `phone` (+989XXXXXXXXX)."""
    _lookup(phone, settings.KAVENEGAR_TEMPLATE, token=code)


def send_reminder(phone: str, weekday: str, time: str) -> None:
    """SPEC-0004: a session reminder. Only a weekday and a time: the template says nothing
    about therapy, so nothing sensitive shows on a lock screen."""
    _lookup(phone, settings.KAVENEGAR_REMINDER_TEMPLATE, token=weekday, token2=time)


def _lookup(phone: str, template: str, **tokens: str) -> None:
    """POST, so neither the phone nor the tokens are in a URL."""
    body = urllib.parse.urlencode(
        {"receptor": "0" + phone[3:], **tokens, "template": template}
    ).encode()
    # S310: the scheme is fixed to https by URL above.
    request = urllib.request.Request(  # noqa: S310
        URL.format(key=settings.KAVENEGAR_API_KEY), data=body
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:  # noqa: S310
            status = response.status
    except urllib.error.HTTPError as error:
        status = error.code
    except OSError:
        log.warning("kavenegar unreachable")
        raise SmsUnavailableError from None
    log.info("kavenegar status %s", status)
    if status != 200:
        raise SmsUnavailableError
