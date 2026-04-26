import tkinter as tk
from tkinter import ttk, messagebox
import database as db

# ── Palette ────────────────────────────────────────────────────────────────
BG        = "#F5F7FA"
HEADER_BG = "#1E2A5E"
HEADER_FG = "#FFFFFF"
ACCENT    = "#4A6CF7"
ACCENT_HV = "#3A5CE5"
WHITE     = "#FFFFFF"
TEXT      = "#1A1A2E"
TEXT_MUTED= "#6B7280"
ROW_ALT   = "#EEF2FF"
BORDER    = "#E2E8F0"
DANGER    = "#EF4444"
DANGER_HV = "#DC2626"

FNT_H1  = ("Segoe UI", 22, "bold")
FNT_LBL = ("Segoe UI", 10)
FNT_BTN = ("Segoe UI", 10, "bold")
FNT_TBL = ("Segoe UI", 10)


# ── Shared widget helpers ──────────────────────────────────────────────────

def _sep(parent):
    tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=12)


def _action_bar(parent, buttons):
    bar = tk.Frame(parent, bg=WHITE, pady=10, padx=12)
    bar.pack(fill="x")
    for text, style, cmd in buttons:
        ttk.Button(bar, text=text, style=style, command=cmd).pack(side="left", padx=4)
    return bar


def _make_table(parent, columns, widths):
    frame = tk.Frame(parent, bg=WHITE)
    frame.pack(fill="both", expand=True, padx=12, pady=(0, 8))
    tree  = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
    for col, w in zip(columns, widths):
        tree.heading(col, text=col)
        tree.column(col, width=w, minwidth=50)
    tree.tag_configure("alt", background=ROW_ALT)
    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")
    return tree


def _add_sorting(tree):
    """Click a column header to sort ascending; click again for descending."""
    state = {"col": None, "asc": True}

    def _apply():
        col = state["col"]
        if col is None:
            return
        asc   = state["asc"]
        items = [(tree.set(iid, col), iid) for iid in tree.get_children("")]

        def key(x):
            v = x[0]
            if v == "":
                return (1, 0.0, "")
            try:
                return (0, float(v), "")
            except (ValueError, TypeError):
                return (0, 0.0, str(v).lower())

        items.sort(key=key, reverse=not asc)
        for i, (_, iid) in enumerate(items):
            tree.move(iid, "", i)
            tree.item(iid, tags=("alt",) if i % 2 else ())
        for c in tree["columns"]:
            tree.heading(c, text=c)
        tree.heading(col, text=col + (" ▲" if asc else " ▼"))

    def _sort(col):
        if state["col"] == col:
            state["asc"] = not state["asc"]
        else:
            state["col"] = col
            state["asc"] = True
        _apply()

    for col in tree["columns"]:
        tree.heading(col, command=lambda c=col: _sort(c))

    return _apply


def _filter_panel(parent, fields, search_cmd, clear_cmd):
    frame = tk.Frame(parent, bg=WHITE, pady=10, padx=12)
    frame.pack(fill="x")
    for col_i, (lbl, var, w) in enumerate(fields):
        c = col_i * 2
        tk.Label(frame, text=lbl, bg=WHITE, fg=TEXT_MUTED,
                 font=("Segoe UI", 9)).grid(row=0, column=c, sticky="w",
                                            padx=(0 if col_i == 0 else 10, 2))
        e = ttk.Entry(frame, textvariable=var, width=w)
        e.grid(row=1, column=c, sticky="ew", padx=(0 if col_i == 0 else 10, 0))
        e.bind("<Return>", lambda _e, f=search_cmd: f())
    bc = len(fields) * 2
    ttk.Button(frame, text="Search", style="Accent.TButton",
               command=search_cmd).grid(row=1, column=bc, padx=(14, 4))
    ttk.Button(frame, text="Clear", style="Secondary.TButton",
               command=clear_cmd).grid(row=1, column=bc + 1, padx=4)


