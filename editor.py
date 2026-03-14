import copy
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import shutil
from datetime import datetime

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "datas")
FILES = ["credits.json", "faq.json", "news.json", "wiki.json"]


def _looks_like_image(path: str) -> bool:
    if not isinstance(path, str):
        return False
    return path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'))

class UltimateEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Dranima Ultimate Data Editor")
        self.geometry("1100x700")
        self.data_store = {}
        self.current_path = None
        
        self.setup_styles()
        self.setup_ui()
        self.load_all_files()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=25)
        style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"))

    def setup_ui(self):
        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(self.paned)
        self.paned.add(left_frame, weight=1)
        
        ttk.Label(left_frame, text=" Structure Explorer", style="Header.TLabel").pack(fill=tk.X, pady=5)
        
        self.tree = ttk.Treeview(left_frame, selectmode="browse")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        
        tree_btns = ttk.Frame(left_frame)
        tree_btns.pack(fill=tk.X)
        self.dup_button = ttk.Button(tree_btns, text="⧉ Duplicate", command=self.duplicate_item, state=tk.DISABLED)
        self.dup_button.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.remove_button = ttk.Button(tree_btns, text="🗑️ Remove", command=self.remove_node, state=tk.DISABLED)
        self.remove_button.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.right_frame = ttk.Frame(self.paned)
        self.paned.add(self.right_frame, weight=2)
        
        ttk.Label(self.right_frame, text=" Properties", style="Header.TLabel").pack(fill=tk.X, pady=5, padx=10)
        
        self.prop_container = ttk.Frame(self.right_frame)
        self.prop_container.pack(fill=tk.BOTH, expand=True, padx=10)

        bottom = ttk.Frame(self)
        bottom.pack(fill=tk.X, pady=5)
        ttk.Button(bottom, text="💾 SAVE ALL CHANGES", command=self.save_all).pack(side=tk.RIGHT, padx=10)

    def load_all_files(self):
        for fname in FILES:
            path = os.path.join(DATA_DIR, fname)
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    self.data_store[fname] = json.load(f)
            else:
                self.data_store[fname] = []
        self.refresh_tree()

    def get_selected_path(self):
        selected = self.tree.selection()
        if not selected:
            return None
        node = selected[0]
        path = []
        while node:
            item = self.tree.item(node)
            path.append(item['values'][1])
            node = self.tree.parent(node)
        return list(reversed(path))

    def find_node_by_path(self, path):
        """Return tree node id matching a value-path, or None."""
        if not path:
            return None
        root_items = self.tree.get_children("")
        def matches(item, val):
            v = self.tree.item(item)['values'][1]
            return str(v) == str(val)

        node = None
        for item in root_items:
            if matches(item, path[0]):
                node = item
                break
        if not node:
            return None

        for val in path[1:]:
            found = None
            for child in self.tree.get_children(node):
                if matches(child, val):
                    found = child
                    break
            if not found:
                return None
            node = found
        return node

    def refresh_tree(self):
        previous_path = self.get_selected_path()
        self.tree.delete(*self.tree.get_children())
        for filename, content in self.data_store.items():
            root_node = self.tree.insert("", "end", text=filename, values=("file", filename))
            self.populate_tree(root_node, content)
        if previous_path:
            node = self.find_node_by_path(previous_path)
            if node:
                self.tree.selection_set(node)
                parent = self.tree.parent(node)
                while parent:
                    self.tree.item(parent, open=True)
                    parent = self.tree.parent(parent)

    def populate_tree(self, parent, data):
        if isinstance(data, dict):
            for key, value in data.items():
                node = self.tree.insert(parent, "end", text=str(key), values=("dict_key", key))
                self.populate_tree(node, value)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                label = f"[{i}]"
                if isinstance(item, dict):
                    label = item.get("name") or item.get("title") or item.get("id") or item.get("question") or label
                node = self.tree.insert(parent, "end", text=str(label), values=("list_idx", i))
                self.populate_tree(node, item)

    def get_data_at_node(self, node_id):
        """Walks up the tree to find the exact reference in self.data_store"""
        path = []
        curr = node_id
        while curr:
            path.append(self.tree.item(curr))
            curr = self.tree.parent(curr)
        path.reverse()

        value_path = [item['values'][1] for item in path]

        filename = value_path[0]
        target = self.data_store[filename]

        for step_val in value_path[1:]:
            if isinstance(target, list):
                try:
                    step_val = int(step_val)
                except Exception:
                    pass
            target = target[step_val]
        return target, filename, value_path

    def find_nearest_list_node(self, node_id):
        """Find nearest ancestor (or self) that points to a list in the data model."""
        curr = node_id
        while curr:
            target, _, _ = self.get_data_at_node(curr)
            if isinstance(target, list):
                return curr
            curr = self.tree.parent(curr)
        return None

    def update_duplicate_button(self, node_id):
        dup_target = self.find_nearest_list_node(node_id)
        if not dup_target:
            self.dup_button.config(state=tk.DISABLED)
            self.dup_target_node = None
            return

        self.dup_button.config(state=tk.NORMAL)
        self.dup_target_node = dup_target

    def on_tree_select(self, event):
        for widget in self.prop_container.winfo_children():
            widget.destroy()
            
        selected = self.tree.selection()
        if not selected: return
        
        node_id = selected[0]

        parent_id = self.tree.parent(node_id)
        can_delete = False
        if parent_id:
            parent_target, _, _ = self.get_data_at_node(parent_id)
            can_delete = isinstance(parent_target, list)

        self.remove_button.config(state=tk.NORMAL if can_delete else tk.DISABLED)
        if can_delete:
            self.update_duplicate_button(node_id)
        else:
            self.dup_button.config(state=tk.DISABLED)
            self.dup_target_node = None

        node_data = self.tree.item(node_id)
        
        if node_data['values'][0] == "file":
            ttk.Label(self.prop_container, text="Select an item inside to edit its values.").pack()
            return

        target, fname, path = self.get_data_at_node(node_id)
        
        if isinstance(target, (str, int, bool)):
            self.render_scalar_editor(target, node_id)
        elif isinstance(target, dict):
            self.render_dict_editor(target, node_id)
        else:
            ttk.Label(self.prop_container, text=f"Container: {type(target).__name__}\nUse '{self.dup_button['text']}' to duplicate.").pack()

    def render_scalar_editor(self, value, node_id):
        ttk.Label(self.prop_container, text="Value:").pack(anchor=tk.W)
        
        if isinstance(value, str) and (len(value) > 50 or '\n' in value):
            txt = tk.Text(self.prop_container, height=15, width=60)
            txt.insert("1.0", value)
            txt.pack(fill=tk.BOTH, expand=True)
            ttk.Button(self.prop_container, text="Update Text", command=lambda: self.update_val(node_id, txt.get("1.0", tk.END).strip())).pack(pady=5)
        else:
            var = tk.StringVar(value=str(value))
            ent = ttk.Entry(self.prop_container, textvariable=var, width=60)
            ent.pack(fill=tk.X, pady=5)
            ttk.Button(self.prop_container, text="Update Value", command=lambda: self.update_val(node_id, var.get())).pack(pady=5)

        if isinstance(value, str) and _looks_like_image(value):
            image_path = value
            if not os.path.isabs(image_path):
                image_path = os.path.join(BASE_DIR, image_path)
            if os.path.exists(image_path):
                try:
                    if Image and ImageTk:
                        pil = Image.open(image_path)
                        pil.thumbnail((450, 450), Image.LANCZOS)
                        tk_img = ImageTk.PhotoImage(pil)
                    else:
                        tk_img = tk.PhotoImage(file=image_path)
                except Exception:
                    tk_img = None
                if tk_img:
                    lbl = ttk.Label(self.prop_container, image=tk_img)
                    lbl.image = tk_img
                    lbl.pack(pady=10)

    def _get_dropdown_options(self, path, key):
        """Return a list of allowed values for a field, or None if no dropdown should be used."""
        if not path:
            return None
        file = path[0]

        if file == "credits.json" and key == "id":
            if "members" in path or "team" in path:
                team = self.data_store.get("credits.json", {}).get("team", [])
                return [m.get("id") for m in team if isinstance(m, dict) and "id" in m]

        if file == "news.json" and key == "type":
            return ["announcement", "update"]

        if file == "wiki.json" and key == "category":
            cats = self.data_store.get("wiki.json", {}).get("categories", [])
            return [c.get("id") for c in cats if isinstance(c, dict) and "id" in c]

        return None

    def render_dict_editor(self, target, node_id):
        ttk.Label(self.prop_container, text="Keys in this object:").pack(anchor=tk.W)

        path = self.get_data_at_node(node_id)[2]
        fields = []

        def make_string_field(f, key, value):
            var = tk.StringVar(value=str(value))
            ttk.Entry(f, textvariable=var).pack(side=tk.LEFT, fill=tk.X, expand=True)
            return var

        def make_bool_field(f, key, value):
            var = tk.BooleanVar(value=bool(value))
            cb = ttk.Checkbutton(f, variable=var)
            cb.pack(side=tk.LEFT, fill=tk.X)
            return var

        def make_dropdown_field(f, key, value, options):
            var = tk.StringVar(value=str(value))
            combo = ttk.Combobox(f, values=options, textvariable=var, state="readonly")
            combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
            return var

        for k, v in target.items():
            if not isinstance(v, (dict, list)):
                f = ttk.Frame(self.prop_container)
                f.pack(fill=tk.X)
                ttk.Label(f, text=f"{k}:", width=15).pack(side=tk.LEFT)

                options = self._get_dropdown_options(path, k)
                if isinstance(v, bool):
                    var = make_bool_field(f, k, v)
                elif options is not None:
                    var = make_dropdown_field(f, k, v, options)
                else:
                    var = make_string_field(f, k, v)

                fields.append((k, var))

        def update_all():
            for key, var in fields:
                self.update_dict_key(node_id, key, var.get())
            messagebox.showinfo("Success", "All values updated!")

        if fields:
            ttk.Button(self.prop_container, text="Update All", command=update_all).pack(pady=5)

    def update_val(self, node_id, new_val):
        parent_node = self.tree.parent(node_id)
        key = self.tree.item(node_id)['values'][1]
        target, _, _ = self.get_data_at_node(parent_node)
        
        if isinstance(target, list):
            try:
                key = int(key)
            except Exception:
                pass

        if isinstance(target[key], bool): target[key] = new_val.lower() in ('true', 'yes', '1')
        elif isinstance(target[key], int): target[key] = int(new_val)
        else: target[key] = new_val
        
        self.refresh_tree()
        self.on_tree_select(None)
        messagebox.showinfo("Success", "Value updated in memory!")

    def update_dict_key(self, node_id, key, new_val):
        target, _, _ = self.get_data_at_node(node_id)
        if isinstance(target[key], bool): target[key] = new_val.lower() in ('true', 'yes', '1')
        elif isinstance(target[key], int): target[key] = int(new_val)
        else: target[key] = new_val
        self.refresh_tree()

    def _make_default_item(self, path):
        """Create a reasonable default object based on the path context."""
        if not path or len(path) < 2:
            return {}
        key = str(path[1]).lower()

        if "team" in key or "members" in key:
            team = self.data_store.get("credits.json", {}).get("team", [])
            first_id = None
            for m in team:
                if isinstance(m, dict) and "id" in m:
                    first_id = m["id"]
                    break

            if "members" in key:
                return {"id": first_id or "new_id", "roles": []}
            return {"id": first_id or "new_id", "name": "New Member", "image": "images/image_users/placeholder.png", "roles": []}
        if "faq" in key:
            return {"question": "New question", "answer": "New answer"}
        if "news" in key:
            return {"type": "update", "important": False, "title": "New update", "image": "", "description": "", "content": "", "date": "2026-01-01"}
        if "entries" in key or "wiki" in key:
            return {"id": "new-entry", "name": "New entry", "category": "", "icon": "images/template.png", "preview": "", "sections": []}
        if "guests" in key:
            return "New Guest"
        return {}

    def duplicate_item(self):
        selected = self.tree.selection()
        if not selected:
            return
        node_id = selected[0]
        parent_id = self.tree.parent(node_id)
        if not parent_id:
            return

        target, _, _ = self.get_data_at_node(parent_id)
        if not isinstance(target, list):
            return

        key = self.tree.item(node_id)['values'][1]
        try:
            key = int(key)
        except Exception:
            return

        item = target[key]
        dup = copy.deepcopy(item)
        target.insert(key + 1, dup)

        self.refresh_tree()

        path = self.get_data_at_node(parent_id)[2]
        new_path = path + [key + 1]
        node = self.find_node_by_path(new_path)
        if node:
            self.tree.selection_set(node)
            self.on_tree_select(None)

    def remove_node(self):
        selected = self.tree.selection()
        if not selected: return
        node_id = selected[0]
        parent_id = self.tree.parent(node_id)
        if not parent_id:
            return

        target, _, _ = self.get_data_at_node(parent_id)
        if not isinstance(target, list):
            messagebox.showwarning("Cannot delete", "You can only delete list items (e.g., FAQ entries / news items). Other keys and categories are protected.")
            return

        if messagebox.askyesno("Confirm", "Delete this item and all its contents?"):
            key = self.tree.item(node_id)['values'][1]
            try:
                key = int(key)
            except Exception:
                pass
            target.pop(key)
            self.refresh_tree()

    def save_all(self):
        for fname, content in self.data_store.items():
            path = os.path.join(DATA_DIR, fname)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=4, ensure_ascii=False)
        messagebox.showinfo("Success", "All files saved!")

if __name__ == "__main__":
    app = UltimateEditor()
    app.mainloop()