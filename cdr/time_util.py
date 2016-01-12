""" Module for date/time utility methods """

from dateutil.parser import parse as dateutilparse
import pytz
from tzlocal import get_localzone


def isoformat_w_tz(dt):
    """Mongo stores all datetime objects in UTC, add the TZ back on"""
    dt = datetime_w_tz(dt)
    return dt.isoformat()


def datetime_w_tz(dt):
    """Mongo stores all datetime objects in UTC, add the TZ back on"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.UTC)
    return dt


def parse_datetime(value):
    """We always want to store a timezone - add local if none provided"""
    # Confirm timezone gets parsed
    dt = dateutilparse(value)
    if not dt.tzinfo:
        tz = get_localzone()
        dt = tz.localize(dt, is_dst=None)
    return dt
