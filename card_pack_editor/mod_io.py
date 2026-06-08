from __future__ import annotations

import json
import shutil
from pathlib import Path

from .constants import (
    BUFF_DATA_COMMENT,
    BUFF_DATA_HEADER,
    BUFF_TEXT_COMMENT,
    BUFF_TEXT_HEADER,
    CARD_DATA_COMMENT,
    CARD_DATA_HEADER,
    CARD_TEXT_COMMENT,
    CARD_TEXT_HEADER,
    CARDPACK_DATA_COMMENT,
    CARDPACK_DATA_HEADER,
    CARDPACK_TEXT_COMMENT,
    CARDPACK_TEXT_HEADER,
)
from .models import Buff, Card, Project
from .utils import (
    BLANK_PNG,
    clean_id,
    clean_mod_name,
    copy_optional_image,
    detect_base_script,
    no_ext_resource_path,
    read_csv_rows,
    resolve_mod_resource,
    runtime_pack_id,
    write_csv,
)


def save_project(project: Project, path: Path) -> None:
    path.write_text(json.dumps(project.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


def load_project(path: Path) -> Project:
    return Project.from_dict(json.loads(path.read_text(encoding="utf-8")))


def import_mod_folder(mod_dir: Path) -> Project:
    mod_dir = Path(mod_dir)
    config_path = mod_dir / "ModConfig.json"
    if not config_path.is_file():
        raise FileNotFoundError(f"找不到 ModConfig.json: {mod_dir}")
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))

    mod_name = config.get("ModName") or mod_dir.name
    project = Project(
        mod_name=mod_name,
        author=config.get("ModAuthor", "YOUR_NAME"),
        version=config.get("ModVersion", "0.1"),
        mod_description=config.get("ModDescription", ""),
        mod_icon_source=str(mod_dir / config.get("IconPath", "Icon.png")) if (mod_dir / config.get("IconPath", "Icon.png")).is_file() else "",
        workshop_visibility=config.get("WorkshopVisibility", "Private"),
    )

    pack_files = sorted((mod_dir / "Data" / "CardPack").glob("*.csv"))
    if not pack_files:
        raise FileNotFoundError("未找到 Data/CardPack/*.csv")
    pack_file = pack_files[0]
    project.csv_name = pack_file.stem
    pack_rows = read_csv_rows(pack_file)
    if not pack_rows:
        raise ValueError(f"卡包表没有数据行: {pack_file}")
    pack_row = pack_rows[0]
    project.pack_id = pack_row.get("Id", "cardpack_imported")
    project.pack_type = pack_row.get("Type", "Normal")
    project.pack_icon_source = resolve_mod_resource(mod_dir, mod_name, pack_row.get("Icon", ""))

    pack_text_rows = _text_rows_by_id(mod_dir / "Text" / "CardPack", project.csv_name)
    pack_text = pack_text_rows.get(project.pack_id, {})
    project.pack_name = pack_text.get("Name", project.pack_id)
    project.pack_name_en = pack_text.get("Name_en", "")
    project.pack_name_hant = pack_text.get("Name_zh-Hant", "")
    project.pack_name_ja = pack_text.get("Name_ja", "")
    project.pack_description = pack_text.get("Description", "")
    project.pack_description_hant = pack_text.get("Description_zh-Hant", "")
    project.pack_description_en = pack_text.get("Description_en", "")
    project.pack_description_ja = pack_text.get("Description_ja", "")

    expected_pack_id = runtime_pack_id(mod_name, project.csv_name, project.pack_id)
    card_text_rows = _text_rows_by_id(mod_dir / "Text" / "Card", None)
    cards: list[Card] = []
    for card_file in sorted((mod_dir / "Data" / "Card").glob("*.csv")):
        for row in read_csv_rows(card_file):
            if row.get("PackBelong") and row.get("PackBelong") != expected_pack_id:
                continue
            card_id = row.get("Id", "")
            text = card_text_rows.get(card_id, {})
            init_script = row.get("InitScript", "")
            cards.append(
                Card(
                    card_id=card_id,
                    card_type=text.get("Type", "技能牌"),
                    name=text.get("Name", card_id),
                    name_en=text.get("Name_en", ""),
                    name_hant=text.get("Name_zh-Hant", ""),
                    name_ja=text.get("Name_ja", ""),
                    description=text.get("Description", ""),
                    description_hant=text.get("Description_zh-Hant", ""),
                    description_en=text.get("Description_en", ""),
                    description_ja=text.get("Description_ja", ""),
                    rarity=row.get("Rarity", "1"),
                    expend=row.get("Expend", "1"),
                    tag=row.get("Tag", ""),
                    base_script=detect_base_script(init_script),
                    init_script=init_script,
                    draw_script=row.get("DrawScript", ""),
                    use_script=row.get("UseScript", ""),
                    drop_script=row.get("DropScript", ""),
                    icon_source=resolve_mod_resource(mod_dir, mod_name, row.get("Icon", "")),
                    effects=row.get("Effects", ""),
                    action=row.get("Action", ""),
                    note=text.get("Note", ""),
                    done=text.get("是否完成", "TRUE"),
                )
            )
    project.cards = cards or [Card()]

    buff_text_rows = _text_rows_by_id(mod_dir / "Text" / "Buff", None)
    buffs: list[Buff] = []
    for buff_file in sorted((mod_dir / "Data" / "Buff").glob("*.csv")):
        for row in read_csv_rows(buff_file):
            buff_id = row.get("Id", "")
            text = buff_text_rows.get(buff_id, {})
            buffs.append(
                Buff(
                    buff_id=buff_id,
                    name=text.get("Name", buff_id),
                    name_en=text.get("Name_en", ""),
                    name_hant=text.get("Name_zh-Hant", ""),
                    name_ja=text.get("Name_ja", ""),
                    description=text.get("Description", ""),
                    description_hant=text.get("Description_zh-Hant", ""),
                    description_en=text.get("Description_en", ""),
                    description_ja=text.get("Description_ja", ""),
                    init_script=row.get("InitScript", ""),
                    apply_script=row.get("ApplyScript", ""),
                    clear_script=row.get("ClearScript", ""),
                    reduce_per_turn=row.get("ReducePerTurn", "0"),
                    reduce_per_attacked=row.get("ReducePerAttacked", "0"),
                    reduce_per_use=row.get("ReducePerUse", "0"),
                    upper_bound=row.get("UpperBound", "99"),
                    icon=row.get("Icon", ""),
                    buff_type=row.get("Type", ""),
                    rarity=row.get("Rarity", "2"),
                    effects=row.get("Effects", ""),
                    sound_effects=row.get("SoundEffects", ""),
                    action=row.get("Action", ""),
                    note=text.get("Note", ""),
                )
            )
    project.buffs = buffs
    return project


