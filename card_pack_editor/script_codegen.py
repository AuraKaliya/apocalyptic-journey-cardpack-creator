from __future__ import annotations

import csv
import io
import re

from .script_model import EffectStep


CALL_RE = re.compile(r"self:(?P<name>\w+)\((?P<args>.*?)\)\s*;?", re.DOTALL)


def steps_to_lua(steps: list[EffectStep]) -> str:
    lines: list[str] = []
    for step in steps:
        if step.kind == "SetStatus":
            lines.append(f'self:SetStatus("{step.target or "Self"}");')
        elif step.kind == "Damage":
            lines.append(f'self:Damage("{step.value or "0"}");')
        elif step.kind == "ChangeDefence":
            lines.append(f'self:ChangeDefence("{step.value or "0"}");')
        elif step.kind == "ChangePower":
            lines.append(f'self:ChangePower("{step.value or "0"}");')
        elif step.kind == "AddBuff":
            lines.append(f'self:AddBuff("{step.buff_id}", "{step.value or "1"}");')
        elif step.kind == "RemoveBuff":
            lines.append(f'self:RemoveBuff("{step.buff_id}");')
    return " ".join(lines)


def lua_to_steps(lua: str) -> tuple[list[EffectStep], list[str]]:
    steps: list[EffectStep] = []
    unsupported: list[str] = []
    for match in CALL_RE.finditer(lua or ""):
        name = match.group("name")
        args = _parse_args(match.group("args"))
        if name == "SetStatus" and args:
            steps.append(EffectStep("SetStatus", target=args[0]))
        elif name == "Damage" and args:
            steps.append(EffectStep("Damage", value=args[0]))
        elif name == "ChangeDefence" and args:
            steps.append(EffectStep("ChangeDefence", value=args[0]))
        elif name == "ChangePower" and args:
            steps.append(EffectStep("ChangePower", value=args[0]))
        elif name == "AddBuff" and len(args) >= 2:
            steps.append(EffectStep("AddBuff", buff_id=args[0], value=args[1]))
        elif name == "RemoveBuff" and args:
            steps.append(EffectStep("RemoveBuff", buff_id=args[0]))
        else:
            unsupported.append(match.group(0).strip())
    return steps, unsupported


def _parse_args(args: str) -> list[str]:
    reader = csv.reader(io.StringIO(args), skipinitialspace=True)
    try:
        row = next(reader)
    except StopIteration:
        return []
    return [item.strip().strip('"').strip("'") for item in row]

