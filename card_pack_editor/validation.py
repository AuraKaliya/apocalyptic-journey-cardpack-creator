from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .models import Project
from .utils import clean_id, clean_mod_name, runtime_pack_id


ADD_BUFF_RE = re.compile(r'AddBuff\("(?P<buff>[^"]+)"')


@dataclass
class ValidationIssue:
    severity: str
    message: str

    def label(self) -> str:
        return f"[{self.severity.upper()}] {self.message}"


def validate_project(project: Project) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if clean_mod_name(project.mod_name) != project.mod_name:
        issues.append(ValidationIssue("error", "ModName should contain only letters, digits, and underscores."))
    if clean_id(project.csv_name, "cards") != project.csv_name:
        issues.append(ValidationIssue("error", "CSV file name should contain only letters, digits, and underscores."))
    if clean_id(project.pack_id, "cardpack_custom") != project.pack_id:
        issues.append(ValidationIssue("error", "Card pack ID should contain only letters, digits, and underscores."))
    if not project.cards:
        issues.append(ValidationIssue("error", "At least one card is required."))

    card_ids: set[str] = set()
    for card in project.cards:
        if card.card_id in card_ids:
            issues.append(ValidationIssue("error", f"Duplicate card ID: {card.card_id}"))
        card_ids.add(card.card_id)
        if clean_id(card.card_id, "card") != card.card_id:
            issues.append(ValidationIssue("error", f"Invalid card ID: {card.card_id}"))
        if not card.name:
            issues.append(ValidationIssue("warning", f"Card {card.card_id} has no name."))
        if not card.use_script:
            issues.append(ValidationIssue("warning", f"Card {card.card_id} has empty UseScript."))
        if "攻击" in card.card_type and "AttackCardItem" not in card.init_script:
            issues.append(ValidationIssue("warning", f"Attack card {card.card_id} does not use AttackCardItem."))
        if "技能" in card.card_type and "CommonCardItem" not in card.init_script:
            issues.append(ValidationIssue("warning", f"Skill card {card.card_id} does not use CommonCardItem."))
        if card.icon_source and not Path(card.icon_source).is_file():
            issues.append(ValidationIssue("warning", f"Card image is missing: {card.card_id}"))

    buff_ids = {buff.buff_id for buff in project.buffs}
    runtime_buff_ids = {f"{project.mod_name}_{project.csv_name}_{buff_id}" for buff_id in buff_ids}
    for buff in project.buffs:
        if clean_id(buff.buff_id, "buff") != buff.buff_id:
            issues.append(ValidationIssue("error", f"Invalid buff ID: {buff.buff_id}"))
        if not buff.name:
            issues.append(ValidationIssue("warning", f"Buff {buff.buff_id} has no name."))

    for card in project.cards:
        for match in ADD_BUFF_RE.finditer(card.use_script or ""):
            buff_ref = match.group("buff")
            if buff_ref not in buff_ids and buff_ref not in runtime_buff_ids:
                issues.append(ValidationIssue("warning", f"Card {card.card_id} references unknown buff: {buff_ref}"))

    if project.pack_icon_source and not Path(project.pack_icon_source).is_file():
        issues.append(ValidationIssue("warning", "Pack cover image path does not exist."))
    if project.mod_icon_source and not Path(project.mod_icon_source).is_file():
        issues.append(ValidationIssue("warning", "Mod icon path does not exist."))

    run_pack_id = runtime_pack_id(project.mod_name, project.csv_name, project.pack_id)
    if not run_pack_id:
        issues.append(ValidationIssue("error", "Runtime pack ID could not be generated."))
    return issues


def has_errors(issues: list[ValidationIssue]) -> bool:
    return any(issue.severity == "error" for issue in issues)

