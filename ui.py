from __future__ import annotations
import sqlite3
import customtkinter as ctk

from models import Todo
from database import Database


class TodoUI(ctk.CTk):
    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db
        self.selected_category_id: int | None = None  # None => "Tümü / All"

        self.title("To-Do List")
        self.geometry("760x560")
        self.minsize(640, 500)

        self._build_widgets()
        self._refresh_categories()
        self._refresh_tasks()

    # ------------------------------------------------------------------ build
    def _build_widgets(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- LEFT: categories ---
        left = ctk.CTkFrame(self, corner_radius=0)
        left.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=16)
        left.grid_rowconfigure(3, weight=1)
        left.grid_columnconfigure(0, weight=1)
        left.configure(width=200)

        ctk.CTkLabel(left, text="Kategoriler", font=("Arial", 14, "bold")).grid(
            row=0, column=0, sticky="w", padx=10, pady=(12, 4)
        )

        cat_top = ctk.CTkFrame(left, fg_color="transparent")
        cat_top.grid(row=1, column=0, sticky="ew", padx=10, pady=4)
        cat_top.grid_columnconfigure(0, weight=1)
        self.cat_entry = ctk.CTkEntry(cat_top, placeholder_text="Yeni kategori...")
        self.cat_entry.grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(
            cat_top, text="Ekle", width=70, command=self._on_add_category
        ).grid(row=0, column=0, sticky="e", padx=(8, 0))

        self.cat_list = ctk.CTkScrollableFrame(left, label_text="")
        self.cat_list.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 8))
        self.cat_list.grid_columnconfigure(0, weight=1)
        self.cat_buttons: dict[int | None, ctk.CTkButton] = {}
        self._cat_default_fg: dict[int, object] = {}

        # --- RIGHT: tasks ---
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(0, 16), pady=16)
        right.grid_columnconfigure(1, weight=1)
        right.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(right, fg_color="transparent")
        top.grid(row=0, column=0, columnspan=4, sticky="ew", pady=4)
        top.grid_columnconfigure(2, weight=1)

        theme_btn = ctk.CTkButton(
            top, text="☀ Tema", width=80,
            command=self._toggle_theme
        )
        theme_btn.grid(row=0, column=0, sticky="w", padx=(4, 0))

        self.back_btn = ctk.CTkButton(
            top, text="← Geri", width=80, command=self._on_back
        )
        self.back_btn.grid(row=0, column=0, sticky="w", padx=4)
        self.back_btn.grid_remove()

        task_input = ctk.CTkFrame(top, fg_color="transparent")
        task_input.grid(row=0, column=1, sticky="ew", padx=4)
        task_input.grid_columnconfigure(0, weight=1)
        task_input.grid_columnconfigure(1, weight=1)
        task_input.grid_columnconfigure(2, weight=0)
        self.task_entry = ctk.CTkEntry(task_input, placeholder_text="Yeni görev...")
        self.task_entry.grid(row=0, column=0, sticky="ew")
        self.task_time_entry = ctk.CTkEntry(task_input, placeholder_text="14:00 - 15:30")
        self.task_time_entry.grid(row=0, column=1, sticky="ew", padx=4)
        ctk.CTkButton(
            task_input, text="Ekle", width=70,
            command=self._on_add_task
        ).grid(row=0, column=2, sticky="w", padx=(4, 0))

        self.task_list = ctk.CTkScrollableFrame(right, label_text="Görevler")
        self.task_list.grid(row=1, column=0, columnspan=4, sticky="nsew", pady=8)
        self.task_list.grid_columnconfigure(1, weight=1)
        self.task_list.grid_columnconfigure(3, weight=0)

        self.status = ctk.CTkLabel(right, text="0 görev", anchor="w")
        self.status.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(0, 8))

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

    def _refresh_categories(self) -> None:
        for widget in self.cat_list.winfo_children():
            widget.destroy()

        self.cat_buttons.clear()

        all_btn = ctk.CTkButton(
            self.cat_list, text="📋 Tümü", anchor="w",
            command=lambda: self._select_category(None),
        )
        all_btn.grid(row=0, column=0, sticky="ew", pady=2)
        self.cat_buttons[None] = all_btn

        for i, row in enumerate(self.db.get_categories(), start=1):
            cid, name = row["id"], row["name"]
            b = ctk.CTkButton(
                self.cat_list, text=name, anchor="w",
                command=lambda c=cid: self._select_category(c),
            )
            b.grid(row=i, column=0, sticky="ew", pady=2)
            self._cat_default_fg[cid] = b.cget("fg_color")
            self.cat_buttons[cid] = b

            if name not in ["Genel", "Tümü"]:
                del_btn = ctk.CTkButton(
                    self.cat_list, text="Sil", width=40,
                    command=lambda c=cid, n=name: self._on_delete_category(c, n),
                )
                del_btn.grid(row=i, column=1, sticky="e", padx=4)

        self._highlight_categories()

    def _highlight_categories(self) -> None:
        for key, b in self.cat_buttons.items():
            if b.winfo_exists():
                if key == self.selected_category_id:
                    b.configure(fg_color=("#29794e", "#215e3f"))
                elif key in self._cat_default_fg:
                    b.configure(fg_color=self._cat_default_fg[key])

    def _select_category(self, category_id: int | None) -> None:
        self.selected_category_id = category_id
        self._highlight_categories()
        self.back_btn.grid() if category_id is not None else self.back_btn.grid_remove()
        self._refresh_tasks()

    def _on_delete_category(self, category_id: int, category_name: str) -> None:
        from tkinter.messagebox import askyesno

        if not askyesno("Onay", f"{category_name} kategorisini silmek istediğinizden emin misiniz?\nBu kategoriye bağlı tüm görevler silinecek."):
            return

        self.db.delete_category(category_id, category_name)
        self._refresh_categories()

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
            command=lambda: self._on_toggle_task(todo, cb),
        )
        cb.grid(row=index, column=1, sticky="ew", padx=4, pady=3)
        cb.select() if todo.completed else cb.deselect()

        del_btn = ctk.CTkButton(
            self.task_list, text="Sil", width=60,
            command=lambda: self._on_delete_task(todo),
        )
        del_btn.grid(row=index, column=2, sticky="ew", padx=(8, 0), pady=3)

        self.row_widgets[todo.id] = {"cb": cb, "del": del_btn}

    # ------------------------------------------------------------------ theme
    def _toggle_theme(self) -> None:
        ctk.set_appearance_mode("dark" if ctk.get_appearance_mode() == "light" else "light")
        self._refresh_categories()
        self._refresh_tasks()
