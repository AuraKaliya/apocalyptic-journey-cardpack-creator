from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .constants import APP_TITLE
from .mod_io import export_mod_folder, import_mod_folder, load_project, save_project
from .models import Buff, Card, Project
from .script_codegen import lua_to_steps, steps_to_lua
from .script_model import (
    SCRIPT_FIELD_BY_LABEL,
    SCRIPT_FIELD_LABELS,
    STEP_KIND_BY_LABEL,
    STEP_KIND_LABELS,
    TARGET_BY_LABEL,
    TARGET_LABELS,
    EffectStep,
)
from .utils import clean_id, clean_mod_name, runtime_pack_id
from .validation import has_errors, validate_project


class CardPackEditor(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1220x780")
        self.minsize(1080, 700)

        self.project = Project()
        self.current_card_index: int | None = None
        self.current_buff_index: int | None = None
        self.card_vars: dict[str, tk.StringVar] = {}
        self.buff_vars: dict[str, tk.StringVar] = {}
        self.project_vars: dict[str, tk.StringVar] = {}
        self.card_texts: dict[str, tk.Text] = {}
        self.buff_texts: dict[str, tk.Text] = {}
        self.script_vars: dict[str, tk.StringVar] = {}
        self.visual_steps: list[EffectStep] = []
        self._preview_image: tk.PhotoImage | None = None
        self._loading = False

        self._build_menu()
        self._build_ui()
        self.load_project_into_ui(Project())

    def _build_menu(self) -> None:
        menu = tk.Menu(self)
        file_menu = tk.Menu(menu, tearoff=False)
        file_menu.add_command(label="新建项目", command=self.new_project)
        file_menu.add_separator()
        file_menu.add_command(label="导入 Mod 文件夹...", command=self.import_mod)
        file_menu.add_command(label="导出 Mod 文件夹...", command=self.export_mod)
        file_menu.add_separator()
        file_menu.add_command(label="打开编辑器项目 JSON...", command=self.open_project_file)
        file_menu.add_command(label="保存编辑器项目 JSON...", command=self.save_project_file)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.destroy)
        menu.add_cascade(label="文件", menu=file_menu)
        self.config(menu=menu)

    def _build_ui(self) -> None:
        root = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        root.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        left = ttk.Frame(root)
        right = ttk.Frame(root)
        root.add(left, weight=3)
        root.add(right, weight=2)

        self.notebook = ttk.Notebook(left)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.project_tab = ttk.Frame(self.notebook, padding=8)
        self.card_tab = ttk.Frame(self.notebook, padding=8)
        self.buff_tab = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(self.project_tab, text="卡包 / Mod")
        self.notebook.add(self.card_tab, text="卡牌")
        self.notebook.add(self.buff_tab, text="Buff / 状态")
        self.notebook.bind("<<NotebookTabChanged>>", lambda _event: self.update_preview())

        self._build_project_tab()
        self._build_card_tab()
        self._build_buff_tab()

        action_bar = ttk.Frame(left)
        action_bar.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(action_bar, text="导入 Mod", command=self.import_mod).pack(side=tk.LEFT)
        ttk.Button(action_bar, text="导出 Mod", command=self.export_mod).pack(side=tk.LEFT, padx=6)
        ttk.Button(action_bar, text="刷新预览", command=self.update_preview).pack(side=tk.RIGHT)

        ttk.Label(right, text="预览", font=("Microsoft YaHei UI", 14, "bold")).pack(anchor=tk.W)
        self.preview_image_label = ttk.Label(right, anchor=tk.CENTER)
        self.preview_image_label.pack(fill=tk.X, pady=(8, 8))
        self.preview_text = tk.Text(right, wrap=tk.WORD)
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        self.preview_text.configure(state=tk.DISABLED)

    def _build_project_tab(self) -> None:
        frame = self.project_tab
        frame.columnconfigure(1, weight=1)
        rows = [
            ("mod_name", "ModName / 文件夹名"),
            ("author", "作者"),
            ("version", "版本"),
            ("csv_name", "CSV 文件名"),
            ("pack_id", "卡包 Id"),
            ("pack_type", "卡包类型"),
            ("pack_name", "卡包名称"),
            ("pack_name_en", "英文名"),
            ("pack_name_hant", "繁中名"),
            ("pack_name_ja", "日文名"),
            ("workshop_visibility", "创意工坊可见性"),
        ]
        for index, (key, label) in enumerate(rows):
            self._entry(frame, index, label, self._project_var(key))
        self._file_entry(frame, len(rows), "Mod 图标", self._project_var("mod_icon_source"))
        self._file_entry(frame, len(rows) + 1, "卡包封面", self._project_var("pack_icon_source"))

        text_frame = ttk.Frame(frame)
        text_frame.grid(row=len(rows) + 2, column=0, columnspan=3, sticky=tk.NSEW, pady=(8, 0))
        frame.rowconfigure(len(rows) + 2, weight=1)
        self.project_text_mod_description = self._text_field(text_frame, "Mod 描述", 4)
        self.project_text_pack_description = self._text_field(text_frame, "卡包描述", 4)
        self.project_text_pack_description_en = self._text_field(text_frame, "卡包英文描述", 4)

    def _build_card_tab(self) -> None:
        pane = ttk.PanedWindow(self.card_tab, orient=tk.HORIZONTAL)
        pane.pack(fill=tk.BOTH, expand=True)
        list_frame = ttk.Frame(pane)
        form_outer = ttk.Frame(pane)
        pane.add(list_frame, weight=1)
        pane.add(form_outer, weight=3)

        self.card_list = tk.Listbox(list_frame)
        self.card_list.pack(fill=tk.BOTH, expand=True)
        self.card_list.bind("<<ListboxSelect>>", self.on_card_selected)
        buttons = ttk.Frame(list_frame)
        buttons.pack(fill=tk.X, pady=(6, 0))
        ttk.Button(buttons, text="新增", command=self.add_card).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(buttons, text="复制", command=self.duplicate_card).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        ttk.Button(buttons, text="删除", command=self.delete_card).pack(side=tk.LEFT, fill=tk.X, expand=True)

        form = self._scrollable_form(form_outer)
        fields = [
            ("card_id", "卡牌 Id"),
            ("card_type", "文本类型"),
            ("name", "名称"),
            ("name_en", "英文名"),
            ("name_hant", "繁中名"),
            ("name_ja", "日文名"),
            ("rarity", "稀有度"),
            ("expend", "费用"),
            ("tag", "标签"),
            ("base_script", "BaseScript"),
            ("effects", "特效路径"),
            ("action", "动作"),
            ("note", "备注"),
        ]
        for row, (key, label) in enumerate(fields):
            self._entry(form, row, label, self._card_var(key))
        self._file_entry(form, len(fields), "卡图资源", self._card_var("icon_source"))

        quick = ttk.Frame(form)
        quick.grid(row=len(fields) + 1, column=1, sticky=tk.W, pady=4)
        ttk.Label(form, text="快捷").grid(row=len(fields) + 1, column=0, sticky=tk.W)
        ttk.Button(quick, text="攻击牌", command=lambda: self.set_card_base("AttackCardItem")).pack(side=tk.LEFT)
        ttk.Button(quick, text="技能/能力牌", command=lambda: self.set_card_base("CommonCardItem")).pack(side=tk.LEFT, padx=6)

        self._build_script_builder(form, len(fields) + 2)

        text_frame = ttk.Frame(form)
        text_frame.grid(row=len(fields) + 3, column=0, columnspan=3, sticky=tk.EW)
        for key, label, height in [
            ("description", "中文描述", 4),
            ("description_hant", "繁中描述", 3),
            ("description_en", "英文描述", 3),
            ("description_ja", "日文描述", 3),
            ("init_script", "InitScript", 3),
            ("draw_script", "抽到时 DrawScript", 3),
            ("use_script", "使用时 UseScript", 5),
            ("drop_script", "弃置时 DropScript", 3),
        ]:
            self.card_texts[key] = self._text_field(text_frame, label, height)

    def _build_script_builder(self, parent: ttk.Frame, row: int) -> None:
        frame = ttk.LabelFrame(parent, text="可视化脚本编辑")
        frame.grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=(8, 4))
        frame.columnconfigure(1, weight=1)

        self.script_vars["field"] = tk.StringVar(value=SCRIPT_FIELD_LABELS["use_script"])
        self.script_vars["kind"] = tk.StringVar(value=STEP_KIND_LABELS["SetStatus"])
        self.script_vars["target"] = tk.StringVar(value=TARGET_LABELS["Self"])
        self.script_vars["value"] = tk.StringVar(value="1")
        self.script_vars["buff_id"] = tk.StringVar(value="")

        ttk.Label(frame, text="触发状态").grid(row=0, column=0, sticky=tk.W, padx=4, pady=3)
        trigger_combo = ttk.Combobox(
            frame,
            textvariable=self.script_vars["field"],
            values=list(SCRIPT_FIELD_BY_LABEL),
            state="readonly",
            width=18,
        )
        trigger_combo.grid(row=0, column=1, sticky=tk.W, pady=3)
        trigger_combo.bind("<<ComboboxSelected>>", lambda _event: self.parse_current_script_to_steps())

        ttk.Label(frame, text="动作").grid(row=0, column=2, sticky=tk.W, padx=4, pady=3)
        ttk.Combobox(
            frame,
            textvariable=self.script_vars["kind"],
            values=list(STEP_KIND_BY_LABEL),
            state="readonly",
            width=18,
        ).grid(
            row=0, column=3, sticky=tk.W, pady=3
        )
        ttk.Label(frame, text="目标").grid(row=1, column=0, sticky=tk.W, padx=4, pady=3)
        ttk.Combobox(frame, textvariable=self.script_vars["target"], values=list(TARGET_BY_LABEL), width=18).grid(
            row=1, column=1, sticky=tk.W, pady=3
        )
        ttk.Label(frame, text="数值").grid(row=1, column=2, sticky=tk.W, padx=4, pady=3)
        ttk.Entry(frame, textvariable=self.script_vars["value"], width=20).grid(row=1, column=3, sticky=tk.W, pady=3)
        ttk.Label(frame, text="Buff Id").grid(row=2, column=0, sticky=tk.W, padx=4, pady=3)
        ttk.Entry(frame, textvariable=self.script_vars["buff_id"], width=34).grid(row=2, column=1, columnspan=3, sticky=tk.W, pady=3)

        self.script_step_list = tk.Listbox(frame, height=5)
        self.script_step_list.grid(row=3, column=0, columnspan=4, sticky=tk.EW, padx=4, pady=(4, 2))
        self.script_status = ttk.Label(frame, text="选择触发状态后，可从对应脚本解析，也可由步骤生成脚本。")
        self.script_status.grid(row=4, column=0, columnspan=4, sticky=tk.W, padx=4)

        buttons = ttk.Frame(frame)
        buttons.grid(row=5, column=0, columnspan=4, sticky=tk.EW, pady=(4, 2))
        ttk.Button(buttons, text="添加步骤", command=self.add_visual_step).pack(side=tk.LEFT)
        ttk.Button(buttons, text="删除选中", command=self.delete_visual_step).pack(side=tk.LEFT, padx=4)
        ttk.Button(buttons, text="从当前脚本解析", command=self.parse_current_script_to_steps).pack(side=tk.LEFT, padx=4)
        ttk.Button(buttons, text="生成到当前脚本", command=self.write_steps_to_current_script).pack(side=tk.LEFT, padx=4)
        ttk.Button(buttons, text="清空步骤", command=self.clear_visual_steps).pack(side=tk.LEFT, padx=4)

    def _build_buff_tab(self) -> None:
        pane = ttk.PanedWindow(self.buff_tab, orient=tk.HORIZONTAL)
        pane.pack(fill=tk.BOTH, expand=True)
        list_frame = ttk.Frame(pane)
        form_outer = ttk.Frame(pane)
        pane.add(list_frame, weight=1)
        pane.add(form_outer, weight=3)

        self.buff_list = tk.Listbox(list_frame)
        self.buff_list.pack(fill=tk.BOTH, expand=True)
        self.buff_list.bind("<<ListboxSelect>>", self.on_buff_selected)
        buttons = ttk.Frame(list_frame)
        buttons.pack(fill=tk.X, pady=(6, 0))
        ttk.Button(buttons, text="新增", command=self.add_buff).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(buttons, text="复制", command=self.duplicate_buff).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        ttk.Button(buttons, text="删除", command=self.delete_buff).pack(side=tk.LEFT, fill=tk.X, expand=True)

        form = self._scrollable_form(form_outer)
        fields = [
            ("buff_id", "Buff Id"),
            ("name", "名称"),
            ("name_en", "英文名"),
            ("name_hant", "繁中名"),
            ("name_ja", "日文名"),
            ("reduce_per_turn", "每回合减少"),
            ("reduce_per_attacked", "受击减少"),
            ("reduce_per_use", "行动减少"),
            ("upper_bound", "层数上限"),
            ("icon", "图标路径"),
            ("buff_type", "类型"),
            ("rarity", "稀有度"),
            ("effects", "特效"),
            ("sound_effects", "音效"),
            ("action", "动作"),
            ("note", "备注"),
        ]
        for row, (key, label) in enumerate(fields):
            self._entry(form, row, label, self._buff_var(key))

        text_frame = ttk.Frame(form)
        text_frame.grid(row=len(fields), column=0, columnspan=3, sticky=tk.EW)
        for key, label, height in [
            ("description", "中文描述", 4),
            ("description_hant", "繁中描述", 3),
            ("description_en", "英文描述", 3),
            ("description_ja", "日文描述", 3),
            ("init_script", "InitScript", 3),
            ("apply_script", "ApplyScript", 5),
            ("clear_script", "ClearScript", 3),
        ]:
            self.buff_texts[key] = self._text_field(text_frame, label, height)

    def _scrollable_form(self, parent: ttk.Frame) -> ttk.Frame:
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        form = ttk.Frame(canvas)
        form.columnconfigure(1, weight=1)
        form.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=form, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        return form

    def _project_var(self, key: str) -> tk.StringVar:
        return self._var(self.project_vars, key)

    def _card_var(self, key: str) -> tk.StringVar:
        return self._var(self.card_vars, key)

    def _buff_var(self, key: str) -> tk.StringVar:
        return self._var(self.buff_vars, key)

    def _var(self, store: dict[str, tk.StringVar], key: str) -> tk.StringVar:
        var = tk.StringVar()
        store[key] = var
        var.trace_add("write", lambda *_: self.update_preview())
        return var

    def _entry(self, parent: ttk.Frame, row: int, label: str, var: tk.StringVar) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, padx=(0, 8), pady=3)
        ttk.Entry(parent, textvariable=var).grid(row=row, column=1, sticky=tk.EW, pady=3)

    def _file_entry(self, parent: ttk.Frame, row: int, label: str, var: tk.StringVar) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, padx=(0, 8), pady=3)
        ttk.Entry(parent, textvariable=var).grid(row=row, column=1, sticky=tk.EW, pady=3)
        ttk.Button(parent, text="选择", command=lambda: self.choose_file(var)).grid(row=row, column=2, padx=(6, 0))

    def _text_field(self, parent: ttk.Frame, label: str, height: int) -> tk.Text:
        ttk.Label(parent, text=label).pack(anchor=tk.W, pady=(8, 2))
        text = tk.Text(parent, wrap=tk.WORD, height=height)
        text.pack(fill=tk.X)
        text.bind("<<Modified>>", self.on_text_modified)
        return text

    def choose_file(self, var: tk.StringVar) -> None:
        file_name = filedialog.askopenfilename(
            title="选择资源",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.gif"), ("All files", "*.*")],
        )
        if file_name:
            var.set(file_name)

    def on_text_modified(self, event: tk.Event) -> None:
        widget = event.widget
        if isinstance(widget, tk.Text) and widget.edit_modified():
            widget.edit_modified(False)
            self.update_preview()

    def set_text(self, widget: tk.Text, value: str) -> None:
        widget.delete("1.0", tk.END)
        widget.insert("1.0", value or "")
        widget.edit_modified(False)

    def get_text(self, widget: tk.Text) -> str:
        return widget.get("1.0", tk.END).strip()

    def new_project(self) -> None:
        self.load_project_into_ui(Project())

    def load_project_into_ui(self, project: Project) -> None:
        self._loading = True
        self.project = project
        self.current_card_index = None
        self.current_buff_index = None
        for key, var in self.project_vars.items():
            var.set(str(getattr(project, key, "")))
        self.set_text(self.project_text_mod_description, project.mod_description)
        self.set_text(self.project_text_pack_description, project.pack_description)
        self.set_text(self.project_text_pack_description_en, project.pack_description_en)
        self.refresh_card_list()
        self.refresh_buff_list()
        self._loading = False
        if self.project.cards:
            self.select_card(0)
        if self.project.buffs:
            self.select_buff(0)
        self.update_preview()

    def save_project_from_ui(self) -> None:
        if self._loading:
            return
        if self.current_card_index is not None:
            self.save_current_card()
        if self.current_buff_index is not None:
            self.save_current_buff()
        for key, var in self.project_vars.items():
            setattr(self.project, key, var.get().strip())
        self.project.mod_name = clean_mod_name(self.project.mod_name)
        self.project.csv_name = clean_id(self.project.csv_name, "cards")
        self.project.pack_id = clean_id(self.project.pack_id, "cardpack_custom")
        self.project.mod_description = self.get_text(self.project_text_mod_description)
        self.project.pack_description = self.get_text(self.project_text_pack_description)
        self.project.pack_description_en = self.get_text(self.project_text_pack_description_en)

    def refresh_card_list(self) -> None:
        self.card_list.delete(0, tk.END)
        for card in self.project.cards:
            self.card_list.insert(tk.END, f"{card.card_id} - {card.name}")

    def refresh_buff_list(self) -> None:
        self.buff_list.delete(0, tk.END)
        for buff in self.project.buffs:
            self.buff_list.insert(tk.END, f"{buff.buff_id} - {buff.name}")

    def on_card_selected(self, _event: tk.Event) -> None:
        selection = self.card_list.curselection()
        if selection:
            self.select_card(selection[0])

    def select_card(self, index: int) -> None:
        if self.current_card_index is not None and not self._loading:
            self.save_current_card()
        self.current_card_index = index
        card = self.project.cards[index]
        self._loading = True
        for key, var in self.card_vars.items():
            var.set(str(getattr(card, key, "")))
        for key, widget in self.card_texts.items():
            self.set_text(widget, getattr(card, key, ""))
        script_field = self.current_script_field()
        self.visual_steps, unsupported = lua_to_steps(getattr(card, script_field))
        if hasattr(self, "script_step_list"):
            self.refresh_visual_steps()
            if unsupported:
                self.script_status.configure(text=f"当前脚本可识别 {len(self.visual_steps)} 步；另有 {len(unsupported)} 段自定义 Lua。")
        self.card_list.selection_clear(0, tk.END)
        self.card_list.selection_set(index)
        self._loading = False
        self.update_preview()

    def save_current_card(self) -> None:
        if self.current_card_index is None:
            return
        card = self.project.cards[self.current_card_index]
        for key, var in self.card_vars.items():
            setattr(card, key, var.get().strip())
        for key, widget in self.card_texts.items():
            setattr(card, key, self.get_text(widget))
        card.card_id = clean_id(card.card_id, f"card_{self.current_card_index + 1}")
        if not card.init_script:
            card.init_script = f'self.Vars:set_Item("BaseScript", "{card.base_script or "CommonCardItem"}");'
        self.refresh_card_list()
        self.card_list.selection_set(self.current_card_index)

    def add_card(self) -> None:
        self.save_current_card()
        index = len(self.project.cards) + 1
        self.project.cards.append(Card(card_id=f"card_{index}", name=f"新卡牌 {index}", name_en=f"New Card {index}"))
        self.refresh_card_list()
        self.select_card(len(self.project.cards) - 1)

    def duplicate_card(self) -> None:
        self.save_current_card()
        if self.current_card_index is None:
            return
        original = self.project.cards[self.current_card_index]
        clone = Card(**original.__dict__)
        clone.card_id = clean_id(f"{original.card_id}_copy", "card_copy")
        clone.name = f"{original.name} 副本"
        self.project.cards.append(clone)
        self.refresh_card_list()
        self.select_card(len(self.project.cards) - 1)

    def delete_card(self) -> None:
        if self.current_card_index is None or len(self.project.cards) <= 1:
            messagebox.showinfo("无法删除", "至少保留一张卡。")
            return
        del self.project.cards[self.current_card_index]
        self.current_card_index = None
        self.refresh_card_list()
        self.select_card(0)

    def set_card_base(self, base_script: str) -> None:
        self.card_vars["base_script"].set(base_script)
        self.set_text(self.card_texts["init_script"], f'self.Vars:set_Item("BaseScript", "{base_script}");')
        if base_script == "AttackCardItem" and not self.get_text(self.card_texts["use_script"]):
            self.set_text(self.card_texts["use_script"], 'self:SetStatus("Target"); self:Damage("6");')
        elif base_script == "CommonCardItem" and not self.get_text(self.card_texts["use_script"]):
            self.set_text(self.card_texts["use_script"], 'self:SetStatus("Self"); self:ChangeDefence("5");')

    def add_visual_step(self) -> None:
        step = EffectStep(
            kind=STEP_KIND_BY_LABEL.get(self.script_vars["kind"].get(), self.script_vars["kind"].get()),
            target=TARGET_BY_LABEL.get(self.script_vars["target"].get(), self.script_vars["target"].get()),
            value=self.script_vars["value"].get().strip(),
            buff_id=self.script_vars["buff_id"].get().strip(),
        )
        self.visual_steps.append(step)
        self.refresh_visual_steps()

    def delete_visual_step(self) -> None:
        selection = self.script_step_list.curselection()
        if not selection:
            return
        del self.visual_steps[selection[0]]
        self.refresh_visual_steps()

    def clear_visual_steps(self) -> None:
        self.visual_steps = []
        self.refresh_visual_steps()

    def current_script_field(self) -> str:
        label = self.script_vars.get("field", tk.StringVar(value=SCRIPT_FIELD_LABELS["use_script"])).get()
        return SCRIPT_FIELD_BY_LABEL.get(label, "use_script")

    def current_script_label(self) -> str:
        field = self.current_script_field()
        return SCRIPT_FIELD_LABELS.get(field, "使用时")

    def parse_current_script_to_steps(self) -> None:
        field = self.current_script_field()
        steps, unsupported = lua_to_steps(self.get_text(self.card_texts[field]))
        self.visual_steps = steps
        self.refresh_visual_steps()
        if unsupported:
            self.script_status.configure(
                text=f"{self.current_script_label()}：识别 {len(steps)} 步；有 {len(unsupported)} 段自定义 Lua 未转换。"
            )
        else:
            self.script_status.configure(text=f"{self.current_script_label()}：识别 {len(steps)} 步。")

    def write_steps_to_current_script(self) -> None:
        field = self.current_script_field()
        self.set_text(self.card_texts[field], steps_to_lua(self.visual_steps))
        self.script_status.configure(text=f"已生成到 {self.current_script_label()} 脚本。")
        self.update_preview()

    def refresh_visual_steps(self) -> None:
        self.script_step_list.delete(0, tk.END)
        for index, step in enumerate(self.visual_steps, start=1):
            self.script_step_list.insert(tk.END, f"{index}. {step.label()}")
        if not self.visual_steps:
            self.script_status.configure(text="尚未添加可视化步骤。")

    def on_buff_selected(self, _event: tk.Event) -> None:
        selection = self.buff_list.curselection()
        if selection:
            self.select_buff(selection[0])

    def select_buff(self, index: int) -> None:
        if self.current_buff_index is not None and not self._loading:
            self.save_current_buff()
        self.current_buff_index = index
        buff = self.project.buffs[index]
        self._loading = True
        for key, var in self.buff_vars.items():
            var.set(str(getattr(buff, key, "")))
        for key, widget in self.buff_texts.items():
            self.set_text(widget, getattr(buff, key, ""))
        self.buff_list.selection_clear(0, tk.END)
        self.buff_list.selection_set(index)
        self._loading = False
        self.update_preview()

    def save_current_buff(self) -> None:
        if self.current_buff_index is None or not self.project.buffs:
            return
        buff = self.project.buffs[self.current_buff_index]
        for key, var in self.buff_vars.items():
            setattr(buff, key, var.get().strip())
        for key, widget in self.buff_texts.items():
            setattr(buff, key, self.get_text(widget))
        buff.buff_id = clean_id(buff.buff_id, f"buff_{self.current_buff_index + 1}")
        self.refresh_buff_list()
        self.buff_list.selection_set(self.current_buff_index)

    def add_buff(self) -> None:
        self.save_current_buff()
        index = len(self.project.buffs) + 1
        self.project.buffs.append(Buff(buff_id=f"buff_{index}", name=f"新状态 {index}", name_en=f"New Buff {index}"))
        self.refresh_buff_list()
        self.select_buff(len(self.project.buffs) - 1)

    def duplicate_buff(self) -> None:
        self.save_current_buff()
        if self.current_buff_index is None or not self.project.buffs:
            return
        original = self.project.buffs[self.current_buff_index]
        clone = Buff(**original.__dict__)
        clone.buff_id = clean_id(f"{original.buff_id}_copy", "buff_copy")
        clone.name = f"{original.name} 副本"
        self.project.buffs.append(clone)
        self.refresh_buff_list()
        self.select_buff(len(self.project.buffs) - 1)

    def delete_buff(self) -> None:
        if self.current_buff_index is None or not self.project.buffs:
            return
        del self.project.buffs[self.current_buff_index]
        self.current_buff_index = None
        self.refresh_buff_list()
        if self.project.buffs:
            self.select_buff(0)
        self.update_preview()

    def selected_card_snapshot(self) -> Card | None:
        if self.current_card_index is None:
            return None
        card = Card(**self.project.cards[self.current_card_index].__dict__)
        for key, var in self.card_vars.items():
            setattr(card, key, var.get().strip())
        for key, widget in self.card_texts.items():
            setattr(card, key, self.get_text(widget))
        return card

    def selected_buff_snapshot(self) -> Buff | None:
        if self.current_buff_index is None or not self.project.buffs:
            return None
        buff = Buff(**self.project.buffs[self.current_buff_index].__dict__)
        for key, var in self.buff_vars.items():
            setattr(buff, key, var.get().strip())
        for key, widget in self.buff_texts.items():
            setattr(buff, key, self.get_text(widget))
        return buff

    def preview_project_snapshot(self) -> Project:
        project = Project.from_dict(self.project.to_dict())
        for key, var in self.project_vars.items():
            setattr(project, key, var.get().strip())
        project.mod_description = self.get_text(self.project_text_mod_description)
        project.pack_description = self.get_text(self.project_text_pack_description)
        project.pack_description_en = self.get_text(self.project_text_pack_description_en)
        card = self.selected_card_snapshot()
        if card is not None and self.current_card_index is not None:
            project.cards[self.current_card_index] = card
        buff = self.selected_buff_snapshot()
        if buff is not None and self.current_buff_index is not None:
            project.buffs[self.current_buff_index] = buff
        return project

    def update_preview(self) -> None:
        if self._loading or not hasattr(self, "preview_text"):
            return
        project = self.preview_project_snapshot()
        run_pack_id = runtime_pack_id(project.mod_name, project.csv_name, project.pack_id)
        card = self.selected_card_snapshot()
        buff = self.selected_buff_snapshot()
        issues = validate_project(project)

        lines = [
            "卡包预览",
            "=" * 32,
            f"Mod: {project.mod_name}",
            f"CSV: {project.csv_name}.csv",
            f"运行时卡包 Id: {run_pack_id}",
            f"卡包: {project.pack_name}",
            f"类型: {project.pack_type}",
            project.pack_description,
            "",
            f"卡牌数量: {len(self.project.cards)}",
            f"Buff 数量: {len(self.project.buffs)}",
        ]

        if card:
            init_script = card.init_script or f'self.Vars:set_Item("BaseScript", "{card.base_script or "CommonCardItem"}");'
            lines.extend([
                "",
                "当前卡牌预览",
                "=" * 32,
                f"[{card.card_type}] {card.name}",
                f"Id: {card.card_id}",
                f"运行时 Id: {project.mod_name}_{project.csv_name}_{card.card_id}",
                f"费用: {card.expend}    稀有度: {card.rarity}    标签: {card.tag or '-'}",
                "",
                card.description,
                "",
                "InitScript:",
                init_script,
                "",
                "抽到时 DrawScript:",
                card.draw_script or "(空)",
                "",
                "UseScript:",
                card.use_script or "(空)",
                "",
                "弃置时 DropScript:",
                card.drop_script or "(空)",
            ])

        if buff:
            lines.extend([
                "",
                "当前 Buff 预览",
                "=" * 32,
                f"{buff.name} ({buff.buff_id})",
                f"运行时 Id: {project.mod_name}_{project.csv_name}_{buff.buff_id}",
                f"类型: {buff.buff_type}    稀有度: {buff.rarity}    上限: {buff.upper_bound}",
                f"减少: 回合 {buff.reduce_per_turn} / 受击 {buff.reduce_per_attacked} / 行动 {buff.reduce_per_use}",
                f"图标: {buff.icon or '-'}",
                "",
                buff.description,
                "",
                "ApplyScript:",
                buff.apply_script or "(空)",
            ])

        lines.extend([
            "",
            "导出结构预览",
            "=" * 32,
            f"{project.mod_name}/",
            "  ModConfig.json",
            "  Icon.png",
            f"  Data/CardPack/{project.csv_name}.csv",
            f"  Text/CardPack/{project.csv_name}.csv",
            f"  Data/Card/{project.csv_name}.csv",
            f"  Text/Card/{project.csv_name}.csv",
        ])
        if project.buffs:
            lines.extend([
                f"  Data/Buff/{project.csv_name}.csv",
                f"  Text/Buff/{project.csv_name}.csv",
            ])
        lines.extend([
            "  ModResource/Images/CardPack/",
            f"  ModResource/Images/Card/{project.mod_name}/",
            "",
            "校验报告",
            "=" * 32,
        ])
        if issues:
            lines.extend(issue.label() for issue in issues)
        else:
            lines.append("未发现错误或警告。")

        self.preview_text.configure(state=tk.NORMAL)
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert("1.0", "\n".join(lines))
        self.preview_text.configure(state=tk.DISABLED)

        image_path = project.pack_icon_source
        try:
            tab_text = self.notebook.tab(self.notebook.select(), "text")
        except tk.TclError:
            tab_text = ""
        if "卡牌" in tab_text and card and card.icon_source:
            image_path = card.icon_source
        elif "Buff" in tab_text and buff and Path(buff.icon).is_file():
            image_path = buff.icon
        self.load_preview_image(image_path)

    def load_preview_image(self, image_path: str) -> None:
        self.preview_image_label.configure(image="", text="未选择预览图片")
        self._preview_image = None
        if not image_path or not Path(image_path).is_file():
            return
        try:
            image = tk.PhotoImage(file=image_path)
            max_w, max_h = 380, 280
            factor = max(1, int(max(image.width() / max_w, image.height() / max_h)))
            if factor > 1:
                image = image.subsample(factor, factor)
            self._preview_image = image
            self.preview_image_label.configure(image=image, text="")
        except tk.TclError:
            self.preview_image_label.configure(text="该图片格式无法在 Tkinter 中预览，但导出时会复制。")

    def import_mod(self) -> None:
        folder = filedialog.askdirectory(title="选择包含 ModConfig.json 的 Mod 文件夹")
        if not folder:
            return
        try:
            project = import_mod_folder(Path(folder))
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("导入失败", str(exc))
            return
        self.load_project_into_ui(project)
        messagebox.showinfo("导入完成", f"已导入 {project.mod_name}\n卡牌: {len(project.cards)}\nBuff: {len(project.buffs)}")

    def export_mod(self) -> None:
        self.save_project_from_ui()
        issues = validate_project(self.project)
        if has_errors(issues):
            messagebox.showerror("无法导出", "\n".join(issue.label() for issue in issues))
            return
        if issues:
            message = "\n".join(issue.label() for issue in issues)
            if not messagebox.askyesno("发现警告", f"{message}\n\n仍然继续导出吗？"):
                return
        folder = filedialog.askdirectory(title="选择导出父目录")
        if not folder:
            return
        target = Path(folder) / clean_mod_name(self.project.mod_name)
        overwrite = False
        if target.exists():
            overwrite = messagebox.askyesno("覆盖确认", f"{target} 已存在，是否删除并重新生成？")
            if not overwrite:
                return
        try:
            exported = export_mod_folder(self.project, Path(folder), overwrite=overwrite)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("导出失败", str(exc))
            return
        messagebox.showinfo("导出完成", f"已导出到:\n{exported}")

    def open_project_file(self) -> None:
        file_name = filedialog.askopenfilename(title="打开编辑器项目", filetypes=[("JSON", "*.json"), ("All files", "*.*")])
        if not file_name:
            return
        try:
            self.load_project_into_ui(load_project(Path(file_name)))
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("打开失败", str(exc))

    def save_project_file(self) -> None:
        self.save_project_from_ui()
        file_name = filedialog.asksaveasfilename(
            title="保存编辑器项目",
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All files", "*.*")],
        )
        if not file_name:
            return
        try:
            save_project(self.project, Path(file_name))
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("保存失败", str(exc))


def main() -> None:
    CardPackEditor().mainloop()
