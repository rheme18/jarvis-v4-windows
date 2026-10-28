import sys
import json
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
try:
    from PIL import Image, ImageTk
except ImportError:  # The contact database remains usable without optional photo support.
    Image = ImageTk = None

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
PNGS_DIR = BASE_DIR / "database" / "pngs"
JSON_FILE = BASE_DIR / "database" / "people.json"

class CyberpersonUI:
    def __init__(self, target_person=None, parent=None):
        self._owns_root = parent is None
        self.root = tk.Tk() if self._owns_root else tk.Toplevel(parent)
        self.root.title("J.A.R.V.I.S V4 · KİŞİ VERİTABANI")
        self.root.geometry("1000x650")
        self.root.minsize(760, 480)
        self.root.configure(bg="#080B10")
        self.root.resizable(True, True)

        self.people = self.load_all_people()
        self.current_person = target_person or (self.people[0] if self.people else None)
        self.search_var = tk.StringVar()

        self.setup_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def load_all_people(self):
        if JSON_FILE.exists():
            try:
                data = json.loads(JSON_FILE.read_text(encoding="utf-8"))
                self.data_error = "" if isinstance(data, list) else "people.json biçimi geçersiz; kişi listesi bekleniyordu."
                return [person for person in data if isinstance(person, dict)] if isinstance(data, list) else []
            except (OSError, json.JSONDecodeError) as exc:
                self.data_error = f"people.json okunamadı: {exc}"
                return []
        self.data_error = ""
        return []

    def get_photo_image(self, person):
        if not person:
            return None
        
        photo_name = str(person.get("photo", "") or "")
        photo_path = None
        
        if photo_name and (PNGS_DIR / photo_name).exists():
            photo_path = PNGS_DIR / photo_name
        else:
            clean_name = str(person.get("name", "")).strip().lower().replace(" ", "_")
            for ext in [".png", ".jpg", ".jpeg"]:
                p = PNGS_DIR / f"{clean_name}{ext}"
                if p.exists():
                    photo_path = p
                    break
        
        if Image is not None and ImageTk is not None and photo_path and photo_path.exists():
            try:
                img = Image.open(photo_path)
                img = img.resize((180, 180), Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(img)
            except Exception:
                pass
        return None

    def setup_ui(self):
        # Header / Başlık
        header_frame = tk.Frame(self.root, bg="#0D131D", bd=1, relief="solid")
        header_frame.pack(fill="x", side="top", padx=14, pady=(14, 10))

        title_label = tk.Label(
            header_frame,
            text="⚡ J.A.R.V.I.S V4 · KİŞİ VERİTABANI ⚡",
            font=("Consolas", 16, "bold"),
            fg="#00F0FF",
            bg="#0D131D"
        )
        title_label.pack(pady=8)

        # Main Layout (Sol: Liste, Sağ: Profil Kartı)
        main_container = tk.Frame(self.root, bg="#080B10")
        main_container.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        # --- SOL PANEL: KİŞİ LİSTESİ ---
        left_panel = tk.Frame(main_container, bg="#0D131D", width=270, bd=1, relief="solid")
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)

        list_title = tk.Label(left_panel, text="KAYITLI KİŞİLER", font=("Consolas", 11, "bold"), fg="#FF0055", bg="#0D131D")
        list_title.pack(anchor="w", padx=10, pady=(10, 6))
        search = tk.Entry(left_panel, textvariable=self.search_var, bg="#05070A", fg="#D9E7EF",
                          insertbackground="#00F0FF", relief="flat", font=("Consolas", 10))
        search.pack(fill="x", padx=9, pady=(0, 5), ipady=7)
        self.search_var.trace_add("write", lambda *_: self.refresh_people())
        if self.data_error:
            tk.Label(left_panel, text="VERİTABANI OKUNAMADI\nKayıt ekleme kapalı",
                     bg="#0D131D", fg="#FF6685", justify="left",
                     font=("Consolas", 8, "bold")).pack(anchor="w", padx=10, pady=4)

        self.listbox = tk.Listbox(
            left_panel,
            bg="#05070A",
            fg="#00F0FF",
            selectbackground="#FF0055",
            selectforeground="#FFFFFF",
            font=("Consolas", 10),
            bd=0,
            highlightthickness=0
        )
        self.listbox.pack(fill="both", expand=True, padx=8, pady=5)
        self.people_count = tk.Label(left_panel, text="", font=("Consolas", 9), fg="#7A8B9E", bg="#0D131D")
        self.people_count.pack(anchor="w", padx=10, pady=(0, 5))
        actions = tk.Frame(left_panel, bg="#0D131D")
        actions.pack(fill="x", padx=7, pady=(0, 8))
        self._button(actions, "＋ EKLE", self.add_person, "#00F0FF").pack(side="left", fill="x", expand=True, padx=2)
        self._button(actions, "↻ YENİLE", self.reload_people, "#D9E7EF").pack(side="left", fill="x", expand=True, padx=2)
        self._button(actions, "− SİL", self.delete_person, "#FF6685").pack(side="left", fill="x", expand=True, padx=2)

        self.listbox.bind("<<ListboxSelect>>", self.on_person_select)
        self.listbox.bind("<Double-Button-1>", lambda _event: self.edit_person())
        self.root.bind("<Control-n>", lambda _event: self.add_person())
        self.root.bind("<Control-f>", lambda _event: search.focus_set())
        self.listbox.bind("<Delete>", lambda _event: self.delete_person())

        # --- SAĞ PANEL: PROFILE CARD ---
        self.right_panel = tk.Frame(main_container, bg="#0D131D", bd=1, relief="solid")
        self.right_panel.pack(side="right", fill="both", expand=True)

        self.refresh_people(self.current_person)
        self.render_person_details()

    @staticmethod
    def _button(parent, text, command, color):
        return tk.Button(parent, text=text, command=command, bg="#101D29", fg=color,
                         activebackground="#18303D", activeforeground=color,
                         relief="flat", bd=0, cursor="hand2", font=("Consolas", 9, "bold"),
                         padx=5, pady=7)

    def refresh_people(self, select_person=None):
        query = self.search_var.get().strip().casefold()
        self.visible_people = [p for p in self.people
                               if query in str(p.get("name", "")).casefold()
                               or query in str(p.get("tags", "")).casefold()]
        self.listbox.delete(0, tk.END)
        for person in self.visible_people:
            self.listbox.insert(tk.END, f"  {person.get('name', 'Bilinmeyen')}")
        self.people_count.configure(text=f"{len(self.visible_people)} / {len(self.people)} kayıt")
        if select_person:
            match = next((i for i, p in enumerate(self.visible_people)
                          if p.get("id") == select_person.get("id")
                          or p.get("name") == select_person.get("name")), None)
            if match is not None:
                self.listbox.selection_set(match)
                self.listbox.activate(match)

    def reload_people(self):
        selected = self.current_person
        self.people = self.load_all_people()
        self.current_person = next((p for p in self.people
                                    if selected and (p.get("id") == selected.get("id")
                                                     or p.get("name") == selected.get("name"))), None)
        if not self.current_person and self.people:
            self.current_person = self.people[0]
        self.refresh_people(self.current_person)
        self.render_person_details()

    def _selected_person(self):
        selection = self.listbox.curselection()
        return self.visible_people[selection[0]] if selection else None

    def add_person(self):
        self._open_person_editor()

    def edit_person(self):
        person = self._selected_person() or self.current_person
        if person:
            self._open_person_editor(person)

    def _open_person_editor(self, person=None):
        editing = person is not None
        dialog = tk.Toplevel(self.root)
        dialog.title("Kişiyi Düzenle" if editing else "Yeni Kişi")
        dialog.configure(bg="#0D131D")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        tk.Label(dialog, text="KİŞİ KARTI" if editing else "YENİ KİŞİ KAYDI",
                 bg="#0D131D", fg="#00F0FF", font=("Consolas", 14, "bold")).pack(anchor="w", padx=16, pady=(14, 10))
        form = tk.Frame(dialog, bg="#0D131D")
        form.pack(fill="both", padx=16)
        entries = {}
        for key, label in (("name", "İsim"), ("role", "Rol / Ünvan"), ("phone", "Telefon"),
                           ("email", "E-posta"), ("tags", "Etiketler")):
            tk.Label(form, text=label.upper(), bg="#0D131D", fg="#7A8B9E",
                     font=("Consolas", 8, "bold")).pack(anchor="w", pady=(5, 2))
            entry = tk.Entry(form, width=44, bg="#05070A", fg="#E0E0E0",
                             insertbackground="#00F0FF", relief="flat", font=("Consolas", 10))
            entry.pack(fill="x", ipady=5)
            entry.insert(0, str((person or {}).get(key, "")))
            entries[key] = entry
        tk.Label(form, text="NOTLAR", bg="#0D131D", fg="#7A8B9E",
                 font=("Consolas", 8, "bold")).pack(anchor="w", pady=(8, 2))
        notes = tk.Text(form, width=44, height=5, bg="#05070A", fg="#E0E0E0",
                        insertbackground="#00F0FF", relief="flat", font=("Consolas", 10), wrap="word")
        notes.pack(fill="x")
        notes.insert("1.0", str((person or {}).get("notes", "")))

        def save():
            if self.data_error:
                messagebox.showerror("Veritabanı okunamıyor", self.data_error, parent=dialog)
                return
            name = entries["name"].get().strip()
            if not name:
                messagebox.showwarning("Eksik bilgi", "Kişi adı boş bırakılamaz.", parent=dialog)
                return
            record = {key: entry.get().strip() for key, entry in entries.items()}
            record["notes"] = notes.get("1.0", "end-1c").strip()
            duplicate = next((p for p in self.people
                              if str(p.get("name", "")).casefold() == name.casefold()
                              and not (editing and (
                                  (person.get("id") is not None and p.get("id") == person.get("id"))
                                  or str(p.get("name", "")).casefold() == str(person.get("name", "")).casefold()
                              ))), None)
            if duplicate:
                messagebox.showwarning("Kayıt zaten var", "Bu isimle kayıtlı başka bir kişi var.", parent=dialog)
                return
            if editing:
                record["id"] = person.get("id")
                record["photo"] = person.get("photo", "")
                for index, existing in enumerate(self.people):
                    if ((person.get("id") is not None and existing.get("id") == person.get("id"))
                            or existing.get("name") == person.get("name")):
                        record["id"] = existing.get("id", record["id"])
                        self.people[index] = {**existing, **record}
                        break
            else:
                valid_ids = []
                for existing in self.people:
                    try:
                        valid_ids.append(int(existing.get("id", 0) or 0))
                    except (TypeError, ValueError):
                        continue
                record["id"] = max(valid_ids, default=0) + 1
                record["photo"] = ""
                self.people.append(record)
            try:
                from core.person_manager import save_people
                save_people(self.people)
            except Exception as exc:
                messagebox.showerror("Kayıt hatası", f"Kişi kaydedilemedi:\n{exc}", parent=dialog)
                return
            self.current_person = record
            dialog.destroy()
            self.refresh_people(record)
            self.render_person_details()

        footer = tk.Frame(dialog, bg="#0D131D")
        footer.pack(fill="x", padx=14, pady=14)
        self._button(footer, "VAZGEÇ", dialog.destroy, "#9AAAB8").pack(side="right", padx=3)
        self._button(footer, "KAYDET", save, "#00F0FF").pack(side="right", padx=3)
        dialog.bind("<Return>", lambda _event: save())

    def delete_person(self):
        if self.data_error:
            messagebox.showerror("Veritabanı okunamıyor", self.data_error, parent=self.root)
            return
        person = self._selected_person() or self.current_person
        if not person:
            return
        if not messagebox.askyesno("Kişiyi Sil", f"{person.get('name', 'Bu kişi')} kaydını silmek istiyor musun?", parent=self.root):
            return
        self.people = [p for p in self.people if not (
            (person.get("id") is not None and p.get("id") == person.get("id"))
            or p.get("name") == person.get("name"))]
        try:
            from core.person_manager import save_people
            save_people(self.people)
        except Exception as exc:
            messagebox.showerror("Silme hatası", f"Kayıt silinemedi:\n{exc}", parent=self.root)
            self.people = self.load_all_people()
        self.current_person = self.people[0] if self.people else None
        self.refresh_people(self.current_person)
        self.render_person_details()

    def render_person_details(self):
        for widget in self.right_panel.winfo_children():
            widget.destroy()

        p = self.current_person
        if not p:
            no_data = tk.Label(self.right_panel, text="KAYIT BULUNAMADI", font=("Consolas", 14), fg="#FF0055", bg="#0D131D")
            no_data.pack(expand=True)
            return

        # İç Container
        content = tk.Frame(self.right_panel, bg="#0D131D")
        content.pack(fill="both", expand=True, padx=20, pady=20)

        # Fotoğraf Alanı (Sol)
        photo_frame = tk.Frame(content, bg="#00F0FF", bd=2)
        photo_frame.grid(row=0, column=0, rowspan=6, padx=(0, 20), pady=10, sticky="n")

        self.photo_img = self.get_photo_image(p)
        if self.photo_img:
            img_lbl = tk.Label(photo_frame, image=self.photo_img, bg="#05070A")
            img_lbl.pack()
        else:
            no_img = tk.Label(photo_frame, text="NO IMAGE\nFOUND", font=("Consolas", 10, "bold"), fg="#FF0055", bg="#05070A", width=22, height=11)
            no_img.pack()

        # Detay Bilgileri (Sağ)
        fields = [
            ("İSİM", p.get("name", "-"), "#00F0FF"),
            ("ROL/UNVAN", p.get("role", "-"), "#E0E0E0"),
            ("TELEFON", p.get("phone", "-"), "#E0E0E0"),
            ("E-POSTA", p.get("email", "-"), "#E0E0E0"),
            ("ETİKETLER", p.get("tags", "-"), "#FF0055"),
            ("NOTLAR", p.get("notes", "-"), "#A0A0A0")
        ]

        content.grid_columnconfigure(2, weight=1)
        for i, (label, val, color) in enumerate(fields):
            lbl = tk.Label(content, text=f"{label}:", font=("Consolas", 10, "bold"), fg="#7A8B9E", bg="#0D131D", anchor="w")
            lbl.grid(row=i, column=1, sticky="w", pady=3)

            val_lbl = tk.Label(content, text=str(val or "-"), font=("Consolas", 11, "bold" if i==0 else "normal"), fg=color, bg="#0D131D", anchor="w", wraplength=420, justify="left")
            val_lbl.grid(row=i, column=2, sticky="w", padx=(10, 0), pady=3)

        actions = tk.Frame(content, bg="#0D131D")
        actions.grid(row=6, column=1, columnspan=2, sticky="w", pady=(22, 0))
        self._button(actions, "DÜZENLE", self.edit_person, "#00F0FF").pack(side="left", padx=(0, 7))
        self._button(actions, "TELEFONU KOPYALA", lambda: self.copy_field(p.get("phone", "")), "#D9E7EF").pack(side="left", padx=7)
        self._button(actions, "E-POSTAYI KOPYALA", lambda: self.copy_field(p.get("email", "")), "#D9E7EF").pack(side="left", padx=7)

    def copy_field(self, value):
        if not value or value == "-":
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(str(value))
        self.root.update_idletasks()

    def on_person_select(self, event):
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            self.current_person = self.visible_people[index]
            self.render_person_details()

    def run(self):
        if self._owns_root:
            self.root.mainloop()

    def close(self):
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def show_person(self, person=None):
        if person:
            self.current_person = person
            self.refresh_people(person)
            self.render_person_details()
        self.root.deiconify()
        self.root.lift()

if __name__ == "__main__":
    target = None
    if len(sys.argv) > 1:
        try:
            target = json.loads(sys.argv[1])
        except Exception:
            pass
    ui = CyberpersonUI(target)
    ui.run()
