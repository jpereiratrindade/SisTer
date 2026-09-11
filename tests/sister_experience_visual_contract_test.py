#!/usr/bin/env python3
from pathlib import Path
import struct
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "assets" / "sister-experience-base"
REFERENCE = BASE / "reference.png"
RENDER = BASE / "sister-experience-base.png"
SVG = BASE / "sister-experience-base.svg"
README = BASE / "README.md"
WEB_REFERENCE = ROOT / "web" / "assets" / "sister-experience-reference.png"


def png_size(path: Path) -> tuple[int, int]:
    payload = path.read_bytes()[:24]
    assert payload[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", payload[16:24])


assert png_size(REFERENCE) == (1672, 941)
assert png_size(RENDER) == (1672, 941)
assert REFERENCE.read_bytes() != b""
assert WEB_REFERENCE.read_bytes() == REFERENCE.read_bytes()

tree = ET.parse(SVG)
root = tree.getroot()
assert root.attrib["viewBox"] == "0 0 1672 941"

namespace = {"svg": "http://www.w3.org/2000/svg"}
ids = {node.attrib["id"] for node in root.findall(".//*[@id]", namespace)}
for required in (
    "background",
    "title",
    "left-principles",
    "ecosystem",
    "context-core",
    "person",
    "sister",
    "urt",
    "atmos",
    "nexo",
    "praxis",
    "territory",
    "right-principles",
    "footer-brand",
):
    assert required in ids

image = root.find(".//svg:image", namespace)
assert image is not None
assert image.attrib.get("href") == "reference.png"

readme = README.read_text(encoding="utf-8")
assert "1672 × 941" in readme
assert "python3 tools/visual-diff/compare.py" in readme

print("sister experience visual contract test: ok")
