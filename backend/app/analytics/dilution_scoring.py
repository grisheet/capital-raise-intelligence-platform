"""
dilution_scoring.py
--------------------
Computes per-issuer dilution metrics and composite risk scores.
All scores are normalized to [0, 10] where 10 = highest risk.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class DilutionInputs:
    """Raw inputs needed to compute dilution and risk scores."""
    shares_outstanding: Optional[int] = None
    shares_float: Optional[int] = None
    # ATM program overhang (shares not yet sold)
    atm_shares_remaining: Optional[int] = None
    # Warrant shares outstanding
    warrant_shares: Optional[int] = None
    # Convertible principal outstanding
    convertible_principal: Optional[float] = None
    # Average conversion price of convertibles
    avg_conversion_price: Optional[float] = None
    # Total shares issued via dilutive raises in trailing 12 months
    shares_issued_12m: Optional[int] = None
    # Number of dilutive raise events in trailing 12 months
    raise_count_12m: int = 0
    # Average discount to market across all raises in trailing 12 months
    avg_discount_12m: Optional[float] = None
    # ATM utilization rate (amount_sold / program_size)
    atm_utilization_rate: Optional[float] = None
    # Proportion of raises in trailing 12m that included warrants
    warrant_usage_rate: Optional[float] = None


@dataclass
class DilutionScores:
    """Output of the dilution scoring engine."""
    dilution_pct_12m: Optional[float] = None
    atm_overhang_pct: Optional[float] = None
    warrant_overhang_pct: Optional[float] = None
    convertible_overhang_pct: Optional[float] = None
    total_overhang_pct: Optional[float] = None
    # Component risk scores [0-10]
    dilution_risk_score: float = 0.0
    deal_frequency_score: float = 0.0
    discount_aggressiveness_score: float = 0.0
    warrant_usage_score: float = 0.0
    atm_utilization_score: float = 0.0
    # Composite score [0-10]
    composite_risk_score: float = 0.0
    risk_tier: str = "low"  # low | medium | high | critical


# Scoring weights (must sum to 1.0)
_WEIGHTS = {
    "dilution_risk": 0.30,
    "deal_frequency": 0.20,
    "discount_aggressiveness": 0.20,
    "warrant_usage": 0.15,
    "atm_utilization": 0.15,
}

# Thresholds for normalization
_DILUTION_CAP = 0.50        # 50% dilution in 12m -> score 10
_DEAL_FREQ_CAP = 12         # 12 deals in 12m -> score 10
_DISCOUNT_CAP = 0.40        # 40% discount -> score 10
_WARRANT_RATE_CAP = 1.0     # 100% warrant usage -> score 10
_ATM_UTIL_CAP = 1.0         # 100% utilization -> score 10


def compute_dilution_scores(inputs: DilutionInputs) -> DilutionScores:
    """Compute dilution metrics and risk scores from raw inputs."""
    scores = DilutionScores()
    so = inputs.shares_outstanding

    # ── Dilution percentages ──
    if so and so > 0:
        if inputs.shares_issued_12m is not None:
            scores.dilution_pct_12m = inputs.shares_issued_12m / so

        if inputs.atm_shares_remaining is not None:
            scores.atm_overhang_pct = inputs.atm_shares_remaining / so

        if inputs.warrant_shares is not None:
            scores.warrant_overhang_pct = inputs.warrant_shares / so

        if (
            inputs.convertible_principal is not None
            and inputs.avg_conversion_price is not None
            and inputs.avg_conversion_price > 0
        ):
            conv_shares = inputs.convertible_principal / inputs.avg_conversion_price
            scores.convertible_overhang_pct = conv_shares / so

        components = [
            scores.atm_overhang_pct or 0.0,
            scores.warrant_overhang_pct or 0.0,
            scores.convertible_overhang_pct or 0.0,
        ]
        scores.total_overhang_pct = sum(components)

    # ── Component risk scores ──
    scores.dilution_risk_score = _normalize(
        scores.dilution_pct_12m or 0.0, _DILUTION_CAP
    )
    scores.deal_frequency_score = _normalize(
        inputs.raise_count_12m, _DEAL_FREQ_CAP
    )
    scores.discount_aggressiveness_score = _normalize(
        abs(inputs.avg_discount_12m or 0.0), _DISCOUNT_CAP
    )
    scores.warrant_usage_score = _normalize(
        inputs.warrant_usage_rate or 0.0, _WARRANT_RATE_CAP
    )
    scores.atm_utilization_score = _normalize(
        inputs.atm_utilization_rate or 0.0, _ATM_UTIL_CAP
    )

    # ── Composite score ──
    scores.composite_risk_score = (
        scores.dilution_risk_score * _WEIGHTS["dilution_risk"]
        + scores.deal_frequency_score * _WEIGHTS["deal_frequency"]
        + scores.discount_aggressiveness_score * _WEIGHTS["discount_aggressiveness"]
        + scores.warrant_usage_score * _WEIGHTS["warrant_usage"]
        + scores.atm_utilization_score * _WEIGHTS["atm_utilization"]
    )

    scores.risk_tier = _risk_tier(scores.composite_risk_score)
    return scores


def _normalize(value: float, cap: float) -> float:
    """Linearly normalize value to [0, 10] capped at `cap`."""
    if cap <= 0:
        return 0.0
    return min(10.0, (value / cap) * 10.0)


def _risk_tier(score: float) -> str:
    if score < 3.0:
        return "low"
    elif score < 5.5:
        return "medium"
    elif score < 7.5:
        return "high"
    return "critical"
