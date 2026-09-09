from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from ssn import config as C


def _write(tmp_path: Path, raw: dict) -> Path:
    p = tmp_path / "base.yaml"
    p.write_text(yaml.safe_dump(raw))
    return p


def test_valid_config_loads_and_seeds(base_config_dict, tmp_path):
    cfg = C.load(_write(tmp_path, base_config_dict))
    assert cfg.seed == base_config_dict["seed"]
    assert cfg.get("capacity.illustrative") is True
    assert cfg.capacity_k_values == [
        10 * w for w in base_config_dict["capacity"]["window_sensitivity_weeks"]
    ]
    assert cfg.path_for("features_yaml").name == "features.yaml"


def test_missing_key_names_the_path(base_config_dict, tmp_path):
    raw = copy.deepcopy(base_config_dict)
    del raw["capacity"]["illustrative"]
    with pytest.raises(C.ConfigError, match="capacity.illustrative"):
        C.load(_write(tmp_path, raw))


def test_wrong_type_is_rejected(base_config_dict, tmp_path):
    raw = copy.deepcopy(base_config_dict)
    raw["seed"] = "forty-two"
    with pytest.raises(C.ConfigError, match="seed: expected int"):
        C.load(_write(tmp_path, raw))


def test_capacity_k_must_match_product(base_config_dict, tmp_path):
    raw = copy.deepcopy(base_config_dict)
    raw["capacity"]["k"] = raw["capacity"]["k"] + 1
    with pytest.raises(C.ConfigError, match="capacity.k"):
        C.load(_write(tmp_path, raw))


def test_illustrative_flag_must_be_true(base_config_dict, tmp_path):
    raw = copy.deepcopy(base_config_dict)
    raw["capacity"]["illustrative"] = False
    with pytest.raises(C.ConfigError, match="illustrative"):
        C.load(_write(tmp_path, raw))


def test_enum_values_are_checked(base_config_dict, tmp_path):
    raw = copy.deepcopy(base_config_dict)
    raw["explain"]["method"] = "crystal_ball"
    with pytest.raises(C.ConfigError, match="explain.method"):
        C.load(_write(tmp_path, raw))


@pytest.mark.parametrize("name", ["dummy", "logreg", "random_forest", "hist_gb"])
def test_model_configs_load_and_substitute_seed(name):
    cfg = C.load("configs/base.yaml")
    mc = C.load_model_config(name, cfg)
    assert mc.name == name
    assert mc.params["random_state"] == cfg.seed
    if name != "dummy":
        assert mc.search_space, "non-dummy models need a search space"
    else:
        assert mc.search_space == {} and mc.n_iter == 0


def test_seed_substitution_rejects_unknown_variable(tmp_path):
    cfg = C.load("configs/base.yaml")
    d = tmp_path / "models"
    d.mkdir()
    (d / "weird.yaml").write_text(
        yaml.safe_dump(
            {
                "name": "weird",
                "estimator": "x.Y",
                "params": {"random_state": "${nope}"},
                "search_space": {},
                "n_iter": 0,
                "use_selection": False,
                "use_pca": False,
            }
        )
    )
    with pytest.raises(C.ConfigError, match="unknown substitution"):
        C.load_model_config("weird", cfg, models_dir=d)
