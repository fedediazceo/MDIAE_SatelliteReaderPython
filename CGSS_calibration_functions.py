# Author: Federico Jose Diaz
# CGSS_calibration_functions.py
# Each function receives the raw value and returns a calibrated value.

import datetime as DT

def obt_seconds_to_datetime(raw: int) -> DT.datetime:
    """
    Convert OBT (seconds since 1980-01-06 00:00:00) to a UTC datetime.
    """
    OBT_EPOCH = DT.datetime(1980, 1, 6, tzinfo=DT.timezone.utc)
    return OBT_EPOCH + DT.timedelta(seconds=float(raw))