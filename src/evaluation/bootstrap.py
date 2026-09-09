"""
src/evaluation/bootstrap.py
Bootstrap utility computing empirical 95% confidence intervals for evaluation metrics.
Uses deterministic random seed (seed=42) and B=1,000 resampling iterations.
"""

import numpy as np
from typing import List, Dict, Any, Callable, Optional

def bootstrap_ci(
    y_true: List[Any],
    y_pred: List[Any],
    metric_fn: Callable[[List[Any], List[Any]], float],
    n_resamples: int = 1000,
    confidence_level: float = 0.95,
    seed: int = 42
) -> Dict[str, float]:
    """
    Computes point estimate and empirical bootstrap confidence interval.
    """
    rng = np.random.RandomState(seed)
    n = len(y_true)
    if n == 0:
        return {"point_estimate": 0.0, "ci_lower": 0.0, "ci_upper": 0.0, "std_err": 0.0}

    point_estimate = float(metric_fn(y_true, y_pred))
    
    indices = np.arange(n)
    boot_stats = []
    
    for _ in range(n_resamples):
        sample_idx = rng.choice(indices, size=n, replace=True)
        sample_true = [y_true[i] for i in sample_idx]
        sample_pred = [y_pred[i] for i in sample_idx]
        try:
            val = float(metric_fn(sample_true, sample_pred))
            boot_stats.append(val)
        except Exception:
            continue

    if not boot_stats:
        return {"point_estimate": point_estimate, "ci_lower": point_estimate, "ci_upper": point_estimate, "std_err": 0.0}

    alpha = (1.0 - confidence_level) / 2.0
    lower = float(np.percentile(boot_stats, alpha * 100))
    upper = float(np.percentile(boot_stats, (1.0 - alpha) * 100))
    std_err = float(np.std(boot_stats))

    return {
        "point_estimate": round(point_estimate, 4),
        "ci_lower": round(lower, 4),
        "ci_upper": round(upper, 4),
        "std_err": round(std_err, 4),
        "n": n
    }

def bootstrap_scalar_ci(
    values: List[float],
    n_resamples: int = 1000,
    confidence_level: float = 0.95,
    seed: int = 42
) -> Dict[str, float]:
    """
    Computes point estimate and empirical bootstrap CI for a list of scalar scores (e.g. 1-5 ratings).
    """
    rng = np.random.RandomState(seed)
    arr = np.array(values, dtype=float)
    n = len(arr)
    if n == 0:
        return {"point_estimate": 0.0, "ci_lower": 0.0, "ci_upper": 0.0, "std_err": 0.0}

    point_estimate = float(np.mean(arr))
    boot_means = []
    
    for _ in range(n_resamples):
        sample = rng.choice(arr, size=n, replace=True)
        boot_means.append(float(np.mean(sample)))

    alpha = (1.0 - confidence_level) / 2.0
    lower = float(np.percentile(boot_means, alpha * 100))
    upper = float(np.percentile(boot_means, (1.0 - alpha) * 100))
    std_err = float(np.std(boot_means))

    return {
        "point_estimate": round(point_estimate, 4),
        "ci_lower": round(lower, 4),
        "ci_upper": round(upper, 4),
        "std_err": round(std_err, 4),
        "n": n
    }
