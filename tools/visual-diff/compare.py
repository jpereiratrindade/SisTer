#!/usr/bin/env python3
"""Render and compare the SisTer canonical visual base reproducibly."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageEnhance


ROOT = Path(__file__).resolve().parents[2]
BASE_DIR = ROOT / "assets" / "sister-experience-base"
REFERENCE = BASE_DIR / "reference.png"
SVG = BASE_DIR / "sister-experience-base.svg"
DEFAULT_CANDIDATE = BASE_DIR / "sister-experience-base.png"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "out"
CANONICAL_SIZE = (1672, 941)


def render_svg(candidate: Path) -> None:
    firefox = shutil.which("firefox")
    if not firefox:
        raise RuntimeError("Firefox is required to render linked local raster assets in the SVG")
    candidate.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="sister-svg-render-") as profile:
        subprocess.run(
            [
                firefox,
                "--headless",
                "--profile",
                profile,
                "--window-size",
                "1672,941",
                "--screenshot",
                str(candidate.resolve()),
                SVG.resolve().as_uri(),
            ],
            check=True,
        )


def dhash(image: Image.Image) -> int:
    reduced = image.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
    pixels = np.asarray(reduced, dtype=np.int16)
    bits = pixels[:, 1:] > pixels[:, :-1]
    value = 0
    for bit in bits.flatten():
        value = (value << 1) | int(bit)
    return value


def global_ssim(reference: np.ndarray, candidate: np.ndarray) -> float:
    scores: list[float] = []
    c1 = (0.01 * 255) ** 2
    c2 = (0.03 * 255) ** 2
    for channel in range(3):
        x = reference[:, :, channel]
        y = candidate[:, :, channel]
        mean_x = float(x.mean())
        mean_y = float(y.mean())
        variance_x = float(x.var())
        variance_y = float(y.var())
        covariance = float(((x - mean_x) * (y - mean_y)).mean())
        numerator = (2 * mean_x * mean_y + c1) * (2 * covariance + c2)
        denominator = (mean_x**2 + mean_y**2 + c1) * (variance_x + variance_y + c2)
        scores.append(numerator / denominator if denominator else 1.0)
    return float(sum(scores) / len(scores))


def compare(reference_path: Path, candidate_path: Path, output_dir: Path) -> dict[str, object]:
    reference_image = Image.open(reference_path).convert("RGB")
    candidate_image = Image.open(candidate_path).convert("RGB")
    if reference_image.size != CANONICAL_SIZE:
        raise ValueError(f"reference must be {CANONICAL_SIZE[0]}x{CANONICAL_SIZE[1]}, got {reference_image.size}")
    if candidate_image.size != CANONICAL_SIZE:
        raise ValueError(f"candidate must be {CANONICAL_SIZE[0]}x{CANONICAL_SIZE[1]}, got {candidate_image.size}")

    reference = np.asarray(reference_image, dtype=np.float64)
    candidate = np.asarray(candidate_image, dtype=np.float64)
    delta = np.abs(reference - candidate)
    mse = float(np.mean((reference - candidate) ** 2))
    rmse = math.sqrt(mse)
    changed = np.any(delta > 0, axis=2)
    changed_over_8 = np.any(delta > 8, axis=2)
    total_pixels = reference.shape[0] * reference.shape[1]
    hash_distance = (dhash(reference_image) ^ dhash(candidate_image)).bit_count()

    def display_path(path: Path) -> str:
        try:
            return str(path.relative_to(ROOT))
        except ValueError:
            return str(path)

    metrics: dict[str, object] = {
        "canonical_size": list(CANONICAL_SIZE),
        "reference": display_path(reference_path),
        "candidate": display_path(candidate_path),
        "mae_rgb_0_255": round(float(delta.mean()), 8),
        "rmse_rgb_0_255": round(rmse, 8),
        "rmse_normalized": round(rmse / 255, 10),
        "psnr_db": "infinity" if mse == 0 else round(20 * math.log10(255 / rmse), 8),
        "global_ssim": round(global_ssim(reference, candidate), 10),
        "dhash_distance_64": hash_distance,
        "changed_pixels": int(changed.sum()),
        "changed_pixels_percent": round(float(changed.sum()) * 100 / total_pixels, 8),
        "changed_pixels_over_delta_8": int(changed_over_8.sum()),
        "max_channel_delta": int(delta.max()),
        "pixel_exact": bool(not changed.any()),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    raw_diff = ImageChops.difference(reference_image, candidate_image)
    ImageEnhance.Contrast(raw_diff).enhance(4).save(output_dir / "diff.png")
    Image.blend(reference_image, candidate_image, 0.5).save(output_dir / "overlay-50.png")
    (output_dir / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return metrics


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, default=DEFAULT_CANDIDATE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--no-render", action="store_true", help="compare an existing candidate without rendering the SVG")
    args = parser.parse_args()

    candidate = args.candidate.resolve()
    if not args.no_render and candidate == DEFAULT_CANDIDATE.resolve():
        render_svg(candidate)
    metrics = compare(REFERENCE, candidate, args.output.resolve())
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    return 0 if metrics["pixel_exact"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
