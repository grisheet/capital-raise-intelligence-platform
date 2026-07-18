"""event_study.py – Event-study analytics for capital raise events.

For each raise event, computes abnormal returns using a market-model
approach over a configurable estimation window and event window.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ESTIMATION_DAYS: int = 120   # trading days before event window
_PRE_EVENT_DAYS: int = 5      # days before announcement
_POST_EVENT_DAYS: int = 20    # days after announcement


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class PriceObservation:
    """Single daily price/return observation for a security."""
    trade_date: date
    close_price: float
    market_return: float        # benchmark (e.g. SPY) daily return
    stock_return: float         # security daily return


@dataclass
class EventStudyResult:
    """Output of run_event_study() for a single raise event."""
    event_id: str
    ticker: str
    announce_date: date
    # Abnormal returns keyed by day-relative-to-event (e.g. -5 … +20)
    abnormal_returns: Dict[int, float] = field(default_factory=dict)
    cumulative_ar: Dict[int, float] = field(default_factory=dict)
    # OLS coefficients from estimation window
    alpha: float = 0.0
    beta: float = 1.0
    # Summary stats
    car_minus5_plus1: Optional[float] = None    # pre-announcement window
    car_0_plus5: Optional[float] = None         # immediate post window
    car_0_plus20: Optional[float] = None        # full post window
    mean_car: Optional[float] = None


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------

def run_event_study(
    event_id: str,
    ticker: str,
    announce_date: date,
    price_series: List[PriceObservation],
    estimation_days: int = _ESTIMATION_DAYS,
    pre_event_days: int = _PRE_EVENT_DAYS,
    post_event_days: int = _POST_EVENT_DAYS,
) -> EventStudyResult:
    """Run a market-model event study for a single raise event.

    Parameters
    ----------
    event_id:        Unique identifier for the raise event.
    ticker:          Equity ticker symbol.
    announce_date:   Announcement / pricing date of the raise.
    price_series:    Chronologically sorted daily observations.
    estimation_days: Length of OLS estimation window (before event window).
    pre_event_days:  Days before announce_date included in event window.
    post_event_days: Days after announce_date included in event window.

    Returns
    -------
    EventStudyResult with abnormal returns, CARs, and model coefficients.
    """
    result = EventStudyResult(
        event_id=event_id,
        ticker=ticker,
        announce_date=announce_date,
    )

    if not price_series:
        return result

    # Locate announcement date index
    date_index = {obs.trade_date: i for i, obs in enumerate(price_series)}
    if announce_date not in date_index:
        return result

    event_idx = date_index[announce_date]

    # ---- Estimation window ------------------------------------------------
    est_end = event_idx - pre_event_days - 1
    est_start = est_end - estimation_days
    est_start = max(est_start, 0)

    estimation_obs = price_series[est_start:est_end + 1]
    alpha, beta = _ols(estimation_obs)
    result.alpha = alpha
    result.beta = beta

    # ---- Event window abnormal returns ------------------------------------
    ew_start = max(event_idx - pre_event_days, 0)
    ew_end = min(event_idx + post_event_days, len(price_series) - 1)

    cumulative = 0.0
    for i in range(ew_start, ew_end + 1):
        obs = price_series[i]
        relative_day = i - event_idx
        expected_return = alpha + beta * obs.market_return
        ar = obs.stock_return - expected_return
        cumulative += ar
        result.abnormal_returns[relative_day] = round(ar, 6)
        result.cumulative_ar[relative_day] = round(cumulative, 6)

    # ---- Summary CARs -----------------------------------------------------
    result.car_minus5_plus1 = _sum_ar(result.abnormal_returns, -pre_event_days, 1)
    result.car_0_plus5 = _sum_ar(result.abnormal_returns, 0, 5)
    result.car_0_plus20 = _sum_ar(result.abnormal_returns, 0, post_event_days)
    if result.abnormal_returns:
        result.mean_car = round(
            sum(result.abnormal_returns.values()) / len(result.abnormal_returns), 6
        )

    return result


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _ols(observations: List[PriceObservation]):
    """Ordinary least squares: stock_return ~ alpha + beta * market_return."""
    n = len(observations)
    if n < 2:
        return 0.0, 1.0

    sum_x = sum(o.market_return for o in observations)
    sum_y = sum(o.stock_return for o in observations)
    sum_xx = sum(o.market_return ** 2 for o in observations)
    sum_xy = sum(o.market_return * o.stock_return for o in observations)

    denom = n * sum_xx - sum_x ** 2
    if denom == 0:
        return 0.0, 1.0

    beta = (n * sum_xy - sum_x * sum_y) / denom
    alpha = (sum_y - beta * sum_x) / n
    return round(alpha, 8), round(beta, 6)


def _sum_ar(
    abnormal_returns: Dict[int, float],
    from_day: int,
    to_day: int,
) -> Optional[float]:
    """Sum abnormal returns over [from_day, to_day] inclusive."""
    total = sum(
        v for k, v in abnormal_returns.items() if from_day <= k <= to_day
    )
    days_present = sum(1 for k in abnormal_returns if from_day <= k <= to_day)
    return round(total, 6) if days_present > 0 else None


# ---------------------------------------------------------------------------
# Batch helper
# ---------------------------------------------------------------------------

def run_batch_event_study(
    events: List[Dict],
    price_map: Dict[str, List[PriceObservation]],
) -> List[EventStudyResult]:
    """Run event studies for a list of events.

    Parameters
    ----------
    events:    List of dicts with keys: event_id, ticker, announce_date.
    price_map: Dict mapping ticker -> sorted list of PriceObservation.

    Returns
    -------
    List of EventStudyResult, one per event.
    """
    results = []
    for ev in events:
        ticker = ev.get("ticker", "")
        series = price_map.get(ticker, [])
        res = run_event_study(
            event_id=ev["event_id"],
            ticker=ticker,
            announce_date=ev["announce_date"],
            price_series=series,
        )
        results.append(res)
    return results
