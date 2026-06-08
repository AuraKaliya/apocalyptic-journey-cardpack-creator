from __future__ import annotations

from dataclasses import dataclass


TARGETS = ["Self", "Target", "AllEnemy", "AllRandomEnemy1"]

STEP_KINDS = [
    "SetStatus",
    "Damage",
    "ChangeDefence",
    "ChangePower",
    "AddBuff",
    "RemoveBuff",
]


@dataclass
class EffectStep:
    kind: str
    target: str = ""
    value: str = ""
    buff_id: str = ""

    def label(self) -> str:
        if self.kind == "SetStatus":
            return f"Set target: {self.target}"
        if self.kind == "Damage":
            return f"Deal damage: {self.value}"
        if self.kind == "ChangeDefence":
            return f"Gain block: {self.value}"
        if self.kind == "ChangePower":
            return f"Change power: {self.value}"
        if self.kind == "AddBuff":
            return f"Add buff: {self.buff_id} x {self.value}"
        if self.kind == "RemoveBuff":
            return f"Remove buff: {self.buff_id}"
        return self.kind

