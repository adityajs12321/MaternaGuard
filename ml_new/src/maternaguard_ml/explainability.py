"""SHAP explainability helpers."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import shap

from .constants import OFFLINE_EXPLANATION_MAP


def _extract_high_risk_shap(shap_values):
    """Handle SHAP output differences across versions for multiclass models."""
    if isinstance(shap_values, list):
        return shap_values[2]

    arr = np.array(shap_values)
    if arr.ndim == 3:
        # Could be (classes, samples, features) or (samples, features, classes)
        if arr.shape[0] == 3:
            return arr[2]
        if arr.shape[-1] == 3:
            return arr[:, :, 2]
    raise ValueError("Unsupported SHAP output shape for multiclass model")


def generate_shap_outputs(rf, X_test_scaled, feature_cols, docs_dir: str = "docs") -> None:
    Path(docs_dir).mkdir(parents=True, exist_ok=True)

    explainer = shap.TreeExplainer(rf)
    shap_values = explainer.shap_values(X_test_scaled)
    high_risk_values = _extract_high_risk_shap(shap_values)

    plt.figure()
    shap.summary_plot(
        high_risk_values,
        X_test_scaled,
        feature_names=feature_cols,
        plot_type="bar",
        show=False,
    )
    plt.tight_layout()
    plt.savefig(Path(docs_dir) / "shap_high_risk_importance.png", dpi=180, bbox_inches="tight")
    plt.close()

    sample_idx = 0
    base_value = explainer.expected_value[2] if isinstance(explainer.expected_value, (list, np.ndarray)) else explainer.expected_value
    explanation = shap.Explanation(
        values=high_risk_values[sample_idx],
        base_values=base_value,
        data=X_test_scaled[sample_idx],
        feature_names=feature_cols,
    )

    plt.figure()
    shap.plots.waterfall(explanation, show=False)
    plt.tight_layout()
    plt.savefig(Path(docs_dir) / "shap_waterfall_sample0.png", dpi=180, bbox_inches="tight")
    plt.close()

    with (Path(docs_dir) / "offline_explanation_map.json").open("w", encoding="utf-8") as fh:
        json.dump(OFFLINE_EXPLANATION_MAP, fh, indent=2)
