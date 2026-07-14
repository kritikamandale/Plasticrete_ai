"""
Partial Dependence Plot + ICE curves and 2D PDP heatmaps.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
from loguru import logger

from modules.m1_prediction.utils.schema import (
    COMPRESSIVE_STRENGTH, FLEXURAL_STRENGTH, REPLACEMENT_PCT, WC_RATIO,
    CURING_DAYS, PARTICLE_SIZE_MM, ADDITIVE_TYPE, TARGET_COLUMNS, INPUT_FEATURES,
)

try:
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm
    _MPL_AVAILABLE = True
except ImportError:
    _MPL_AVAILABLE = False


def _feature_idx(preprocessor, feature: str) -> int:
    feat_names = preprocessor.feature_names
    if feature in feat_names:
        return feat_names.index(feature)
    raise ValueError(f"Feature '{feature}' not in preprocessor.feature_names: {feat_names}")


def _grid_for_feature(X_train: np.ndarray, feat_idx: int, grid_resolution: int = 50) -> np.ndarray:
    col = X_train[:, feat_idx]
    return np.linspace(col.min(), col.max(), grid_resolution)


def plot_pdp(
    ensemble,
    preprocessor,
    X_train: np.ndarray,
    feature: str,
    target: str,
    grid_resolution: int = 50,
    save_path: Optional[str] = None,
) -> None:
    if not _MPL_AVAILABLE:
        logger.warning("matplotlib not available — skipping PDP")
        return
    try:
        fidx    = _feature_idx(preprocessor, feature)
        tidx    = TARGET_COLUMNS.index(target)
        grid    = _grid_for_feature(X_train, fidx, grid_resolution)
        X_med   = np.median(X_train, axis=0, keepdims=True)

        pdp_vals = []
        for v in grid:
            X_row = X_med.copy()
            X_row[0, fidx] = v
            means, _, _ = ensemble.predict_batch(X_row)
            pdp_vals.append(means[0, tidx])

        fig, ax = plt.subplots(figsize=(7, 4))
        ax.plot(grid, pdp_vals, lw=2, color="steelblue")
        ax.set_xlabel(feature)
        ax.set_ylabel(target)
        ax.set_title(f"PDP: {feature} → {target}")
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=120)
        plt.close(fig)
    except Exception as exc:
        logger.warning(f"plot_pdp [{feature}→{target}]: {exc}")


def plot_ice(
    ensemble,
    preprocessor,
    X_train: np.ndarray,
    feature: str,
    target: str,
    n_ice_lines: int = 50,
    grid_resolution: int = 50,
    save_path: Optional[str] = None,
) -> None:
    if not _MPL_AVAILABLE:
        logger.warning("matplotlib not available — skipping ICE")
        return
    try:
        fidx = _feature_idx(preprocessor, feature)
        tidx = TARGET_COLUMNS.index(target)
        grid = _grid_for_feature(X_train, fidx, grid_resolution)

        n   = min(n_ice_lines, len(X_train))
        idx = np.random.choice(len(X_train), n, replace=False)
        ice_matrix = np.zeros((n, grid_resolution))

        for j, v in enumerate(grid):
            X_batch = X_train[idx].copy()
            X_batch[:, fidx] = v
            means, _, _ = ensemble.predict_batch(X_batch)
            ice_matrix[:, j] = means[:, tidx]

        pdp = ice_matrix.mean(axis=0)

        fig, ax = plt.subplots(figsize=(7, 4))
        for row in ice_matrix:
            ax.plot(grid, row, color="steelblue", alpha=0.15, lw=0.8)
        ax.plot(grid, pdp, color="red", lw=2, label="PDP mean")
        ax.set_xlabel(feature)
        ax.set_ylabel(target)
        ax.set_title(f"PDP + ICE: {feature} → {target}")
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=120)
        plt.close(fig)
    except Exception as exc:
        logger.warning(f"plot_ice [{feature}→{target}]: {exc}")


def plot_2d_pdp(
    ensemble,
    preprocessor,
    X_train: np.ndarray,
    feat1: str,
    feat2: str,
    target: str,
    grid_resolution: int = 20,
    save_path: Optional[str] = None,
) -> None:
    if not _MPL_AVAILABLE:
        logger.warning("matplotlib not available — skipping 2D PDP")
        return
    try:
        fi1  = _feature_idx(preprocessor, feat1)
        fi2  = _feature_idx(preprocessor, feat2)
        tidx = TARGET_COLUMNS.index(target)
        g1   = _grid_for_feature(X_train, fi1, grid_resolution)
        g2   = _grid_for_feature(X_train, fi2, grid_resolution)

        Z = np.zeros((len(g2), len(g1)))
        X_med = np.median(X_train, axis=0, keepdims=True)

        for j, v2 in enumerate(g2):
            X_batch = np.tile(X_med, (len(g1), 1))
            X_batch[:, fi1] = g1
            X_batch[:, fi2] = v2
            means, _, _ = ensemble.predict_batch(X_batch)
            Z[j, :] = means[:, tidx]

        fig, ax = plt.subplots(figsize=(7, 5))
        c = ax.pcolormesh(g1, g2, Z, cmap="viridis", shading="auto")
        fig.colorbar(c, ax=ax, label=target)
        ax.set_xlabel(feat1)
        ax.set_ylabel(feat2)
        ax.set_title(f"2D PDP: {feat1} × {feat2} → {target}")
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=120)
        plt.close(fig)
    except Exception as exc:
        logger.warning(f"plot_2d_pdp [{feat1}×{feat2}→{target}]: {exc}")


def generate_all_plots(
    ensemble,
    preprocessor,
    X_train: np.ndarray,
    output_dir: str = "models/m1/plots",
) -> None:
    """Generate the standard battery of PDP+ICE and 2D PDP plots."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    pdp_ice_cases = [
        (REPLACEMENT_PCT,  COMPRESSIVE_STRENGTH),
        (WC_RATIO,         COMPRESSIVE_STRENGTH),
        (CURING_DAYS,      COMPRESSIVE_STRENGTH),
        (PARTICLE_SIZE_MM, COMPRESSIVE_STRENGTH),
        (REPLACEMENT_PCT,  FLEXURAL_STRENGTH),
    ]
    for feat, targ in pdp_ice_cases:
        slug = f"ice_{feat}_vs_{targ}"
        try:
            plot_ice(ensemble, preprocessor, X_train, feat, targ,
                     save_path=str(out / f"{slug}.png"))
            logger.info(f"Saved {slug}.png")
        except Exception as exc:
            logger.warning(f"generate_all_plots ICE [{feat}]: {exc}")

    twod_cases = [
        (REPLACEMENT_PCT, ADDITIVE_TYPE, COMPRESSIVE_STRENGTH),
        (REPLACEMENT_PCT, WC_RATIO,      COMPRESSIVE_STRENGTH),
    ]
    for f1, f2, targ in twod_cases:
        slug = f"2dpdp_{f1}_x_{f2}_vs_{targ}"
        try:
            plot_2d_pdp(ensemble, preprocessor, X_train, f1, f2, targ,
                        save_path=str(out / f"{slug}.png"))
            logger.info(f"Saved {slug}.png")
        except Exception as exc:
            logger.warning(f"generate_all_plots 2D [{f1}×{f2}]: {exc}")
