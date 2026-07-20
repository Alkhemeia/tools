import sys
import tkinter as tk
from tkinter import ttk, messagebox
from controllers import CLICK_TYPE_MAP
from i18n import ACTION_DISPLAY_NAMES

class ActionDialog:
    """Dialog to create or edit macro actions."""
    def __init__(self, app, save_callback, action_data=None):
        self.app = app
        self.parent = app.root
        self.save_callback = save_callback
        self.action_data = action_data
        
        self.win = tk.Toplevel(self.parent)
        self.win.title(self.app.t("action_edit") if action_data else self.app.t("action_add"))
        self.win.geometry("380x365")
        self.win.resizable(False, False)
        self.win.transient(self.parent)
        self.win.grab_set()
        
        self.win.configure(bg="#1e1e2e")
        
        # Center the window on parent
        self.win.update_idletasks()
        px = self.parent.winfo_x()
        py = self.parent.winfo_y()
        pw = self.parent.winfo_width()
        ph = self.parent.winfo_height()
        w = 380
        h = 365
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.win.geometry(f"{w}x{h}+{x}+{y}")
        
        # Colors
        self.bg_dark = "#1e1e2e"
        self.bg_card = "#181825"
        self.fg_light = "#cdd6f4"
        
        # Layout container
        container = tk.Frame(self.win, bg=self.bg_dark, padx=15, pady=15)
        container.pack(fill="both", expand=True)
        
        # Header
        lbl_title = tk.Label(container, text=self.app.t("action_properties"), font=("Helvetica", 11, "bold"), fg="#b4befe", bg=self.bg_dark)
        lbl_title.pack(anchor="w", pady=(0, 15))
        
        # Action Type Selector
        type_frame = tk.Frame(container, bg=self.bg_dark)
        type_frame.pack(fill="x", pady=5)
        
        lbl_type = tk.Label(type_frame, text=self.app.t("action_type"), font=("Helvetica", 10), fg=self.fg_light, bg=self.bg_dark)
        lbl_type.pack(side="left", padx=(0, 10))
        
        types_internal = ["wait", "click", "key_combo", "type_text", "play_sound", "ntfy"]
        self.action_type_values = [ACTION_DISPLAY_NAMES[self.app.current_lang][t] for t in types_internal]
        
        self.action_type = tk.StringVar()
        if action_data:
            internal_type = action_data["type"]
            self.action_type.set(ACTION_DISPLAY_NAMES[self.app.current_lang].get(internal_type, self.action_type_values[0]))
        else:
            self.action_type.set(self.action_type_values[0])
        
        self.type_cb = ttk.Combobox(type_frame, textvariable=self.action_type, 
                                    values=self.action_type_values, 
                                    state="readonly", width=18, style='Combobox.TCombobox')
        self.type_cb.pack(side="left")
        self.type_cb.bind("<<ComboboxSelected>>", self.on_type_changed)
        
        self.action_enabled = tk.BooleanVar(value=True)
        if action_data:
            self.action_enabled.set(action_data.get("enabled", True))
            
        self.cb_enabled = tk.Checkbutton(type_frame, text=self.app.t("active"), variable=self.action_enabled,
                                         bg=self.bg_dark, fg=self.fg_light, activebackground=self.bg_dark,
                                         activeforeground=self.fg_light, selectcolor=self.bg_card)
        self.cb_enabled.pack(side="right", padx=(10, 0))
        
        # Dynamic Options Frame
        self.options_frame = tk.Frame(container, bg=self.bg_card, bd=1, relief="solid", highlightthickness=0)
        self.options_frame.pack(fill="both", expand=True, pady=15, padx=2)
        
        # Comment Input Frame
        comment_frame = tk.Frame(container, bg=self.bg_dark)
        comment_frame.pack(fill="x", side="bottom", pady=(0, 10))
        
        lbl_comment = tk.Label(comment_frame, text="Kommentar:", font=("Helvetica", 10), fg=self.fg_light, bg=self.bg_dark)
        lbl_comment.pack(side="left", padx=(0, 10))
        
        self.comment_val = tk.StringVar()
        if action_data:
            self.comment_val.set(action_data.get("comment", ""))
            
        self.comment_ent = tk.Entry(comment_frame, textvariable=self.comment_val, font=("Helvetica", 10), 
                                    bg=self.bg_card, fg=self.fg_light, relief="flat", insertbackground=self.fg_light, bd=2)
        self.comment_ent.pack(side="left", fill="x", expand=True)

        # Bottom Buttons
        btn_frame = tk.Frame(container, bg=self.bg_dark)
        btn_frame.pack(fill="x", side="bottom")
        
        btn_cancel = ttk.Button(btn_frame, text=self.app.t("action_cancel"), command=self.close)
        btn_cancel.pack(side="left", padx=5)
        
        btn_save = ttk.Button(btn_frame, text=self.app.t("action_save"), style='Primary.TButton', command=self.save)
        btn_save.pack(side="right", padx=5)
        
        # Values
        self.wait_ms = tk.StringVar(value="500")
        self.click_x = tk.StringVar(value="0")
        self.click_y = tk.StringVar(value="0")
        self.click_type_val = "left"
        
        self.key_combo_val = tk.StringVar(value="f5")
        self.type_text_val = tk.StringVar(value="Hello World")
        
        self.ntfy_topic = tk.StringVar(value="")
        self.ntfy_title = tk.StringVar(value="Color Monitor")
        self.ntfy_message = tk.StringVar(value="Alarm: Farbänderung erkannt!")
        
        if action_data:
            if action_data["type"] == "wait":
                self.wait_ms.set(str(action_data["value"]))
            elif action_data["type"] == "click":
                self.click_x.set(str(action_data["x"]))
                self.click_y.set(str(action_data["y"]))
                self.click_type_val = action_data.get("click_type", "left")
            elif action_data["type"] == "key_combo":
                self.key_combo_val.set(action_data.get("value", "f5"))
            elif action_data["type"] == "type_text":
                self.type_text_val.set(action_data.get("value", "Hello World"))
            elif action_data["type"] == "ntfy":
                self.ntfy_topic.set(action_data.get("topic", ""))
                self.ntfy_title.set(action_data.get("title", ""))
                self.ntfy_message.set(action_data.get("message", ""))
                
        self.show_fields()
        
    def on_type_changed(self, event):
        self.show_fields()
        
    def show_fields(self):
        for child in self.options_frame.winfo_children():
            child.destroy()
            
        a_type_disp = self.action_type.get()
        a_type = "wait"
        for k, v in ACTION_DISPLAY_NAMES[self.app.current_lang].items():
            if v == a_type_disp:
                a_type = k
                break
                
        if a_type == "wait":
            inner = tk.Frame(self.options_frame, bg=self.bg_card, padx=15, pady=20)
            inner.pack(fill="both", expand=True)
            
            lbl = tk.Label(inner, text=self.app.t("action_wait_time"), font=("Helvetica", 10), fg=self.fg_light, bg=self.bg_card)
            lbl.pack(anchor="w", pady=(0, 5))
            
            ent = tk.Entry(inner, textvariable=self.wait_ms, width=12, font=("Consolas", 10), bg="#313244", fg=self.fg_light, relief="flat", bd=2, insertbackground=self.fg_light)
            ent.pack(anchor="w")
            ent.focus_set()
            
        elif a_type == "click":
            inner = tk.Frame(self.options_frame, bg=self.bg_card, padx=15, pady=10)
            inner.pack(fill="both", expand=True)
            
            grid = tk.Frame(inner, bg=self.bg_card)
            grid.pack(fill="x", anchor="w", pady=(0, 5))
            
            lbl_x = tk.Label(grid, text=self.app.t("x_coordinate"), font=("Helvetica", 10), fg=self.fg_light, bg=self.bg_card)
            lbl_x.grid(row=0, column=0, sticky="w", pady=4, padx=(0, 10))
            ent_x = tk.Entry(grid, textvariable=self.click_x, width=8, font=("Consolas", 10), bg="#313244", fg=self.fg_light, relief="flat", bd=2, insertbackground=self.fg_light)
            ent_x.grid(row=0, column=1, sticky="w", pady=4)
            
            lbl_y = tk.Label(grid, text=self.app.t("y_coordinate"), font=("Helvetica", 10), fg=self.fg_light, bg=self.bg_card)
            lbl_y.grid(row=1, column=0, sticky="w", pady=4, padx=(0, 10))
            ent_y = tk.Entry(grid, textvariable=self.click_y, width=8, font=("Consolas", 10), bg="#313244", fg=self.fg_light, relief="flat", bd=2, insertbackground=self.fg_light)
            ent_y.grid(row=1, column=1, sticky="w", pady=4)
            
            lbl_click_type = tk.Label(grid, text=self.app.t("action_click_type"), font=("Helvetica", 10), fg=self.fg_light, bg=self.bg_card)
            lbl_click_type.grid(row=2, column=0, sticky="w", pady=4, padx=(0, 10))
            
            click_types_translated = [self.app.t("left_click"), self.app.t("right_click"), self.app.t("double_click")]
            self.click_type_var = tk.StringVar(value=self.app.t(self.click_type_val + "_click"))
            click_type_cb = ttk.Combobox(grid, textvariable=self.click_type_var, values=click_types_translated, state="readonly", width=18, style='Combobox.TCombobox')
            click_type_cb.grid(row=2, column=1, sticky="w", pady=4)
            
            btn_pick = ttk.Button(inner, text=self.app.t("action_pick_coords"), command=self.pick_position)
            btn_pick.pack(fill="x", pady=5)
            
        elif a_type == "key_combo":
            inner = tk.Frame(self.options_frame, bg=self.bg_card, padx=15, pady=15)
            inner.pack(fill="both", expand=True)
            
            lbl = tk.Label(inner, text=self.app.t("action_shortcut_label"), font=("Helvetica", 10), fg=self.fg_light, bg=self.bg_card)
            lbl.pack(anchor="w", pady=(0, 5))
            
            ent = tk.Entry(inner, textvariable=self.key_combo_val, width=22, font=("Consolas", 10), bg="#313244", fg=self.fg_light, relief="flat", bd=2, insertbackground=self.fg_light)
            ent.pack(anchor="w")
            ent.focus_set()
            
        elif a_type == "type_text":
            inner = tk.Frame(self.options_frame, bg=self.bg_card, padx=15, pady=15)
            inner.pack(fill="both", expand=True)
            
            lbl = tk.Label(inner, text=self.app.t("action_text_label"), font=("Helvetica", 10), fg=self.fg_light, bg=self.bg_card)
            lbl.pack(anchor="w", pady=(0, 5))
            
            ent = tk.Entry(inner, textvariable=self.type_text_val, width=22, font=("Helvetica", 10), bg="#313244", fg=self.fg_light, relief="flat", bd=2, insertbackground=self.fg_light)
            ent.pack(anchor="w")
            ent.focus_set()
            
        elif a_type == "play_sound":
            inner = tk.Frame(self.options_frame, bg=self.bg_card, padx=15, pady=25)
            inner.pack(fill="both", expand=True)
            
            lbl = tk.Label(inner, text=self.app.t("action_sound_label"), font=("Helvetica", 10), fg=self.fg_light, bg=self.bg_card)
            lbl.pack(anchor="center")
            
        elif a_type == "ntfy":
            inner = tk.Frame(self.options_frame, bg=self.bg_card, padx=15, pady=10)
            inner.pack(fill="both", expand=True)
            
            grid = tk.Frame(inner, bg=self.bg_card)
            grid.pack(fill="both", expand=True)
            
            tk.Label(grid, text=self.app.t("action_ntfy_topic"), font=("Helvetica", 9), fg=self.fg_light, bg=self.bg_card).grid(row=0, column=0, sticky="w", pady=4)
            ent_top = tk.Entry(grid, textvariable=self.ntfy_topic, width=22, font=("Consolas", 9), bg="#313244", fg=self.fg_light, relief="flat", bd=2, insertbackground=self.fg_light)
            ent_top.grid(row=0, column=1, sticky="w", pady=4, padx=(5, 0))
            ent_top.focus_set()
            
            tk.Label(grid, text=self.app.t("action_ntfy_title"), font=("Helvetica", 9), fg=self.fg_light, bg=self.bg_card).grid(row=1, column=0, sticky="w", pady=4)
            ent_ttl = tk.Entry(grid, textvariable=self.ntfy_title, width=22, font=("Helvetica", 9), bg="#313244", fg=self.fg_light, relief="flat", bd=2, insertbackground=self.fg_light)
            ent_ttl.grid(row=1, column=1, sticky="w", pady=4, padx=(5, 0))
            
            tk.Label(grid, text=self.app.t("action_ntfy_message"), font=("Helvetica", 9), fg=self.fg_light, bg=self.bg_card).grid(row=2, column=0, sticky="w", pady=4)
            ent_msg = tk.Entry(grid, textvariable=self.ntfy_message, width=22, font=("Helvetica", 9), bg="#313244", fg=self.fg_light, relief="flat", bd=2, insertbackground=self.fg_light)
            ent_msg.grid(row=2, column=1, sticky="w", pady=4, padx=(5, 0))

    def pick_position(self):
        should_hide = self.app.hide_on_pick.get()
        if should_hide:
            self.app.saved_geometry = self.parent.geometry()
            self.win_geometry = self.win.geometry()
            self.win.withdraw()
            self.parent.withdraw()
            self.parent.update()
            time.sleep(0.25)
        PositionPicker(self.win, self.on_position_picked)
        
    def on_position_picked(self, x, y):
        should_hide = self.app.hide_on_pick.get()
        if should_hide:
            self.parent.deiconify()
            if hasattr(self.app, 'saved_geometry') and self.app.saved_geometry:
                self.parent.geometry(self.app.saved_geometry)
            self.win.deiconify()
            if hasattr(self, 'win_geometry') and self.win_geometry:
                self.win.geometry(self.win_geometry)
            self.parent.update()
            self.win.update()
        else:
            self.win.deiconify()
            self.win.update()
            
        if x is not None and y is not None:
            self.click_x.set(str(x))
            self.click_y.set(str(y))

    def save(self):
        a_type_disp = self.action_type.get()
        a_type = "wait"
        for k, v in ACTION_DISPLAY_NAMES[self.app.current_lang].items():
            if v == a_type_disp:
                a_type = k
                break
                
        action = None
        if a_type == "wait":
            try:
                val = int(self.wait_ms.get())
                if val < 0:
                    raise ValueError
                action = {"type": "wait", "value": val, "enabled": self.action_enabled.get()}
            except ValueError:
                messagebox.showerror(self.app.t("int_err_title"), self.app.t("int_err_ms"))
                return
        elif a_type == "click":
            try:
                x = int(self.click_x.get())
                y = int(self.click_y.get())
                
                val_disp = self.click_type_var.get()
                ct = "left"
                if val_disp == self.app.t("right_click"):
                    ct = "right"
                elif val_disp == self.app.t("double_click"):
                    ct = "double"
                    
                if x < 0 or y < 0:
                    raise ValueError
                action = {"type": "click", "x": x, "y": y, "click_type": ct, "enabled": self.action_enabled.get()}
            except ValueError:
                messagebox.showerror(self.app.t("int_err_title"), self.app.t("int_err_xy"))
                return
        elif a_type == "key_combo":
            val = self.key_combo_val.get().strip()
            if not val:
                messagebox.showerror(self.app.t("int_err_title"), self.app.t("int_err_key"))
                return
            action = {"type": "key_combo", "value": val, "enabled": self.action_enabled.get()}
        elif a_type == "type_text":
            val = self.type_text_val.get()
            action = {"type": "type_text", "value": val, "enabled": self.action_enabled.get()}
        elif a_type == "play_sound":
            action = {"type": "play_sound", "enabled": self.action_enabled.get()}
        elif a_type == "ntfy":
            top = self.ntfy_topic.get().strip()
            ttl = self.ntfy_title.get().strip()
            msg = self.ntfy_message.get().strip()
            
            if not top:
                messagebox.showerror(self.app.t("int_err_title"), self.app.t("int_err_topic"))
                return
                
            action = {
                "type": "ntfy",
                "topic": top,
                "title": ttl,
                "message": msg,
                "enabled": self.action_enabled.get()
            }

        if action:
            comment = self.comment_val.get().strip()
            if comment:
                action["comment"] = comment
            self.save_callback(action)
            self.close()

    def close(self):
        self.win.destroy()

