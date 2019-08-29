""" Module for date/time utility methods """

from datetime import datetime
from dateutil.parser import parse as dateutilparse
import pytz
from tzlocal import get_localzone


def utc_now():
    """ datetime does have a utcnow method, but it doesn't contain tz """
    utc = pytz.timezone('UTC')
    n = datetime.now(utc)
    return n


def isoformat_w_tz(dt):
    """Mongo stores all datetime objects in UTC, add the TZ back on"""
    dt = datetime_w_tz(dt)
    return dt.isoformat()


def datetime_w_tz(dt):
    """All datetime objects stored in UTC, add the TZ back on if absent"""
    # Don't mess with uninitialized
    if not isinstance(dt, datetime):
        return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.UTC)
    return dt


def parse_datetime(value):
    """We always want to store as UTZ; assume local tz if none provided"""
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        dt = dateutilparse(value)
    if not dt.tzinfo:
        # If no tz info or offset was defined, assume local
        tz = get_localzone()
        dt = tz.localize(dt, is_dst=None)

    # Store everything in UTC - convert if necessary
    if dt.tzinfo != pytz.UTC:
        dt = dt.astimezone(pytz.UTC)
    return dt
