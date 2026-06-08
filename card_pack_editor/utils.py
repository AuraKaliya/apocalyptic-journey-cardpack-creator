from __future__ import annotations

import base64
import csv
import re
import shutil
from pathlib import Path


BLANK_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


def clean_id(value: str, fallback: str) -> str:
    value = re.sub(r"[^0-9A-Za-z_]+", "_", (value or "").strip())
    value = re.sub(r"_+", "_", value).strip("_")
    return value or fallback


def clean_mod_name(value: str) -> str:
    value = re.sub(r"[^0-9A-Za-z_]+", "", (value or "").strip())
    if not value:
        value = "YourMod"
    if value[0].isdigit():
        value = f"Mod{value}"
    return value


def runtime_pack_id(mod_name: str, csv_name: str, pack_id: str) -> str:
    return f"{clean_mod_name(mod_name)}_{clean_id(csv_name, 'cards')}_{clean_id(pack_id, 'cardpack_custom')}"


def no_ext_resource_path(path: Path) -> str:
    return path.with_suffix("").as_posix()


def unique_destination(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    counter = 2
    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def copy_optional_image(source: str, destination_dir: Path, fallback_name: str) -> Path | None:
    source = (source or "").strip()
    if not source:
        return None
    source_path = Path(source)
    if not source_path.is_file():
        raise FileNotFoundError(f"找不到图片资源: {source}")
    suffix = source_path.suffix or ".png"
    safe_stem = clean_id(source_path.stem, fallback_name)
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = unique_destination(destination_dir / f"{safe_stem}{suffix}")
    shutil.copy2(source_path, destination)
    return destination


def write_csv(path: Path, header: list[str], comment: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerow(comment)
        writer.writerows(rows)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration:
            return []
        next(reader, None)
        rows: list[dict[str, str]] = []
        for row in reader:
            if not row or not any(cell.strip() for cell in row):
                continue
            padded = row + [""] * (len(header) - len(row))
            rows.append({key: padded[index] if index < len(padded) else "" for index, key in enumerate(header)})
        return rows


def resolve_mod_resource(mod_dir: Path, mod_name: str, resource: str) -> str:
    resource = (resource or "").strip()
    if not resource:
        return ""
    normalized = resource.replace("\\", "/")
    prefix = f"Mods/{mod_name}/"
    if normalized.startswith(prefix):
        candidate = mod_dir / normalized[len(prefix):]
    else:
        candidate = mod_dir / normalized
    if candidate.is_file():
        return str(candidate)
    if candidate.suffix:
        return str(candidate) if candidate.exists() else ""
    for suffix in [".png", ".jpg", ".jpeg", ".gif"]:
        with_suffix = candidate.with_suffix(suffix)
        if with_suffix.is_file():
            return str(with_suffix)
    return ""


def detect_base_script(init_script: str) -> str:
    if "AttackCardItem" in (init_script or ""):
        return "AttackCardItem"
    return "CommonCardItem"

