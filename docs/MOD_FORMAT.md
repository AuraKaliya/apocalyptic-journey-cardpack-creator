# Mod Format Notes

The editor exports a pure data mod folder compatible with the structure used by `MoonRite`.

## Exported Structure

```text
<ModName>/
  ModConfig.json
  Icon.png
  README.md
  Data/
    CardPack/<csv_name>.csv
    Card/<csv_name>.csv
    Buff/<csv_name>.csv        # only when buffs exist
  Text/
    CardPack/<csv_name>.csv
    Card/<csv_name>.csv
    Buff/<csv_name>.csv        # only when buffs exist
  ModResource/
    Images/
      CardPack/
      Card/<ModName>/
```

## CSV Rules

Game CSV files keep two header rows:

1. Row 1 is the real field name row.
2. Row 2 is the Chinese comment/description row.
3. Row 3 and later contain data.

Script columns are Lua code and may contain commas and quotes, so CSV files are written with Python's `csv` module rather than manual string concatenation.

## Runtime IDs

The game prefixes mod data IDs as:

```text
<ModName>_<CsvFileName>_<OriginalId>
```

For a card pack:

```text
ModName: MoonRite
CSV: moonrite.csv
Original pack Id: cardpack_moonrite
Runtime pack Id: MoonRite_moonrite_cardpack_moonrite
```

Cards must use that runtime pack ID in `PackBelong`; otherwise the pack detail view can appear empty.

## Card Scripts

Cards must set `BaseScript` in `InitScript`:

```lua
self.Vars:set_Item("BaseScript", "AttackCardItem");
```

or:

```lua
self.Vars:set_Item("BaseScript", "CommonCardItem");
```

Use `AttackCardItem` for target-selecting attack cards and `CommonCardItem` for self-targeting skill or power cards.

