from datetime import datetime, timedelta
from typing import List, Optional, Tuple

BUSINESS_START_HOUR = 7
BUSINESS_END_HOUR = 16
LUNCH_BREAK_START_HOUR = 12
LUNCH_BREAK_END_HOUR = 13
BUSINESS_WEEKDAYS = {0, 1, 2, 3, 4}


def _is_business_day(value):
    return value.weekday() in BUSINESS_WEEKDAYS


def _business_window_for_day(value):
    start = value.replace(hour=BUSINESS_START_HOUR, minute=0, second=0, microsecond=0)
    end = value.replace(hour=BUSINESS_END_HOUR, minute=0, second=0, microsecond=0)
    return start, end


def _lunch_window_for_day(value):
    lunch_start = value.replace(hour=LUNCH_BREAK_START_HOUR, minute=0, second=0, microsecond=0)
    lunch_end = value.replace(hour=LUNCH_BREAK_END_HOUR, minute=0, second=0, microsecond=0)
    return lunch_start, lunch_end


def _next_business_start(value):
    cursor = value.replace(second=0, microsecond=0)
    while not _is_business_day(cursor):
        cursor = (cursor + timedelta(days=1)).replace(second=0, microsecond=0)
    day_start, day_end = _business_window_for_day(cursor)
    if cursor < day_start:
        return day_start
    if cursor >= day_end:
        next_day = (cursor + timedelta(days=1)).replace(hour=BUSINESS_START_HOUR, minute=0, second=0, microsecond=0)
        return _next_business_start(next_day)
    lunch_start, lunch_end = _lunch_window_for_day(cursor)
    if lunch_start <= cursor < lunch_end:
        return lunch_end
    return cursor


def _is_valid_business_start(start):
    if not _is_business_day(start):
        return False
    day_start, day_end = _business_window_for_day(start)
    if not (day_start <= start < day_end):
        return False
    lunch_start, lunch_end = _lunch_window_for_day(start)
    return not (lunch_start <= start < lunch_end)


def _align_to_slot(value, slot_minutes):
    value = value.replace(second=0, microsecond=0)
    minutes = value.hour * 60 + value.minute
    remainder = minutes % slot_minutes
    if remainder:
        value += timedelta(minutes=(slot_minutes - remainder))
    return value


def _advance_after_invalid_interval(cursor, slot_minutes):
    lunch_start, lunch_end = _lunch_window_for_day(cursor)
    if lunch_start <= cursor < lunch_end:
        next_cursor = lunch_end
    else:
        next_cursor = cursor + timedelta(minutes=slot_minutes)
    next_cursor = _align_to_slot(next_cursor, slot_minutes)
    return _next_business_start(next_cursor)


def _compute_business_rollover_end(start, hours):
    remaining_seconds = float(hours) * 3600
    if remaining_seconds <= 0:
        return start
    cursor = _next_business_start(start)
    while True:
        day_start, day_end = _business_window_for_day(cursor)
        lunch_start, lunch_end = _lunch_window_for_day(cursor)
        if cursor < day_start:
            cursor = day_start
            continue
        if lunch_start <= cursor < lunch_end:
            cursor = lunch_end
            continue
        if cursor >= day_end:
            next_day = (cursor + timedelta(days=1)).replace(hour=BUSINESS_START_HOUR, minute=0, second=0, microsecond=0)
            cursor = _next_business_start(next_day)
            continue
        block_end = lunch_start if cursor < lunch_start else day_end
        available_seconds = (block_end - cursor).total_seconds()
        if remaining_seconds <= available_seconds:
            return cursor + timedelta(seconds=remaining_seconds)
        remaining_seconds -= available_seconds
        if block_end == lunch_start:
            cursor = lunch_end
        else:
            next_day = (cursor + timedelta(days=1)).replace(hour=BUSINESS_START_HOUR, minute=0, second=0, microsecond=0)
            cursor = next_day


def _intervals_overlap(a0, a1, b0, b1):
    return a0 < b1 and a1 > b0


def _first_overlap(start, end, intervals):
    for b_start, b_end in intervals:
        if _intervals_overlap(start, end, b_start, b_end):
            return (b_start, b_end)
    return None


start_from = datetime(2026, 8, 20, 18, 52, 36)
slot_minutes = 30
start_from = _align_to_slot(start_from, slot_minutes)
start_from = _next_business_start(start_from)
start_from = _align_to_slot(start_from, slot_minutes)
start_from = _next_business_start(start_from)
search_end = start_from + timedelta(days=30)
step = timedelta(minutes=slot_minutes)
print('start_from', start_from, 'search_end', search_end)

durations = [24, 24, 24, 27]
dependency_start = start_from
chain_blocked = False
combined_busy = []
max_proposals = 2

for i, duration_hours in enumerate(durations):
    proposals = []
    if not chain_blocked:
        cursor = _align_to_slot(max(start_from, dependency_start), slot_minutes)
        cursor = _next_business_start(cursor)
    else:
        cursor = search_end
    print('stage', i + 1, 'start cursor', cursor, 'chain_blocked', chain_blocked)
    iters = 0
    while cursor < search_end and len(proposals) < max_proposals:
        iters += 1
        if iters > 100000:
            print('TOO MANY ITERS')
            break
        candidate_end = _compute_business_rollover_end(cursor, duration_hours)
        if candidate_end > search_end:
            print('  break: candidate_end > search_end', candidate_end)
            break
        if not _is_valid_business_start(cursor):
            cursor = _advance_after_invalid_interval(cursor, slot_minutes)
            continue
        overlap = _first_overlap(cursor, candidate_end, combined_busy)
        if overlap is None:
            proposals.append((cursor, candidate_end))
            cursor = cursor + step
            cursor = _align_to_slot(cursor, slot_minutes)
            cursor = _next_business_start(cursor)
        else:
            cursor = _align_to_slot(max(cursor + step, overlap[1]), slot_minutes)
            cursor = _next_business_start(cursor)
    print('  proposals', proposals)
    if proposals:
        dependency_start = proposals[0][1]
    else:
        chain_blocked = True
