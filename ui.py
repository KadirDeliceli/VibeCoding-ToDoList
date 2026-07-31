from __future__ import annotations
import sqlite3
import customtkinter as ctk

from models import Todo
from database import Database

FONT = "Segoe UI"

ACCENT = ("#2E8B66", "#35A97E")
ACCENT_HOVER = ("#257150", "#2C8F6A")
SURFACE = ("#FFFFFF", "#20242B")
BG = ("#EFF0F3", "#15171C")
HOVER = ("#E7E9EE", "#2A2E37")
TEXT = ("#1F2937", "#E6E9EF")
SUBTLE = ("#6B7280", "#98A2B3")
DANGER_BG = ("#FCE8E8", "#54272A")
DANGER_FG = ("#C0392B", "#F0716B")


class TodoUI(ctk.CTk):
    def __init__(self, db: Database) -> None:
        super().__init__(fg_color=BG)
        self.db = db
        self.selected_category_id: int | None = None  # None => "Tümü / All"

        self.title("To-Do List")
        self.geometry("820x580")
        self.minsize(680, 520)

        self._build_widgets()
        self._refresh_categories()
        self._refresh_tasks()

    # ------------------------------------------------------------------ build
    def _build_widgets(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- LEFT: categories ---
        left = ctk.CTkFrame(self, corner_radius=16, fg_color=SURFACE)
        left.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=16)
        left.grid_rowconfigure(3, weight=1)
        left.grid_columnconfigure(0, weight=1)
        left.configure(width=220)

        ctk.CTkLabel(
            left, text="Kategoriler",
            font=(FONT, 15, "bold"),
            text_color=TEXT, anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 6))

        cat_top = ctk.CTkFrame(left, fg_color="transparent")
        cat_top.grid(row=1, column=0, sticky="ew", padx=12, pady=4)
        cat_top.grid_columnconfigure(0, weight=1)
        self.cat_entry = ctk.CTkEntry(
            cat_top, placeholder_text="Yeni kategori...",
            height=36, corner_radius=10,
            font=(FONT, 13),
        )
        self.cat_entry.grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(
            cat_top, text="Ekle", width=64, height=36, corner_radius=10,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            text_color=("#FFFFFF", "#FFFFFF"),
            font=(FONT, 13, "bold"),
            command=self._on_add_category,
        ).grid(row=0, column=1, padx=(6, 0))

        self.cat_list = ctk.CTkScrollableFrame(
            left, label_text="", fg_color="transparent"
        )
        self.cat_list.grid(row=2, column=0, sticky="nsew", padx=8, pady=(6, 10))
        self.cat_list.grid_columnconfigure(0, weight=1)
        self.cat_buttons: dict[int | None, ctk.CTkButton] = {}
        self._cat_defaults: dict[int, dict] = {}

        # --- RIGHT: tasks ---
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(0, 16), pady=16)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(right, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            header, text="Yapılacaklar",
            font=(FONT, 22, "bold"),
            text_color=TEXT, anchor="w",
        )
        self.title_label.grid(row=0, column=0, sticky="w")

        self.theme_btn = ctk.CTkButton(
            header, width=110, height=34, corner_radius=10,
            fg_color="transparent", hover_color=HOVER,
            text_color=TEXT, font=(FONT, 13),
            text="☀ Aydınlık",
            command=self._toggle_theme,
        )
        self.theme_btn.grid(row=0, column=1, sticky="e")

        nav = ctk.CTkFrame(right, fg_color="transparent")
        nav.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        nav.grid_columnconfigure(2, weight=1)

        self.back_btn = ctk.CTkButton(
            nav, text="← Geri", width=84, height=32, corner_radius=10,
            fg_color="transparent", hover_color=HOVER,
            text_color=SUBTLE, font=(FONT, 13),
            command=self._on_back,
        )
        self.back_btn.grid(row=0, column=0, sticky="w")
        self.back_btn.grid_remove()

        task_input = ctk.CTkFrame(nav, fg_color="transparent")
        task_input.grid(row=0, column=2, sticky="ew")
        task_input.grid_columnconfigure(0, weight=1)
        task_input.grid_columnconfigure(1, weight=1)
        task_input.grid_columnconfigure(2, weight=0)
        self.task_entry = ctk.CTkEntry(
            task_input, placeholder_text="Yeni görev...",
            height=36, corner_radius=10,
            font=(FONT, 13),
        )
        self.task_entry.grid(row=0, column=0, sticky="ew")
        self.task_time_entry = ctk.CTkEntry(
            task_input, placeholder_text="Saat aralığı (opsiyonel)",
            height=36, corner_radius=10,
            font=(FONT, 13),
        )
        self.task_time_entry.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        ctk.CTkButton(
            task_input, text="Ekle", width=72, height=36, corner_radius=10,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            text_color=("#FFFFFF", "#FFFFFF"),
            font=(FONT, 13, "bold"),
            command=self._on_add_task,
        ).grid(row=0, column=2, sticky="w", padx=(8, 0))

        self.task_list = ctk.CTkScrollableFrame(
            right, label_text="", fg_color="transparent"
        )
        self.task_list.grid(row=2, column=0, sticky="nsew", pady=(14, 8))
        self.task_list.grid_columnconfigure(1, weight=1)
        self.task_list.grid_columnconfigure(3, weight=0)

        self.status = ctk.CTkLabel(
            right, text="0 görev",
            anchor="w", text_color=SUBTLE, font=(FONT, 12),
        )
        self.status.grid(row=3, column=0, sticky="ew", pady=(0, 4))

        self.row_widgets: dict[int, dict] = {}

    # ----------------------------------------------------------------- categories
    def _on_add_category(self) -> None:
        name = self.cat_entry.get().strip()
        if not name:
            return
        try:
            self.db.add_category(name)
        except sqlite3.IntegrityError:
            return  # duplicate name
        self.cat_entry.delete(0, "end")
        self._refresh_categories()

    def _category_button(self, text: str, command) -> ctk.CTkButton:
        return ctk.CTkButton(
            self.cat_list, text=text, anchor="w",
            height=34, corner_radius=10,
            fg_color="transparent", hover_color=HOVER,
            text_color=TEXT, font=(FONT, 13),
            command=command,
        )

    def _refresh_categories(self) -> None:
        for widget in self.cat_list.winfo_children():
            widget.destroy()

        self.cat_buttons.clear()
        self._cat_defaults.clear()

        all_btn = self._category_button(
            "📋 Tümü", lambda: self._select_category(None)
        )
        all_btn.grid(row=0, column=0, sticky="ew", pady=2)
        self.cat_buttons[None] = all_btn

        for i, row in enumerate(self.db.get_categories(), start=1):
            cid, name = row["id"], row["name"]
            b = self._category_button(name, lambda c=cid: self._select_category(c))
            b.grid(row=i, column=0, sticky="ew", pady=2)
            self._cat_defaults[cid] = {
                "fg_color": b.cget("fg_color"),
                "hover_color": b.cget("hover_color"),
                "text_color": b.cget("text_color"),
            }
            self.cat_buttons[cid] = b

            if name not in ["Genel", "Tümü"]:
                del_btn = ctk.CTkButton(
                    self.cat_list, text="✕", width=28, height=34,
                    corner_radius=10,
                    fg_color="transparent", hover_color=DANGER_BG,
                    text_color=SUBTLE, font=(FONT, 12, "bold"),
                    command=lambda c=cid, n=name: self._on_delete_category(c, n),
                )
                del_btn.grid(row=i, column=1, sticky="e", padx=(4, 0))

        self._highlight_categories()

    def _highlight_categories(self) -> None:
        for key, b in self.cat_buttons.items():
            if not b.winfo_exists():
                continue
            if key == self.selected_category_id:
                b.configure(
                    fg_color=ACCENT, hover_color=ACCENT_HOVER,
                    text_color=("#FFFFFF", "#FFFFFF"),
                )
            elif key in self._cat_defaults:
                b.configure(**self._cat_defaults[key])

    def _select_category(self, category_id: int | None) -> None:
        self.selected_category_id = category_id
        self._highlight_categories()
        if category_id is not None:
            self.back_btn.grid()
            name = dict((r["id"], r["name"]) for r in self.db.get_categories()).get(category_id, "")
            self.title_label.configure(text=name)
        else:
            self.back_btn.grid_remove()
            self.title_label.configure(text="Yapılacaklar")
        self._refresh_tasks()

    def _on_delete_category(self, category_id: int, category_name: str) -> None:
        from tkinter.messagebox import askyesno

        if not askyesno("Onay", f"{category_name} kategorisini silmek istediğinizden emin misiniz?\nBu kategoriye bağlı tüm görevler silinecek."):
            return

        self.db.delete_category(category_id, category_name)
        if self.selected_category_id == category_id:
            self.selected_category_id = None
            self.back_btn.grid_remove()
            self.title_label.configure(text="Yapılacaklar")
        self._refresh_categories()
        self._refresh_tasks()

    def _on_back(self) -> None:
        self._select_category(None)

    # -------------------------------------------------------------------- tasks
    def _on_add_task(self) -> None:
        title = self.task_entry.get().strip()
        time_range = self.task_time_entry.get().strip() if hasattr(self, 'task_time_entry') else None

        if not title:
            return

        self.db.add(title, category_id=self.selected_category_id, time_range=time_range if time_range else None)
        self.task_entry.delete(0, "end")
        if hasattr(self, 'task_time_entry'):
            self.task_time_entry.delete(0, "end")
        self._refresh_tasks()

    def _on_toggle_task(self, todo: Todo, cb: ctk.CTkCheckBox) -> None:
        def apply() -> None:
            self.db.update(todo.id, completed=bool(cb.get()))
            self._refresh_tasks()
        cb.after(0, apply)

    def _on_delete_task(self, todo: Todo) -> None:
        from tkinter.messagebox import askyesno

        if not askyesno("Onay", f"'{todo.title}' görevini silmek istediğinizden emin misiniz?"):
            return

        self.db.delete(todo.id)
        self._refresh_tasks()

    # ----------------------------------------------------------------- rendering
    def _refresh_tasks(self) -> None:
        for widgets in self.row_widgets.values():
            for w in widgets.values():
                w.destroy()
        self.row_widgets.clear()

        todos = self.db.get_all(self.selected_category_id)
        completed = sum(1 for t in todos if t.completed)

        for index, todo in enumerate(todos):
            self._add_task_row(index, todo)

        self.status.configure(
            text=f"{len(todos)} görev • {len(todos) - completed} bekliyor"
        )

    def _add_task_row(self, index: int, todo: Todo) -> None:
        cb_text = todo.title
        if todo.time_range:
            cb_text = f"{todo.title} ({todo.time_range})"

        cb = ctk.CTkCheckBox(
            self.task_list, text=cb_text,
            corner_radius=6, border_width=2,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            font=(FONT, 13),
            text_color=SUBTLE if todo.completed else TEXT,
            command=lambda: self._on_toggle_task(todo, cb),
        )
        cb.grid(row=index, column=1, sticky="ew", padx=4, pady=3)
        cb.select() if todo.completed else cb.deselect()

        del_btn = ctk.CTkButton(
            self.task_list, text="Sil", width=56, height=28,
            corner_radius=10,
            fg_color="transparent", hover_color=DANGER_BG,
            text_color=DANGER_FG, font=(FONT, 12, "bold"),
            command=lambda: self._on_delete_task(todo),
        )
        del_btn.grid(row=index, column=2, sticky="ew", padx=(8, 0), pady=3)

        self.row_widgets[todo.id] = {"cb": cb, "del": del_btn}

    # ------------------------------------------------------------------ theme
    def _toggle_theme(self) -> None:
        is_light = ctk.get_appearance_mode().lower() == "light"
        ctk.set_appearance_mode("dark" if is_light else "light")
        self.theme_btn.configure(text="☀ Aydınlık" if is_light else "☾ Karanlık")
        self._refresh_categories()
        self._refresh_tasks()
