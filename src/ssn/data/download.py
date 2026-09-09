"""Acquire the UCI dataset 697 CSV and verify its checksum.

Contract: specs/001-dropout-risk-navigator/contracts/cli.md (`data download`).
Constitution III: provenance recorded, raw data never committed.
"""

from __future__ import annotations

import hashlib
import io
import logging
import shutil
import urllib.request
import zipfile
from pathlib import Path

from ssn.config import Config, ConfigError

log = logging.getLogger(__name__)

UCI_ID = 697
UCI_ZIP_URL = (
    "https://archive.ics.uci.edu/static/public/697/"
    "predict+students+dropout+and+academic+success.zip"
)
UCI_CSV_URL = "https://archive.ics.uci.edu/static/public/697/data.csv"
UCI_PAGE_URL = (
    "https://archive.ics.uci.edu/dataset/697/predict+students+dropout+and+academic+success"
)
MEMBER_NAME = "data.csv"


class DownloadError(RuntimeError):
    pass


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _fetch(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "student-success-navigator/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (fixed https URL)
        return resp.read()


def fetch_csv_bytes() -> bytes:
    """Download the zip archive and return the CSV member; fall back to the direct CSV URL."""
    try:
        blob = _fetch(UCI_ZIP_URL)
        with zipfile.ZipFile(io.BytesIO(blob)) as zf:
            names = zf.namelist()
            member = (
                MEMBER_NAME
                if MEMBER_NAME in names
                else next((n for n in names if n.lower().endswith(".csv")), None)
            )
            if member is None:
                raise DownloadError(f"no CSV member in archive; members={names}")
            return zf.read(member)
    except (zipfile.BadZipFile, urllib.error.URLError, DownloadError) as exc:  # type: ignore[attr-defined]
        log.warning("zip download failed (%s); trying direct CSV URL", exc)
        return _fetch(UCI_CSV_URL)


def acquire(cfg: Config, *, from_local: Path | None = None, force: bool = False) -> Path:
    """Place data.csv at cfg.paths.raw_csv and verify sha256 against config.

    Returns the path. Raises ConfigError with instructions when the expected hash is unset or
    does not match, so a wrong or tampered file is never used silently.
    """
    target = cfg.path_for("raw_csv")
    target.parent.mkdir(parents=True, exist_ok=True)
    expected = (cfg.get("data.expected_sha256") or "").strip().lower()

    if target.is_file() and not force and expected and sha256_of(target) == expected:
        log.info("raw CSV present and checksum matches: %s", target)
        return target

    if from_local is not None:
        if not from_local.is_file():
            raise ConfigError(f"--from-local file not found: {from_local}")
        shutil.copyfile(from_local, target)
        log.info("copied local file %s -> %s", from_local, target)
    else:
        log.info("downloading UCI dataset %s", UCI_ID)
        target.write_bytes(fetch_csv_bytes())

    actual = sha256_of(target)
    if not expected:
        raise ConfigError(
            "data.expected_sha256 is empty. Downloaded file sha256 is\n"
            f"    {actual}\n"
            "Record it in configs/base.yaml (data.expected_sha256) and data/README.md, then rerun."
        )
    if actual != expected:
        raise ConfigError(
            f"sha256 mismatch for {target}: expected {expected}, got {actual}. "
            "Refusing to use the file. Re-download or update the recorded hash deliberately."
        )
    log.info("checksum verified: %s", actual)
    return target
