#!/usr/bin/env python3
"""Generate docs/requirements.xml and docs/technology.xml from md frontmatter.

Scans `docs/superpowers/specs/` for `*-discovery.md` (→ `requirements.xml`) and
`*-design.md` (→ `technology.xml`). Parses YAML frontmatter of each file and
aggregates into a single XML per type.

Usage:
    generate_xml_from_md.py [--project-root PATH]
                            [--specs-dir docs/superpowers/specs]
                            [--docs-dir docs]

Exits with status 0 even when specs dir is missing (no-op for projects without specs).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from xml.dom import minidom
from xml.etree import ElementTree as ET

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# Valid XML element name: start char then name chars (subset; no colons to avoid
# namespace ambiguity). Frontmatter map keys are author free-text and may contain
# spaces / punctuation, which are illegal as element names and crash the XML
# serializer. Sanitize to a safe tag and preserve the original via a key attribute.
_XML_NAME_START = re.compile(r"[A-Za-z_]")
_XML_NAME_CHAR = re.compile(r"[\w.\-]")


def sanitize_tag(key: str) -> tuple[str, str | None]:
    """Return (safe_tag, original_if_changed). Always a valid XML element name."""
    raw = str(key)
    chars = []
    for i, ch in enumerate(raw):
        ok = _XML_NAME_CHAR.match(ch) if i else _XML_NAME_START.match(ch)
        chars.append(ch if ok else "_")
    safe = "".join(chars) or "_"
    if not _XML_NAME_START.match(safe[0]):
        safe = "_" + safe
    return safe, (raw if safe != raw else None)


def _sub_element(parent: ET.Element, key: str) -> ET.Element:
    safe, original = sanitize_tag(key)
    child = ET.SubElement(parent, safe)
    if original is not None:
        child.set("key", original)
    return child


def parse_frontmatter(md_text: str) -> dict:
    match = FRONTMATTER_RE.match(md_text)
    if not match:
        return {}
    try:
        return yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as exc:
        print(f"YAML parse error: {exc}", file=sys.stderr)
        return {}


def dict_to_xml(parent: ET.Element, data, item_tag: str = "Item") -> None:
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                child = _sub_element(parent, key)
                dict_to_xml(child, value, item_tag)
            else:
                child = _sub_element(parent, key)
                child.text = "" if value is None else str(value)
    elif isinstance(data, list):
        for item in data:
            child = ET.SubElement(parent, item_tag)
            if isinstance(item, dict):
                if "id" in item:
                    child.set("id", str(item["id"]))
                for key, value in item.items():
                    if key == "id":
                        continue
                    if isinstance(value, (dict, list)):
                        sub = _sub_element(child, key)
                        dict_to_xml(sub, value, item_tag)
                    else:
                        sub = _sub_element(child, key)
                        sub.text = "" if value is None else str(value)
            else:
                child.text = "" if item is None else str(item)


def build_xml(md_files: list[Path], root_tag: str, feature_tag: str = "Feature") -> str:
    root = ET.Element(root_tag)
    root.set("generated", "auto")
    root.set("source", "YAML frontmatter of markdown specs")

    attribute_keys = {"feature_id", "bd_id"}

    for md_file in sorted(md_files):
        text = md_file.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(text)
        if not frontmatter:
            continue

        feature = ET.SubElement(root, feature_tag)
        feature.set("source", md_file.name)
        for attr in attribute_keys:
            if attr in frontmatter:
                feature.set(attr, str(frontmatter[attr]))

        for key, value in frontmatter.items():
            if key in attribute_keys:
                continue
            if isinstance(value, (dict, list)):
                sub = _sub_element(feature, key)
                dict_to_xml(sub, value)
            else:
                sub = _sub_element(feature, key)
                sub.text = "" if value is None else str(value)

    raw = ET.tostring(root, encoding="unicode")
    pretty = minidom.parseString(raw).toprettyxml(indent="  ")
    lines = [line for line in pretty.splitlines() if line.strip()]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--specs-dir", default="docs/superpowers/specs")
    parser.add_argument("--docs-dir", default="docs")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    specs_dir = project_root / args.specs_dir
    docs_dir = project_root / args.docs_dir

    if not specs_dir.exists():
        print(f"No specs dir at {specs_dir}, nothing to do", file=sys.stderr)
        return 0

    docs_dir.mkdir(parents=True, exist_ok=True)

    discovery_files = list(specs_dir.glob("*-discovery.md"))
    design_files = list(specs_dir.glob("*-design.md"))

    requirements_xml = build_xml(discovery_files, "Requirements")
    technology_xml = build_xml(design_files, "Technology")

    (docs_dir / "requirements.xml").write_text(requirements_xml + "\n", encoding="utf-8")
    (docs_dir / "technology.xml").write_text(technology_xml + "\n", encoding="utf-8")

    print(
        f"Generated {docs_dir / 'requirements.xml'} from {len(discovery_files)} discovery.md files",
        file=sys.stderr,
    )
    print(
        f"Generated {docs_dir / 'technology.xml'} from {len(design_files)} design.md files",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
