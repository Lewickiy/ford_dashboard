"""Composable processors for raw OBD-II telemetry."""

from .alerts import build_alerts
from .clutch import is_clutch
from .driving_style import assess_driving_style
from .gear import estimate_gear
from .misfire import detect_misfires
from .shift import shift_advice
from .snapshot import enrich_state

__all__ = [
    "assess_driving_style",
    "build_alerts",
    "detect_misfires",
    "enrich_state",
    "estimate_gear",
    "is_clutch",
    "shift_advice",
]
