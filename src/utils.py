import datetime as dt
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

def month_bounds(date: dt.date):
    first = date.replace(day=1)
    if first.month == 12:
        next_m = first.replace(year=first.year+1, month=1, day=1)
    else:
        next_m = first.replace(month=first.month+1, day=1)
    return first, next_m