def _center_window(win, w, h, parent):
    win.update_idletasks()
    x = parent.winfo_rootx() + max(0, (parent.winfo_width()  - w) // 2)
    y = parent.winfo_rooty() + max(0, (parent.winfo_height() - h) // 2)
    win.geometry(f"{w}x{h}+{x}+{y}")


# ── Base dialog ────────────────────────────────────────────────────────────

class _BaseDialog(tk.Toplevel):
    def __init__(self, parent, title, width, height):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()
        _center_window(self, width, height, parent)
        tk.Label(self, text=title, font=("Segoe UI", 14, "bold"),
                 bg=BG, fg=TEXT).pack(pady=(20, 10))

    def _field(self, label, var, row_frame=None):
        target = row_frame or self
        tk.Label(target, text=label, bg=BG, fg=TEXT_MUTED,
                 font=FNT_LBL, anchor="w").pack(fill="x", padx=24, pady=(4, 0))
        e = ttk.Entry(target, textvariable=var)
        e.pack(fill="x", padx=24, pady=(0, 2))
        return e

    def _combo(self, label, var, values):
        tk.Label(self, text=label, bg=BG, fg=TEXT_MUTED,
                 font=FNT_LBL, anchor="w").pack(fill="x", padx=24, pady=(4, 0))
        cb = ttk.Combobox(self, textvariable=var, values=values, state="readonly")
        cb.pack(fill="x", padx=24, pady=(0, 2))
        return cb

    def _btn_row(self, save_cmd):
        f = tk.Frame(self, bg=BG)
        f.pack(pady=14)
        ttk.Button(f, text="Save",   style="Accent.TButton",
                   command=save_cmd).pack(side="left", padx=6)
        ttk.Button(f, text="Cancel", style="Secondary.TButton",
                   command=self.destroy).pack(side="left", padx=6)


# ── Artist dialog ──────────────────────────────────────────────────────────

class ArtistDialog(_BaseDialog):
    def __init__(self, parent, on_save, initial=None):
        title = "Edit Artist" if initial else "Add Artist"
        super().__init__(parent, title, 420, 320)
        ini   = initial or {}
        self.on_save  = on_save
        self.v_name   = tk.StringVar(value=ini.get("name", ""))
        self.v_country= tk.StringVar(value=ini.get("country", ""))
        self.v_genre  = tk.StringVar(value=ini.get("genre", ""))
        self.v_year   = tk.StringVar(value=str(ini.get("active_year", "")) if ini.get("active_year") else "")
        self._field("Name *",              self.v_name)
        self._field("Country",             self.v_country)
        self._field("Genre",               self.v_genre)
        self._field("Active Since (Year)", self.v_year)
        self._btn_row(self._save)

    def _save(self):
        name = self.v_name.get().strip()
        if not name:
            messagebox.showwarning("Validation", "Please fill in the Name field.", parent=self)
            return
        year = self.v_year.get().strip()
        if year:
            try:
                year = int(year)
            except ValueError:
                messagebox.showwarning("Validation", "Active Since must be a number.", parent=self)
                return
        else:
            year = None
        self.on_save({"name": name, "country": self.v_country.get().strip(),
                      "genre": self.v_genre.get().strip(), "active_year": year})
        self.destroy()


# ── Album dialog ───────────────────────────────────────────────────────────

class AlbumDialog(_BaseDialog):
    def __init__(self, parent, on_save, initial=None):
        title = "Edit Album" if initial else "Add Album"
        super().__init__(parent, title, 440, 360)
        ini       = initial or {}
        self.on_save = on_save
        self.v_title  = tk.StringVar(value=ini.get("title", ""))
        self.v_year   = tk.StringVar(value=str(ini.get("release_year", "")) if ini.get("release_year") else "")
        self.v_genre  = tk.StringVar(value=ini.get("genre", ""))
        self.v_artist = tk.StringVar()

        self._field("Title *",       self.v_title)
        self._field("Release Year",  self.v_year)
        self._field("Genre",         self.v_genre)

        artists          = db.get_all_artists()
        self.artist_map  = {a["name"]: str(a["_id"]) for a in artists}
        cb = self._combo("Artist *", self.v_artist, list(self.artist_map))
        if ini.get("artist_name") in self.artist_map:
            self.v_artist.set(ini["artist_name"])

        self._btn_row(self._save)

    def _save(self):
        title = self.v_title.get().strip()
        if not title:
            messagebox.showwarning("Validation", "Please fill in the Title field.", parent=self)
            return
        if not self.v_artist.get():
            messagebox.showwarning("Validation", "Please select an artist.", parent=self)
            return
        year = self.v_year.get().strip()
        if year:
            try:
                year = int(year)
            except ValueError:
                messagebox.showwarning("Validation", "Release Year must be a number.", parent=self)
                return
        else:
            year = None
        self.on_save({"title": title, "release_year": year,
                      "genre": self.v_genre.get().strip(),
                      "artist_id": self.artist_map[self.v_artist.get()]})
        self.destroy()


# ── Song dialog ────────────────────────────────────────────────────────────

class SongDialog(_BaseDialog):
    def __init__(self, parent, on_save, initial=None):
        title = "Edit Song" if initial else "Add Song"
        super().__init__(parent, title, 450, 430)
        ini       = initial or {}
        self.on_save = on_save
        self.v_title  = tk.StringVar(value=ini.get("title", ""))
        self.v_dur    = tk.StringVar(value=ini.get("duration", ""))
        self.v_track  = tk.StringVar(value=str(ini.get("track_number", "")) if ini.get("track_number") else "")
        self.v_album  = tk.StringVar()
        self.v_artist = tk.StringVar()

        self._field("Title *", self.v_title)

        # Duration + Track on same row
        row = tk.Frame(self, bg=BG)
        row.pack(fill="x", padx=24, pady=(4, 2))
        tk.Label(row, text="Duration (m:ss)", bg=BG, fg=TEXT_MUTED, font=FNT_LBL).pack(side="left")
        ttk.Entry(row, textvariable=self.v_dur, width=9).pack(side="left", padx=(6, 20))
        tk.Label(row, text="Track #", bg=BG, fg=TEXT_MUTED, font=FNT_LBL).pack(side="left")
        ttk.Entry(row, textvariable=self.v_track, width=6).pack(side="left", padx=6)

        # Album dropdown
        albums          = db.get_all_albums()
        self.album_map  = {a.get("title", "?"): str(a["_id"]) for a in albums}
        self._album_artist = {}
        for a in albums:
            ai = a.get("artist_info") or {}
            if isinstance(ai, dict) and ai.get("name"):
                self._album_artist[str(a["_id"])] = (ai["name"], str(a.get("artist_id", "")))

        cb_al = self._combo("Album *", self.v_album, list(self.album_map))
        if ini.get("album_name") in self.album_map:
            self.v_album.set(ini["album_name"])
        cb_al.bind("<<ComboboxSelected>>", self._autofill_artist)

        # Artist dropdown
        artists         = db.get_all_artists()
        self.artist_map = {a["name"]: str(a["_id"]) for a in artists}
        self._combo("Artist *", self.v_artist, list(self.artist_map))
        if ini.get("artist_name") in self.artist_map:
            self.v_artist.set(ini["artist_name"])

        self._btn_row(self._save)

    def _autofill_artist(self, _event=None):
        album_id = self.album_map.get(self.v_album.get())
        if album_id and album_id in self._album_artist:
            name, _ = self._album_artist[album_id]
            if name in self.artist_map:
                self.v_artist.set(name)

    def _save(self):
        title = self.v_title.get().strip()
        if not title:
            messagebox.showwarning("Validation", "Please fill in the Title field.", parent=self)
            return
        if not self.v_album.get():
            messagebox.showwarning("Validation", "Please select an album.", parent=self)
            return
        if not self.v_artist.get():
            messagebox.showwarning("Validation", "Please select an artist.", parent=self)
            return
        track = self.v_track.get().strip()
        if track:
            try:
                track = int(track)
            except ValueError:
                messagebox.showwarning("Validation", "Track number must be a number.", parent=self)
                return
        else:
            track = None
        self.on_save({
            "title":        title,
            "duration":     self.v_dur.get().strip(),
            "track_number": track,
            "album_id":     self.album_map[self.v_album.get()],
            "artist_id":    self.artist_map[self.v_artist.get()],
        })
        self.destroy()


# ── Artists Tab ────────────────────────────────────────────────────────────

class ArtistsTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.configure(style="Card.TFrame")
        self.f_name    = tk.StringVar()
        self.f_country = tk.StringVar()
        self.f_genre   = tk.StringVar()

        _filter_panel(self,
            [("Artist Name", self.f_name, 20),
             ("Country",     self.f_country, 16),
             ("Genre",       self.f_genre, 16)],
            self.load, self.clear_filters)
        _sep(self)

        self.tree = _make_table(self,
            ("Name", "Country", "Genre", "Active Since"),
            (270, 160, 180, 110))
        self.tree.bind("<Double-1>", lambda _: self.edit())
        self._resort = _add_sorting(self.tree)

        _sep(self)
        _action_bar(self, [
            ("+ Add Artist",    "Accent.TButton",    self.add),
            ("Edit Selected",   "Secondary.TButton", self.edit),
            ("Delete Selected", "Danger.TButton",    self.delete),
        ])
        self.load()

    def load(self):
        rows = db.get_all_artists(self.f_name.get(), self.f_country.get(), self.f_genre.get())
        self.tree.delete(*self.tree.get_children())
        for i, a in enumerate(rows):
            self.tree.insert("", "end", iid=str(a["_id"]),
                values=(a.get("name",""), a.get("country",""),
                        a.get("genre",""),  a.get("active_year","")),
                tags=("alt",) if i % 2 else ())
        self._resort()

    def clear_filters(self):
        self.f_name.set(""); self.f_country.set(""); self.f_genre.set("")
        self.load()

    def add(self):
        ArtistDialog(self, on_save=self._on_add)

    def _on_add(self, data):
        db.insert_artist(**data)
        messagebox.showinfo("Success", "Artist added successfully.")
        self.load()

    def edit(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select an artist.")
            return
        vals = self.tree.item(sel[0])["values"]
        ini  = {"name": vals[0], "country": vals[1], "genre": vals[2], "active_year": vals[3]}
        ArtistDialog(self, on_save=lambda d: self._on_edit(sel[0], d), initial=ini)

    def _on_edit(self, artist_id, data):
        db.update_artist(artist_id, **data)
        messagebox.showinfo("Success", "Artist updated successfully.")
        self.load()

    def delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select an artist.")
            return
        name = self.tree.item(sel[0])["values"][0]
        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{name}'?"):
            return
        ok, msg = db.delete_artist(sel[0])
        (messagebox.showinfo if ok else messagebox.showerror)("Result", msg)
        self.load()


# ── Albums Tab ─────────────────────────────────────────────────────────────

class AlbumsTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.configure(style="Card.TFrame")
        self.f_title  = tk.StringVar()
        self.f_artist = tk.StringVar()
        self.f_genre  = tk.StringVar()
        self.f_year   = tk.StringVar()

        _filter_panel(self,
            [("Album Title", self.f_title, 20), ("Artist", self.f_artist, 16),
             ("Genre",       self.f_genre, 16), ("Year",   self.f_year,   8)],
            self.load, self.clear_filters)
        _sep(self)

        self.tree = _make_table(self,
            ("Title", "Artist", "Genre", "Release Year"),
            (310, 200, 160, 100))
        self.tree.bind("<Double-1>", lambda _: self.edit())
        self._resort = _add_sorting(self.tree)

        _sep(self)
        _action_bar(self, [
            ("+ Add Album",     "Accent.TButton",    self.add),
            ("Edit Selected",   "Secondary.TButton", self.edit),
            ("Delete Selected", "Danger.TButton",    self.delete),
        ])
        self.load()

    def load(self):
        rows = db.get_all_albums(self.f_title.get(), self.f_artist.get(),
                                  self.f_genre.get(),  self.f_year.get())
        self.tree.delete(*self.tree.get_children())
        for i, a in enumerate(rows):
            ai   = a.get("artist_info") or {}
            name = ai.get("name", "—") if isinstance(ai, dict) else "—"
            self.tree.insert("", "end", iid=str(a["_id"]),
                values=(a.get("title",""), name, a.get("genre",""), a.get("release_year","")),
                tags=("alt",) if i % 2 else ())
        self._resort()

    def clear_filters(self):
        self.f_title.set(""); self.f_artist.set("")
        self.f_genre.set(""); self.f_year.set("")
        self.load()

    def add(self):
        AlbumDialog(self, on_save=self._on_add)

    def _on_add(self, data):
        db.insert_album(**data)
        messagebox.showinfo("Success", "Album added successfully.")
        self.load()

    def edit(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select an album.")
            return
        vals = self.tree.item(sel[0])["values"]
        ini  = {"title": vals[0], "artist_name": vals[1],
                "genre": vals[2], "release_year": vals[3]}
        AlbumDialog(self, on_save=lambda d: self._on_edit(sel[0], d), initial=ini)

    def _on_edit(self, album_id, data):
        db.update_album(album_id, **data)
        messagebox.showinfo("Success", "Album updated successfully.")
        self.load()

    def delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select an album.")
            return
        title = self.tree.item(sel[0])["values"][0]
        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{title}'?"):
            return
        ok, msg = db.delete_album(sel[0])
        (messagebox.showinfo if ok else messagebox.showerror)("Result", msg)
        self.load()


# ── Songs Tab ──────────────────────────────────────────────────────────────

class SongsTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.configure(style="Card.TFrame")
        self.f_title  = tk.StringVar()
        self.f_album  = tk.StringVar()
        self.f_artist = tk.StringVar()

        _filter_panel(self,
            [("Song Title", self.f_title, 20),
             ("Album",      self.f_album, 20),
             ("Artist",     self.f_artist, 16)],
            self.load, self.clear_filters)
        _sep(self)

        self.tree = _make_table(self,
            ("#", "Title", "Album", "Artist", "Duration"),
            (45, 240, 250, 180, 90))
        self.tree.bind("<Double-1>", lambda _: self.edit())
        self._resort = _add_sorting(self.tree)

        _sep(self)
        _action_bar(self, [
            ("+ Add Song",      "Accent.TButton",    self.add),
            ("Edit Selected",   "Secondary.TButton", self.edit),
            ("Delete Selected", "Danger.TButton",    self.delete),
        ])
        self.load()

    def load(self):
        rows = db.get_all_songs(self.f_title.get(), self.f_album.get(), self.f_artist.get())
        self.tree.delete(*self.tree.get_children())
        for i, s in enumerate(rows):
            ai = s.get("album_info")  or {}
            ri = s.get("artist_info") or {}
            album_name  = ai.get("title", "—") if isinstance(ai, dict) else "—"
            artist_name = ri.get("name",  "—") if isinstance(ri, dict) else "—"
            self.tree.insert("", "end", iid=str(s["_id"]),
                values=(s.get("track_number",""), s.get("title",""),
                        album_name, artist_name, s.get("duration","")),
                tags=("alt",) if i % 2 else ())
        self._resort()

    def clear_filters(self):
        self.f_title.set(""); self.f_album.set(""); self.f_artist.set("")
        self.load()

    def add(self):
        SongDialog(self, on_save=self._on_add)

    def _on_add(self, data):
        db.insert_song(**data)
        messagebox.showinfo("Success", "Song added successfully.")
        self.load()

    def edit(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select a song.")
            return
        vals = self.tree.item(sel[0])["values"]
        ini  = {"track_number": vals[0], "title": vals[1],
                "album_name":   vals[2], "artist_name": vals[3], "duration": vals[4]}
        SongDialog(self, on_save=lambda d: self._on_edit(sel[0], d), initial=ini)

    def _on_edit(self, song_id, data):
        db.update_song(song_id, **data)
        messagebox.showinfo("Success", "Song updated successfully.")
        self.load()

    def delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select a song.")
            return
        title = self.tree.item(sel[0])["values"][1]
        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{title}'?"):
            return
        ok, msg = db.delete_song(sel[0])
        messagebox.showinfo("Success", msg)
        self.load()


# ── Statistics Tab ─────────────────────────────────────────────────────────

class StatisticsTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.configure(style="Card.TFrame")

        btn_bar = tk.Frame(self, bg=WHITE, pady=14, padx=12)
        btn_bar.pack(fill="x")
        tk.Label(btn_bar, text="Choose a report:", bg=WHITE, fg=TEXT,
                 font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 14))

        reports = [
            ("Albums per Artist", self._albums_per_artist),
            ("Songs per Album",   self._songs_per_album),
            ("Songs per Artist",  self._songs_per_artist),
            ("Albums by Genre",   self._albums_by_genre),
            ("All Songs Detail",  self._all_songs),
        ]
        for text, cmd in reports:
            ttk.Button(btn_bar, text=text, style="Secondary.TButton",
                       command=cmd).pack(side="left", padx=4)

        _sep(self)

        self.avg_lbl = tk.Label(self, text="", bg=WHITE, fg=ACCENT,
                                font=("Segoe UI", 11, "bold"))
        self.avg_lbl.pack(pady=(10, 2))

        self.result_area = tk.Frame(self, bg=WHITE)
        self.result_area.pack(fill="both", expand=True, padx=12, pady=8)

        self._tree = None
        self._refresh_avg()

    def _refresh_avg(self):
        avg = db.stat_avg_songs_per_album()
        self.avg_lbl.config(text=f"Average number of songs per album: {avg}")

    def _build_tree(self, columns, widths):
        for w in self.result_area.winfo_children():
            w.destroy()
        t = ttk.Treeview(self.result_area, columns=columns, show="headings", selectmode="none")
        for col, w in zip(columns, widths):
            t.heading(col, text=col)
            t.column(col, width=w, minwidth=50)
        t.tag_configure("alt", background=ROW_ALT)
        vsb = ttk.Scrollbar(self.result_area, orient="vertical", command=t.yview)
        t.configure(yscrollcommand=vsb.set)
        t.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        _add_sorting(t)
        self._tree = t
        return t

    def _albums_per_artist(self):
        t = self._build_tree(("Artist", "Number of Albums"), (320, 180))
        for i, r in enumerate(db.stat_albums_per_artist()):
            t.insert("", "end", values=(r.get("artist",""), r.get("album_count",0)),
                     tags=("alt",) if i % 2 else ())
        self._refresh_avg()

    def _songs_per_album(self):
        t = self._build_tree(("Album", "Number of Songs"), (380, 180))
        for i, r in enumerate(db.stat_songs_per_album()):
            t.insert("", "end", values=(r.get("album",""), r.get("song_count",0)),
                     tags=("alt",) if i % 2 else ())
        self._refresh_avg()

    def _songs_per_artist(self):
        t = self._build_tree(("Artist", "Number of Songs"), (320, 180))
        for i, r in enumerate(db.stat_songs_per_artist()):
            t.insert("", "end", values=(r.get("artist",""), r.get("song_count",0)),
                     tags=("alt",) if i % 2 else ())
        self._refresh_avg()

    def _albums_by_genre(self):
        t = self._build_tree(("Genre", "Number of Albums"), (320, 180))
        for i, r in enumerate(db.stat_albums_by_genre()):
            t.insert("", "end", values=(r.get("genre",""), r.get("count",0)),
                     tags=("alt",) if i % 2 else ())
        self._refresh_avg()

    def _all_songs(self):
        t = self._build_tree(
            ("#", "Title", "Album", "Artist", "Duration"),
            (45, 220, 250, 180, 90))
        for i, r in enumerate(db.stat_all_songs_with_details()):
            t.insert("", "end",
                values=(r.get("track_number",""), r.get("title",""),
                        r.get("album",""), r.get("artist",""), r.get("duration","")),
                tags=("alt",) if i % 2 else ())
        self._refresh_avg()


# ── Main application ───────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Music Album Archive")
        self.geometry("1120x720")
        self.minsize(900, 600)
        self.configure(bg=BG)

        if not db.check_connection():
            messagebox.showerror(
                "Connection Error",
                "Cannot connect to MongoDB at localhost:27017.\n\n"
                "Please start MongoDB and try again."
            )
            self.destroy()
            return

        self._apply_styles()
        self._build_header()
        self._build_tabs()

    def _apply_styles(self):
        s = ttk.Style(self)
        s.theme_use("clam")

        s.configure("TNotebook", background=BG, borderwidth=0)
        s.configure("TNotebook.Tab", background="#DDE3F5", foreground=TEXT_MUTED,
                    padding=[22, 8], font=("Segoe UI", 11), borderwidth=0)
        s.map("TNotebook.Tab",
              background=[("selected", WHITE)],
              foreground=[("selected", ACCENT)],
              padding=[("selected", [22, 11])])

        s.configure("Treeview", background=WHITE, foreground=TEXT,
                    fieldbackground=WHITE, font=FNT_TBL, rowheight=32, borderwidth=0)
        s.configure("Treeview.Heading", background=HEADER_BG, foreground=WHITE,
                    font=("Segoe UI", 10, "bold"), relief="flat", padding=8)
        s.map("Treeview",
              background=[("selected", ACCENT)],
              foreground=[("selected", WHITE)])
        s.map("Treeview.Heading", background=[("active", "#2A3A7A")])

        for name, bg, hv in [
            ("Accent",    ACCENT,  ACCENT_HV),
            ("Danger",    DANGER,  DANGER_HV),
            ("Secondary", BORDER,  "#CBD5E1"),
        ]:
            fg = WHITE if name != "Secondary" else TEXT
            s.configure(f"{name}.TButton", background=bg, foreground=fg,
                        font=FNT_BTN, borderwidth=0, focuscolor="none", padding=[14, 8])
            s.map(f"{name}.TButton",
                  background=[("active", hv), ("pressed", hv)])

        s.configure("Card.TFrame", background=WHITE, relief="flat")
        s.configure("TFrame",      background=BG)

    def _build_header(self):
        h = tk.Frame(self, bg=HEADER_BG, height=72)
        h.pack(fill="x")
        h.pack_propagate(False)
        tk.Label(h, text="♪", font=("Segoe UI", 26), bg=HEADER_BG, fg=WHITE
                 ).pack(side="left", padx=(22, 6), pady=10)
        tk.Label(h, text="Music Album Archive", font=FNT_H1, bg=HEADER_BG, fg=WHITE
                 ).pack(side="left", pady=10)

    def _build_tabs(self):
        outer = ttk.Frame(self)
        outer.pack(fill="both", expand=True, padx=14, pady=14)
        nb = ttk.Notebook(outer)
        nb.pack(fill="both", expand=True)
        nb.add(ArtistsTab(nb),    text="  Artists  ")
        nb.add(AlbumsTab(nb),     text="  Albums   ")
        nb.add(SongsTab(nb),      text="  Songs    ")
        nb.add(StatisticsTab(nb), text="  Statistics  ")


if __name__ == "__main__":
    App().mainloop()
