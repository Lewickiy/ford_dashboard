"""Compatibility facade for vehicle processing helpers."""

from vehicle_processors.clutch import is_clutch
from vehicle_processors.gear import estimate_gear

__all__ = ["is_clutch", "estimate_gear"]
