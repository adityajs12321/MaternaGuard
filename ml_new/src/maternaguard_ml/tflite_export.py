"""TFLite export and verification utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import numpy as np
import tensorflow as tf


def export_ann_to_tflite(ann_model, X_test_scaled: np.ndarray, models_dir: str = "models") -> Dict[str, object]:
    Path(models_dir).mkdir(parents=True, exist_ok=True)

    converter = tf.lite.TFLiteConverter.from_keras_model(ann_model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_model = converter.convert()

    model_path = Path(models_dir) / "model.tflite"
    with model_path.open("wb") as fh:
        fh.write(tflite_model)

    interpreter = tf.lite.Interpreter(model_path=str(model_path))
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    test_input = X_test_scaled[0:1].astype(np.float32)
    interpreter.set_tensor(input_details[0]["index"], test_input)
    interpreter.invoke()
    tflite_output = interpreter.get_tensor(output_details[0]["index"])

    ann_pred = int(np.argmax(ann_model.predict(test_input, verbose=0), axis=1)[0])
    tflite_pred = int(np.argmax(tflite_output, axis=1)[0])

    return {
        "model_path": str(model_path),
        "model_size_kb": round(len(tflite_model) / 1024.0, 2),
        "input_shape": input_details[0]["shape"].tolist(),
        "output_shape": output_details[0]["shape"].tolist(),
        "ann_prediction": ann_pred,
        "tflite_prediction": tflite_pred,
        "predictions_match": ann_pred == tflite_pred,
        "tflite_probabilities": tflite_output.tolist(),
    }
