"""Service failures the API turns into a status and a fixed code. Never carries input."""


class ServiceError(Exception):
    status = 400
    code = "bad_request"


class AccessDeniedError(ServiceError):
    status = 403
    code = "forbidden"


class ConsentRequiredError(ServiceError):
    status = 403
    code = "consent_required"


class OutdatedVersionError(ServiceError):
    status = 422
    code = "outdated_version"


class CodeRejectedError(ServiceError):
    status = 400
    code = "code_rejected"


class RateLimitedError(ServiceError):
    status = 429
    code = "rate_limited"


class SmsUnavailableError(ServiceError):
    status = 503
    code = "sms_unavailable"


class NotFoundError(ServiceError):
    status = 404
    code = "not_found"


class WrongStateError(ServiceError):
    """The object is not in a state that allows this, e.g. editing a profile under review."""

    status = 409
    code = "wrong_state"


class IncompleteError(ServiceError):
    status = 422
    code = "incomplete"


class BadFileError(ServiceError):
    status = 422
    code = "bad_file"
