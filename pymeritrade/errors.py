
class TDAError(Exception):
   pass


class TDAPermissionsError(TDAError):
   pass


class TDUsageError(TDAError):
   pass


def check_assert(val, msg=''):
    if not val:
        raise TDUsageError(msg)