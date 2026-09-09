"""PCA analysis (T038): explained variance on the training split, 2-D projection for
visualisation, and a CV comparison of PCA vs no-PCA pipelines. PCA is a pipeline step, so under
cross_validate it is fitted on training folds only. Component count comes from the configured
variance threshold, never from test data.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.decomposition import PCA  # noqa: E402
from sklearn.model_selection import cross_validate  # noqa: E402
from sklearn.pipeline import Pipeline  # noqa: E402

from ssn.config import Config  # noqa: E402
from ssn.features.allowlist import Allowlist  # noqa: E402
from ssn.features.preprocess import build_preprocessor  # noqa: E402
from ssn.modeling.cv import make_cv  # noqa: E402
from ssn.modeling.selection import SCORING, reference_estimator  # noqa: E402


def build_pca_pipeline(allow: Allowlist, n_components: float | int, seed: int) -> Pipeline:
    return Pipeline(
        [
            ("pre", build_preprocessor(allow)),
            ("pca", PCA(n_components=n_components, random_state=seed)),
            ("clf", reference_estimator(seed)),
        ]
    )


def build_nopca_pipeline(allow: Allowlist, seed: int) -> Pipeline:
    return Pipeline([("pre", build_preprocessor(allow)), ("clf", reference_estimator(seed))])


def explained_variance(
    X: pd.DataFrame, y: pd.Series, allow: Allowlist, cfg: Config
) -> tuple[pd.DataFrame, np.ndarray]:
    """Fit preprocess + full PCA on the TRAINING split for description.

    Returns the explained-variance table and the 2-D scores."""
    pre = build_preprocessor(allow).fit(X, y)
    Xt = pre.transform(X)
    pca = PCA(random_state=cfg.seed).fit(Xt)
    evr = pca.explained_variance_ratio_
    table = pd.DataFrame(
        {
            "component": np.arange(1, len(evr) + 1),
            "explained_variance_ratio": evr,
            "cumulative": np.cumsum(evr),
        }
    )
    scores2d = pca.transform(Xt)[:, :2]
    return table, scores2d


def n_components_for(table: pd.DataFrame, threshold: float) -> int:
    return int(table.index[table["cumulative"] >= threshold][0] + 1)


def compare_cv(X: pd.DataFrame, y: pd.Series, allow: Allowlist, cfg: Config) -> pd.DataFrame:
    cv = make_cv(cfg)
    thr = float(cfg.get("pca.variance_threshold"))
    rows = []
    for name, pipe in (
        ("no_pca", build_nopca_pipeline(allow, cfg.seed)),
        (f"pca_{thr:.2f}_variance", build_pca_pipeline(allow, thr, cfg.seed)),
        ("pca_2_components", build_pca_pipeline(allow, 2, cfg.seed)),
    ):
        res = cross_validate(pipe, X, y, cv=cv, scoring=SCORING, n_jobs=1)
        rows.append(
            {
                "pipeline": name,
                "pr_auc_mean": float(np.mean(res["test_pr_auc"])),
                "pr_auc_std": float(np.std(res["test_pr_auc"], ddof=1)),
                "roc_auc_mean": float(np.mean(res["test_roc_auc"])),
                "roc_auc_std": float(np.std(res["test_roc_auc"], ddof=1)),
                "fit_time_s": float(np.mean(res["fit_time"])),
            }
        )
    return pd.DataFrame(rows)


def fig_scree(table: pd.DataFrame, threshold: float, n_thr: int, path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(
        table["component"],
        table["cumulative"],
        color="#4c72b0",
        label="cumulative explained variance",
    )
    ax.bar(
        table["component"],
        table["explained_variance_ratio"],
        color="#dd8452",
        alpha=0.5,
        label="per component",
    )
    ax.axhline(threshold, color="gray", ls="--", lw=1)
    ax.axvline(
        n_thr, color="#c44e52", ls=":", lw=1, label=f"{n_thr} components reach {threshold:.0%}"
    )
    ax.set_xlabel("principal component")
    ax.set_ylabel("explained variance ratio")
    ax.set_title("PCA scree plot (fitted on the training split; one-hot + scaled numeric features)")
    ax.legend(fontsize=8)
    fig.text(
        0.01,
        0.005,
        "Source: UCI 697, training split only. `python -m ssn pca`.",
        fontsize=7,
        color="gray",
    )
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def fig_projection(scores2d: np.ndarray, y: pd.Series, table: pd.DataFrame, path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    for label, color, name in ((0, "#55a868", "non-dropout"), (1, "#c44e52", "dropout")):
        m = np.asarray(y) == label
        ax.scatter(
            scores2d[m, 0],
            scores2d[m, 1],
            s=6,
            alpha=0.35,
            color=color,
            label=f"{name} (n={m.sum()})",
        )
    ax.set_xlabel(f"PC1 ({table.loc[0, 'explained_variance_ratio']:.1%} variance)")
    ax.set_ylabel(f"PC2 ({table.loc[1, 'explained_variance_ratio']:.1%} variance)")
    ax.set_title("First two principal components, training split, coloured by is_dropout")
    ax.legend(fontsize=8)
    fig.text(
        0.01,
        0.005,
        "Source: UCI 697, training split only. `python -m ssn pca`.",
        fontsize=7,
        color="gray",
    )
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def run_pca(
    X: pd.DataFrame, y: pd.Series, cfg: Config, allow: Allowlist, tables_dir: Path, figs_dir: Path
) -> dict[str, Path]:
    thr = float(cfg.get("pca.variance_threshold"))
    table, scores2d = explained_variance(X, y, allow, cfg)
    n_thr = n_components_for(table, thr)
    compare = compare_cv(X, y, allow, cfg) if cfg.get("pca.compare_in_cv") else pd.DataFrame()
    tables_dir.mkdir(parents=True, exist_ok=True)
    out = {}
    out["explained_variance"] = tables_dir / "pca_explained_variance.csv"
    table.to_csv(out["explained_variance"], index=False)
    out["compare"] = tables_dir / "pca_vs_nopca_cv.csv"
    compare.assign(n_components_at_threshold=n_thr, n_transformed_features=len(table)).to_csv(
        out["compare"], index=False
    )
    out["scree"] = fig_scree(table, thr, n_thr, figs_dir / "pca_scree.png")
    out["projection"] = fig_projection(scores2d, y, table, figs_dir / "pca_2d_train.png")
    return out
