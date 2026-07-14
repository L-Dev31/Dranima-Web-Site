import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import copy
import json
import os
import re
from html import escape, unescape
from datetime import datetime
from collections import OrderedDict

try:
    from PIL import Image, ImageTk
except ImportError:
    # Pillow is optional: without it the app still opens, image previews just show a hint.
    Image = ImageTk = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
FILES = ["credits.json", "faq.json", "news.json", "wiki.json"]
TAB_LABELS = {"credits.json": "Team", "faq.json": "FAQ", "news.json": "News", "wiki.json": "Wiki"}

HINT = "Select an item — New: Ctrl+N · Save: Ctrl+S · Delete: Del · Drag items to move or reorder"

# System / fixed categories: marked with an icon so they read differently from
# the user-created ones. The pseudo-categories are also always pinned to the bottom.
GUESTS_LABEL = "\N{BUSTS IN SILHOUETTE}  Guests"
UNCAT_LABEL = "\N{CARD INDEX DIVIDERS}  Uncategorized"
NEWS_LABELS = {"announcement": "\N{PUBLIC ADDRESS LOUDSPEAKER}  Announcement",
               "update": "\N{ANTICLOCKWISE DOWNWARDS AND UPWARDS OPEN CIRCLE ARROWS}  Update"}

# Flat dark palette
COLORS = {
    "bg": "#121212",
    "surface": "#1a1a1a",
    "field": "#1f1f1f",
    "fg": "#e4e4e4",
    "muted": "#8a8a8a",
    "accent": "#EF8D34",        
    "accent_fg": "#1a1a1a",     
    "danger": "#ef4444",
    "border": "#2a2a2a",
}


def make_dark_text(parent, **kwargs):
    """tk.Text is a classic widget (not themed by ttk.Style)."""
    return tk.Text(parent, bg=COLORS["field"], fg=COLORS["fg"], insertbackground=COLORS["fg"],
                   relief="flat", bd=0, highlightthickness=1,
                   highlightbackground=COLORS["border"], highlightcolor=COLORS["accent"], **kwargs)


def make_dark_listbox(parent, **kwargs):
    return tk.Listbox(parent, bg=COLORS["field"], fg=COLORS["fg"], relief="flat", bd=0,
                      highlightthickness=1, highlightbackground=COLORS["border"],
                      highlightcolor=COLORS["accent"], selectbackground=COLORS["accent"],
                      selectforeground=COLORS["accent_fg"], activestyle="none", **kwargs)


def optimize_json(obj):
    """Alphabetically sorted keys on save."""
    if isinstance(obj, dict):
        return OrderedDict(sorted((k, optimize_json(v)) for k, v in obj.items()))
    elif isinstance(obj, list):
        return [optimize_json(item) for item in obj]
    return obj


class DranimaContentManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Dranima Content Manager - by Léo TOSKU (L-DEV)")
        self.geometry("1450x900")
        self.minsize(1000, 650)
        self.configure(bg=COLORS["bg"])
        try:
            self._icon = tk.PhotoImage(file=os.path.join(BASE_DIR, "images", "favicon.png"))
            self.iconphoto(True, self._icon)
        except Exception:
            pass

        self.data_store = {}
        self.current = None          # (fname, iid)
        self.unsaved = False
        self._drag = None
        self._drag_hover = None
        self._first_field = None
        self._status_msg = ""
        self.status_var = tk.StringVar(value="")

        # Undo/redo: snapshot the whole data_store. Rapid edits (typing) are
        # coalesced into one step via a short debounce so undo stays useful.
        self._undo, self._redo = [], []
        self._snapshot = None
        self._commit_job = None
        self._restoring = False
        self._history_limit = 200

        self.setup_styles()
        self.setup_ui()
        self.load_all()
        self._snapshot = copy.deepcopy(self.data_store)
        self.after_idle(self._maximize_window)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _maximize_window(self):
        """Use the available desktop space while retaining a cross-platform fallback."""
        try:
            self.state("zoomed")
        except tk.TclError:
            width = max(self.winfo_screenwidth() - 80, self.winfo_reqwidth())
            height = max(self.winfo_screenheight() - 120, self.winfo_reqheight())
            self.geometry(f"{width}x{height}+20+20")

    # ---------- theme ----------
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", background=COLORS["bg"], foreground=COLORS["fg"], font=("Segoe UI", 10),
                        fieldbackground=COLORS["field"], bordercolor=COLORS["border"],
                        darkcolor=COLORS["bg"], lightcolor=COLORS["bg"], borderwidth=1,
                        focuscolor=COLORS["accent"])
        style.configure("TFrame", background=COLORS["bg"])
        style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["fg"])
        style.configure("Muted.TLabel", foreground=COLORS["muted"])
        style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"))
        style.configure("CardTitle.TLabel", font=("Segoe UI", 10, "bold"), foreground=COLORS["accent"])
        style.configure("Status.TLabel", font=("Segoe UI", 9), foreground=COLORS["muted"])
        style.configure("TButton", background="#2c2c2c", foreground=COLORS["fg"],
                        bordercolor="#3a3a3a", padding=(10, 6), relief="flat")
        style.map("TButton",
                  background=[("active", COLORS["accent"]), ("pressed", COLORS["accent"]),
                              ("disabled", COLORS["surface"])],
                  foreground=[("active", COLORS["accent_fg"]), ("pressed", COLORS["accent_fg"]),
                              ("disabled", COLORS["muted"])],
                  bordercolor=[("active", COLORS["accent"])])
        style.configure("TEntry", fieldbackground=COLORS["field"], foreground=COLORS["fg"],
                        bordercolor=COLORS["border"], insertcolor=COLORS["fg"])
        style.configure("TCombobox", fieldbackground=COLORS["field"], background=COLORS["field"],
                        foreground=COLORS["fg"], arrowcolor=COLORS["fg"], bordercolor=COLORS["border"])
        style.map("TCombobox", fieldbackground=[("readonly", COLORS["field"])])
        style.configure("TCheckbutton", background=COLORS["bg"], foreground=COLORS["fg"])
        style.map("TCheckbutton", background=[("active", COLORS["bg"])])
        style.configure("TNotebook", background=COLORS["bg"], bordercolor=COLORS["border"])
        style.configure("TNotebook.Tab", background=COLORS["surface"], foreground=COLORS["muted"],
                        padding=[12, 6], bordercolor=COLORS["border"])
        style.map("TNotebook.Tab",
                  background=[("selected", COLORS["accent"])],
                  foreground=[("selected", COLORS["accent_fg"])])
        style.configure("Treeview", background=COLORS["field"], fieldbackground=COLORS["field"],
                        foreground=COLORS["fg"], bordercolor=COLORS["border"], rowheight=26, relief="flat")
        style.map("Treeview",
                  background=[("selected", COLORS["accent"])],
                  foreground=[("selected", COLORS["accent_fg"])])
        style.configure("Card.TFrame", background=COLORS["bg"], bordercolor=COLORS["border"],
                        relief="solid", borderwidth=1)
        style.configure("TSeparator", background=COLORS["border"])
        style.configure("TPanedwindow", background=COLORS["bg"])
        for orient in ("Vertical", "Horizontal"):
            style.configure(f"{orient}.TScrollbar", background=COLORS["surface"],
                            troughcolor=COLORS["bg"], bordercolor=COLORS["border"],
                            arrowcolor=COLORS["fg"], relief="flat")

    # ---------- layout ----------
    def setup_ui(self):
        root = ttk.Frame(self)
        root.pack(fill=tk.BOTH, expand=True)

        # native menu bar: Action ▸ item actions · undo/redo · save
        menubar = tk.Menu(self)
        action = tk.Menu(menubar, tearoff=0)
        action.add_command(label="New", accelerator="Ctrl+N", command=self.create_item)
        action.add_command(label="New Category", accelerator="Ctrl+Shift+N", command=self.create_category)
        action.add_command(label="Delete", accelerator="Del", command=self.delete_item)
        action.add_separator()
        action.add_command(label="Undo", accelerator="Ctrl+Z", command=self.undo)
        action.add_command(label="Redo", accelerator="Ctrl+Shift+Z", command=self.redo)
        action.add_separator()
        action.add_command(label="Save All", accelerator="Ctrl+S", command=self.save_all)
        menubar.add_cascade(label="Action", menu=action)
        self.config(menu=menubar)

        paned = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # sidebar
        left = ttk.Frame(paned)
        paned.add(left, weight=1)

        self.file_tabs = ttk.Notebook(left)
        self.file_tabs.pack(fill=tk.BOTH, expand=True)
        self.trees = {}
        for fname in FILES:
            frame = ttk.Frame(self.file_tabs)
            self.file_tabs.add(frame, text=TAB_LABELS[fname])
            sb = ttk.Scrollbar(frame)
            sb.pack(side=tk.RIGHT, fill=tk.Y)
            tree = ttk.Treeview(frame, selectmode="browse", show="tree", yscrollcommand=sb.set)
            tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
            sb.config(command=tree.yview)
            tree.bind("<<TreeviewSelect>>", lambda e, f=fname: self.on_select(f))
            tree.bind("<ButtonPress-1>", lambda e, f=fname: self._dnd_press(e, f))
            tree.bind("<B1-Motion>", lambda e, f=fname: self._dnd_motion(e, f))
            tree.bind("<ButtonRelease-1>", lambda e, f=fname: self._dnd_release(e, f))
            tree.tag_configure("drop-target", foreground="#f6b17a")
            tree.tag_configure("drop-hover", background=COLORS["accent"], foreground=COLORS["accent_fg"])
            tree.tag_configure("drop-disabled", foreground=COLORS["muted"])
            tree.tag_configure("dragging", foreground="#fbbf24")
            self.trees[fname] = tree

        btns = ttk.Frame(left)
        btns.pack(fill=tk.X, pady=(6, 0))
        ttk.Button(btns, text="New", command=self.create_item).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(btns, text="New Category", command=self.create_category).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        ttk.Button(btns, text="Delete", command=self.delete_item).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(btns, text="Save", command=self.save_all).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))

        # editor panel
        right = ttk.Frame(paned)
        paned.add(right, weight=2)
        self.editor_canvas = tk.Canvas(right, bg=COLORS["bg"], highlightthickness=0, bd=0)
        editor_scrollbar = ttk.Scrollbar(right, orient=tk.VERTICAL, command=self.editor_canvas.yview)
        self.editor_canvas.configure(yscrollcommand=editor_scrollbar.set)
        editor_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        self.editor_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(18, 12), pady=10)
        self.editor = ttk.Frame(self.editor_canvas)
        self._editor_window = self.editor_canvas.create_window((0, 0), window=self.editor, anchor=tk.NW)
        self.editor.bind("<Configure>", self._update_editor_scroll_region)
        self.editor_canvas.bind("<Configure>", self._resize_editor_content)

        # status bar
        ttk.Separator(root, orient=tk.HORIZONTAL).pack(fill=tk.X)
        status = ttk.Frame(root)
        status.pack(fill=tk.X, padx=10, pady=4)
        ttk.Label(status, textvariable=self.status_var, style="Status.TLabel").pack(side=tk.LEFT)
        self.unsaved_label = ttk.Label(status, text="", style="Status.TLabel", foreground=COLORS["danger"])
        self.unsaved_label.pack(side=tk.RIGHT)

        # shortcuts — New/Delete only when the tree has focus (not while typing)
        self.bind("<Control-s>", lambda e: self.save_all())
        self.bind("<Control-n>", lambda e: self._tree_focused() and self.create_item())
        self.bind("<Control-N>", lambda e: self._tree_focused() and self.create_category())
        self.bind("<Delete>", lambda e: self._tree_focused() and self.delete_item())
        # Undo/redo work everywhere, including while editing a field.
        self.bind_all("<Control-z>", lambda e: (self.undo(), "break")[1])
        self.bind_all("<Control-y>", lambda e: (self.redo(), "break")[1])
        self.bind_all("<Control-Z>", lambda e: (self.redo(), "break")[1])  # Ctrl+Shift+Z
        self.file_tabs.bind("<<NotebookTabChanged>>", lambda e: self._on_tab_change())

        self.clear_editor(HINT)

    def _tree_focused(self):
        w = self.focus_get()
        return w is not None and w.winfo_class() == "Treeview"

    def _update_editor_scroll_region(self, _event=None):
        self.editor_canvas.configure(scrollregion=self.editor_canvas.bbox("all"))

    def _resize_editor_content(self, event):
        self.editor_canvas.itemconfigure(self._editor_window, width=event.width)

    def _on_tab_change(self):
        self.current = None
        self.clear_editor(HINT)

    def _current_fname(self):
        return FILES[self.file_tabs.index(self.file_tabs.select())]

    # ---------- data ----------
    def load_all(self):
        try:
            for fname in FILES:
                path = os.path.join(DATA_DIR, fname)
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        self.data_store[fname] = json.load(f)
                else:
                    self.data_store[fname] = [] if fname in ("faq.json", "news.json") else {}
            credits = self.data_store["credits.json"]
            credits.setdefault("team", [])
            credits.setdefault("categories", [])
            credits["guests"] = [{"name": g, "link": None} if isinstance(g, str) else g
                                 for g in credits.get("guests", [])]
            wiki = self.data_store["wiki.json"]
            wiki.setdefault("categories", [])
            wiki.setdefault("entries", [])
            for fname in FILES:
                self.refresh_tree(fname)
        except Exception as e:
            messagebox.showerror("Load error", str(e))

    def save_all(self):
        try:
            for fname, content in self.data_store.items():
                with open(os.path.join(DATA_DIR, fname), "w", encoding="utf-8") as f:
                    json.dump(optimize_json(content), f, indent=2, ensure_ascii=False)
            self.unsaved = False
            self.unsaved_label.config(text="")
            self.set_status("Saved")
        except Exception as e:
            messagebox.showerror("Save error", str(e))

    def mark_unsaved(self):
        self.unsaved = True
        self.unsaved_label.config(text="● Unsaved")
        self._touch_history()

    # ---------- undo / redo ----------
    def _touch_history(self):
        """Debounce a history commit so a burst of edits collapses into one step."""
        if self._restoring or self._snapshot is None:
            return
        if self._commit_job is not None:
            self.after_cancel(self._commit_job)
        self._commit_job = self.after(500, self._commit_history)

    def _commit_history(self):
        self._commit_job = None
        if self._snapshot is None:
            return
        if self.data_store != self._snapshot:
            self._undo.append(self._snapshot)
            del self._undo[:-self._history_limit]
            self._redo.clear()
            self._snapshot = copy.deepcopy(self.data_store)

    def _flush_history(self):
        if self._commit_job is not None:
            self.after_cancel(self._commit_job)
            self._commit_job = None
        self._commit_history()

    def undo(self):
        self._flush_history()
        if not self._undo:
            self.set_status("Nothing to undo")
            return
        self._redo.append(copy.deepcopy(self.data_store))
        self._apply_state(self._undo.pop())
        self.set_status("Undo")

    def redo(self):
        self._flush_history()
        if not self._redo:
            self.set_status("Nothing to redo")
            return
        self._undo.append(copy.deepcopy(self.data_store))
        self._apply_state(self._redo.pop())
        self.set_status("Redo")

    def _apply_state(self, state):
        """Replace the data and rebuild every view; editors hold stale object refs."""
        self._restoring = True
        try:
            self.data_store = copy.deepcopy(state)
            self._snapshot = copy.deepcopy(state)
            self.current = None
            for fname in FILES:
                self.refresh_tree(fname)
            self.clear_editor(HINT)
            self.unsaved = True
            self.unsaved_label.config(text="● Unsaved")
        finally:
            self._restoring = False

    def set_status(self, msg):
        self._status_msg = msg
        self.status_var.set(msg)
        self.after(4000, lambda m=msg: self.status_var.set("") if self._status_msg == m else None)

    # ---------- trees ----------
    def _iter_iids(self, tree, parent=""):
        for iid in tree.get_children(parent):
            yield iid
            yield from self._iter_iids(tree, iid)

    def refresh_tree(self, fname):
        tree = self.trees[fname]
        open_state = {iid: tree.item(iid, "open") for iid in self._iter_iids(tree)}
        tree.delete(*tree.get_children())
        data = self.data_store[fname]

        if fname == "credits.json":
            team = {t.get("id"): t for t in data["team"]}
            for ci, cat in enumerate(data["categories"]):
                node = tree.insert("", "end", iid=f"cat_{ci}", text=cat.get("title", ""), open=True)
                for mi, m in enumerate(cat.get("members", [])):
                    name = team.get(m.get("id"), {}).get("name", m.get("id", ""))
                    tree.insert(node, "end", iid=f"mem_{ci}_{mi}", text=name)
            gnode = tree.insert("", "end", iid="guests", text=GUESTS_LABEL, open=True)
            for gi, g in enumerate(data["guests"]):
                tree.insert(gnode, "end", iid=f"guest_{gi}", text=g.get("name", ""))

        elif fname == "wiki.json":
            entries = data["entries"]
            for cat in data["categories"]:
                node = tree.insert("", "end", iid=f"wcat_{cat.get('id', '')}", text=cat.get("name", ""), open=False)
                for ei, e in enumerate(entries):
                    if e.get("category") == cat.get("id"):
                        tree.insert(node, "end", iid=f"ent_{ei}", text=e.get("name", ""))
            orphans = [ei for ei, e in enumerate(entries) if not e.get("category")]
            if orphans:
                node = tree.insert("", "end", iid="uncat", text=UNCAT_LABEL, open=False)
                for ei in orphans:
                    tree.insert(node, "end", iid=f"ent_{ei}", text=entries[ei].get("name", ""))

        elif fname == "faq.json":
            for i, item in enumerate(data):
                tree.insert("", "end", iid=f"item_{i}", text=item.get("question", "") or "(untitled)")

        elif fname == "news.json":
            for category in ("announcement", "update"):
                node = tree.insert("", "end", iid=f"news_{category}", text=NEWS_LABELS[category], open=True)
                for i, item in enumerate(data.get(category, [])):
                    tree.insert(node, "end", iid=f"news_{category}_{i}", text=item.get("title", "") or "(untitled)")

        for iid, is_open in open_state.items():
            if tree.exists(iid):
                tree.item(iid, open=is_open)

    def _select(self, fname, iid):
        tree = self.trees[fname]
        if tree.exists(iid):
            tree.see(iid)
            tree.selection_set(iid)

    # ---------- selection / editors ----------
    def on_select(self, fname):
        tree = self.trees[fname]
        sel = tree.selection()
        if not sel:
            return
        iid = sel[0]
        self.current = (fname, iid)
        self.clear_editor()

        if fname == "credits.json":
            if iid.startswith("mem_"):
                ci, mi = map(int, iid[4:].split("_"))
                self.edit_member(ci, mi, iid)
            elif iid.startswith("guest_"):
                self.edit_guest(int(iid[6:]), iid)
            elif iid.startswith("cat_"):
                self.edit_credits_category(int(iid[4:]), iid)
            else:
                self.clear_editor("Guests — New adds a guest here")
        elif fname == "wiki.json":
            if iid.startswith("ent_"):
                self.edit_wiki_entry(int(iid[4:]), iid)
            elif iid.startswith("wcat_"):
                self.edit_wiki_category(iid[5:], iid)
            else:
                self.clear_editor("Uncategorized entries")
        elif fname == "faq.json":
            self.edit_faq(int(iid[5:]), iid)
        elif fname == "news.json" and iid.startswith("news_"):
            parts = iid.split("_", 2)
            if len(parts) == 3:
                self.edit_news(parts[1], int(parts[2]), iid)
            else:
                self.clear_editor("Select an article or use New to add one to this category")

    def clear_editor(self, hint=None):
        for w in self.editor.winfo_children():
            w.destroy()
        self.editor_canvas.yview_moveto(0)
        self._first_field = None
        if hint:
            ttk.Label(self.editor, text=hint, style="Muted.TLabel").pack(pady=30)

    # form helpers — every field applies instantly (no save buttons, no popups)
    def _header(self, text):
        ttk.Label(self.editor, text=text, style="Header.TLabel").pack(anchor=tk.W, pady=(0, 16))

    def _focus_new_block(self, widget):
        """Reveal a just-added block and place the cursor in its first input."""
        try:
            self.editor_canvas.update_idletasks()
            self.editor.update_idletasks()
            widget.focus_set()
            # Bring the freshly added block (always appended at the end) into view.
            bbox = self.editor_canvas.bbox(self._editor_window)
            if bbox:
                wy = widget.winfo_rooty() - self.editor.winfo_rooty()
                total = max(bbox[3], 1)
                self.editor_canvas.yview_moveto(max(0.0, (wy - 40) / total))
        except tk.TclError:
            pass

    def _editor_notebook(self, *names):
        """Split a record editor into top-level tabs so bulky content gets its own space."""
        nb = ttk.Notebook(self.editor)
        nb.pack(fill=tk.BOTH, expand=True)
        frames = []
        for name in names:
            fr = ttk.Frame(nb, padding=(4, 14, 6, 4))
            nb.add(fr, text=name)
            frames.append(fr)
        return [nb] + frames

    def field(self, parent, label, value, setter, browse=False):
        ttk.Label(parent, text=label, style="Muted.TLabel").pack(anchor=tk.W, pady=(0, 3))
        wrap = ttk.Frame(parent)
        wrap.pack(fill=tk.X, pady=(0, 12))
        var = tk.StringVar(value=value or "")
        ent = ttk.Entry(wrap, textvariable=var)
        ent.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        if browse:
            ttk.Button(wrap, text="…", width=3, command=lambda: self._browse(var)).pack(side=tk.LEFT, padx=(6, 0))
        var.trace_add("write", lambda *a: (setter(var.get().strip()), self.mark_unsaved()))
        if browse:
            preview = ttk.Label(parent, style="Muted.TLabel")
            preview.pack(anchor=tk.W, pady=(0, 12))
            var.trace_add("write", lambda *a: self._update_image_preview(preview, var.get()))
            self._update_image_preview(preview, var.get())
        if self._first_field is None:
            self._first_field = ent
        return ent

    def text_field(self, parent, label, value, setter, height=6, expand=False):
        ttk.Label(parent, text=label, style="Muted.TLabel").pack(anchor=tk.W, pady=(0, 3))
        txt = make_dark_text(parent, height=height, width=1, font=("Segoe UI", 10), wrap=tk.WORD,
                             padx=8, pady=6)
        txt.insert("1.0", value or "")
        txt.edit_modified(False)

        def on_mod(_e):
            if txt.edit_modified():
                setter(txt.get("1.0", "end-1c").strip())
                self.mark_unsaved()
                txt.edit_modified(False)

        txt.bind("<<Modified>>", on_mod)
        txt.pack(fill=tk.BOTH if expand else tk.X, expand=expand, pady=(0, 12))
        if self._first_field is None:
            self._first_field = txt
        return txt

    def html_field(self, parent, label, value, setter, height=8, expand=False):
        """Offer common content blocks without hiding the original HTML escape hatch."""
        if label:
            ttk.Label(parent, text=label, style="Muted.TLabel").pack(anchor=tk.W, pady=(0, 3))
        tabs = ttk.Notebook(parent)
        tabs.pack(fill=tk.BOTH if expand else tk.X, expand=expand, pady=(0, 12))
        easy = ttk.Frame(tabs, padding=12)
        raw = ttk.Frame(tabs, padding=12)
        tabs.add(easy, text="Easy editor")
        tabs.add(raw, text="Raw HTML")

        raw_text = make_dark_text(raw, height=height, width=1, font=("Consolas", 10), wrap=tk.WORD,
                                  padx=8, pady=6)
        raw_text.insert("1.0", value or "")
        raw_text.edit_modified(False)
        raw_text.pack(fill=tk.BOTH, expand=True)
        blocks = self._html_to_blocks(value or "")
        last_raw = [value or ""]
        focus_last = [False]   # set when a freshly added block should grab focus

        def update_raw(html_value):
            raw_text.delete("1.0", tk.END)
            raw_text.insert("1.0", html_value)
            raw_text.edit_modified(False)
            last_raw[0] = html_value
            setter(html_value or None)
            self.mark_unsaved()

        def render_easy():
            for widget in easy.winfo_children():
                widget.destroy()

            def save_blocks():
                update_raw(self._blocks_to_html(blocks))

            def add_block(kind):
                defaults = {
                    "paragraph": {"kind": "paragraph", "text": ""},
                    "list": {"kind": "list", "items": []},
                    "image": {"kind": "image", "src": "", "alt": ""},
                    "table": {"kind": "table", "rows": [["Column 1", "Column 2"], ["", ""]]},
                }
                blocks.append(defaults[kind])
                focus_last[0] = True   # jump straight into the new block
                save_blocks()
                render_easy()

            def swap(i, j):
                if 0 <= i < len(blocks) and 0 <= j < len(blocks):
                    blocks[i], blocks[j] = blocks[j], blocks[i]
                    save_blocks()
                    render_easy()

            def remove_at(i):
                del blocks[i]
                save_blocks()
                render_easy()

            toolbar = ttk.Frame(easy)
            toolbar.pack(fill=tk.X, pady=(0, 12))
            ttk.Label(toolbar, text="Add block:", style="Muted.TLabel").pack(side=tk.LEFT, padx=(0, 8))
            ttk.Button(toolbar, text="Paragraph", command=lambda: add_block("paragraph")).pack(side=tk.LEFT)
            ttk.Button(toolbar, text="Bullet list", command=lambda: add_block("list")).pack(side=tk.LEFT, padx=(6, 0))
            ttk.Button(toolbar, text="Image", command=lambda: add_block("image")).pack(side=tk.LEFT, padx=(6, 0))
            ttk.Button(toolbar, text="Table", command=lambda: add_block("table")).pack(side=tk.LEFT, padx=(6, 0))

            names = {"paragraph": "Paragraph", "list": "Bullet list", "image": "Image",
                     "table": "Table", "raw": "Advanced HTML"}

            if not blocks:
                ttk.Label(easy, text="Empty — use the buttons above to add your first block.",
                          style="Muted.TLabel").pack(anchor=tk.W, pady=(4, 0))
                return

            last = len(blocks) - 1
            for index, block in enumerate(blocks):
                # Each block is a bordered card so it reads as one self-contained unit.
                card = ttk.Frame(easy, style="Card.TFrame", padding=(16, 12, 16, 14))
                card.pack(fill=tk.X, pady=(0, 12))

                head = ttk.Frame(card)
                head.pack(fill=tk.X, pady=(0, 10))
                head.columnconfigure(0, weight=1)
                ttk.Label(head, text=names[block["kind"]], style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
                up = ttk.Button(head, text="Up", width=5, command=lambda i=index: swap(i, i - 1))
                up.grid(row=0, column=1, padx=(0, 6))
                down = ttk.Button(head, text="Down", width=6, command=lambda i=index: swap(i, i + 1))
                down.grid(row=0, column=2, padx=(0, 6))
                ttk.Button(head, text="Remove", width=8, command=lambda i=index: remove_at(i)).grid(row=0, column=3)
                if index == 0:
                    up.state(["disabled"])
                if index == last:
                    down.state(["disabled"])

                first_input = None
                if block["kind"] == "paragraph":
                    first_input = self.text_field(card, "Text", block["text"],
                                    lambda text, b=block: (b.update(text=text), save_blocks()), height=4)
                elif block["kind"] == "list":
                    first_input = self.text_field(card, "One item per line", "\n".join(block["items"]),
                                    lambda text, b=block: (b.update(items=[line for line in text.splitlines() if line]),
                                                           save_blocks()), height=5)
                elif block["kind"] == "image":
                    first_input = self.field(card, "File", block["src"],
                               lambda text, b=block: (b.update(src=text), save_blocks()), browse=True)
                    self.field(card, "Description (alt text)", block["alt"],
                               lambda text, b=block: (b.update(alt=text), save_blocks()))
                    ttk.Label(card, text="Tip: images next to each other show side by side as one gallery.",
                              style="Muted.TLabel").pack(anchor=tk.W)
                elif block["kind"] == "table":
                    rows_text = "\n".join(" | ".join(cell for cell in row) for row in block.get("rows", []))
                    first_input = self.text_field(card, "One row per line · separate cells with  |", rows_text,
                                    lambda text, b=block: (b.update(rows=[[c.strip() for c in line.split("|")]
                                                                          for line in text.splitlines() if line.strip()]),
                                                           save_blocks()), height=5)
                    ttk.Label(card, text="Tip: the first row is the header.",
                              style="Muted.TLabel").pack(anchor=tk.W)
                else:
                    ttk.Label(card, text="This advanced block is preserved. Edit it in the Raw HTML tab.",
                              style="Muted.TLabel").pack(anchor=tk.W, pady=(4, 0))

                if index == last and focus_last[0] and first_input is not None:
                    focus_last[0] = False
                    self.after(60, lambda w=first_input: self._focus_new_block(w))

        def on_raw_modified(_event):
            if raw_text.edit_modified():
                html_value = raw_text.get("1.0", "end-1c").strip()
                last_raw[0] = html_value
                setter(html_value or None)
                self.mark_unsaved()
                raw_text.edit_modified(False)

        def on_tab_changed(_event):
            if tabs.index(tabs.select()) == 0:
                html_value = raw_text.get("1.0", "end-1c").strip()
                if html_value != last_raw[0]:
                    blocks[:] = self._html_to_blocks(html_value)
                    last_raw[0] = html_value
                render_easy()

        raw_text.bind("<<Modified>>", on_raw_modified)
        tabs.bind("<<NotebookTabChanged>>", on_tab_changed)
        render_easy()
        return tabs

    @staticmethod
    def _html_to_blocks(html_value):
        pattern = re.compile(r"(<ul\b[^>]*>.*?</ul>|<div\b[^>]*class=[\"'][^\"']*news-update-images[^\"']*[\"'][^>]*>.*?</div>|<p\b[^>]*>.*?</p>|<table\b[^>]*>.*?</table>)", re.I | re.S)
        blocks = []
        position = 0
        for match in pattern.finditer(html_value):
            plain = html_value[position:match.start()].strip()
            if plain:
                blocks.append({"kind": "raw", "html": plain})
            chunk = match.group(0)
            lower = chunk.lower()
            if lower.startswith("<p"):
                text = re.sub(r"<br\s*/?>", "\n", re.sub(r"^<p\b[^>]*>|</p>$", "", chunk, flags=re.I)).strip()
                blocks.append({"kind": "paragraph", "text": unescape(re.sub(r"<[^>]+>", "", text))})
            elif lower.startswith("<ul"):
                items = [unescape(re.sub(r"<[^>]+>", "", item)).strip()
                         for item in re.findall(r"<li\b[^>]*>(.*?)</li>", chunk, re.I | re.S)]
                blocks.append({"kind": "list", "items": items})
            elif "news-update-images" in lower:
                images = re.findall(r"<img\b[^>]*src=[\"']([^\"']+)[\"'][^>]*>", chunk, re.I | re.S)
                alt_values = re.findall(r"<img\b[^>]*alt=[\"']([^\"']*)[\"'][^>]*>", chunk, re.I | re.S)
                for index, src in enumerate(images):
                    blocks.append({"kind": "image", "src": unescape(src),
                                   "alt": unescape(alt_values[index]) if index < len(alt_values) else ""})
            elif lower.startswith("<table"):
                rows = []
                for tr in re.findall(r"<tr\b[^>]*>(.*?)</tr>", chunk, re.I | re.S):
                    cells = [unescape(re.sub(r"<[^>]+>", "", cell)).strip()
                             for cell in re.findall(r"<t[hd]\b[^>]*>(.*?)</t[hd]>", tr, re.I | re.S)]
                    if cells:
                        rows.append(cells)
                blocks.append({"kind": "table", "rows": rows})
            else:
                blocks.append({"kind": "raw", "html": chunk})
            position = match.end()
        plain = html_value[position:].strip()
        if plain:
            blocks.append({"kind": "paragraph", "text": unescape(re.sub(r"<[^>]+>", "", plain))})
        return blocks or [{"kind": "paragraph", "text": ""}]

    @staticmethod
    def _blocks_to_html(blocks):
        output = []
        i = 0
        while i < len(blocks):
            block = blocks[i]
            if block["kind"] == "paragraph":
                text = escape(block["text"]).replace("\n", "<br>\n")
                if text:
                    output.append(f"<p>{text}</p>")
                i += 1
            elif block["kind"] == "list":
                items = [f"  <li>{escape(item)}</li>" for item in block["items"] if item]
                if items:
                    output.append("<ul>\n" + "\n".join(items) + "\n</ul>")
                i += 1
            elif block["kind"] == "image":
                # Consecutive image blocks share one .news-update-images div so the
                # site renders them as a single side-by-side gallery, not separated.
                imgs = []
                while i < len(blocks) and blocks[i]["kind"] == "image":
                    src = blocks[i].get("src")
                    if src:
                        imgs.append('  <img src="{}" alt="{}" />'.format(
                            escape(src, quote=True), escape(blocks[i].get("alt", ""), quote=True)))
                    i += 1
                if imgs:
                    output.append('<div class="news-update-images">\n' + "\n".join(imgs) + "\n</div>")
            elif block["kind"] == "table":
                rows = block.get("rows", [])
                if any(any(cell for cell in row) for row in rows):
                    html_rows = []
                    for ri, row in enumerate(rows):
                        tag = "th" if ri == 0 else "td"
                        cells = "".join("<{0}>{1}</{0}>".format(tag, escape(cell)) for cell in row)
                        html_rows.append("  <tr>{}</tr>".format(cells))
                    output.append("<table>\n" + "\n".join(html_rows) + "\n</table>")
                i += 1
            elif block["kind"] == "raw":
                output.append(block["html"])
                i += 1
            else:
                i += 1
        return "\n".join(output)

    def combo(self, parent, label, value, values, setter):
        ttk.Label(parent, text=label, style="Muted.TLabel").pack(anchor=tk.W, pady=(0, 3))
        var = tk.StringVar(value=value)
        cb = ttk.Combobox(parent, textvariable=var, values=values, state="readonly", width=18)
        cb.pack(anchor=tk.W, pady=(0, 12))
        var.trace_add("write", lambda *a: (setter(var.get()), self.mark_unsaved()))

    def check(self, parent, label, value, setter):
        var = tk.BooleanVar(value=bool(value))
        ttk.Checkbutton(parent, text=label, variable=var,
                        command=lambda: (setter(var.get()), self.mark_unsaved())).pack(anchor=tk.W, pady=(0, 12))

    def _browse(self, var):
        p = filedialog.askopenfilename(initialdir=os.path.join(BASE_DIR, "images"),
                                       filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.webp *.svg"),
                                                  ("All files", "*.*")])
        if not p:
            return
        try:
            rel = os.path.relpath(p, BASE_DIR)
        except ValueError:
            rel = p
        var.set(rel.replace("\\", "/"))

    def _update_image_preview(self, preview, path):
        path = path.strip()
        if not path:
            preview.configure(image="", text="")
            preview.image = None
            return
        if Image is None:
            preview.configure(image="", text="Install Pillow (py -m pip install pillow) to see image previews")
            preview.image = None
            return
        absolute_path = path if os.path.isabs(path) else os.path.join(BASE_DIR, path)
        try:
            with Image.open(absolute_path) as source:
                image = source.convert("RGBA")
                image.thumbnail((260, 150))
                photo = ImageTk.PhotoImage(image)
        except (OSError, ValueError):
            preview.configure(image="", text="Preview unavailable")
            preview.image = None
            return
        preview.configure(image=photo, text="")
        preview.image = photo

    # ---------- editors (one per structure) ----------
    def edit_member(self, ci, mi, iid):
        data = self.data_store["credits.json"]
        membership = data["categories"][ci]["members"][mi]
        mid = membership.get("id")
        team_obj = next((t for t in data["team"] if t.get("id") == mid), None)
        if team_obj is None:
            team_obj = {"id": mid, "name": mid, "image": None, "link": None, "alias": None}
            data["team"].append(team_obj)
        tree = self.trees["credits.json"]

        self._header("Team member")
        f = ttk.Frame(self.editor)
        f.pack(fill=tk.BOTH, expand=True)
        self.field(f, "Name", team_obj.get("name"),
                   lambda v: (team_obj.update(name=v), tree.item(iid, text=v or "(unnamed)")))
        self.field(f, "ID", team_obj.get("id"),
                   lambda v: (team_obj.update(id=v), membership.update(id=v)))
        self.field(f, "Alias", team_obj.get("alias"), lambda v: team_obj.update(alias=v or None))
        self.field(f, "Image", team_obj.get("image"), lambda v: team_obj.update(image=v or None), browse=True)
        self.field(f, "Link", team_obj.get("link"), lambda v: team_obj.update(link=v or None))
        self.text_field(f, "Roles (one per line)", "\n".join(membership.get("roles", [])),
                        lambda v: membership.update(roles=[l.strip() for l in v.splitlines() if l.strip()]),
                        height=8, expand=True)

    def edit_guest(self, gi, iid):
        guest = self.data_store["credits.json"]["guests"][gi]
        tree = self.trees["credits.json"]
        self._header("Guest artist")
        f = ttk.Frame(self.editor)
        f.pack(fill=tk.X)
        self.field(f, "Name", guest.get("name"),
                   lambda v: (guest.update(name=v), tree.item(iid, text=v or "(unnamed)")))
        self.field(f, "Link", guest.get("link"), lambda v: guest.update(link=v or None))

    def edit_credits_category(self, ci, iid):
        cat = self.data_store["credits.json"]["categories"][ci]
        tree = self.trees["credits.json"]
        self._header("Team category")
        f = ttk.Frame(self.editor)
        f.pack(fill=tk.X)
        self.field(f, "Title", cat.get("title"),
                   lambda v: (cat.update(title=v), tree.item(iid, text=v or "(untitled)")))
        ttk.Label(f, text="New (Ctrl+N) adds a member in this category · drag members between categories",
                  style="Muted.TLabel").pack(anchor=tk.W, pady=(8, 0))

    def edit_faq(self, i, iid):
        item = self.data_store["faq.json"][i]
        tree = self.trees["faq.json"]
        self._header("FAQ entry")
        f = ttk.Frame(self.editor)
        f.pack(fill=tk.BOTH, expand=True)
        self.text_field(f, "Question", item.get("question"),
                        lambda v: (item.update(question=v), tree.item(iid, text=v or "(untitled)")), height=3)
        self.text_field(f, "Answer", item.get("answer"),
                        lambda v: item.update(answer=v), height=10, expand=True)

    def edit_news(self, category, i, iid):
        item = self.data_store["news.json"][category][i]
        tree = self.trees["news.json"]
        self._header("Article")
        _, details, content = self._editor_notebook("Details", "Content")
        self.field(details, "Title", item.get("title"),
                   lambda v: (item.update(title=v), tree.item(iid, text=v or "(untitled)")))
        self.field(details, "Description", item.get("description"), lambda v: item.update(description=v))
        self.field(details, "Image", item.get("image"), lambda v: item.update(image=v or None), browse=True)
        self.field(details, "Date (YYYY-MM-DD)", item.get("date"), lambda v: item.update(date=v))
        self.html_field(content, "", item.get("content"),
                        lambda v: item.update(content=v or None), height=16, expand=True)

    def edit_wiki_category(self, cid, iid):
        cat = next((c for c in self.data_store["wiki.json"]["categories"] if c.get("id") == cid), None)
        if cat is None:
            return
        tree = self.trees["wiki.json"]
        self._header("Wiki category")
        f = ttk.Frame(self.editor)
        f.pack(fill=tk.X)
        self.field(f, "Name", cat.get("name"),
                   lambda v: (cat.update(name=v), tree.item(iid, text=v or "(untitled)")))
        ttk.Label(f, text=f"id: {cid} · New (Ctrl+N) adds an entry here · drag entries between categories",
                  style="Muted.TLabel").pack(anchor=tk.W, pady=(8, 0))

    def edit_wiki_entry(self, ei, iid):
        entry = self.data_store["wiki.json"]["entries"][ei]
        tree = self.trees["wiki.json"]
        self._header("Wiki entry")
        _, details, sections_tab = self._editor_notebook("Details", "Sections")
        self.field(details, "Name", entry.get("name"),
                   lambda v: (entry.update(name=v), tree.item(iid, text=v or "(untitled)")))
        self.field(details, "ID", entry.get("id"), lambda v: entry.update(id=v))
        row = ttk.Frame(details)
        row.pack(fill=tk.X)
        col1 = ttk.Frame(row)
        col1.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.field(col1, "Icon", entry.get("icon"), lambda v: entry.update(icon=v or None), browse=True)
        col2 = ttk.Frame(row)
        col2.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.field(col2, "Image", entry.get("image"), lambda v: entry.update(image=v or None), browse=True)
        self.html_field(details, "Intro", entry.get("intro") or entry.get("preview"),
                        lambda v: entry.update(intro=v or None), height=5)

        # sections
        if not isinstance(entry.get("sections"), list):
            entry["sections"] = []
            self.mark_unsaved()
        sections = entry["sections"]
        wrap = ttk.Frame(sections_tab)
        wrap.pack(fill=tk.BOTH, expand=True)
        left = ttk.Frame(wrap)
        left.pack(side=tk.LEFT, fill=tk.Y)
        lb = make_dark_listbox(left, width=26, height=18, exportselection=False)
        lb.pack(fill=tk.Y, expand=True)
        lbtns = ttk.Frame(left)
        lbtns.pack(fill=tk.X, pady=(4, 0))
        right = ttk.Frame(wrap)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))

        def load_section(idx):
            for w in right.winfo_children():
                w.destroy()
            if not (0 <= idx < len(sections)):
                return
            sec = sections[idx]

            def set_title(v, i=idx, s=sec):
                s["title"] = v
                lb.delete(i)
                lb.insert(i, v or "(untitled)")
                lb.selection_set(i)

            self.field(right, "Section title", sec.get("title"), set_title)
            self.html_field(right, "Content", sec.get("content"),
                            lambda v, s=sec: s.update(content=v), height=8, expand=True)

        def on_lb(_e):
            sel = lb.curselection()
            if sel:
                load_section(sel[0])

        def add_section():
            sections.append({"title": "New section", "content": ""})
            lb.insert(tk.END, "New section")
            lb.selection_clear(0, tk.END)
            lb.selection_set(tk.END)
            load_section(len(sections) - 1)
            self.mark_unsaved()

        def remove_section():
            sel = lb.curselection()
            if not sel:
                return
            idx = sel[0]
            del sections[idx]
            lb.delete(idx)
            for w in right.winfo_children():
                w.destroy()
            if sections:
                nxt = min(idx, len(sections) - 1)
                lb.selection_set(nxt)
                load_section(nxt)
            else:
                show_empty_state()
            self.mark_unsaved()

        def show_empty_state():
            for w in right.winfo_children():
                w.destroy()
            ttk.Label(right, text="No sections yet", style="Muted.TLabel").pack(anchor=tk.W, pady=(8, 6))
            ttk.Button(right, text="Add section", command=add_section).pack(anchor=tk.W)

        lb.bind("<<ListboxSelect>>", on_lb)
        ttk.Button(lbtns, text="Add section", command=add_section).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(lbtns, text="Remove", command=remove_section).pack(side=tk.LEFT, padx=(6, 0))
        for sec in sections:
            lb.insert(tk.END, sec.get("title") or "(untitled)")
        if sections:
            lb.selection_set(0)
            load_section(0)
        else:
            show_empty_state()

    # ---------- create (in place, straight into editing) ----------
    def create_category(self):
        """Add a real category (Team or Wiki). System pseudo-categories stay pinned below."""
        fname = self._current_fname()
        data = self.data_store[fname]
        if fname == "credits.json":
            data.setdefault("categories", []).append({"title": "New Category", "members": []})
            new_iid = f"cat_{len(data['categories']) - 1}"
        elif fname == "wiki.json":
            cid = self._unique_id("new-category", [c.get("id") for c in data["categories"]])
            data["categories"].append({"id": cid, "name": "New Category"})
            new_iid = f"wcat_{cid}"
        else:
            self.set_status("Categories exist only for Team and Wiki")
            return
        self.mark_unsaved()
        self.refresh_tree(fname)
        self._select(fname, new_iid)
        self.after(80, lambda: self._first_field.focus_set() if self._first_field else None)

    def create_item(self):
        fname = self._current_fname()
        tree = self.trees[fname]
        sel = tree.selection()
        sel_iid = sel[0] if sel else ""
        data = self.data_store[fname]
        new_iid = None

        if fname == "faq.json":
            new = {"question": "New question?", "answer": ""}
            pos = int(sel_iid[5:]) + 1 if sel_iid.startswith("item_") else len(data)
            data.insert(pos, new)
            new_iid = f"item_{pos}"

        elif fname == "news.json":
            category = "update"
            if sel_iid.startswith("news_"):
                category = sel_iid.split("_", 2)[1]
            articles = data[category]
            new = {"content": None, "date": datetime.now().strftime("%Y-%m-%d"), "description": "",
                   "image": None, "title": "New Article"}
            pos = int(sel_iid.rsplit("_", 1)[1]) + 1 if sel_iid.count("_") == 2 else len(articles)
            articles.insert(pos, new)
            new_iid = f"news_{category}_{pos}"

        elif fname == "credits.json":
            if sel_iid == "guests" or sel_iid.startswith("guest_"):
                data["guests"].append({"name": "New Guest", "link": None})
                new_iid = f"guest_{len(data['guests']) - 1}"
            else:
                if not data["categories"]:
                    self.set_status("No team category to add into")
                    return
                ci = 0
                if sel_iid.startswith("cat_"):
                    ci = int(sel_iid[4:])
                elif sel_iid.startswith("mem_"):
                    ci = int(sel_iid[4:].split("_")[0])
                mid = self._unique_id("new-member", [t.get("id") for t in data["team"]])
                data["team"].append({"id": mid, "name": "New Member", "image": None, "link": None, "alias": None})
                data["categories"][ci]["members"].append({"id": mid, "roles": []})
                new_iid = f"mem_{ci}_{len(data['categories'][ci]['members']) - 1}"

        elif fname == "wiki.json":
            cat = None
            if sel_iid.startswith("wcat_"):
                cat = sel_iid[5:] or None
            elif sel_iid.startswith("ent_"):
                cat = data["entries"][int(sel_iid[4:])].get("category")
            eid = self._unique_id("new-entry", [e.get("id") for e in data["entries"]])
            data["entries"].append({"category": cat, "content": None, "icon": None, "id": eid,
                                    "image": None, "intro": None, "name": "New Entry", "sections": []})
            new_iid = f"ent_{len(data['entries']) - 1}"

        if new_iid:
            self.mark_unsaved()
            self.refresh_tree(fname)
            self._select(fname, new_iid)
            self.after(80, lambda: self._first_field.focus_set() if self._first_field else None)

    @staticmethod
    def _unique_id(base, existing):
        if base not in existing:
            return base
        n = 2
        while f"{base}-{n}" in existing:
            n += 1
        return f"{base}-{n}"

    # ---------- delete ----------
    def delete_item(self):
        if not self.current:
            self.set_status("Select an item first")
            return
        fname, iid = self.current
        tree = self.trees[fname]
        if not tree.exists(iid):
            return
        label = tree.item(iid, "text")
        data = self.data_store[fname]

        # Built-in categories aren't user data and can't be deleted.
        if iid in ("guests", "uncat") or (iid.startswith("news_") and iid.count("_") == 1):
            self.set_status("This category is built in and cannot be deleted")
            return

        # Deleting a category takes its children with it — say so up front.
        child_note = ""
        if fname == "credits.json" and iid.startswith("cat_"):
            n = len(data["categories"][int(iid[4:])].get("members", []))
            if n:
                child_note = f"\n\nThis also deletes its {n} member(s)."
        elif fname == "wiki.json" and iid.startswith("wcat_"):
            n = sum(1 for e in data["entries"] if e.get("category") == iid[5:])
            if n:
                child_note = f"\n\nThis also deletes its {n} entr{'y' if n == 1 else 'ies'}."
        if not messagebox.askyesno("Delete", f'Delete "{label}"?{child_note}'):
            return

        def _prune_team(members):
            """Drop team records whose only membership was in the removed category."""
            for m in members:
                mid = m.get("id")
                if not any(mm.get("id") == mid for c in data["categories"] for mm in c.get("members", [])):
                    data["team"][:] = [t for t in data["team"] if t.get("id") != mid]

        if fname == "faq.json":
            del data[int(iid[5:])]
        elif fname == "news.json" and iid.count("_") == 2:
            _, category, index = iid.split("_", 2)
            del data[category][int(index)]
        elif fname == "credits.json":
            if iid.startswith("mem_"):
                ci, mi = map(int, iid[4:].split("_"))
                _prune_team([data["categories"][ci]["members"].pop(mi)])
            elif iid.startswith("guest_"):
                del data["guests"][int(iid[6:])]
            elif iid.startswith("cat_"):
                cat = data["categories"].pop(int(iid[4:]))
                _prune_team(cat.get("members", []))
        elif fname == "wiki.json":
            if iid.startswith("ent_"):
                del data["entries"][int(iid[4:])]
            elif iid.startswith("wcat_"):
                cid = iid[5:]
                data["entries"][:] = [e for e in data["entries"] if e.get("category") != cid]
                data["categories"][:] = [c for c in data["categories"] if c.get("id") != cid]
                if isinstance(data.get("groups"), list):
                    data["groups"] = [[g for g in grp if g != cid] for grp in data["groups"]]

        self.current = None
        self.mark_unsaved()
        self.refresh_tree(fname)
        self.clear_editor(HINT)
        self.set_status("Deleted")

    # ---------- drag & drop ----------
    DRAGGABLE = ("mem_", "guest_", "ent_", "item_", "news_")

    def _dnd_press(self, event, fname):
        iid = self.trees[fname].identify_row(event.y)
        self._drag = iid if iid and self._is_draggable(iid) else None
        self._drag_hover = None
        if self._drag:
            self.status_var.set("Choose a blue destination")
            self._update_drag_feedback(fname)

    def _dnd_motion(self, event, fname):
        if self._drag:
            tree = self.trees[fname]
            self._drag_hover = tree.identify_row(event.y)
            tree.configure(cursor="hand2" if self._can_drop(fname, self._drag, self._drag_hover) else "arrow")
            self._show_drop_destination(fname)
            self._update_drag_feedback(fname)

    def _dnd_release(self, event, fname):
        tree = self.trees[fname]
        tree.configure(cursor="")
        drag, self._drag = self._drag, None
        self._drag_hover = None
        self._clear_drag_feedback(fname)
        self.status_var.set("")
        if not drag:
            return
        target = tree.identify_row(event.y)
        if not self._can_drop(fname, drag, target):
            return
        new_iid = self._perform_move(fname, drag, target)
        if new_iid:
            self.mark_unsaved()
            self.refresh_tree(fname)
            self._select(fname, new_iid)
            self.set_status("Moved")

    @staticmethod
    def _is_category(iid):
        return (iid.startswith("cat_") or iid in ("guests", "uncat") or
                iid.startswith("wcat_") or (iid.startswith("news_") and iid.count("_") == 1))

    @staticmethod
    def _is_draggable(iid):
        return (iid.startswith(("mem_", "guest_", "ent_", "item_")) or
                (iid.startswith("news_") and iid.count("_") == 2))

    def _can_drop(self, fname, drag, target):
        if not target or target == drag:
            return False
        if fname == "faq.json":
            return drag.startswith("item_") and target.startswith("item_")
        if fname == "news.json":
            return (drag.startswith("news_") and drag.count("_") == 2 and
                    target.startswith("news_") and target.count("_") in (1, 2))
        if fname == "credits.json":
            return ((drag.startswith("mem_") and target.startswith(("cat_", "mem_"))) or
                    (drag.startswith("guest_") and target.startswith("guest_")))
        if fname == "wiki.json":
            return drag.startswith("ent_") and (target.startswith(("wcat_", "ent_")) or target == "uncat")
        return False

    def _clear_drag_feedback(self, fname):
        tree = self.trees[fname]
        for iid in self._iter_iids(tree):
            tree.item(iid, tags=())

    def _show_drop_destination(self, fname):
        target = self._drag_hover
        if not self._can_drop(fname, self._drag, target):
            self.status_var.set("This location cannot accept the item")
            return
        tree = self.trees[fname]
        label = tree.item(target, "text")
        if self._is_category(target):
            self.status_var.set(f"Drop in: {label}")
        else:
            self.status_var.set(f"Drop after: {label}")

    def _update_drag_feedback(self, fname):
        tree = self.trees[fname]
        for iid in self._iter_iids(tree):
            if iid == self._drag:
                tags = ("dragging",)
            elif iid == self._drag_hover and self._can_drop(fname, self._drag, iid):
                tags = ("drop-hover",)
            elif self._can_drop(fname, self._drag, iid):
                tags = ("drop-target",)
            elif self._is_category(iid):
                # Treeview has no alpha channel; muted text provides the half-opacity cue.
                tags = ("drop-disabled",)
            else:
                tags = ()
            tree.item(iid, tags=tags)

    def _perform_move(self, fname, drag, target):
        """Move/reorder `drag` relative to `target`. Only compatible structures accept a drop."""
        data = self.data_store[fname]

        if fname == "faq.json":
            if not target.startswith("item_"):
                return None
            i, j = int(drag[5:]), int(target[5:])
            t_obj = data[j]
            obj = data.pop(i)
            data.insert(data.index(t_obj) + 1, obj)
            return f"item_{data.index(obj)}"

        if fname == "news.json":
            if not self._can_drop(fname, drag, target):
                return None
            _, source_category, source_index = drag.split("_", 2)
            target_parts = target.split("_", 2)
            target_category = target_parts[1]
            article = data[source_category].pop(int(source_index))
            if len(target_parts) == 2:
                data[target_category].append(article)
            else:
                target_obj = data[target_category][int(target_parts[2])]
                data[target_category].insert(data[target_category].index(target_obj) + 1, article)
            return f"news_{target_category}_{data[target_category].index(article)}"

        if fname == "credits.json":
            if drag.startswith("mem_"):
                if target.startswith("cat_"):
                    cj, t_obj = int(target[4:]), None
                elif target.startswith("mem_"):
                    cj, mj = map(int, target[4:].split("_"))
                    t_obj = data["categories"][cj]["members"][mj]
                else:
                    return None  # guests: incompatible structure
                ci, mi = map(int, drag[4:].split("_"))
                m = data["categories"][ci]["members"].pop(mi)
                dest = data["categories"][cj]["members"]
                pos = dest.index(t_obj) + 1 if t_obj is not None else len(dest)
                dest.insert(pos, m)
                return f"mem_{cj}_{dest.index(m)}"
            if drag.startswith("guest_") and target.startswith("guest_"):
                i, j = int(drag[6:]), int(target[6:])
                t_obj = data["guests"][j]
                g = data["guests"].pop(i)
                data["guests"].insert(data["guests"].index(t_obj) + 1, g)
                return f"guest_{data['guests'].index(g)}"
            return None

        if fname == "wiki.json" and drag.startswith("ent_"):
            entries = data["entries"]
            e = entries[int(drag[4:])]
            if target.startswith("wcat_"):
                e["category"] = target[5:] or None
            elif target == "uncat":
                e["category"] = None
            elif target.startswith("ent_"):
                t_obj = entries[int(target[4:])]
                entries.remove(e)
                e["category"] = t_obj.get("category")
                entries.insert(entries.index(t_obj) + 1, e)
            else:
                return None
            return f"ent_{entries.index(e)}"

        return None

    # ---------- close ----------
    def on_close(self):
        if self.unsaved:
            r = messagebox.askyesnocancel("Unsaved changes", "Save before closing?")
            if r is None:
                return
            if r:
                self.save_all()
        self.destroy()


if __name__ == "__main__":
    try:
        DranimaContentManager().mainloop()
    except Exception:
        # Never close silently: leave a log and, if possible, a dialog explaining why.
        import traceback
        report = traceback.format_exc()
        try:
            with open(os.path.join(BASE_DIR, "editor_error.log"), "w", encoding="utf-8") as _fh:
                _fh.write(report)
        except Exception:
            pass
        try:
            from tkinter import messagebox
            messagebox.showerror("Dranima Content Manager failed to start", report)
        except Exception:
            pass
        raise
