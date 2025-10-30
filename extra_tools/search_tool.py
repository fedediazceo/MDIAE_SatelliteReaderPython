""" 
Tool to search for candidate OBT fields in binary frame data.

IT's a bit hardcoded, so don't pay too much attention to it. 
"""

import datetime as DT


def obt_to_datetime(obt_seconds: int) -> DT.datetime:
    OBT_EPOCH = DT.datetime(1980, 1, 6, tzinfo=DT.timezone.utc)
    return OBT_EPOCH + DT.timedelta(seconds=obt_seconds)

def find_obt_candidates(input_path: str):
    """
    frames: each one of 4000 bytes
    returns: offset of values that might be OBT
    """

    with open(input_path, "rb") as in_file:
        data = in_file.read()

    frames = [data[i:i+4000] for i in range(0, len(data), 4000)]

    if not frames:
        return []

    frame = frames[0]
    frame_len = len(frames[0])
    candidates = []

    # knowing an approximate epoch is kinda necessary for this to work
    MIN_OBT = 1_116_547_200   # 2015-05-25 
    MAX_OBT = 1_117_843_200   # 2015-06-09

    for offset in range(0, frame_len - 4):
        be = int.from_bytes(frame[offset:offset+4], "big")
        if MIN_OBT <= be <= MAX_OBT:
            print(offset, "is a candidate:", be)
            candidates.append(offset)
    # it is nice to know the approximate time difference between values, that might work
    # search for values that increase roughly by 8 seconds per frame
    candidates = refine(frames, candidates, time_difference_between_values=8) 
    print(candidates)
    return candidates


def refine(frames, offsets, time_difference_between_values=2):
    good = []

    for off in offsets:
        count = 0
        prev_v = int.from_bytes(frames[0][off:off+4], "big")
        ok = True
        for i, fr in enumerate(frames[1:], 1):
            v = int.from_bytes(fr[off:off+4], "big")
            if v - (prev_v + i) > time_difference_between_values:
                ok = False
                print(off, "fails at frame", i, "value", v, "previous", obt_to_datetime(prev_v), "current", obt_to_datetime(v))
                break
            prev_v = v
            count += 1
        if ok:
            good.append(off)
    return good