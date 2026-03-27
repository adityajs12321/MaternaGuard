"""End-to-end runner for Member A ML deliverables."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .explainability import generate_shap_outputs
from .pipeline import build_merged_dataset, save_inspection, split_scale_and_balance
from .reporting import write_accuracy_report, write_model_card
from .tflite_export import export_ann_to_tflite
from .training import evaluate_all, print_metrics, save_artifacts, train_ann, train_random_forest, train_svm, train_xgboost, train_gbt


def main() -> None:
    parser = argparse.ArgumentParser(description="Run MaternaGuard ML pipeline")
    parser.add_argument("--ds1", required=True, help="Path to DS1 CSV")
    parser.add_argument("--ds2", required=True, help="Path to DS2 CSV")
    parser.add_argument("--ds3", required=True, help="Path to DS3 CSV")
    parser.add_argument("--models-dir", default="models", help="Output model directory")
    parser.add_argument("--docs-dir", default="docs", help="Output docs directory")
    parser.add_argument("--data-dir", default="data", help="Output data directory")
    args = parser.parse_args()

    Path(args.data_dir).mkdir(parents=True, exist_ok=True)
    Path(f"{args.data_dir}/processed").mkdir(parents=True, exist_ok=True)

    merged, inspection = build_merged_dataset(args.ds1, args.ds2, args.ds3)
    merged.to_csv(Path(args.data_dir) / "processed" / "merged_dataset.csv", index=False)
    save_inspection(inspection, str(Path(args.docs_dir) / "dataset_inspection.json"))

    prep = split_scale_and_balance(merged, models_dir=args.models_dir)

    ann = train_ann(prep["X_train_scaled"], prep["y_train_sm"])
    rf = train_random_forest(prep["X_train_scaled"], prep["y_train_sm"], ann)
    svm = train_svm(prep["X_train_scaled"], prep["y_train_sm"], ann)
    xgb = train_xgboost(prep["X_train_scaled"], prep["y_train_sm"])
    gbt = train_gbt(prep["X_train_scaled"], prep["y_train_sm"])

    metrics = evaluate_all(rf, svm, ann, xgb, gbt, prep["X_test_scaled"], prep["y_test"])
    print_metrics(metrics)
    save_artifacts(rf, svm, ann, xgb, gbt, metrics, models_dir=args.models_dir, docs_dir=args.docs_dir)

    import numpy as np
    from tensorflow import keras
    extractor = keras.Model(inputs=ann.inputs, outputs=ann.layers[-2].output)
    X_ann_test_features = extractor.predict(prep["X_test_scaled"], verbose=0)
    X_fused_test = np.concatenate([prep["X_test_scaled"], X_ann_test_features], axis=1)
    fused_feature_cols = prep["feature_cols"] + [f"ANN_F{i}" for i in range(16)]

    generate_shap_outputs(rf, X_fused_test, fused_feature_cols, docs_dir=args.docs_dir)

    tflite_info = export_ann_to_tflite(ann, prep["X_test_scaled"], models_dir=args.models_dir)
    with (Path(args.docs_dir) / "tflite_verification.json").open("w", encoding="utf-8") as fh:
        json.dump(tflite_info, fh, indent=2)

    write_accuracy_report(
        metrics,
        inspection,
        prep["class_counts_before_smote"],
        prep["class_counts_after_smote"],
        docs_dir=args.docs_dir,
    )
    write_model_card(metrics, docs_dir=args.docs_dir)

    print("Pipeline finished. Critical files:")
    print(f"- {Path(args.models_dir) / 'model.tflite'}")
    print(f"- {Path(args.models_dir) / 'scaler_params.json'}")


if __name__ == "__main__":
    main()