class RegionOverlayBorder:
    """Creates a transparent red border around the monitored screen region using 4 thin windows and 4 corner squares."""
    def __init__(self, parent, on_drag_callback=None):
        self.parent = parent
        self.on_drag_callback = on_drag_callback
        self.visible = False
        self.x1, self.y1, self.x2, self.y2 = 0, 0, 0, 0
        
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.drag_start_x1 = 0
        self.drag_start_y1 = 0
        self.drag_start_x2 = 0
        self.drag_start_y2 = 0
        
        self.windows = []
        # Store cursors for Top (0), Bottom (1), Left (2), Right (3), Top-Left (4), Top-Right (5), Bottom-Left (6), Bottom-Right (7)
        self.cursors = [
            "sb_v_double_arrow", "sb_v_double_arrow", "sb_h_double_arrow", "sb_h_double_arrow",
            "top_left_corner", "top_right_corner", "bottom_left_corner", "bottom_right_corner"
        ]
        
        for i in range(8):
            win = tk.Toplevel(parent)
            win.overrideredirect(True)
            win.attributes("-topmost", True)
            win.configure(bg="#ff4f4f")
            win.configure(cursor=self.cursors[i])
            win.withdraw()
            
            # Bind drag & drop events (pass index i so we know which border is being dragged)
            win.bind("<Button-1>", lambda event, idx=i: self.on_press(event, idx))
            win.bind("<B1-Motion>", lambda event, idx=i: self.on_drag(event, idx))
            
            # Shift + click/drag to move the entire box
            win.bind("<Shift-Button-1>", lambda event: self.on_press_move(event))
            win.bind("<Shift-B1-Motion>", lambda event: self.on_drag_move(event))
            
            # Key bindings on individual overlay windows
            win.bind("<KeyPress-Shift_L>", self.set_move_cursors)
            win.bind("<KeyPress-Shift_R>", self.set_move_cursors)
            win.bind("<KeyRelease-Shift_L>", self.restore_resize_cursors)
            win.bind("<KeyRelease-Shift_R>", self.restore_resize_cursors)
            
            self.windows.append(win)
            
        # Bind key events to parent root window to capture them globally
        parent.bind("<KeyPress-Shift_L>", self.set_move_cursors, add="+")
        parent.bind("<KeyPress-Shift_R>", self.set_move_cursors, add="+")
        parent.bind("<KeyRelease-Shift_L>", self.restore_resize_cursors, add="+")
        parent.bind("<KeyRelease-Shift_R>", self.restore_resize_cursors, add="+")
        
    def set_move_cursors(self, event=None):
        for win in self.windows:
            try:
                win.configure(cursor="fleur")
            except:
                pass
                
    def restore_resize_cursors(self, event=None):
        for win, cur in zip(self.windows, self.cursors):
            try:
                win.configure(cursor=cur)
            except:
                pass
            
    def on_press(self, event, idx):
        self.drag_start_x = event.x_root
        self.drag_start_y = event.y_root
        self.drag_start_x1 = self.x1
        self.drag_start_y1 = self.y1
        self.drag_start_x2 = self.x2
        self.drag_start_y2 = self.y2
        
    def on_drag(self, event, idx):
        dx = event.x_root - self.drag_start_x
        dy = event.y_root - self.drag_start_y
        
        new_x1, new_y1, new_x2, new_y2 = self.x1, self.y1, self.x2, self.y2
        
        # Determine which edges/corners to resize based on window index
        if idx in (0, 4, 5):  # Top / Top-Left / Top-Right
            new_y1 = self.drag_start_y1 + dy
            if new_y2 - new_y1 < 2:
                new_y1 = new_y2 - 2
        
        if idx in (1, 6, 7):  # Bottom / Bottom-Left / Bottom-Right
            new_y2 = self.drag_start_y2 + dy
            if new_y2 - new_y1 < 2:
                new_y2 = new_y1 + 2
                
        if idx in (2, 4, 6):  # Left / Top-Left / Bottom-Left
            new_x1 = self.drag_start_x1 + dx
            if new_x2 - new_x1 < 2:
                new_x1 = new_x2 - 2
                
        if idx in (3, 5, 7):  # Right / Top-Right / Bottom-Right
            new_x2 = self.drag_start_x2 + dx
            if new_x2 - new_x1 < 2:
                new_x2 = new_x1 + 2
                
        if self.on_drag_callback:
            self.on_drag_callback(new_x1, new_y1, new_x2, new_y2)
            
    def on_press_move(self, event):
        self.drag_start_x = event.x_root
        self.drag_start_y = event.y_root
        self.drag_start_x1 = self.x1
        self.drag_start_y1 = self.y1
        self.drag_start_x2 = self.x2
        self.drag_start_y2 = self.y2
        
    def on_drag_move(self, event):
        dx = event.x_root - self.drag_start_x
        dy = event.y_root - self.drag_start_y
        
        new_x1 = self.drag_start_x1 + dx
        new_y1 = self.drag_start_y1 + dy
        new_x2 = self.drag_start_x2 + dx
        new_y2 = self.drag_start_y2 + dy
        
        if self.on_drag_callback:
            self.on_drag_callback(new_x1, new_y1, new_x2, new_y2)
            
    def update_position(self, x1, y1, x2, y2):
        self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2
        if x2 <= x1 or y2 <= y1:
            self.hide()
            return
            
        w = x2 - x1
        h = y2 - y1
        thickness = 4  # Border line thickness
        cs = 8         # Corner square size (8x8 px)
        
        # Position borders exactly outside the bbox (x1, y1, x2, y2)
        # to prevent them from being captured in screenshot grabs.
        geoms = [
            # 0: Top
            f"{w + 2*thickness}x{thickness}+{x1 - thickness}+{y1 - thickness}",
            # 1: Bottom
            f"{w + 2*thickness}x{thickness}+{x1 - thickness}+{y2}",
            # 2: Left
            f"{thickness}x{h}+{x1 - thickness}+{y1}",
            # 3: Right
            f"{thickness}x{h}+{x2}+{y1}",
            
            # 4: Top-Left
            f"{cs}x{cs}+{x1 - thickness - cs//2}+{y1 - thickness - cs//2}",
            # 5: Top-Right
            f"{cs}x{cs}+{x2 + thickness - cs//2}+{y1 - thickness - cs//2}",
            # 6: Bottom-Left
            f"{cs}x{cs}+{x1 - thickness - cs//2}+{y2 + thickness - cs//2}",
            # 7: Bottom-Right
            f"{cs}x{cs}+{x2 + thickness - cs//2}+{y2 + thickness - cs//2}"
        ]
        
        for win, geom in zip(self.windows, geoms):
            win.geometry(geom)
            if self.visible:
                win.deiconify()
                
    def show(self, x1, y1, x2, y2):
        self.visible = True
        self.update_position(x1, y1, x2, y2)
        
    def hide(self):
        self.visible = False
        for win in self.windows:
            win.withdraw()
            
    def destroy(self):
        for win in self.windows:
            try:
                win.destroy()
            except:
                pass


