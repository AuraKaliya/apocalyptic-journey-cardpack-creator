from __future__ import annotations

from dataclasses import dataclass


TARGETS = ["Self", "Target", "AllEnemy", "AllRandomEnemy1"]
TARGET_LABELS = {
    "Self": "自己",
    "Target": "选中敌人",
    "AllEnemy": "所有敌人",
    "AllRandomEnemy1": "随机敌人",
}
TARGET_BY_LABEL = {label: value for value, label in TARGET_LABELS.items()}

STEP_KINDS = [
    "SetStatus",
    "Damage",
    "ChangeDefence",
    "ChangePower",
    "AddBuff",
    "RemoveBuff",
]
STEP_KIND_LABELS = {
    "SetStatus": "设置目标",
    "Damage": "造成伤害",
    "ChangeDefence": "获得格挡",
    "ChangePower": "改变魔能",
    "AddBuff": "添加 Buff",
    "RemoveBuff": "移除 Buff",
}
STEP_KIND_BY_LABEL = {label: value for value, label in STEP_KIND_LABELS.items()}

SCRIPT_FIELD_LABELS = {
    "draw_script": "抽到时",
    "use_script": "使用时",
    "drop_script": "弃置时",
}
SCRIPT_FIELD_BY_LABEL = {label: value for value, label in SCRIPT_FIELD_LABELS.items()}


def kind_label(kind: str) -> str:
    return STEP_KIND_LABELS.get(kind, kind)


def kind_from_label(label: str) -> str:
    return STEP_KIND_BY_LABEL.get(label, label)


def target_label(target: str) -> str:
    return TARGET_LABELS.get(target, target)


def target_from_label(label: str) -> str:
    return TARGET_BY_LABEL.get(label, label)


@dataclass
class EffectStep:
    kind: str
    target: str = ""
    value: str = ""
    buff_id: str = ""

    def label(self) -> str:
        if self.kind == "SetStatus":
            return f"设置目标：{target_label(self.target)}"
        if self.kind == "Damage":
            return f"造成伤害：{self.value}"
        if self.kind == "ChangeDefence":
            return f"获得格挡：{self.value}"
        if self.kind == "ChangePower":
            return f"改变魔能：{self.value}"
        if self.kind == "AddBuff":
            return f"添加 Buff：{self.buff_id} x {self.value}"
        if self.kind == "RemoveBuff":
            return f"移除 Buff：{self.buff_id}"
        return kind_label(self.kind)
