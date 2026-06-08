from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class Card:
    card_id: str = "new_card"
    card_type: str = "技能牌"
    name: str = "新卡牌"
    name_en: str = "New Card"
    name_hant: str = ""
    name_ja: str = ""
    description: str = "描述这张卡的效果。"
    description_hant: str = ""
    description_en: str = ""
    description_ja: str = ""
    rarity: str = "1"
    expend: str = "1"
    tag: str = ""
    base_script: str = "CommonCardItem"
    init_script: str = ""
    draw_script: str = ""
    use_script: str = 'self:SetStatus("Self"); self:ChangeDefence("5");'
    drop_script: str = ""
    icon_source: str = ""
    effects: str = ""
    action: str = ""
    note: str = ""
    done: str = "TRUE"


@dataclass
class Buff:
    buff_id: str = "new_buff"
    name: str = "新状态"
    name_en: str = "New Buff"
    name_hant: str = ""
    name_ja: str = ""
    description: str = "描述这个状态。"
    description_hant: str = ""
    description_en: str = ""
    description_ja: str = ""
    init_script: str = ""
    apply_script: str = ""
    clear_script: str = ""
    reduce_per_turn: str = "0"
    reduce_per_attacked: str = "0"
    reduce_per_use: str = "0"
    upper_bound: str = "99"
    icon: str = "Icon/Buff/启示"
    buff_type: str = "能力"
    rarity: str = "2"
    effects: str = ""
    sound_effects: str = ""
    action: str = ""
    note: str = ""


@dataclass
class Project:
    mod_name: str = "YourCardPack"
    author: str = "YOUR_NAME"
    version: str = "0.1"
    mod_description: str = "新增一个自定义卡包。"
    mod_icon_source: str = ""
    csv_name: str = "cards"
    pack_id: str = "cardpack_yourpack"
    pack_type: str = "Normal"
    pack_name: str = "自定义卡包"
    pack_name_en: str = "Custom Card Pack"
    pack_name_hant: str = ""
    pack_name_ja: str = ""
    pack_description: str = "一组自定义卡牌。"
    pack_description_hant: str = ""
    pack_description_en: str = ""
    pack_description_ja: str = ""
    pack_icon_source: str = ""
    workshop_visibility: str = "Private"
    cards: list[Card] = field(default_factory=lambda: [Card()])
    buffs: list[Buff] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Project":
        cards = [Card(**item) for item in data.get("cards", [])]
        buffs = [Buff(**item) for item in data.get("buffs", [])]
        fields = {key: value for key, value in data.items() if key not in {"cards", "buffs"}}
        project = cls(**fields)
        project.cards = cards or [Card()]
        project.buffs = buffs
        return project

