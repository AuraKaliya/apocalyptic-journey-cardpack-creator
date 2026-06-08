from __future__ import annotations

import argparse
import tempfile
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from card_pack_editor.mod_io import export_mod_folder, import_mod_folder
from card_pack_editor.script_codegen import lua_to_steps, steps_to_lua
from card_pack_editor.validation import has_errors, validate_project


def main() -> None:
    parser = argparse.ArgumentParser(description="Import MoonRite and export it again as a smoke test.")
    parser.add_argument(
        "--moonrite",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "MoonRite",
        help="Path to the MoonRite mod folder.",
    )
    args = parser.parse_args()

    project = import_mod_folder(args.moonrite)
    assert project.mod_name == "MoonRite"
    assert project.csv_name == "moonrite"
    assert project.pack_id == "cardpack_moonrite"
    assert len(project.cards) == 18
    assert len(project.buffs) == 6
    assert Path(project.cards[0].icon_source).is_file()
    assert not has_errors(validate_project(project))

    steps, unsupported = lua_to_steps('self:SetStatus("Target"); self:Damage("6"); self:AddBuff("buff_x", "1");')
    assert len(steps) == 3
    assert not unsupported
    assert steps_to_lua(steps) == 'self:SetStatus("Target"); self:Damage("6"); self:AddBuff("buff_x", "1");'

    project.mod_name = "MoonRiteImportedTest"
    export_parent = Path(tempfile.mkdtemp(prefix="cardpack_editor_smoke_"))
    exported = export_mod_folder(project, export_parent)

    expected = [
        "ModConfig.json",
        "Data/CardPack/moonrite.csv",
        "Text/CardPack/moonrite.csv",
        "Data/Card/moonrite.csv",
        "Text/Card/moonrite.csv",
        "Data/Buff/moonrite.csv",
        "Text/Buff/moonrite.csv",
    ]
    for relative in expected:
        assert (exported / relative).is_file(), relative
    assert len(list((exported / "ModResource" / "Images" / "Card" / "MoonRiteImportedTest").glob("*.png"))) == 18
    print(f"Smoke test passed. Exported to: {exported}")


if __name__ == "__main__":
    main()
