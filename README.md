# Apocalyptic Journey Card Pack Creator

一个用 Python/Tkinter 编写的《魔女：终末旅途》卡包编辑器。它用于创建、导入、预览和导出纯数据卡包 Mod：编辑 `ModConfig`、卡包、卡牌、可选 Buff/状态、图片资源，并导出为游戏可以直接读取的 Mod 文件夹。

项目以 `MoonRite` 这种纯数据卡包为参考：不默认生成 DLL，也不默认生成 Lua 入口 Hook。对“新增一套卡牌/状态/卡包封面”的场景，优先生成稳定、轻量的 CSV + 资源文件结构。

## 运行

```powershell
cd apocalyptic-journey-cardpack-creator
python cardpack_editor.py
```

也可以双击 `run_editor.bat`。

也支持模块方式启动：

```powershell
python -m card_pack_editor
```

## 工程结构

```text
CardPackEditor/
  cardpack_editor.py          # 兼容旧入口的薄启动器
  run_editor.bat              # Windows 双击启动
  card_pack_editor/
    app.py                    # Tkinter GUI
    mod_io.py                 # 导入/导出真实 Mod 文件夹、保存/打开编辑器项目
    models.py                 # Project/Card/Buff 数据模型
    constants.py              # 游戏 CSV 表头和说明行
    utils.py                  # CSV、路径、Id、资源复制工具
    __main__.py               # python -m card_pack_editor
  tests/
    smoke_test.py             # 使用 MoonRite 做导入/导出烟测
  docs/
    MOD_FORMAT.md             # 导出的 Mod 文件结构说明
```

## 能做什么

- 创建卡包基础信息：`ModName`、作者、版本、卡包 Id、卡包名称、描述、封面。
- 创建和管理卡牌：Id、费用、稀有度、标签、名称、多语言描述、图片、脚本、特效和动作字段。
- 自动生成卡牌 `PackBelong`，格式为 `ModName_CsvFileName_CardPackId`。
- 自动按攻击牌/技能牌补充 `BaseScript`。
- 创建可选 Buff/状态：脚本、层数规则、文本和表现字段。
- 导入已有 Mod 文件夹，例如 `MoonRite`。
- 保存/打开编辑器项目 JSON，便于中途继续编辑。
- 预览当前卡牌文本和图片；PNG/GIF 可直接显示，JPG 会保留路径并在导出时复制。
- 导出实际 Mod 文件夹，包含：
  - `ModConfig.json`
  - `Data/CardPack/*.csv`
  - `Text/CardPack/*.csv`
  - `Data/Card/*.csv`
  - `Text/Card/*.csv`
  - `Data/Buff/*.csv` 和 `Text/Buff/*.csv`，如果创建了 Buff
  - `ModResource/Images/...`
  - `Icon.png`

## 导入 / 导出

导入时选择包含 `ModConfig.json` 的实际 Mod 根目录，例如：

```text
path\to\MoonRite
```

编辑器会读取：

- `ModConfig.json`
- `Data/CardPack/*.csv` 和 `Text/CardPack/*.csv`
- `Data/Card/*.csv` 和 `Text/Card/*.csv`
- `Data/Buff/*.csv` 和 `Text/Buff/*.csv`
- `Mods/<ModName>/...` 形式的图片资源路径

导出时选择“父目录”，编辑器会在里面生成 `<ModName>/` 文件夹。若同名目录已存在，界面会询问是否删除并重新生成。

## MoonRite 烟测

可以用内置烟测脚本验证导入/导出链路：

```powershell
python tests\smoke_test.py --moonrite path\to\MoonRite
```

通过时会输出临时导出目录。

## 开发检查

```powershell
$files = @('cardpack_editor.py') + (Get-ChildItem card_pack_editor -Filter *.py | ForEach-Object { $_.FullName }) + (Get-ChildItem tests -Filter *.py | ForEach-Object { $_.FullName })
python -m py_compile @files
```

核心格式说明见 [docs/MOD_FORMAT.md](docs/MOD_FORMAT.md)。

## 使用建议

1. `ModName` 使用英文、数字或下划线，并保持和导出后的文件夹名一致。
2. `CSV 文件名` 会参与运行时 Id。例如：

   ```text
   YourMod_cards_cardpack_yourpack
   ```

3. 卡牌脚本字段必须写 Lua。常用模板：

   ```lua
   self:SetStatus("Target"); self:Damage("6");
   ```

   ```lua
   self:SetStatus("Self"); self:ChangeDefence("8");
   ```

4. 引用自己 Mod 里的 Buff 时，要用运行时 Id：

   ```text
   YourMod_cards_your_buff_id
   ```

5. 导出后把生成的 Mod 文件夹放进：

   ```text
   ...\Witch's Apocalyptic Journey_Data\Mods\
   ```

6. 在游戏里启用 Mod，进入卡包选择界面确认卡包出现，右键确认卡牌列表不为空。

## 说明

这个编辑器按 `MoonRite` 的可行结构生成纯数据 Mod，不生成 DLL，也不默认生成 `Scripts/Entry.lua`。如果你后续要做 UI Hook、资源重定向或复杂全局逻辑，可以在导出的 Mod 上再手动添加脚本入口。