def export_mod_folder(project: Project, parent: Path, overwrite: bool = False) -> Path:
    mod_name = clean_mod_name(project.mod_name)
    csv_name = clean_id(project.csv_name, "cards")
    pack_id = clean_id(project.pack_id, "cardpack_custom")
    mod_dir = Path(parent) / mod_name
    if mod_dir.exists():
        if not overwrite:
            raise FileExistsError(f"导出目录已存在: {mod_dir}")
        shutil.rmtree(mod_dir)
    mod_dir.mkdir(parents=True, exist_ok=True)

    cardpack_resource_dir = mod_dir / "ModResource" / "Images" / "CardPack"
    card_resource_dir = mod_dir / "ModResource" / "Images" / "Card" / mod_name

    pack_icon = copy_optional_image(project.pack_icon_source, cardpack_resource_dir, pack_id)
    if pack_icon is None:
        pack_icon = cardpack_resource_dir / f"{pack_id}.png"
        cardpack_resource_dir.mkdir(parents=True, exist_ok=True)
        pack_icon.write_bytes(BLANK_PNG)

    icon_source = project.mod_icon_source or project.pack_icon_source
    if icon_source and Path(icon_source).is_file():
        shutil.copy2(icon_source, mod_dir / "Icon.png")
    else:
        (mod_dir / "Icon.png").write_bytes(BLANK_PNG)

    mod_config = {
        "ModName": mod_name,
        "ModVersion": project.version or "0.1",
        "ModAuthor": project.author or "YOUR_NAME",
        "ModDescription": project.mod_description,
        "IconPath": "Icon.png",
        "Enabled": True,
        "Dependencies": None,
        "MustSame": False,
        "WorkshopVisibility": project.workshop_visibility or "Private",
        "PublishedFileId": "",
    }
    (mod_dir / "ModConfig.json").write_text(json.dumps(mod_config, ensure_ascii=False, indent=2), encoding="utf-8")

    pack_icon_resource = no_ext_resource_path(pack_icon.relative_to(mod_dir))
    write_csv(
        mod_dir / "Data" / "CardPack" / f"{csv_name}.csv",
        CARDPACK_DATA_HEADER,
        CARDPACK_DATA_COMMENT,
        [[pack_id, project.pack_type or "Normal", f"Mods/{mod_name}/{pack_icon_resource}"]],
    )
    write_csv(
        mod_dir / "Text" / "CardPack" / f"{csv_name}.csv",
        CARDPACK_TEXT_HEADER,
        CARDPACK_TEXT_COMMENT,
        [[
            pack_id, "", project.pack_name, project.pack_name_hant, project.pack_name_en, project.pack_name_ja,
            project.pack_description, project.pack_description_hant, project.pack_description_ja, project.pack_description_en,
        ]],
    )

    run_pack_id = runtime_pack_id(mod_name, csv_name, pack_id)
    card_data_rows: list[list[str]] = []
    card_text_rows: list[list[str]] = []
    for index, card in enumerate(project.cards, start=1):
        card_id = clean_id(card.card_id, f"card_{index}")
        copied_icon = copy_optional_image(card.icon_source, card_resource_dir, card_id)
        icon_resource = ""
        if copied_icon is not None:
            icon_resource = f"Mods/{mod_name}/{no_ext_resource_path(copied_icon.relative_to(mod_dir))}"
        init_script = card.init_script or f'self.Vars:set_Item("BaseScript", "{card.base_script or "CommonCardItem"}");'
        card_data_rows.append([
            card_id, card.rarity or "1", card.expend or "1", card.tag, run_pack_id,
            init_script, card.draw_script, card.use_script, card.drop_script, icon_resource, card.effects, card.action,
        ])
        card_text_rows.append([
            card_id, card.done or "TRUE", card.card_type, card.note, card.name, card.name_en, card.name_hant,
            card.name_ja, card.description, card.description_hant, card.description_en, card.description_ja,
        ])
    write_csv(mod_dir / "Data" / "Card" / f"{csv_name}.csv", CARD_DATA_HEADER, CARD_DATA_COMMENT, card_data_rows)
    write_csv(mod_dir / "Text" / "Card" / f"{csv_name}.csv", CARD_TEXT_HEADER, CARD_TEXT_COMMENT, card_text_rows)

    if project.buffs:
        buff_data_rows: list[list[str]] = []
        buff_text_rows: list[list[str]] = []
        for index, buff in enumerate(project.buffs, start=1):
            buff_id = clean_id(buff.buff_id, f"buff_{index}")
            buff_data_rows.append([
                buff_id, buff.init_script, buff.apply_script, buff.clear_script,
                buff.reduce_per_turn or "0", buff.reduce_per_attacked or "0", buff.reduce_per_use or "0",
                buff.upper_bound or "99", buff.icon, buff.buff_type, buff.rarity or "2",
                buff.effects, buff.sound_effects, buff.action,
            ])
            buff_text_rows.append([
                buff_id, buff.note, buff.name, buff.name_hant, buff.name_en, buff.name_ja,
                buff.description, buff.description_hant, buff.description_ja, buff.description_en,
            ])
        write_csv(mod_dir / "Data" / "Buff" / f"{csv_name}.csv", BUFF_DATA_HEADER, BUFF_DATA_COMMENT, buff_data_rows)
        write_csv(mod_dir / "Text" / "Buff" / f"{csv_name}.csv", BUFF_TEXT_HEADER, BUFF_TEXT_COMMENT, buff_text_rows)

    readme = (
        f"# {project.pack_name or mod_name}\n\n{project.mod_description}\n\n"
        "本 Mod 由 CardPackEditor 导出，为纯数据卡包。\n\n"
        f"- 运行时卡包 Id: `{run_pack_id}`\n"
        f"- 卡牌数量: {len(project.cards)}\n"
        f"- Buff 数量: {len(project.buffs)}\n"
    )
    (mod_dir / "README.md").write_text(readme, encoding="utf-8")
    return mod_dir


def _text_rows_by_id(folder: Path, preferred_stem: str | None) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    if not folder.is_dir():
        return rows
    files = sorted(folder.glob("*.csv"))
    if preferred_stem:
        preferred = folder / f"{preferred_stem}.csv"
        if preferred in files:
            files = [preferred] + [item for item in files if item != preferred]
    for file in files:
        for row in read_csv_rows(file):
            row_id = row.get("Id", "")
            if row_id:
                rows[row_id] = row
    return rows
