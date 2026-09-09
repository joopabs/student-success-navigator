"""Cross-validation helpers (T036).

- `make_cv`: StratifiedKFold with the single project seed.
- `oof_predict`: out-of-fold scores with fold ids (every row scored exactly once, by a model that
  never saw it).
- `k_for_fold`: scales the illustrative outreach capacity K to a validation fold so the selection
  rate matches deployment (research R-08).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.model_selection import StratifiedKFold

from ssn.config import Config


def make_cv(cfg: Config) -> StratifiedKFold:
    return StratifiedKFold(
        n_splits=int(cfg.get("split.cv_folds")), shuffle=True, random_state=cfg.seed
    )


def k_for_fold(k: int, n_fold: int, n_test_expected: int) -> int:
    """K scaled to a fold of size n_fold so that K/n_test_expected == k_fold/n_fold (min 1)."""
    if n_test_expected <= 0:
        raise ValueError("n_test_expected must be positive")
    return max(1, int(round(k * n_fold / n_test_expected)))


@dataclass
class OOFResult:
    scores: np.ndarray
    folds: np.ndarray
    y: np.ndarray
    index: pd.Index

    def frame(self, record_id: pd.Series | None = None) -> pd.DataFrame:
        out = pd.DataFrame(
            {"fold": self.folds, "y_true": self.y, "score": self.scores}, index=self.index
        )
        if record_id is not None:
            out.insert(0, "record_id", record_id.loc[self.index].to_numpy())
        return out.reset_index(drop=True)


def oof_predict(pipeline, X: pd.DataFrame, y: pd.Series, cv: StratifiedKFold) -> OOFResult:
    """Fit a fresh clone per fold on the training rows only; score the held-out fold."""
    scores = np.full(len(X), np.nan)
    folds = np.full(len(X), -1)
    y_arr = np.asarray(y)
    for fold, (tr, va) in enumerate(cv.split(X, y_arr)):
        model = clone(pipeline).fit(X.iloc[tr], y_arr[tr])
        scores[va] = model.predict_proba(X.iloc[va])[:, 1]
        folds[va] = fold
    assert not np.isnan(scores).any() and (folds >= 0).all(), (
        "OOF did not cover every row exactly once"
    )
    return OOFResult(scores=scores, folds=folds, y=y_arr, index=X.index)
