class TDAError(Exception):
    pass


class TDAPermissionsError(TDAError):
    pass


class TDAAPIError(TDAError):
    pass


class TDAUsageError(TDAError):
    pass


def check_assert(val, msg=""):
    if not val:
        raise TDAUsageError(msg)
