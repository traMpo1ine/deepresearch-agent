from __future__ import annotations

import math
import random
from statistics import mean, pstdev


def bootstrap_ci(values: list[float], samples: int = 1000, confidence: float = 0.95) -> tuple[float, float]:
    if not values:
        raise ValueError("values must not be empty")
    estimates = []
    for _ in range(samples):
        draw = [random.choice(values) for _ in values]
        estimates.append(mean(draw))
    estimates.sort()
    alpha = 1.0 - confidence
    lower = estimates[int((alpha / 2) * samples)]
    upper = estimates[min(int((1 - alpha / 2) * samples), samples - 1)]
    return lower, upper


def cohens_d(before: list[float], after: list[float]) -> float:
    if not before or not after:
        raise ValueError("before and after must not be empty")
    pooled = math.sqrt((pstdev(before) ** 2 + pstdev(after) ** 2) / 2)
    if pooled == 0:
        return 0.0
    return (mean(after) - mean(before)) / pooled
