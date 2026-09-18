"""Persists Stage 2 understanding output to disk."""
from __future__ import annotations

from pathlib import Path

from .models import UnderstandingResult


def save_understanding_result(result: UnderstandingResult, output_dir: str | Path) -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    (output_path / "understanding.json").write_text(
        result.model_dump_json(indent=2, by_alias=True), encoding="utf-8"
    )
    return output_path
