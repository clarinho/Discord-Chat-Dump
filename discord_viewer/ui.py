import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from typing import List, Set

from .themes import THEMES
from .config import APP_TITLE, DEFAULT_GEOMETRY, DEFAULT_THEME
from .model import Row, Attachment
from .image_viewer import ImageViewer


def _looks_like_image(filename: str) -> bool:
    fn = (filename or "").lower()
    return fn.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"))


class ChatViewer(tk.Tk):
    def __init__(self, rows: List[Row]):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(DEFAULT_GEOMETRY)

        self.rows = rows
        self.row_index_by_tree_id = {}
        self.current_attachments: List[Attachment] = []

        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        self._build_ui()
        theme = DEFAULT_THEME if DEFAULT_THEME in THEMES else list(THEMES.keys())[0]
        self._apply_theme(theme)
        self._populate_tree()

    def _build_ui(self):
        top = ttk.Frame(self, padding=8)
        top.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(top, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(top, textvariable=self.search_var, width=40)
        search_entry.pack(side=tk.LEFT, padx=(6, 12))
        search_entry.bind("<Return>", lambda e: self._apply_filter())

        ttk.Button(top, text="Apply", command=self._apply_filter).pack(side=tk.LEFT)
        ttk.Button(top, text="Clear", command=self._clear_filter).pack(side=tk.LEFT, padx=(6, 18))

        ttk.Label(top, text="Theme:").pack(side=tk.LEFT)
        self.theme_var = tk.StringVar(value=list(THEMES.keys())[0])
        theme_combo = ttk.Combobox(
            top,
            textvariable=self.theme_var,
            values=list(THEMES.keys()),
            state="readonly",
            width=18
        )
        theme_combo.pack(side=tk.LEFT, padx=(6, 0))
        theme_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_theme(self.theme_var.get()))

        main = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        main.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=8, pady=8)

        left = ttk.Frame(main)
        main.add(left, weight=3)

        columns = ("time", "text")
        self.tree = ttk.Treeview(left, columns=columns, show="tree headings", selectmode="browse")
        self.tree.heading("#0", text="Section")
        self.tree.heading("time", text="Time")
        self.tree.heading("text", text="Message")
        self.tree.column("#0", width=320, stretch=False)
        self.tree.column("time", width=100, stretch=False)
        self.tree.column("text", width=650, stretch=True)

        yscroll = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        right = ttk.Frame(main, padding=(10, 0))
        main.add(right, weight=1)

        ttk.Label(right, text="Attachments (double-click to open):").pack(anchor="w")

        self.att_list = tk.Listbox(right, height=14, activestyle="none")
        self.att_list.pack(fill=tk.BOTH, expand=False, pady=(6, 6))
        self.att_list.bind("<Double-Button-1>", self._open_selected_attachment)

        ttk.Label(
            right,
            text="Select a message row to see attachments.\nDouble-click a filename to preview.\nIf not an image, it opens in browser.",
            justify="left"
        ).pack(anchor="w", pady=(6, 0))

    def _apply_theme(self, theme_name: str):
        if theme_name not in THEMES:
            return
        t = THEMES[theme_name]

        self.configure(bg=t["bg"])

        self.style.configure("TFrame", background=t["bg"])
        self.style.configure("TLabel", background=t["bg"], foreground=t["fg"])
        self.style.configure("TButton", padding=6)
        self.style.configure("TEntry", fieldbackground=t["panel_bg"], foreground=t["fg"])
        self.style.configure("TCombobox", fieldbackground=t["panel_bg"], foreground=t["fg"])
        self.style.map("TCombobox", fieldbackground=[("readonly", t["panel_bg"])])

        self.style.configure(
            "Treeview",
            background=t["tree_bg"],
            fieldbackground=t["tree_bg"],
            foreground=t["tree_fg"],
            bordercolor=t["border"],
            rowheight=24
        )
        self.style.configure(
            "Treeview.Heading",
            background=t["heading_bg"],
            foreground=t["heading_fg"]
        )
        self.style.map(
            "Treeview",
            background=[("selected", t["tree_sel_bg"])],
            foreground=[("selected", t["tree_sel_fg"])]
        )

        self.att_list.configure(
            bg=t["list_bg"],
            fg=t["list_fg"],
            selectbackground=t["tree_sel_bg"],
            selectforeground=t["tree_sel_fg"],
            highlightbackground=t["border"],
            highlightcolor=t["border"]
        )

        if self.theme_var.get() != theme_name:
            self.theme_var.set(theme_name)

    def _populate_tree(self, kept_indices: Set[int] = None):
        self.tree.delete(*self.tree.get_children())
        self.row_index_by_tree_id.clear()

        if kept_indices is None:
            kept_indices = set(range(len(self.rows)))

        for i, r in enumerate(self.rows):
            if i not in kept_indices:
                continue

            if r.type == "date":
                tree_id = self.tree.insert("", tk.END, text=r.date, values=("", ""))
            elif r.type == "header":
                tree_id = self.tree.insert("", tk.END, text=f"{r.server} / {r.channel}", values=("", ""))
            else:
                tree_id = self.tree.insert("", tk.END, text="", values=(r.time, r.content))

            self.row_index_by_tree_id[tree_id] = i

    def _apply_filter(self):
        q = (self.search_var.get() or "").strip().lower()
        if not q:
            self._populate_tree()
            return

        kept = set()
        matching_msgs = []

        for i, r in enumerate(self.rows):
            if r.type != "msg":
                continue
            if q in (r.content or "").lower():
                matching_msgs.append(i)
                kept.add(i)

        for idx in matching_msgs:
            last_date = None
            last_header = None
            j = idx
            while j >= 0:
                rt = self.rows[j].type
                if rt == "msg" and j != idx:
                    break
                if rt == "header" and last_header is None:
                    last_header = j
                if rt == "date":
                    last_date = j
                    break
                j -= 1
            if last_date is not None:
                kept.add(last_date)
            if last_header is not None:
                kept.add(last_header)

        self._populate_tree(kept_indices=kept)

    def _clear_filter(self):
        self.search_var.set("")
        self._populate_tree()

    def _on_select(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        tree_id = sel[0]
        idx = self.row_index_by_tree_id.get(tree_id)
        if idx is None:
            return
        row = self.rows[idx]

        self.att_list.delete(0, tk.END)
        self.current_attachments = []

        if row.type != "msg" or not row.attachments:
            return

        for att in row.attachments:
            self.att_list.insert(tk.END, att.filename)
            self.current_attachments.append(att)

    def _open_selected_attachment(self, event=None):
        sel = self.att_list.curselection()
        if not sel:
            return
        i = sel[0]
        att = self.current_attachments[i]
        if not att.url:
            messagebox.showerror("Open attachment", "No URL found for this attachment.")
            return

        # If it looks like an image, preview in-app, else open in browser.
        if _looks_like_image(att.filename):
            try:
                ImageViewer(self, att.filename, att.url)
            except Exception as e:
                # Fallback
                messagebox.showerror("Preview failed", f"{e}\n\nOpening in browser instead.")
                webbrowser.open(att.url)
        else:
            webbrowser.open(att.url)
