class FeishuError(Exception):
    pass


class AuthError(FeishuError):
    pass


class PermissionDeniedError(FeishuError):
    pass


class RateLimitError(FeishuError):
    pass


class ConflictError(FeishuError):
    pass


class NotFoundError(FeishuError):
    pass


class ValidationError(FeishuError):
    pass


class TransientApiError(FeishuError):
    pass
