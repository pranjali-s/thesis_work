"""
BL2 -- Random Forest baseline, live rerun.

Adapted from the original train_bl2.py (no longer present in this
workspace, see BL2_status.md for its documented methodology). Trains a
Random Forest (100 trees, max_features="sqrt", unlimited depth,
random_state=42) on four features (n_reviews, avg_rating, delta_rating_app,
n_distinct_app_versions) to predict e2_matched, evaluated with
Leave-One-Out cross-validation across all 77 live-rerun clusters.

This run's E2 target label (e2_matched) is 0/77 positive (see
E2_LIVE_RUN_LOG.md) -- an even more extreme class imbalance than the
original run's 2/65. This is disclosed explicitly and handled without
pretending SMOTE or a meaningful positive-class metric can be computed:
with zero positive examples there is no minority class to resample and no
positive-class precision/recall/F1 to report (undefined, not zero).
"""
import json
import os

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import LeaveOneOut
from sklearn.metrics import roc_auc_score, accuracy_score, confusion_matrix

HERE = os.path.dirname(os.path.abspath(__file__))
FEATURES_JSON = os.path.join(HERE, "cluster_features_bl2.json")
E2_JSON = os.path.join(HERE, "e2_final.json")

FEATURE_NAMES = ["n_reviews", "avg_rating", "delta_rating_app", "n_distinct_app_versions"]


