"""
event_grouping.py
-----------------
Groups individual raise events into logical "capital raise programs" for an
issuer, collapsing related tranches (e.g., a base offering + over-allotment
option) into a single grouped record.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional


@dataclass
class RaiseEventRow:
    """Lightweight projection of a raise event row used for grouping."""
    raise_event_id: int
    issuer_id: int
    raise_type: str
    announced_date: Optional[date]
    gross_proceeds: Optional[float]
    structure_class: Optional[str]
    has_warrants: bool = False


@dataclass
class GroupedRaiseProgram:
    """Aggregated view of a set of related raise events."""
    issuer_id: int
    raise_type: str
    event_ids: List[int] = field(default_factory=list)
    first_announced: Optional[date] = None
    last_announced: Optional[date] = None
    total_gross_proceeds: float = 0.0
    tranche_count: int = 0
    has_warrants: bool = False
    structure_classes: List[str] = field(default_factory=list)


def group_raise_events(
    events: List[RaiseEventRow],
    window_days: int = 14,
) -> List[GroupedRaiseProgram]:
    """
    Groups raise events for a single issuer into programs.

    Two events are merged into the same program if:
    - They share the same raise_type
    - Their announced_dates are within `window_days` of each other

    Parameters
    ----------
    events : List[RaiseEventRow]
        Events for a *single* issuer, sorted by announced_date ascending.
    window_days : int
        Maximum calendar-day gap between events to be grouped together.

    Returns
    -------
    List[GroupedRaiseProgram]
    """
    if not events:
        return []

    # Sort by raise_type then announced_date
    sorted_events = sorted(
        events,
        key=lambda e: (e.raise_type, e.announced_date or date.min),
    )

    programs: List[GroupedRaiseProgram] = []
    current: Optional[GroupedRaiseProgram] = None

    for evt in sorted_events:
        if current is None:
            current = _start_program(evt)
            continue

        same_type = evt.raise_type == current.raise_type
        within_window = (
            evt.announced_date is not None
            and current.last_announced is not None
            and (evt.announced_date - current.last_announced) <= timedelta(days=window_days)
        )

        if same_type and within_window:
            _merge_event(current, evt)
        else:
            programs.append(current)
            current = _start_program(evt)

    if current is not None:
        programs.append(current)

    return programs


def _start_program(evt: RaiseEventRow) -> GroupedRaiseProgram:
    prog = GroupedRaiseProgram(
        issuer_id=evt.issuer_id,
        raise_type=evt.raise_type,
        event_ids=[evt.raise_event_id],
        first_announced=evt.announced_date,
        last_announced=evt.announced_date,
        total_gross_proceeds=evt.gross_proceeds or 0.0,
        tranche_count=1,
        has_warrants=evt.has_warrants,
    )
    if evt.structure_class:
        prog.structure_classes.append(evt.structure_class)
    return prog


def _merge_event(prog: GroupedRaiseProgram, evt: RaiseEventRow) -> None:
    prog.event_ids.append(evt.raise_event_id)
    prog.total_gross_proceeds += evt.gross_proceeds or 0.0
    prog.tranche_count += 1
    prog.has_warrants = prog.has_warrants or evt.has_warrants
    if evt.structure_class and evt.structure_class not in prog.structure_classes:
        prog.structure_classes.append(evt.structure_class)
    if evt.announced_date:
        if prog.first_announced is None or evt.announced_date < prog.first_announced:
            prog.first_announced = evt.announced_date
        if prog.last_announced is None or evt.announced_date > prog.last_announced:
            prog.last_announced = evt.announced_date
