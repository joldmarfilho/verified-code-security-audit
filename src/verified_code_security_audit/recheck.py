"""Re-check recorded evidence against a newer repository revision.

An audit record is a snapshot: every path, line and snippet is true for the
revision it was produced against. This module answers one question per piece of
evidence — does that snippet still exist at the revision being checked?
"""

from __future__ import annotations

import subprocess
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path
from typing import NamedTuple

INTACT = "intact"
MOVED = "moved"
STALE = "stale"
UNVERIFIABLE = "unverifiable"

_REDACTION = "[REDACTED]"


class EvidenceStatus(NamedTuple):
    """Outcome of comparing one evidence entry against a revision."""

    owner: str
    path: str
    recorded_line: int
    status: str
    current_line: int | None


class GitUnavailableError(RuntimeError):
    """Git is missing, or the directory is not a repository."""


def _git(repository: Path, arguments: Sequence[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", "-C", str(repository), *arguments],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError as exc:  # git absent from PATH
        raise GitUnavailableError(str(exc)) from exc


def resolve_revision(repository: Path, revision: str) -> str:
    """Return the full commit SHA for ``revision``."""

    completed = _git(repository, ["rev-parse", "--verify", f"{revision}^{{commit}}"])
    if completed.returncode != 0:
        raise GitUnavailableError(completed.stderr.strip() or f"unknown revision: {revision}")
    return completed.stdout.strip()


def _blob(repository: Path, revision: str, path: str) -> str | None:
    completed = _git(repository, ["show", f"{revision}:{path}"])
    if completed.returncode != 0:
        return None
    return completed.stdout


def _normalized(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _locate(blob: str, snippet: str) -> int | None:
    """Return the 1-based line where ``snippet`` starts, ignoring indentation."""

    wanted = _normalized(snippet)
    if not wanted:
        return None
    # ponytail: whitespace-normalized line match. A reformat-only diff still
    # reads as stale; upgrade to a token-level compare if that gets noisy.
    haystack = blob.splitlines()
    stripped = [line.strip() for line in haystack]
    for index in range(len(stripped) - len(wanted) + 1):
        if stripped[index] != wanted[0]:
            continue
        cursor = index
        for expected in wanted:
            while cursor < len(stripped) and not stripped[cursor]:
                cursor += 1
            if cursor >= len(stripped) or stripped[cursor] != expected:
                break
            cursor += 1
        else:
            return index + 1
    return None


def _entries(report: Mapping[str, object]) -> Iterator[tuple[str, Mapping[str, object]]]:
    labels = (
        ("findings", "finding"),
        ("strengths", "strength"),
        ("categories", "category"),
        ("stack", "stack"),
    )
    for key, kind in labels:
        items = report.get(key)
        if not isinstance(items, Sequence):
            continue
        for position, item in enumerate(items, start=1):
            if not isinstance(item, Mapping):
                continue
            name = item.get("id") or item.get("name") or item.get("title") or position
            evidence = item.get("evidence")
            if not isinstance(evidence, Sequence):
                continue
            for entry in evidence:
                if isinstance(entry, Mapping):
                    yield f"{kind}:{name}", entry


def recheck_evidence(
    owner: str,
    evidence: Mapping[str, object],
    repository: Path,
    revision: str,
    blobs: dict[str, str | None] | None = None,
) -> EvidenceStatus:
    """Classify one evidence entry against ``revision``."""

    path = str(evidence["path"])
    recorded_line = int(evidence["start_line"])
    snippet = str(evidence["snippet"])

    if _REDACTION in snippet:
        return EvidenceStatus(owner, path, recorded_line, UNVERIFIABLE, None)

    cache = blobs if blobs is not None else {}
    if path not in cache:
        cache[path] = _blob(repository, revision, path)
    blob = cache[path]
    if blob is None:
        return EvidenceStatus(owner, path, recorded_line, STALE, None)

    current_line = _locate(blob, snippet)
    if current_line is None:
        return EvidenceStatus(owner, path, recorded_line, STALE, None)
    status = INTACT if current_line == recorded_line else MOVED
    return EvidenceStatus(owner, path, recorded_line, status, current_line)


def recheck_report(
    report: Mapping[str, object],
    repository: Path,
    revision: str = "HEAD",
) -> list[EvidenceStatus]:
    """Classify every evidence entry in ``report`` against ``revision``."""

    resolved = resolve_revision(repository, revision)
    blobs: dict[str, str | None] = {}
    return [
        recheck_evidence(owner, entry, repository, resolved, blobs)
        for owner, entry in _entries(report)
    ]
