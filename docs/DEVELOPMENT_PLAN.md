# Development Plan

This plan turns the creator from a CSV form editor into a card-pack authoring workbench.

## Goals

- Preview the pack, cards, buffs, runtime IDs, and exported folder structure before export.
- Provide visual script editing for common card and buff effects while preserving raw Lua editing for advanced users.
- Validate common mod errors before export.
- Keep import/export compatible with existing pure-data mods such as `MoonRite`.

## Phase 1: Preview And Safety

- Add pack cover preview:
  - cover image path
  - pack name, type, description
  - card and buff counts
- Add card preview:
  - image, name, type, cost, rarity, tags
  - description
  - `InitScript` and `UseScript`
- Add buff preview:
  - icon/path
  - name, type, rarity, upper bound
  - reduction rules and scripts
- Add export preview:
  - generated folder tree
  - runtime pack ID
  - card runtime IDs
  - buff runtime IDs
- Add validation:
  - invalid or duplicate IDs
  - missing cards
  - missing scripts
  - missing resources
  - suspicious `BaseScript` mismatch
  - missing referenced buffs in common `AddBuff` calls

## Phase 2: Visual Script Editing

Add a structured effect-chain editor backed by a small intermediate representation.

Initial supported steps:

- `SetStatus`
- `Damage`
- `ChangeDefence`
- `ChangePower`
- `AddBuff`
- `RemoveBuff`

Conversion rules:

- Visual steps -> Lua must be reliable.
- Lua -> visual steps is best effort and only supports known simple patterns.
- Unsupported Lua remains editable in raw source mode.

New modules:

```text
card_pack_editor/
  script_model.py      # EffectStep and supported operations
  script_codegen.py    # visual steps <-> Lua
  validation.py        # project validation before export
```

## Phase 3: Buff Script Templates

- End-of-turn damage by stack count.
- Start-of-turn gain block/power/buff.
- Decrease stacks and remove at zero.
- Event templates for supported fight events.

## Phase 4: Resource Management

- Resource browser for pack cover, card images, and buff icons.
- Missing resource report.
- Open resource location.
- Consistent export copy behavior.

## Phase 5: Project Workflow

- Recent projects.
- Autosave draft JSON.
- Field help/tooltips.
- Template library for common cards and archetypes.

## Current Implementation Target

The immediate target is Phase 1 plus the first slice of Phase 2:

- pack/card/buff/export preview in the existing right-side panel
- validation report in preview and before export
- visual card `UseScript` builder for common effect chains
- best-effort parser for existing simple `UseScript`