def main():
    with open(FEATURES_JSON, encoding="utf-8") as f:
        features = {(c["category"], c["cluster_id"]): c for c in json.load(f)["clusters"]}
    with open(E2_JSON, encoding="utf-8") as f:
        labels = {(r["category"], r["cluster_id"]): r["e2_matched"] for r in json.load(f)}

    feat_keys = set(features.keys())
    label_keys = set(labels.keys())
    assert feat_keys == label_keys, f"Key mismatch: {feat_keys ^ label_keys}"
    print(f"Joined {len(feat_keys)} clusters on (category, cluster_id) -- exact key match confirmed.")

    keys = sorted(feat_keys)
    X = np.array([[features[k][fn] for fn in FEATURE_NAMES] for k in keys], dtype=float)
    y = np.array([int(labels[k]) for k in keys])

    n_pos = int(y.sum())
    n_neg = len(y) - n_pos
    print(f"Target label e2_matched: {n_pos} positive / {n_neg} negative out of {len(y)} "
          f"({n_pos / len(y) * 100:.1f}% positive).")

    results = {"n_clusters": len(y), "n_positive": n_pos, "n_negative": n_neg,
               "feature_names": FEATURE_NAMES}

    if n_pos == 0:
        print("\nZERO positive examples in this run's E2 ground truth.")
        print("A classifier cannot learn a positive-class decision boundary from zero positive "
              "examples -- this is not a training failure, it is a direct, mechanical consequence "
              "of the label distribution. Precision/recall/F1 for the positive class and ROC-AUC "
              "are UNDEFINED (not zero, not computable) with no positive examples to score against.")
        print("Running LOOCV anyway to report accuracy / confusion matrix for transparency, and to "
              "confirm the model does exactly what a 0-positive label set implies: predicts negative "
              "for every held-out cluster.")

        loo = LeaveOneOut()
        preds = []
        for train_idx, test_idx in loo.split(X):
            clf = RandomForestClassifier(n_estimators=100, max_features="sqrt",
                                          max_depth=None, random_state=42)
            clf.fit(X[train_idx], y[train_idx])
            preds.append(int(clf.predict(X[test_idx])[0]))
        preds = np.array(preds)
        acc = accuracy_score(y, preds)
        cm = confusion_matrix(y, preds, labels=[0, 1])
        print(f"LOOCV accuracy: {acc:.4f} (trivially 1.0 if the model predicts 0 for every cluster, "
              "which is the only thing it CAN learn from an all-negative training set)")
        print(f"Confusion matrix [[TN FP][FN TP]]: {cm.tolist()}")

        clf_full = RandomForestClassifier(n_estimators=100, max_features="sqrt",
                                           max_depth=None, random_state=42)
        clf_full.fit(X, y)
        importances = dict(zip(FEATURE_NAMES, [round(float(v), 4) for v in clf_full.feature_importances_]))
        print(f"Feature importances (single fit, all-negative target -- not meaningful, reported for "
              f"transparency only): {importances}")

        results["variants"] = {
            "no_smote": {
                "accuracy": round(float(acc), 4),
                "precision_pos": None, "recall_pos": None, "f1_pos": None,
                "roc_auc": None,
                "confusion_matrix": cm.tolist(),
                "note": "Positive-class metrics and ROC-AUC are undefined with 0 positive examples.",
            },
            "smote_k1": {
                "note": "SMOTE could not be run: it requires at least 1 minority-class example to "
                        "interpolate from (k_neighbors>=1), and this run's E2 ground truth has 0. "
                        "No SMOTE variant exists for this run.",
            },
        }
        results["feature_importances_full_fit"] = importances
        results["headline_finding"] = (
            "BL2 cannot be trained meaningfully at all on this run's E2 ground truth -- there is no "
            "positive class whatsoever (0/77), a more severe degeneration of the same problem the "
            "original run already found at 2/65."
        )

    else:
        # (kept for completeness / future reruns where E2 finds >=1 match)
        from imblearn.over_sampling import SMOTE
        loo = LeaveOneOut()

        def run_variant(use_smote, k=None):
            preds, scores = [], []
            for train_idx, test_idx in loo.split(X):
                X_train, y_train = X[train_idx], y[train_idx]
                if use_smote:
                    sm = SMOTE(k_neighbors=k, random_state=42)
                    X_train, y_train = sm.fit_resample(X_train, y_train)
                clf = RandomForestClassifier(n_estimators=100, max_features="sqrt",
                                              max_depth=None, random_state=42)
                clf.fit(X_train, y_train)
                preds.append(int(clf.predict(X[test_idx])[0]))
                scores.append(float(clf.predict_proba(X[test_idx])[0][1]) if 1 in clf.classes_ else 0.0)
            return np.array(preds), np.array(scores)

        for name, use_smote, k in [("no_smote", False, None), ("smote_k1", True, min(1, n_pos - 1) or 1)]:
            preds, scores = run_variant(use_smote, k)
            acc = accuracy_score(y, preds)
            cm = confusion_matrix(y, preds, labels=[0, 1])
            try:
                auc = roc_auc_score(y, scores)
            except ValueError:
                auc = None
            tp = cm[1][1]
            fp = cm[0][1]
            fn = cm[1][0]
            precision = tp / (tp + fp) if (tp + fp) else 0.0
            recall = tp / (tp + fn) if (tp + fn) else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
            print(f"{name}: acc={acc:.4f} precision={precision:.4f} recall={recall:.4f} f1={f1:.4f} "
                  f"auc={auc}")
            results.setdefault("variants", {})[name] = {
                "accuracy": round(float(acc), 4), "precision_pos": round(precision, 4),
                "recall_pos": round(recall, 4), "f1_pos": round(f1, 4),
                "roc_auc": round(auc, 4) if auc is not None else None,
                "confusion_matrix": cm.tolist(),
            }

    with open(os.path.join(HERE, "bl2_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=1)

    import csv as csvmod
    with open(os.path.join(HERE, "bl2_predictions.csv"), "w", newline="", encoding="utf-8") as f:
        w = csvmod.writer(f)
        w.writerow(["category", "cluster_id"] + FEATURE_NAMES + ["e2_matched"])
        for k in keys:
            w.writerow([k[0], k[1]] + [features[k][fn] for fn in FEATURE_NAMES] + [int(labels[k])])

    print("\nWrote bl2_metadata.json and bl2_predictions.csv")


if __name__ == "__main__":
    main()
