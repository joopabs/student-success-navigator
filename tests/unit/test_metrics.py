from __future__ import annotations

import math

import numpy as np
import pytest

from ssn.modeling import evaluate as EV
from ssn.modeling.cv import k_for_fold

Y = np.array([1, 0, 1, 0, 0, 1])
S = np.array([0.9, 0.8, 0.7, 0.6, 0.2, 0.1])


def test_top_k_and_precision_recall_at_k_hand_computed():
    # top-2 by score: idx0 (y=1), idx1 (y=0) -> tp=1
    assert EV.precision_at_k(Y, S, 2) == 0.5
    assert EV.recall_at_k(Y, S, 2) == pytest.approx(1 / 3)
    # top-3: idx0, idx1, idx2 -> tp=2
    assert EV.precision_at_k(Y, S, 3) == pytest.approx(2 / 3)
    assert EV.recall_at_k(Y, S, 3) == pytest.approx(2 / 3)
    # k >= n -> recall 1, precision = base rate
    assert EV.recall_at_k(Y, S, 10) == 1.0
    assert EV.precision_at_k(Y, S, 10) == pytest.approx(3 / 6)


def test_ties_at_k_boundary_are_deterministic_first_occurrence():
    y = np.array([0, 1, 1])
    s = np.array([0.5, 0.5, 0.5])
    mask = EV.top_k_mask(s, 1)
    assert mask.tolist() == [True, False, False]
    assert EV.precision_at_k(y, s, 1) == 0.0
    assert EV.precision_at_k(y[::-1], s[::-1], 1) == 1.0  # order changes the tie-break, by design


def test_k_zero_and_no_positives_return_nan():
    assert math.isnan(EV.precision_at_k(Y, S, 0))
    assert math.isnan(EV.recall_at_k(np.zeros(4), np.array([0.1, 0.2, 0.3, 0.4]), 2))


def test_pr_auc_and_roc_auc_on_perfect_and_constant_scores():
    assert EV.pr_auc(Y, S) == pytest.approx(EV.pr_auc(Y, S))
    perfect = np.array([0.9, 0.1, 0.8, 0.2, 0.1, 0.7])
    assert EV.pr_auc(Y, perfect) == 1.0 and EV.roc_auc(Y, perfect) == 1.0
    constant = np.full(6, 0.3)
    assert EV.pr_auc(Y, constant) == pytest.approx(3 / 6)  # base rate
    assert EV.roc_auc(Y, constant) == pytest.approx(0.5)
    assert math.isnan(EV.roc_auc(np.ones(3), np.array([0.1, 0.2, 0.3])))


def test_brier_and_ece_hand_computed():
    y = np.array([1, 0, 1, 0])
    s = np.array([0.8, 0.2, 0.6, 0.4])
    assert EV.brier(y, s) == pytest.approx(((0.2**2) + (0.2**2) + (0.4**2) + (0.4**2)) / 4)
    # n_bins=2: bin [0,.5] has scores .2,.4 (y=0,0): |0-.3|=.3, weight .5;
    #           bin (.5,1] has scores .8,.6 (y=1,1): |1-.7|=.3, weight .5 => ECE .3
    assert EV.expected_calibration_error(y, s, n_bins=2) == pytest.approx(0.3)
    assert EV.expected_calibration_error(y, y.astype(float), n_bins=2) == 0.0


def test_confusion_at_threshold_and_at_k():
    c = EV.confusion_at_threshold(Y, S, 0.65)  # pred = [1,1,1,0,0,0]
    assert (c.tp, c.fp, c.fn, c.tn) == (2, 1, 1, 2)
    ck = EV.confusion_at_k(Y, S, 2)
    assert (ck.tp, ck.fp, ck.fn, ck.tn) == (1, 1, 2, 2)
    assert c.as_dict("thr_") == {"thr_tn": 2, "thr_fp": 1, "thr_fn": 1, "thr_tp": 2}


def test_threshold_metrics_and_metrics_table_keys():
    m = EV.threshold_metrics(Y, S, 0.65)
    assert m["precision"] == pytest.approx(2 / 3) and m["recall"] == pytest.approx(2 / 3)
    assert m["accuracy"] == pytest.approx(4 / 6) and m["n_predicted_positive"] == 3
    t = EV.metrics_table(Y, S, threshold=0.5, k=2, k_values={"k4": 4})
    for key in (
        "pr_auc",
        "roc_auc",
        "brier",
        "ece",
        "recall_at_k",
        "precision_at_k",
        "precision_at_threshold",
        "recall_at_threshold",
        "f1_at_threshold",
        "accuracy_at_threshold",
        "thr_tp",
        "topk_tp",
        "recall_at_k4",
        "precision_at_k4",
    ):
        assert key in t, key
    assert t["k"] == 2 and t["recall_at_k4"] == pytest.approx(2 / 3)


def test_reliability_table_bins_cover_all_rows():
    rel = EV.reliability_table(Y, S, n_bins=5)
    assert rel["n"].sum() == len(Y) and len(rel) == 5


def test_pr_curve_frame_shape():
    c = EV.pr_curve(Y, S)
    assert {"precision", "recall", "threshold"} <= set(c.columns) and len(c) == len(np.unique(S))


def test_k_for_fold_used_by_cv_matches_selection_rate():
    assert k_for_fold(50, 708, 885) == 40 and k_for_fold(50, 707, 885) == 40
