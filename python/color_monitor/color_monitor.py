#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, colorchooser, messagebox, simpledialog
import time
import os
import sys
import numpy as np
from PIL import Image, ImageGrab, ImageTk, ImageDraw
import ctypes
from ctypes.util import find_library
import threading
import json
import locale
import urllib.request

from i18n import I18N, MODE_TRANSLATIONS, ACTION_DISPLAY_NAMES
from controllers import CLICK_TYPE_MAP, CLICK_TYPE_REV, KEY_SYM_MAP, X11MouseController, WindowsMouseController
from widgets import RegionOverlayBorder, ActionDialog

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")

class ColorMonitorApp:
    def t(self, key, *args):
        lang = getattr(self, "current_lang", "en")
        trans_dict = I18N.get(lang, I18N["en"])
        val = trans_dict.get(key, I18N["en"].get(key, key))
        if args:
            try:
                return val.format(*args)
            except Exception:
                pass
        return val

    def change_language(self, lang):
        self.current_lang = lang
        self.save_config()
        self.update_ui_text()
        self.update_zones_listbox()
        self.update_macro_listbox()
        if hasattr(self, 'menubar'):
            try:
                self.menubar.destroy()
            except:
                pass
        self.create_menu_bar()

    def update_mode_combobox(self):
        modes_internal = [
            "Ziel-Farbe erscheint",
            "Ziel-Farbe verschwindet",
            "Ziel-Farbe vorhanden",
            "Ziel-Farbe nicht vorhanden",
            "Generelle Farbänderung"
        ]
        translated_values = [MODE_TRANSLATIONS[self.current_lang][m] for m in modes_internal]
        self.mode_cb.config(values=translated_values)
        
        current_internal = self.mode.get()
        translated_active = MODE_TRANSLATIONS[self.current_lang].get(current_internal, current_internal)
        self.mode_cb.set(translated_active)

    def create_menu_bar(self):
        self.menubar = tk.Menu(self.root, bg="#11111b", fg="#cdd6f4", activebackground="#313244", activeforeground="#cdd6f4", relief="flat")
        self.root.config(menu=self.menubar)
        
        self.file_menu = tk.Menu(self.menubar, tearoff=0, bg="#11111b", fg="#cdd6f4", activebackground="#313244", activeforeground="#cdd6f4", relief="flat")
        self.menubar.add_cascade(label=self.t("menu_file"), menu=self.file_menu)
        self.file_menu.add_command(label=self.t("menu_save_profile"), command=self.save_profile_btn)
        self.file_menu.add_command(label=self.t("menu_delete_profile"), command=self.delete_profile_btn)
        self.file_menu.add_separator()
        self.file_menu.add_command(label=self.t("menu_export_macro"), command=self.export_macro_btn)
        self.file_menu.add_command(label=self.t("menu_import_macro"), command=self.import_macro_btn)
        self.file_menu.add_separator()
        self.file_menu.add_command(label=self.t("menu_export_log"), command=self.export_log_btn)
        self.file_menu.add_separator()
        self.file_menu.add_command(label=self.t("menu_exit"), command=self.on_closing)
        
        self.mon_menu = tk.Menu(self.menubar, tearoff=0, bg="#11111b", fg="#cdd6f4", activebackground="#313244", activeforeground="#cdd6f4", relief="flat")
        self.menubar.add_cascade(label=self.t("menu_monitoring"), menu=self.mon_menu)
        self.mon_menu.add_command(label=self.t("menu_start_stop"), command=self.toggle_monitoring)
        self.mon_menu.add_command(label=self.t("menu_pause_resume"), command=self.toggle_pause)
        
        self.zones_menu = tk.Menu(self.menubar, tearoff=0, bg="#11111b", fg="#cdd6f4", activebackground="#313244", activeforeground="#cdd6f4", relief="flat")
        self.menubar.add_cascade(label=self.t("menu_zones"), menu=self.zones_menu)
        self.zones_menu.add_command(label=self.t("menu_add_zone"), command=self.add_zone)
        self.zones_menu.add_command(label=self.t("menu_delete_zone"), command=self.delete_zone)
        
        self.opts_menu = tk.Menu(self.menubar, tearoff=0, bg="#11111b", fg="#cdd6f4", activebackground="#313244", activeforeground="#cdd6f4", relief="flat")
        self.menubar.add_cascade(label=self.t("menu_options"), menu=self.opts_menu)
        self.opts_menu.add_checkbutton(label=self.t("menu_always_on_top"), variable=self.always_on_top, command=self.update_always_on_top)
        self.opts_menu.add_checkbutton(label=self.t("menu_hide_on_pick"), variable=self.hide_on_pick, command=self.save_config)
        self.opts_menu.add_checkbutton(label=self.t("menu_show_overlay"), variable=self.show_overlay_border, command=self.update_overlay_border_visibility)
        
        self.lang_menu = tk.Menu(self.opts_menu, tearoff=0, bg="#11111b", fg="#cdd6f4", activebackground="#313244", activeforeground="#cdd6f4", relief="flat")
        self.opts_menu.add_cascade(label=self.t("menu_language"), menu=self.lang_menu)
        self.lang_menu.add_command(label="English", command=lambda: self.change_language("en"))
        self.lang_menu.add_command(label="Deutsch", command=lambda: self.change_language("de"))
        self.lang_menu.add_command(label="Español", command=lambda: self.change_language("es"))
        self.lang_menu.add_command(label="Français", command=lambda: self.change_language("fr"))
        
        self.help_menu = tk.Menu(self.menubar, tearoff=0, bg="#11111b", fg="#cdd6f4", activebackground="#313244", activeforeground="#cdd6f4", relief="flat")
        self.menubar.add_cascade(label=self.t("menu_help"), menu=self.help_menu)
        self.help_menu.add_command(label=self.t("menu_shortcuts"), command=self.show_shortcuts_dialog)
        self.help_menu.add_command(label=self.t("menu_about"), command=self.show_about_dialog)

    def update_ui_text(self):
        self.root.title(self.t("title"))
        if hasattr(self, 'title_lbl'): self.title_lbl.config(text=self.t("app_title"))
        if hasattr(self, 'prof_title'): self.prof_title.config(text=self.t("profile_manager"))
        if hasattr(self, 'btn_load_prof'): self.btn_load_prof.config(text=self.t("load"))
        if hasattr(self, 'btn_save_prof'): self.btn_save_prof.config(text=self.t("save"))
        if hasattr(self, 'btn_del_prof'): self.btn_del_prof.config(text=self.t("delete"))
        if hasattr(self, 'reg_title'): self.reg_title.config(text=self.t("select_region"))
        if hasattr(self, 'select_btn'): self.select_btn.config(text=self.t("mark_region"))
        if hasattr(self, 'pixel_btn'): self.pixel_btn.config(text=self.t("pick_pixel"))
        if hasattr(self, 'col_title'): self.col_title.config(text=self.t("target_color_tolerance"))
        if hasattr(self, 'color_pick_btn'): self.color_pick_btn.config(text=self.t("color_palette"))
        if hasattr(self, 'eyedropper_btn'): self.eyedropper_btn.config(text=self.t("eyedropper"))
        if hasattr(self, 'tol_lbl'): self.tol_lbl.config(text=self.t("color_tolerance"))
        if hasattr(self, 'trig_title'): self.trig_title.config(text=self.t("trigger_settings"))
        if hasattr(self, 'mode_lbl'): self.mode_lbl.config(text=self.t("trigger_mode"))
        if hasattr(self, 'interval_lbl'): self.interval_lbl.config(text=self.t("check_interval"))
        
        if hasattr(self, 'min_area_lbl'):
            if self.mode.get() == "Generelle Farbänderung":
                self.min_area_lbl.config(text=self.t("change_area"))
            else:
                self.min_area_lbl.config(text=self.t("min_area"))
                
        if hasattr(self, 'zone_active_lbl'): self.zone_active_lbl.config(text=self.t("active") + ":")
        if hasattr(self, 'zones_title'): self.zones_title.config(text=self.t("monitoring_zones"))
        if hasattr(self, 'btn_add_zone'): self.btn_add_zone.config(text=self.t("add"))
        if hasattr(self, 'btn_del_zone'): self.btn_del_zone.config(text=self.t("delete_btn"))
        if hasattr(self, 'btn_rename_zone'): self.btn_rename_zone.config(text=self.t("rename"))
        if hasattr(self, 'btn_zone_up'): self.btn_zone_up.config(text=self.t("move_up"))
        if hasattr(self, 'btn_zone_down'): self.btn_zone_down.config(text=self.t("move_down"))
        
        if hasattr(self, 'start_btn'):
            self.start_btn.config(text=self.t("stop_monitoring_btn") if self.is_monitoring else self.t("start_monitoring_btn"))
        if hasattr(self, 'pause_btn'):
            self.pause_btn.config(text=self.t("resume_btn") if self.monitoring_paused else self.t("pause_btn"))
            
        if hasattr(self, 'mac_title'): self.mac_title.config(text=self.t("automation_macro"))
        if hasattr(self, 'btn_add_mac'): self.btn_add_mac.config(text=self.t("add"))
        if hasattr(self, 'btn_edit_mac'): self.btn_edit_mac.config(text=self.t("edit"))
        if hasattr(self, 'btn_del_mac'): self.btn_del_mac.config(text=self.t("delete_btn"))
        if hasattr(self, 'btn_up_mac'): self.btn_up_mac.config(text=self.t("up"))
        if hasattr(self, 'btn_down_mac'): self.btn_down_mac.config(text=self.t("down"))
        if hasattr(self, 'btn_test_mac'): self.btn_test_mac.config(text=self.t("test_macro"))
        
        if hasattr(self, 'lbl_preview'): self.lbl_preview.config(text=self.t("live_preview"))
        if hasattr(self, 'lbl_log'): self.lbl_log.config(text=self.t("activity_log"))
        
        if hasattr(self, 'status_lbl'):
            if getattr(self, 'macro_running', False):
                self.status_lbl.config(text=self.t("status_macro_running"), fg="#f9e2af")
            elif getattr(self, 'monitoring_paused', False):
                self.status_lbl.config(text=self.t("status_paused"), fg="#f9e2af")
            elif getattr(self, 'is_monitoring', False):
                self.status_lbl.config(text=self.t("status_active"), fg="#a6e3a1")
            else:
                self.status_lbl.config(text=self.t("status_inactive"), fg="#7f849c")
                
        if hasattr(self, 'size_lbl'):
            self.update_size_label()
            
        if hasattr(self, 'mode_cb'):
            self.update_mode_combobox()

    def __init__(self, root):
        self.root = root
        # Determine language default
        self.current_lang = 'en'
        try:
            loc = locale.getdefaultlocale()[0]
            if loc:
                loc = loc.split('_')[0].lower()
                if loc in ['en', 'de', 'es', 'fr']:
                    self.current_lang = loc
        except Exception:
            pass
        self.root.title(self.t("title"))
        self.root.geometry("1020x680")
        self.root.minsize(580, 450)
        self.root.configure(bg="#1e1e2e")
        
        # Screen bounds variables
        self.x1, self.y1, self.x2, self.y2 = 0, 0, 100, 100
        self.target_color = (255, 0, 0) # Default Red
        self.is_monitoring = False
        self.monitoring_paused = False
        self.macro_paused = False
        self.macro_aborted = False
        self.was_color_present = None
        self.baseline_img = None
        self.last_trigger_time = 0
        self.zones = []
        self.selected_zone_idx = 0
        self._updating_editor = False
        self.profile_modified = False
        self.current_profile_name = "default"
        
        # Macro actions list
        self.macro_actions = [
            {"type": "wait", "value": 500},
            {"type": "click", "x": 500, "y": 500, "click_type": "left"}
        ]
        self.macro_running = False
        self._testing_macro = False
        self.hide_on_pick = tk.BooleanVar(value=True)
        self.show_overlay_border = tk.BooleanVar(value=True)
        self.always_on_top = tk.BooleanVar(value=False)
        self.overlay_border = RegionOverlayBorder(self.root, self.on_border_dragged)
        
        # Initialize platform-appropriate mouse/keyboard controller
        if sys.platform.startswith("win"):
            self.mouse_controller = WindowsMouseController()
        else:
            self.mouse_controller = X11MouseController()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Setup modern dark styles
        self.setup_styles()
        
        # Build UI
        self.create_widgets()
        
        # Setup profile directory and refresh
        self.refresh_profile_list()
        
        # Load configuration if saved previously, otherwise default profile
        if os.path.exists(CONFIG_PATH):
            self.load_config()
        else:
            self.load_profile_from_file("default")
        
        # Update UI texts for selected language
        self.update_ui_text()

        # Load macro listbox values
        self.update_macro_listbox()
        
        # Start the continuous live preview loop
        self.start_preview_loop()

        # Bind keyboard shortcuts
        self.root.bind("<space>", self.on_space_pressed)
        self.root.bind("<Delete>", self.on_delete_pressed)

    def on_closing(self):
        """Clean closure of app to avoid orphaned threads and Tkinter errors."""
        if getattr(self, 'profile_modified', False):
            profile_name = self.profile_name_var.get() if hasattr(self, 'profile_name_var') else "default"
            ans = messagebox.askyesnocancel(self.t("unsaved_changes"), self.t("unsaved_changes_msg", profile_name), parent=self.root)
            if ans is True:
                self.save_profile_to_file(profile_name)
            elif ans is None:
                return
                
        self.stop_monitoring()
        self.save_config()
        if hasattr(self, 'overlay_border'):
            self.overlay_border.destroy()
        if hasattr(self, 'mouse_controller'):
            self.mouse_controller.close()
        self.root.destroy()

    def save_config(self):
        """Saves current state and macro actions list to a local JSON file."""
        try:
            serializable_zones = []
            if hasattr(self, 'zones'):
                for zone in self.zones:
                    sz = zone.copy()
                    if "target_color" in sz:
                        sz["target_color"] = list(sz["target_color"])
                    if "was_color_present" in sz:
                        sz.pop("was_color_present")
                    if "baseline_img" in sz:
                        sz.pop("baseline_img")
                    serializable_zones.append(sz)
            
            data = {
                "language": self.current_lang,
                "x1": self.x1,
                "y1": self.y1,
                "x2": self.x2,
                "y2": self.y2,
                "target_color": list(self.target_color),
                "tolerance": self.tolerance.get(),
                "mode": self.mode.get(),
                "interval": self.interval.get(),
                "min_area_pct": self.min_area_pct.get(),
                "hide_on_pick": self.hide_on_pick.get(),
                "show_overlay_border": self.show_overlay_border.get(),
                "always_on_top": self.always_on_top.get() if hasattr(self, 'always_on_top') else False,
                "macro_actions": self.macro_actions,
                "zones": serializable_zones,
                "selected_zone_idx": self.selected_zone_idx,
                "last_profile": self.profile_name_var.get() if hasattr(self, 'profile_name_var') else "default"
            }
            
            try:
                geom = self.root.geometry()
                parts = geom.split('+')[0].split('x')
                w, h = int(parts[0]), int(parts[1])
                if w > 200 and h > 200:
                    data["window_geometry"] = geom
            except:
                pass
                
            if hasattr(self, 'paned'):
                try:
                    s_pos = self.paned.sashpos(0)
                    if s_pos > 100:
                        data["sash_position"] = s_pos
                except:
                    pass
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Fehler beim Speichern der Konfiguration: {e}", file=sys.stderr)

    def load_config(self):
        """Loads saved settings and macro actions list from local JSON file."""
        if not os.path.exists(CONFIG_PATH):
            # Populate default zone if no config exists yet
            self.zones = [{
                "name": "Zone 1",
                "x1": self.x1,
                "y1": self.y1,
                "x2": self.x2,
                "y2": self.y2,
                "target_color": self.target_color,
                "tolerance": self.tolerance.get(),
                "mode": self.mode.get(),
                "min_area_pct": self.min_area_pct.get(),
                "was_color_present": None
            }]
            self.selected_zone_idx = 0
            self.update_zones_listbox()
            self.zones_listbox.selection_set(0)
            return
        self._updating_editor = True
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            self.current_lang = data.get("language", self.current_lang)
            self.x1 = data.get("x1", self.x1)
            self.y1 = data.get("y1", self.y1)
            self.x2 = data.get("x2", self.x2)
            self.y2 = data.get("y2", self.y2)
            
            tc = data.get("target_color")
            if tc and len(tc) == 3:
                self.target_color = tuple(tc)
                
            self.tolerance.set(data.get("tolerance", self.tolerance.get()))
            self.mode.set(data.get("mode", self.mode.get()))
            self.interval.set(data.get("interval", self.interval.get()))
            self.min_area_pct.set(data.get("min_area_pct", self.min_area_pct.get()))
            self.hide_on_pick.set(data.get("hide_on_pick", self.hide_on_pick.get()))
            self.show_overlay_border.set(data.get("show_overlay_border", self.show_overlay_border.get()))
            self.update_overlay_border_visibility()
            
            if hasattr(self, 'always_on_top'):
                self.always_on_top.set(data.get("always_on_top", False))
                self.root.attributes("-topmost", self.always_on_top.get())
            
            # Restore window geometry and sash position
            win_geom = data.get("window_geometry")
            if win_geom:
                try:
                    parts = win_geom.split('+')[0].split('x')
                    w, h = int(parts[0]), int(parts[1])
                    if w > 200 and h > 200:
                        self.root.geometry(win_geom)
                except:
                    pass
            
            sash_pos = data.get("sash_position")
            if sash_pos is not None and hasattr(self, 'paned'):
                try:
                    if int(sash_pos) > 100:
                        self.root.after(100, lambda: self.paned.sashpos(0, int(sash_pos)))
                except:
                    pass
            
            # Legacy migrations (in case click_type was missing)
            actions = data.get("macro_actions", self.macro_actions)
            for act in actions:
                if act["type"] == "click" and "click_type" not in act:
                    act["click_type"] = "left"
            self.macro_actions = actions
            
            # Load zones
            zones_data = data.get("zones")
            if zones_data:
                self.zones = []
                for zd in zones_data:
                    zone = zd.copy()
                    if "target_color" in zone:
                        zone["target_color"] = tuple(zone["target_color"])
                    zone["was_color_present"] = None
                    self.zones.append(zone)
                self.selected_zone_idx = data.get("selected_zone_idx", 0)
                if self.selected_zone_idx >= len(self.zones):
                    self.selected_zone_idx = 0
            else:
                self.zones = [{
                    "name": "Zone 1",
                    "x1": self.x1,
                    "y1": self.y1,
                    "x2": self.x2,
                    "y2": self.y2,
                    "target_color": self.target_color,
                    "tolerance": self.tolerance.get(),
                    "mode": self.mode.get(),
                    "min_area_pct": self.min_area_pct.get(),
                    "was_color_present": None
                }]
                self.selected_zone_idx = 0
            
            # Populate listbox
            self.update_zones_listbox()
            self.zones_listbox.selection_clear(0, "end")
            if 0 <= self.selected_zone_idx < len(self.zones):
                self.zones_listbox.selection_set(self.selected_zone_idx)
                self.load_zone_to_editor(self.selected_zone_idx)
            
            last_profile = data.get("last_profile")
            if last_profile and hasattr(self, 'profile_name_var'):
                self.profile_name_var.set(last_profile)
                self.load_profile_from_file(last_profile)

            self.interval_val_lbl.config(text=f"{self.interval.get():.1f} s")
            
            # Run layout updates
            self.on_mode_change(None)
            self.profile_modified = False
            
        except Exception as e:
            print(f"Fehler beim Laden der Konfiguration: {e}", file=sys.stderr)
        finally:
            self._updating_editor = False

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Catppuccin Mocha theme palettes
        bg_dark = '#1e1e2e'
        bg_card = '#181825'
        bg_input = '#313244'
        fg_light = '#cdd6f4'
        accent_blue = '#89b4fa'
        
        style.configure('.', background=bg_dark, foreground=fg_light, fieldbackground=bg_input)
        style.configure('TFrame', background=bg_dark)
        style.configure('Card.TFrame', background=bg_card, relief="flat")
        style.configure('TLabel', background=bg_dark, foreground=fg_light)
        style.configure('Card.TLabel', background=bg_card, foreground=fg_light)
        
        # Button styles
        style.configure('TButton', background=bg_input, foreground=fg_light, borderwidth=0, focuscolor='none', padding=6)
        style.map('TButton', background=[('active', '#45475a'), ('pressed', '#585b70')])
        
        style.configure('Primary.TButton', background=accent_blue, foreground='#11111b', borderwidth=0, focuscolor='none', padding=6)
        style.map('Primary.TButton', background=[('active', '#b4befe'), ('pressed', '#cba6f7')])
        
        style.configure('Combobox.TCombobox', background=bg_input, fieldbackground=bg_input, foreground=fg_light, borderwidth=0)
        style.map('Combobox.TCombobox',
                  fieldbackground=[('readonly', bg_input), ('disabled', bg_input)],
                  foreground=[('readonly', fg_light), ('disabled', '#7f849c')],
                  selectbackground=[('readonly', '#313244')],
                  selectforeground=[('readonly', fg_light)])
        
        # Scrollbar styling (clam theme)
        style.configure('Vertical.TScrollbar', 
                        troughcolor='#11111b', 
                        background='#313244', 
                        bordercolor='#1e1e2e', 
                        arrowcolor='#cdd6f4',
                        lightcolor='#313244', 
                        darkcolor='#313244',
                        gripcount=0)
        style.map('Vertical.TScrollbar', 
                  background=[('active', '#45475a'), ('pressed', '#585b70')])

        style.configure('Horizontal.TScrollbar', 
                        troughcolor='#11111b', 
                        background='#313244', 
                        bordercolor='#1e1e2e', 
                        arrowcolor='#cdd6f4',
                        lightcolor='#313244', 
                        darkcolor='#313244',
                        gripcount=0)
        style.map('Horizontal.TScrollbar', 
                  background=[('active', '#45475a'), ('pressed', '#585b70')])
        
        # Fonts
        self.title_font = ("Helvetica", 14, "bold")
        self.header_font = ("Helvetica", 11, "bold")
        self.body_font = ("Helvetica", 10)
        self.code_font = ("Consolas", 10)

    def create_widgets(self):
        # Create Menu Bar
        self.create_menu_bar()
        
        # 1. Status Bar at the very bottom of root (outside scroll view)
        self.status_bar = tk.Frame(self.root, bg="#11111b", height=24)
        self.status_bar.pack(fill="x", side="bottom")
        
        self.status_lbl = tk.Label(self.status_bar, text="🔴 Status: Inaktiv", bg="#11111b", fg="#7f849c", font=("Helvetica", 9), anchor="w", padx=10)
        self.status_lbl.pack(fill="both", expand=True)

        # 1b. Horizontal Scrollbar (above status bar, below canvas)
        self.hscrollbar = ttk.Scrollbar(self.root, orient="horizontal")
        self.hscrollbar.pack(side="bottom", fill="x")

        # 2. Vertical Scrollbar for scrollable view
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical")
        self.scrollbar.pack(side="right", fill="y")
        
        self.canvas = tk.Canvas(self.root, bg="#1e1e2e", highlightthickness=0, 
                                yscrollcommand=self.scrollbar.set, xscrollcommand=self.hscrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        
        self.scrollbar.config(command=lambda *args: (self.canvas.yview(*args), self.canvas.update_idletasks()))
        self.hscrollbar.config(command=lambda *args: (self.canvas.xview(*args), self.canvas.update_idletasks()))
        
        # 3. Master container frame inside canvas
        container = ttk.Frame(self.canvas, style='TFrame')
        self.canvas_window = self.canvas.create_window((0, 0), window=container, anchor="nw")
        
        # Adjust scroll region when size of container changes
        def _configure_container(event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            self.canvas.update_idletasks()
        container.bind("<Configure>", _configure_container)
        
        # Adjust container width/height when canvas size changes (min width 980 to prevent squishing)
        def _configure_canvas(event):
            w = max(event.width, 980)
            self.canvas.itemconfig(self.canvas_window, width=w)
            self.canvas.update_idletasks()
        self.canvas.bind("<Configure>", _configure_canvas)
        
        # Bind Mousewheel scrolling on canvas and all its children recursively (horizontal on Shift)
        def _on_mousewheel(event):
            w = event.widget
            if w and hasattr(w, 'winfo_class') and w.winfo_class() in ('Listbox', 'Text'):
                return
            is_shift = (event.state & 0x0001) or (event.state & 0x0002) # Shift key state
            if event.num == 4:
                if is_shift:
                    self.canvas.xview_scroll(-1, "units")
                else:
                    self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                if is_shift:
                    self.canvas.xview_scroll(1, "units")
                else:
                    self.canvas.yview_scroll(1, "units")
            else:
                scroll_dir = int(-1 * (event.delta / 120))
                if is_shift:
                    self.canvas.xview_scroll(scroll_dir, "units")
                else:
                    self.canvas.yview_scroll(scroll_dir, "units")
            self.canvas.update_idletasks()
                
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.canvas.bind_all("<Button-4>", _on_mousewheel)
        self.canvas.bind_all("<Button-5>", _on_mousewheel)

        # Add inner padding inside container
        inner_container = ttk.Frame(container, style='TFrame', padding=20)
        inner_container.pack(fill="both", expand=True)

        # Title Header
        header_frame = ttk.Frame(inner_container, style='TFrame')
        header_frame.pack(fill="x", pady=(0, 10))
        
        self.title_lbl = ttk.Label(header_frame, text="🔍 Screen Color Monitor & Automation", font=self.title_font, foreground="#b4befe")
        self.title_lbl.pack(side="left")
        
        subtitle_lbl = ttk.Label(header_frame, text="v2.1.0 (Dashboard)", font=self.code_font, foreground="#7f849c")
        subtitle_lbl.pack(side="right", pady=5)

        # Single-column container
        main_col = ttk.Frame(inner_container, style='TFrame')

        main_col.pack(fill="both", expand=True)

        # 1. Profile Manager
        profile_card = ttk.Frame(main_col, style='Card.TFrame', padding=15)
        profile_card.pack(fill="x", pady=5)
        
        self.prof_title = ttk.Label(profile_card, text="Profil Manager", font=self.header_font, style='Card.TLabel')
        self.prof_title.pack(anchor="w", pady=(0, 10))
        
        prof_row = ttk.Frame(profile_card, style='Card.TFrame')
        prof_row.pack(fill="x")
        
        self.profile_name_var = tk.StringVar(value="default")
        self.profile_cb = ttk.Combobox(prof_row, textvariable=self.profile_name_var, state="readonly", width=25, style='Combobox.TCombobox')
        self.profile_cb.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.profile_cb.bind("<<ComboboxSelected>>", lambda e: self.load_profile_btn())
        
        self.btn_load_prof = ttk.Button(prof_row, text="Laden", command=self.load_profile_btn)
        self.btn_load_prof.pack(side="left", padx=4)
        
        self.btn_save_prof = ttk.Button(prof_row, text="Speichern", command=self.save_profile_btn)
        self.btn_save_prof.pack(side="left", padx=4)
        
        self.btn_del_prof = ttk.Button(prof_row, text="Löschen", command=self.delete_profile_btn)
        self.btn_del_prof.pack(side="left", padx=(4, 0))

        # 3. Zonen auswählen Card
        region_card = ttk.Frame(main_col, style='Card.TFrame', padding=15)
        region_card.pack(fill="x", pady=5)
        
        self.reg_title = ttk.Label(region_card, text="Zonen auswählen", font=self.header_font, style='Card.TLabel')
        self.reg_title.pack(anchor="w", pady=(0, 10))
        
        reg_row = ttk.Frame(region_card, style='Card.TFrame')
        reg_row.pack(fill="x")
        
        reg_left = ttk.Frame(reg_row, style='Card.TFrame')
        reg_left.pack(side="left", fill="y")
        
        coords_frame = ttk.Frame(reg_left, style='Card.TFrame')
        coords_frame.pack(side="top", anchor="w")
        
        self.entry_x1 = tk.StringVar(value=str(self.x1))
        self.entry_y1 = tk.StringVar(value=str(self.y1))
        self.entry_x2 = tk.StringVar(value=str(self.x2))
        self.entry_y2 = tk.StringVar(value=str(self.y2))
        
        self.entry_x1.trace_add("write", self.on_manual_coords_change)
        self.entry_y1.trace_add("write", self.on_manual_coords_change)
        self.entry_x2.trace_add("write", self.on_manual_coords_change)
        self.entry_y2.trace_add("write", self.on_manual_coords_change)
        
        labels = ["X1:", "Y1:", "X2:", "Y2:"]
        self.vars = [self.entry_x1, self.entry_y1, self.entry_x2, self.entry_y2]
        
        for i, (label_txt, var) in enumerate(zip(labels, self.vars)):
            col = i * 2
            lbl = ttk.Label(coords_frame, text=label_txt, font=self.body_font, style='Card.TLabel')
            lbl.grid(row=0, column=col, padx=(5 if col > 0 else 0, 2), pady=5)
            
            ent = tk.Entry(coords_frame, textvariable=var, width=6, font=self.code_font, bg="#313244", fg="#cdd6f4", 
                           insertbackground="#cdd6f4", relief="flat", bd=2)
            ent.grid(row=0, column=col+1, padx=2, pady=5)
            
        self.size_lbl = ttk.Label(reg_left, text="Größe: 100 x 100 px", font=self.body_font, style='Card.TLabel', foreground="#a6adc8")
        self.size_lbl.pack(side="top", anchor="w", pady=(5, 0))
        
        reg_right = ttk.Frame(reg_row, style='Card.TFrame')
        reg_right.pack(side="right", fill="y", padx=(10, 0))
        
        self.pixel_btn = ttk.Button(reg_right, text="🎯 Pixel wählen", command=self.start_pixel_selection, width=20)
        self.pixel_btn.pack(side="top", fill="x", pady=2)
        
        self.select_btn = ttk.Button(reg_right, text="🖥️ Bereich markieren", command=self.start_region_selection, width=20)
        self.select_btn.pack(side="top", fill="x", pady=2)

        # 4. Zonen Card
        zones_card = ttk.Frame(main_col, style='Card.TFrame', padding=15)
        zones_card.pack(fill="x", pady=5)
        
        self.zones_title = ttk.Label(zones_card, text="Zonen", font=self.header_font, style='Card.TLabel')
        self.zones_title.pack(anchor="w", pady=(0, 10))
        
        zones_content = ttk.Frame(zones_card, style='Card.TFrame')
        zones_content.pack(fill="x")
        
        zones_left = ttk.Frame(zones_content, style='Card.TFrame')
        zones_left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        self.zones_listbox = tk.Listbox(zones_left, bg="#11111b", fg="#cdd6f4", selectbackground="#313244", 
                                        font=self.code_font, height=5, relief="flat", highlightthickness=0)
        self.zones_listbox.pack(side="left", fill="both", expand=True)
        self.zones_listbox.bind("<<ListboxSelect>>", self.on_zone_selected)
        self.zones_listbox.bind("<Double-Button-1>", self.rename_zone)
        
        scrollbar = ttk.Scrollbar(zones_left, orient="vertical", command=self.zones_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.zones_listbox.config(yscrollcommand=scrollbar.set)
        
        zones_right = ttk.Frame(zones_content, style='Card.TFrame')
        zones_right.pack(side="right", fill="y", padx=(10, 0))
        
        # Align buttons inside a 3-row grid (2 columns wide) on the right side of the listbox to save horizontal space
        self.btn_add_zone = ttk.Button(zones_right, text="➕ Hinzufügen", width=12, command=self.add_zone)
        self.btn_add_zone.grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        
        self.btn_del_zone = ttk.Button(zones_right, text="❌ Löschen", width=12, command=self.delete_zone)
        self.btn_del_zone.grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        
        self.btn_rename_zone = ttk.Button(zones_right, text="✏️ Umbenennen", width=12, command=self.rename_zone)
        self.btn_rename_zone.grid(row=1, column=0, padx=2, pady=2, sticky="ew")
        
        self.btn_zone_up = ttk.Button(zones_right, text="🔼 Nach oben", width=12, command=self.move_zone_up)
        self.btn_zone_up.grid(row=1, column=1, padx=2, pady=2, sticky="ew")
        
        self.btn_zone_down = ttk.Button(zones_right, text="🔽 Nach unten", width=12, command=self.move_zone_down)
        self.btn_zone_down.grid(row=2, column=0, columnspan=2, padx=2, pady=2, sticky="ew")



        # 5. Trigger Settings Card
        trigger_settings_card = ttk.Frame(main_col, style='Card.TFrame', padding=15)
        trigger_settings_card.pack(fill="x", pady=5)
        
        self.trig_title = ttk.Label(trigger_settings_card, text="Auslöser Einstellungen", font=self.header_font, style='Card.TLabel')
        self.trig_title.pack(anchor="w", pady=(0, 10))
        
        # Internals structured as two columns inside trigger_settings_card
        card_content = ttk.Frame(trigger_settings_card, style='Card.TFrame')
        card_content.pack(fill="x", expand=True)
        
        card_left = ttk.Frame(card_content, style='Card.TFrame')
        card_left.pack(side="left", fill="y", padx=(0, 15))
        
        card_right = ttk.Frame(card_content, style='Card.TFrame')
        card_right.pack(side="left", fill="y", padx=(15, 0), anchor="n")
        
        # Live Preview (right side)
        self.lbl_preview = ttk.Label(card_right, text="Live-Vorschau", font=self.header_font, style='Card.TLabel')
        self.lbl_preview.pack(anchor="n", pady=(0, 5))
        
        self.preview_canvas = tk.Canvas(card_right, width=160, height=160, bg="#181825", highlightthickness=1, highlightbackground="#313244")
        self.preview_canvas.pack(padx=5, pady=5)
        
        self.match_stats_lbl = ttk.Label(card_right, text="Übereinstimmung: 0.0%", font=self.body_font, style='Card.TLabel', foreground="#a6adc8")
        self.match_stats_lbl.pack(pady=2)
        
        self.gauge_canvas = tk.Canvas(card_right, width=160, height=12, bg="#313244", highlightthickness=0)
        self.gauge_canvas.pack(pady=5)
        
        # Color Controls Sub-Frame (left side)
        col_controls = ttk.Frame(card_left, style='Card.TFrame')
        col_controls.pack(fill="x", pady=(0, 5))
        
        self.color_patch = tk.Canvas(col_controls, width=44, height=44, bg=self.get_hex_color(self.target_color), 
                                     highlightthickness=1, highlightbackground="#45475a", relief="flat")
        self.color_patch.pack(side="left", padx=(0, 10))
        
        color_info_frame = ttk.Frame(col_controls, style='Card.TFrame')
        color_info_frame.pack(side="left", fill="y")
        
        self.color_text_lbl = ttk.Label(color_info_frame, text=f"RGB: {self.target_color}\nHEX: {self.get_hex_color(self.target_color)}", 
                                        font=self.code_font, style='Card.TLabel')
        self.color_text_lbl.pack(anchor="w")
        
        color_btns_frame = ttk.Frame(card_left, style='Card.TFrame')
        color_btns_frame.pack(fill="x", pady=(5, 0))
        
        self.color_pick_btn = ttk.Button(color_btns_frame, text="Farbpalette", command=self.choose_color_dialog)
        self.color_pick_btn.pack(side="left", padx=(0, 4))
        
        self.eyedropper_btn = ttk.Button(color_btns_frame, text="Pipette (Bildschirm)", command=self.start_eyedropper)
        self.eyedropper_btn.pack(side="left", padx=4)
        
        tolerance_frame = ttk.Frame(card_left, style='Card.TFrame')
        tolerance_frame.pack(fill="x", pady=(10, 10))
        
        tol_lbl_container = ttk.Frame(tolerance_frame, style='Card.TFrame')
        tol_lbl_container.pack(fill="x")
        
        self.tol_lbl = ttk.Label(tol_lbl_container, text="Farb-Toleranz (Abweichung):", font=self.body_font, style='Card.TLabel')
        self.tol_lbl.pack(side="left")
        
        self.tolerance = tk.IntVar(value=30)
        self.tol_val_lbl = ttk.Label(tol_lbl_container, text=str(self.tolerance.get()), font=self.code_font, style='Card.TLabel', foreground="#a6e3a1")
        self.tol_val_lbl.pack(side="right")
        
        tol_slider = tk.Scale(tolerance_frame, from_=0, to=255, variable=self.tolerance, orient="horizontal", 
                              bg="#181825", fg="#cdd6f4", highlightthickness=0, troughcolor="#313244", 
                              activebackground="#89b4fa", showvalue=False, command=self.on_tolerance_change, length=180)
        tol_slider.pack(fill="x", pady=(5, 0))
        tol_slider.bind("<ButtonRelease-1>", lambda e: self.save_config())
        
        trig_grid = ttk.Frame(card_left, style='Card.TFrame')
        trig_grid.pack(fill="x", pady=(10, 0))
        
        self.mode_lbl = ttk.Label(trig_grid, text="Auslöser-Modus:", font=self.body_font, style='Card.TLabel')
        self.mode_lbl.grid(row=0, column=0, sticky="w", pady=5, padx=(0, 10))
        
        self.mode = tk.StringVar(value="Ziel-Farbe erscheint")
        self.mode_cb = ttk.Combobox(trig_grid, textvariable=self.mode, values=[
            "Ziel-Farbe erscheint", 
            "Ziel-Farbe verschwindet", 
            "Ziel-Farbe vorhanden",
            "Ziel-Farbe nicht vorhanden",
            "Generelle Farbänderung"
        ], state="readonly", width=22, style='Combobox.TCombobox')
        self.mode_cb.grid(row=0, column=1, sticky="w", pady=5)
        self.mode_cb.bind("<<ComboboxSelected>>", self.on_mode_change)
        
        self.interval_lbl = ttk.Label(trig_grid, text="Prüf-Intervall (Sek.):", font=self.body_font, style='Card.TLabel')
        self.interval_lbl.grid(row=1, column=0, sticky="w", pady=10, padx=(0, 10))
        
        interval_slider_frame = ttk.Frame(trig_grid, style='Card.TFrame')
        interval_slider_frame.grid(row=1, column=1, sticky="ew")
        
        self.interval = tk.DoubleVar(value=0.5)
        self.interval_val_lbl = ttk.Label(interval_slider_frame, text=f"{self.interval.get():.1f} s", font=self.code_font, style='Card.TLabel', foreground="#a6e3a1")
        self.interval_val_lbl.pack(side="right", padx=(10, 0))
        
        interval_slider = tk.Scale(interval_slider_frame, from_=0.1, to=5.0, resolution=0.1, variable=self.interval, orient="horizontal",
                                   bg="#181825", fg="#cdd6f4", highlightthickness=0, troughcolor="#313244", 
                                   activebackground="#89b4fa", showvalue=False, command=self.on_interval_change, width=12, length=140)
        interval_slider.pack(side="left", fill="x", expand=True)
        interval_slider.bind("<ButtonRelease-1>", lambda e: self.save_config())
        
        self.min_area_lbl = ttk.Label(trig_grid, text="Mindest-Fläche (%):", font=self.body_font, style='Card.TLabel')
        self.min_area_lbl.grid(row=2, column=0, sticky="w", pady=10, padx=(0, 10))
        
        self.min_area_frame = ttk.Frame(trig_grid, style='Card.TFrame')
        self.min_area_frame.grid(row=2, column=1, sticky="ew")
        
        self.min_area_pct = tk.DoubleVar(value=1.0)
        self.min_area_val_lbl = ttk.Label(self.min_area_frame, text=f"{self.min_area_pct.get():.1f}%", font=self.code_font, style='Card.TLabel', foreground="#a6e3a1")
        self.min_area_val_lbl.pack(side="right", padx=(10, 0))
        
        self.min_area_slider = tk.Scale(self.min_area_frame, from_=0.0, to=100.0, resolution=0.1, variable=self.min_area_pct, orient="horizontal",
                                        bg="#181825", fg="#cdd6f4", highlightthickness=0, troughcolor="#313244", 
                                        activebackground="#89b4fa", showvalue=False, command=self.on_min_area_change, width=12, length=140)
        self.min_area_slider.pack(side="left", fill="x", expand=True)
        self.min_area_slider.bind("<ButtonRelease-1>", lambda e: self.save_config())
        
        self.zone_active_lbl = ttk.Label(trig_grid, text=self.t("active") + ":", font=self.body_font, style='Card.TLabel')
        self.zone_active_lbl.grid(row=3, column=0, sticky="w", pady=10, padx=(0, 10))
        
        self.zone_active_var = tk.BooleanVar(value=True)
        self.zone_active_cb = tk.Checkbutton(trig_grid, variable=self.zone_active_var, bg="#181825", fg="#cdd6f4",
                                             activebackground="#181825", activeforeground="#cdd6f4", selectcolor="#313244",
                                             command=self.on_zone_active_changed)
        self.zone_active_cb.grid(row=3, column=1, sticky="w", pady=10)
        
        trig_grid.columnconfigure(1, weight=1)


        # 6. Automatisierungs-Makro bei Alarm
        macro_card = ttk.Frame(main_col, style='Card.TFrame', padding=15)
        macro_card.pack(fill="x", pady=5)
        
        self.mac_title = ttk.Label(macro_card, text="Ausgelöstes Makro", font=self.header_font, style='Card.TLabel')
        self.mac_title.pack(anchor="w", pady=(0, 10))
        
        list_frame = ttk.Frame(macro_card, style='Card.TFrame')
        list_frame.pack(fill="x", pady=(0, 10))
        
        self.macro_listbox = tk.Listbox(list_frame, bg="#11111b", fg="#cdd6f4", selectbackground="#313244", 
                                        font=self.code_font, height=6, relief="flat", highlightthickness=0)
        self.macro_listbox.pack(side="left", fill="x", expand=True)
        self.macro_listbox.bind("<Double-Button-1>", self.edit_action)
        self.macro_listbox.bind("<space>", self.toggle_action_enabled)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.macro_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.macro_listbox.config(yscrollcommand=scrollbar.set)
        
        btns_frame = ttk.Frame(macro_card, style='Card.TFrame')
        btns_frame.pack(fill="x")
        
        row1 = ttk.Frame(btns_frame, style='Card.TFrame')
        row1.pack(fill="x", pady=2)
        self.btn_add_mac = ttk.Button(row1, text="➕ Hinzufügen", width=12, command=self.add_action)
        self.btn_add_mac.pack(side="left", padx=(0, 4))
        self.btn_toggle_mac = ttk.Button(row1, text="🔘 Ein/Aus", width=12, command=self.toggle_action_enabled)
        self.btn_toggle_mac.pack(side="left", padx=4)
        self.btn_edit_mac = ttk.Button(row1, text="✏️ Bearbeiten", width=12, command=self.edit_action)
        self.btn_edit_mac.pack(side="left", padx=4)
        self.btn_del_mac = ttk.Button(row1, text="❌ Löschen", width=12, command=self.delete_action)
        self.btn_del_mac.pack(side="left", padx=4)
        
        row2 = ttk.Frame(btns_frame, style='Card.TFrame')
        row2.pack(fill="x", pady=2)
        self.btn_up_mac = ttk.Button(row2, text="🔼 Hoch", width=8, command=self.move_action_up)
        self.btn_up_mac.pack(side="left", padx=(0, 4))
        self.btn_down_mac = ttk.Button(row2, text="🔽 Runter", width=8, command=self.move_action_down)
        self.btn_down_mac.pack(side="left", padx=4)
        self.btn_test_mac = ttk.Button(row2, text="▶️ Makro testen", width=16, style='Primary.TButton', command=self.test_macro)
        self.btn_test_mac.pack(side="left", padx=4)

        # 7. Activity Log Card
        log_card = ttk.Frame(main_col, style='Card.TFrame', padding=15)
        log_card.pack(fill="both", expand=True, pady=5)
        
        log_header_frame = ttk.Frame(log_card, style='Card.TFrame')
        log_header_frame.pack(fill="x", pady=(0, 5))
        
        self.lbl_log = ttk.Label(log_header_frame, text="Aktivitätsprotokoll", font=self.header_font, style='Card.TLabel')
        self.lbl_log.pack(side="left", anchor="w")
        
        self.btn_copy_log = ttk.Button(log_header_frame, text="Kopieren", style='TButton', command=self.copy_all_logs, width=8)
        self.btn_copy_log.pack(side="right")
        
        log_list_frame = ttk.Frame(log_card, style='Card.TFrame')
        log_list_frame.pack(fill="both", expand=True)
        
        scrollbar_y = ttk.Scrollbar(log_list_frame, orient="vertical")
        scrollbar_x = ttk.Scrollbar(log_list_frame, orient="horizontal")
        
        self.log_list = tk.Listbox(log_list_frame, bg="#11111b", fg="#cdd6f4", selectbackground="#313244", 
                                   font=self.code_font, height=6, relief="flat", highlightthickness=0,
                                   yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set,
                                   selectmode="extended")
        
        scrollbar_y.config(command=self.log_list.yview)
        scrollbar_x.config(command=self.log_list.xview)
        
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")
        self.log_list.pack(side="left", fill="both", expand=True)
        
        self.log_list.bind("<Control-c>", self.copy_selected_log)
        self.log_list.bind("<Control-C>", self.copy_selected_log)
        
        self.log_context_menu = tk.Menu(self.root, tearoff=0, bg="#181825", fg="#cdd6f4", activebackground="#313244", activeforeground="#cdd6f4", relief="flat")
        self.log_context_menu.add_command(label="Kopieren (Auswahl)", command=self.copy_selected_log)
        self.log_context_menu.add_command(label="Alles kopieren", command=self.copy_all_logs)
        
        def show_log_context(event):
            self.log_context_menu.post(event.x_root, event.y_root)
            
        self.log_list.bind("<Button-3>", show_log_context)

        # 8. Large Action Trigger Buttons (at the very bottom of main column)
        control_frame = ttk.Frame(main_col, style='Card.TFrame', padding=10)
        control_frame.pack(fill="x", pady=5)
        
        self.start_btn = ttk.Button(control_frame, text="▶️ Starten", style='Primary.TButton', command=self.toggle_monitoring)
        self.start_btn.pack(side="left", fill="x", expand=True, ipady=4, padx=(0, 2))
        
        self.pause_btn = ttk.Button(control_frame, text="⏸️ Pause", style='Secondary.TButton', command=self.toggle_pause, state="disabled")
        self.pause_btn.pack(side="left", fill="x", expand=True, ipady=4, padx=(2, 2))
        
        self.restart_btn = ttk.Button(control_frame, text="🔄 Neustart", style='Secondary.TButton', command=self.restart_monitoring)
        self.restart_btn.pack(side="left", fill="x", expand=True, ipady=4, padx=(2, 0))


    def get_hex_color(self, rgb_tuple):
        return f"#{rgb_tuple[0]:02x}{rgb_tuple[1]:02x}{rgb_tuple[2]:02x}"

    def update_size_label(self):
        w = abs(self.x2 - self.x1)
        h = abs(self.y2 - self.y1)
        self.size_lbl.config(text=self.t("size_lbl", w, h))

    def save_current_editor_to_zone(self):
        if getattr(self, '_updating_editor', False):
            return
        if hasattr(self, 'zones') and self.selected_zone_idx is not None and 0 <= self.selected_zone_idx < len(self.zones):
            zone = self.zones[self.selected_zone_idx]
            zone["x1"] = self.x1
            zone["y1"] = self.y1
            zone["x2"] = self.x2
            zone["y2"] = self.y2
            zone["target_color"] = self.target_color
            zone["tolerance"] = self.tolerance.get()
            zone["mode"] = self.mode.get()
            zone["min_area_pct"] = self.min_area_pct.get()
            if hasattr(self, 'zone_active_var'):
                zone["enabled"] = self.zone_active_var.get()
            self.update_zones_listbox_item(self.selected_zone_idx)
            self.profile_modified = True

    def add_zone(self):
        zone_id = len(self.zones) + 1
        new_zone = {
            "name": f"Zone {zone_id}",
            "x1": self.x1,
            "y1": self.y1,
            "x2": self.x2,
            "y2": self.y2,
            "target_color": self.target_color,
            "tolerance": self.tolerance.get(),
            "mode": self.mode.get(),
            "min_area_pct": self.min_area_pct.get(),
            "enabled": True,
            "was_color_present": None
        }
        self.zones.append(new_zone)
        self.update_zones_listbox()
        self.zones_listbox.selection_clear(0, "end")
        self.zones_listbox.selection_set("end")
        self.selected_zone_idx = len(self.zones) - 1
        self.save_config()
        self.profile_modified = True

    def delete_zone(self):
        if len(self.zones) <= 1:
            messagebox.showwarning(self.t("zone_min_req"), self.t("zone_min_req_msg"), parent=self.root)
            return
        
        idx = self.selected_zone_idx
        if idx is not None and 0 <= idx < len(self.zones):
            self.zones.pop(idx)
            self.selected_zone_idx = max(0, idx - 1)
            self.update_zones_listbox()
            self.zones_listbox.selection_clear(0, "end")
            self.zones_listbox.selection_set(self.selected_zone_idx)
            self.load_zone_to_editor(self.selected_zone_idx)
            self.save_config()
            self.profile_modified = True

    def rename_zone(self, event=None):
        if event:
            idx = self.zones_listbox.nearest(event.y)
            if idx >= 0:
                self.zones_listbox.selection_clear(0, "end")
                self.zones_listbox.selection_set(idx)
                self.zones_listbox.activate(idx)
                self.on_zone_selected(None)
        selections = self.zones_listbox.curselection()
        if not selections:
            return
        idx = selections[0]
        zone = self.zones[idx]
        new_name = simpledialog.askstring(self.t("rename_zone"), self.t("rename_zone_msg"), initialvalue=zone["name"], parent=self.root)
        if new_name and new_name.strip():
            zone["name"] = new_name.strip()
            self.update_zones_listbox_item(idx)
            self.save_config()
            self.profile_modified = True

    def move_zone_up(self):
        selections = self.zones_listbox.curselection()
        if not selections:
            return
        idx = selections[0]
        if idx > 0:
            self.zones[idx], self.zones[idx-1] = self.zones[idx-1], self.zones[idx]
            if self.selected_zone_idx == idx:
                self.selected_zone_idx = idx - 1
            elif self.selected_zone_idx == idx - 1:
                self.selected_zone_idx = idx
            self.update_zones_listbox()
            self.zones_listbox.selection_clear(0, "end")
            self.zones_listbox.selection_set(idx-1)
            self.save_config()
            self.profile_modified = True

    def move_zone_down(self):
        selections = self.zones_listbox.curselection()
        if not selections:
            return
        idx = selections[0]
        if idx < len(self.zones) - 1:
            self.zones[idx], self.zones[idx+1] = self.zones[idx+1], self.zones[idx]
            if self.selected_zone_idx == idx:
                self.selected_zone_idx = idx + 1
            elif self.selected_zone_idx == idx + 1:
                self.selected_zone_idx = idx
            self.update_zones_listbox()
            self.zones_listbox.selection_clear(0, "end")
            self.zones_listbox.selection_set(idx+1)
            self.save_config()
            self.profile_modified = True

    def update_zones_listbox(self):
        self.zones_listbox.delete(0, "end")
        for i, zone in enumerate(self.zones):
            w = abs(zone["x2"] - zone["x1"])
            h = abs(zone["y2"] - zone["y1"])
            prefix = "[✓] " if zone.get("enabled", True) else "[ ] "
            desc = prefix + self.t("zone_desc", zone['name'], w, h, zone['x1'], zone['y1'], MODE_TRANSLATIONS[self.current_lang].get(zone['mode'], zone['mode']))
            self.zones_listbox.insert("end", desc)

    def update_zones_listbox_item(self, idx):
        if idx is not None and 0 <= idx < len(self.zones):
            zone = self.zones[idx]
            w = abs(zone["x2"] - zone["x1"])
            h = abs(zone["y2"] - zone["y1"])
            prefix = "[✓] " if zone.get("enabled", True) else "[ ] "
            desc = prefix + self.t("zone_desc", zone['name'], w, h, zone['x1'], zone['y1'], MODE_TRANSLATIONS[self.current_lang].get(zone['mode'], zone['mode']))
            self.zones_listbox.delete(idx)
            self.zones_listbox.insert(idx, desc)
            self.zones_listbox.selection_set(idx)

    def on_zone_selected(self, event=None):
        if getattr(self, '_updating_editor', False):
            return
        selections = self.zones_listbox.curselection()
        if selections:
            self.selected_zone_idx = selections[0]
            self.load_zone_to_editor(self.selected_zone_idx)

    def load_zone_to_editor(self, idx):
        if idx is None or not (0 <= idx < len(self.zones)):
            return
        if getattr(self, '_updating_editor', False):
            return
            
        self._updating_editor = True
        try:
            zone = self.zones[idx]
            self.x1, self.y1, self.x2, self.y2 = zone["x1"], zone["y1"], zone["x2"], zone["y2"]
            self.target_color = zone["target_color"]
            
            try:
                self.entry_x1.trace_remove("write", self.entry_x1.trace_info()[0][1])
                self.entry_y1.trace_remove("write", self.entry_y1.trace_info()[0][1])
                self.entry_x2.trace_remove("write", self.entry_x2.trace_info()[0][1])
                self.entry_y2.trace_remove("write", self.entry_y2.trace_info()[0][1])
            except:
                pass
                
            self.entry_x1.set(str(self.x1))
            self.entry_y1.set(str(self.y1))
            self.entry_x2.set(str(self.x2))
            self.entry_y2.set(str(self.y2))
            
            self.entry_x1.trace_add("write", self.on_manual_coords_change)
            self.entry_y1.trace_add("write", self.on_manual_coords_change)
            self.entry_x2.trace_add("write", self.on_manual_coords_change)
            self.entry_y2.trace_add("write", self.on_manual_coords_change)
            
            self.tolerance.set(zone["tolerance"])
            self.tol_val_lbl.config(text=str(zone["tolerance"]))
            
            self.mode.set(zone["mode"])
            if hasattr(self, 'mode_cb'):
                translated_active = MODE_TRANSLATIONS[self.current_lang].get(zone["mode"], zone["mode"])
                self.mode_cb.set(translated_active)
            self.min_area_pct.set(zone["min_area_pct"])
            self.min_area_val_lbl.config(text=f"{zone['min_area_pct']:.1f}%")
            if hasattr(self, 'zone_active_var'):
                self.zone_active_var.set(zone.get("enabled", True))
            
            self.color_patch.config(bg=self.get_hex_color(self.target_color))
            self.color_text_lbl.config(text=f"RGB: {self.target_color}\nHEX: {self.get_hex_color(self.target_color)}")
            self.update_size_label()
            self.update_live_preview()
            self.update_overlay_border_visibility()
        finally:
            self._updating_editor = False

    def on_tolerance_change(self, val):
        if getattr(self, '_updating_editor', False):
            return
        self.tol_val_lbl.config(text=str(val))
        self.save_current_editor_to_zone()
        self.update_live_preview()

    def on_interval_change(self, val):
        self.interval_val_lbl.config(text=f"{float(val):.1f} s")

    def on_min_area_change(self, val):
        if getattr(self, '_updating_editor', False):
            return
        self.min_area_val_lbl.config(text=f"{float(val):.1f}%")
        self.save_current_editor_to_zone()
        self.update_live_preview()

    def on_mode_change(self, event):
        if getattr(self, '_updating_editor', False):
            return
        if hasattr(self, 'mode_cb'):
            val = self.mode_cb.get()
            for k, v in MODE_TRANSLATIONS[self.current_lang].items():
                if v == val:
                    self.mode.set(k)
                    break
        mode_val = self.mode.get()
        if mode_val == "Generelle Farbänderung":
            self.min_area_lbl.config(text="Änderungs-Fläche (%):")
            self.min_area_slider.config(from_=0.0, to=100.0)
            self.baseline_img = None
        else:
            self.min_area_lbl.config(text="Mindest-Fläche (%):")
            self.min_area_slider.config(from_=0.0, to=100.0)
        self.save_current_editor_to_zone()
        self.save_config()
        self.update_live_preview()

    def on_zone_active_changed(self):
        if getattr(self, '_updating_editor', False):
            return
        idx = self.selected_zone_idx
        if idx is not None and 0 <= idx < len(self.zones):
            self.zones[idx]["enabled"] = self.zone_active_var.get()
            self.update_zones_listbox_item(idx)
            self.save_config()
            self.profile_modified = True

    def on_border_dragged(self, x1, y1, x2, y2):
        if getattr(self, '_updating_editor', False):
            return
            
        self._updating_editor = True
        try:
            self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2
            
            try:
                self.entry_x1.trace_remove("write", self.entry_x1.trace_info()[0][1])
                self.entry_y1.trace_remove("write", self.entry_y1.trace_info()[0][1])
                self.entry_x2.trace_remove("write", self.entry_x2.trace_info()[0][1])
                self.entry_y2.trace_remove("write", self.entry_y2.trace_info()[0][1])
            except:
                pass
                
            self.entry_x1.set(str(self.x1))
            self.entry_y1.set(str(self.y1))
            self.entry_x2.set(str(self.x2))
            self.entry_y2.set(str(self.y2))
            
            self.entry_x1.trace_add("write", self.on_manual_coords_change)
            self.entry_y1.trace_add("write", self.on_manual_coords_change)
            self.entry_x2.trace_add("write", self.on_manual_coords_change)
            self.entry_y2.trace_add("write", self.on_manual_coords_change)
            
            self.update_size_label()
            self.update_live_preview()
            
            # Save state in zone and config
            if hasattr(self, 'zones') and self.selected_zone_idx is not None and 0 <= self.selected_zone_idx < len(self.zones):
                zone = self.zones[self.selected_zone_idx]
                zone["x1"] = self.x1
                zone["y1"] = self.y1
                zone["x2"] = self.x2
                zone["y2"] = self.y2
                self.update_zones_listbox_item(self.selected_zone_idx)
                
            self.save_config()
            self.overlay_border.update_position(x1, y1, x2, y2)
        finally:
            self._updating_editor = False

    def on_manual_coords_change(self, *args):
        if getattr(self, '_updating_editor', False):
            return
        try:
            x1 = int(self.entry_x1.get())
            y1 = int(self.entry_y1.get())
            x2 = int(self.entry_x2.get())
            y2 = int(self.entry_y2.get())
            
            if x2 > x1 and y2 > y1:
                self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2
                self.update_size_label()
                self.baseline_img = None
                self.update_overlay_border_visibility()
                self.root.after_cancel(self._preview_after_id) if hasattr(self, '_preview_after_id') else None
                self._preview_after_id = self.root.after(200, self.update_live_preview)
                self.save_current_editor_to_zone()
                self.save_config()
        except ValueError:
            pass

    def start_region_selection(self):
        self.overlay_border.hide()
        if self.hide_on_pick.get():
            self.saved_geometry = self.root.geometry()
            self.root.withdraw()
            self.root.update()
            time.sleep(0.25)
        RegionSelector(self.root, self.on_region_selected)

    def on_region_selected(self, x1, y1, x2, y2):
        if self.hide_on_pick.get():
            self.root.deiconify()
            if hasattr(self, 'saved_geometry') and self.saved_geometry:
                self.root.geometry(self.saved_geometry)
            self.root.update()
            
        if x1 is not None:
            self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2
            
            self.entry_x1.trace_remove("write", self.entry_x1.trace_info()[0][1])
            self.entry_y1.trace_remove("write", self.entry_y1.trace_info()[0][1])
            self.entry_x2.trace_remove("write", self.entry_x2.trace_info()[0][1])
            self.entry_y2.trace_remove("write", self.entry_y2.trace_info()[0][1])
            
            self.entry_x1.set(str(x1))
            self.entry_y1.set(str(y1))
            self.entry_x2.set(str(x2))
            self.entry_y2.set(str(y2))
            
            self.entry_x1.trace_add("write", self.on_manual_coords_change)
            self.entry_y1.trace_add("write", self.on_manual_coords_change)
            self.entry_x2.trace_add("write", self.on_manual_coords_change)
            self.entry_y2.trace_add("write", self.on_manual_coords_change)
            
            self.update_size_label()
            self.baseline_img = None
            self.update_live_preview()
            self.update_overlay_border_visibility()
            self.log_event(self.t("log_region_selected", x1, y1, x2, y2))
            self.save_current_editor_to_zone()
            self.save_config()
        else:
            self.update_overlay_border_visibility()

    def start_pixel_selection(self):
        self.overlay_border.hide()
        if self.hide_on_pick.get():
            self.saved_geometry = self.root.geometry()
            self.root.withdraw()
            self.root.update()
            time.sleep(0.25)
        PixelSelector(self.root, self.on_pixel_selected)

    def on_pixel_selected(self, x, y):
        if self.hide_on_pick.get():
            self.root.deiconify()
            if hasattr(self, 'saved_geometry') and self.saved_geometry:
                self.root.geometry(self.saved_geometry)
            self.root.update()
            
        if x is not None and y is not None:
            self.x1, self.y1, self.x2, self.y2 = x, y, x + 1, y + 1
            
            self.entry_x1.trace_remove("write", self.entry_x1.trace_info()[0][1])
            self.entry_y1.trace_remove("write", self.entry_y1.trace_info()[0][1])
            self.entry_x2.trace_remove("write", self.entry_x2.trace_info()[0][1])
            self.entry_y2.trace_remove("write", self.entry_y2.trace_info()[0][1])
            
            self.entry_x1.set(str(self.x1))
            self.entry_y1.set(str(self.y1))
            self.entry_x2.set(str(self.x2))
            self.entry_y2.set(str(self.y2))
            
            self.entry_x1.trace_add("write", self.on_manual_coords_change)
            self.entry_y1.trace_add("write", self.on_manual_coords_change)
            self.entry_x2.trace_add("write", self.on_manual_coords_change)
            self.entry_y2.trace_add("write", self.on_manual_coords_change)
            
            self.update_size_label()
            self.baseline_img = None
            self.update_live_preview()
            self.update_overlay_border_visibility()
            self.log_event(self.t("log_pixel_selected", x, y))
            self.save_current_editor_to_zone()
            self.save_config()
        else:
            self.update_overlay_border_visibility()

    def choose_color_dialog(self):
        _, hex_color = colorchooser.askcolor(initialcolor=self.get_hex_color(self.target_color), title="Ziel-Farbe wählen")
        if hex_color:
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            self.set_target_color((r, g, b))

    def start_eyedropper(self):
        self.overlay_border.hide()
        if self.hide_on_pick.get():
            self.saved_geometry = self.root.geometry()
            self.root.withdraw()
            self.root.update()
            time.sleep(0.25)
        ColorPickerEyedropper(self.root, self.on_color_picked)

    def on_color_picked(self, rgb_tuple):
        if self.hide_on_pick.get():
            self.root.deiconify()
            if hasattr(self, 'saved_geometry') and self.saved_geometry:
                self.root.geometry(self.saved_geometry)
            self.root.update()
            
        if rgb_tuple:
            self.set_target_color(rgb_tuple)
            self.log_event(self.t("log_color_picked", self.get_hex_color(rgb_tuple), rgb_tuple))
        self.update_overlay_border_visibility()

    def set_target_color(self, rgb_tuple):
        self.target_color = rgb_tuple
        hex_color = self.get_hex_color(rgb_tuple)
        self.color_patch.config(bg=hex_color)
        self.color_text_lbl.config(text=f"RGB: {rgb_tuple}\nHEX: {hex_color}")
        self.update_live_preview()
        self.save_current_editor_to_zone()
        self.save_config()

    def safe_after(self, delay, callback):
        """Thread-safe way to schedule callbacks on the main Tkinter thread, avoiding exit crashes."""
        try:
            if self.root and self.root.winfo_exists():
                self.root.after(delay, callback)
        except:
            pass

    def log_event(self, text):
        timestamp = time.strftime("[%H:%M:%S]")
        formatted_text = f"{timestamp} {text}"
        self.safe_after(0, lambda: self._safe_log_event(formatted_text))

    def _safe_log_event(self, text):
        try:
            self.log_list.insert(0, text)
            if self.log_list.size() > 100:
                self.log_list.delete(100, tk.END)
        except:
            pass

    def copy_selected_log(self, event=None):
        try:
            selected_indices = self.log_list.curselection()
            if selected_indices:
                selected_lines = [self.log_list.get(idx) for idx in selected_indices]
                text_to_copy = "\n".join(selected_lines)
                if text_to_copy:
                    self.root.clipboard_clear()
                    self.root.clipboard_append(text_to_copy)
                    self.root.update()
        except:
            pass

    def copy_all_logs(self):
        try:
            all_lines = self.log_list.get(0, tk.END)
            text_to_copy = "\n".join(all_lines)
            if text_to_copy:
                self.root.clipboard_clear()
                self.root.clipboard_append(text_to_copy)
                self.root.update()
        except:
            pass


    def update_live_preview(self):
        w = abs(self.x2 - self.x1)
        h = abs(self.y2 - self.y1)
        if w < 1 or h < 1:
            return
            
        try:
            target_w, target_h = 160, 160
            
            if w == 1 and h == 1:
                # Zoomed-in preview for a single pixel
                img = ImageGrab.grab(bbox=(self.x1 - 4, self.y1 - 4, self.x1 + 5, self.y1 + 5))
                arr = np.array(img)
                if arr.shape[-1] == 4:
                    arr = arr[:, :, :3]
                
                center_pixel = arr[4, 4]
                
                if self.mode.get() != "Generelle Farbänderung":
                    target = np.array(self.target_color)
                    diff = np.abs(center_pixel.astype(np.int16) - target)
                    dist = np.linalg.norm(diff, axis=-1)
                    
                    is_matching = dist <= self.tolerance.get()
                    matching_percentage = 100.0 if is_matching else 0.0
                    
                    self.match_stats_lbl.config(text=self.t("match_percentage", matching_percentage), foreground="#a6e3a1")
                    self.update_gauge(matching_percentage, self.min_area_pct.get())
                    
                    if is_matching:
                        green_color = np.array([166, 227, 161], dtype=np.uint8)
                        arr[4, 4] = (arr[4, 4] * 0.4 + green_color * 0.6).astype(np.uint8)
                else:
                    # Generelle Farbänderung
                    if self.is_monitoring and self.baseline_img is not None:
                        baseline_pixel = self.baseline_img[0, 0] if len(self.baseline_img.shape) >= 2 else self.baseline_img
                        diff = np.abs(center_pixel.astype(np.int16) - baseline_pixel.astype(np.int16))
                        dist = np.linalg.norm(diff, axis=-1)
                        
                        is_changed = dist > self.tolerance.get()
                        changed_percentage = 100.0 if is_changed else 0.0
                        
                        self.match_stats_lbl.config(text=self.t("change_percentage", changed_percentage), foreground="#f9e2af")
                        self.update_gauge(changed_percentage, self.min_area_pct.get())
                        
                        if is_changed:
                            yellow_color = np.array([249, 226, 175], dtype=np.uint8)
                            arr[4, 4] = (arr[4, 4] * 0.4 + yellow_color * 0.6).astype(np.uint8)
                    else:
                        self.match_stats_lbl.config(text=self.t("ready"), foreground="#a6adc8")
                        self.update_gauge(0.0, self.min_area_pct.get())
                
                display_img = Image.fromarray(arr)
                resized = display_img.resize((160, 160), Image.Resampling.NEAREST)
                self.preview_photo = ImageTk.PhotoImage(resized)
                self.preview_canvas.delete("all")
                self.preview_canvas.create_image(0, 0, anchor="nw", image=self.preview_photo)
                # Draw a highlight box around the center pixel
                self.preview_canvas.create_rectangle(71, 71, 89, 89, outline="#f38ba8", width=2)
                
            else:
                # Normal region preview
                img = ImageGrab.grab(bbox=(self.x1, self.y1, self.x2, self.y2))
                ratio = min(target_w / w, target_h / h)
                new_w = max(1, int(w * ratio))
                new_h = max(1, int(h * ratio))
                
                display_img = img.copy()
                arr = np.array(display_img)
                if arr.shape[-1] == 4:
                    arr = arr[:, :, :3]
                    
                total_pixels = arr.shape[0] * arr.shape[1]
                
                if self.mode.get() != "Generelle Farbänderung":
                    target = np.array(self.target_color)
                    diff = np.abs(arr.astype(np.int16) - target)
                    dist = np.linalg.norm(diff, axis=-1)
                    
                    mask = dist <= self.tolerance.get()
                    matching_pixels = np.sum(mask)
                    matching_percentage = (matching_pixels / total_pixels) * 100.0
                    
                    self.match_stats_lbl.config(text=self.t("match_percentage", matching_percentage), foreground="#a6e3a1")
                    self.update_gauge(matching_percentage, self.min_area_pct.get())
                    
                    green_color = np.array([166, 227, 161], dtype=np.uint8)
                    arr[mask] = (arr[mask] * 0.4 + green_color * 0.6).astype(np.uint8)
                    display_img = Image.fromarray(arr)
                else:
                    if self.is_monitoring and self.baseline_img is not None and self.baseline_img.shape == arr.shape:
                        diff = np.abs(arr.astype(np.int16) - self.baseline_img.astype(np.int16))
                        dist = np.linalg.norm(diff, axis=-1)
                        
                        changed_mask = dist > self.tolerance.get()
                        changed_pixels = np.sum(changed_mask)
                        changed_percentage = (changed_pixels / total_pixels) * 100.0
                        
                        self.match_stats_lbl.config(text=self.t("change_percentage", changed_percentage), foreground="#f9e2af")
                        self.update_gauge(changed_percentage, self.min_area_pct.get())
                        
                        yellow_color = np.array([249, 226, 175], dtype=np.uint8)
                        arr[changed_mask] = (arr[changed_mask] * 0.4 + yellow_color * 0.6).astype(np.uint8)
                        display_img = Image.fromarray(arr)
                    else:
                        self.match_stats_lbl.config(text=self.t("ready"), foreground="#a6adc8")
                        self.update_gauge(0.0, self.min_area_pct.get())
                
                resized = display_img.resize((new_w, new_h), Image.Resampling.NEAREST)
                bg = Image.new("RGB", (target_w, target_h), "#181825")
                offset_x = (target_w - new_w) // 2
                offset_y = (target_h - new_h) // 2
                bg.paste(resized, (offset_x, offset_y))
                
                self.preview_photo = ImageTk.PhotoImage(bg)
                self.preview_canvas.delete("all")
                self.preview_canvas.create_image(0, 0, anchor="nw", image=self.preview_photo)
                
        except Exception:
            pass

    def start_preview_loop(self):
        """Continuously captures the monitored screen region and updates the preview canvas."""
        if self.root.state() != "withdrawn":
            self.update_live_preview()
        self.root.after(150, self.start_preview_loop)

    def update_gauge(self, percentage, threshold):
        """Draws a clean, styled gauge bar indicating current match vs threshold."""
        self.gauge_canvas.delete("all")
        w = 160
        h = 12
        
        # Fill width
        fill_w = int((percentage / 100.0) * w)
        fill_w = max(0, min(w, fill_w))
        
        # Fill color: green if matches/exceeds threshold, else blue
        color = "#a6e3a1" if percentage >= threshold else "#89b4fa"
        self.gauge_canvas.create_rectangle(0, 0, fill_w, h, fill=color, width=0)
        
        # Threshold marker line (dashed red)
        thresh_x = int((threshold / 100.0) * w)
        thresh_x = max(1, min(w - 2, thresh_x))
        self.gauge_canvas.create_line(thresh_x, 0, thresh_x, h, fill="#ff4f4f", width=2, dash=(4, 2))

    def toggle_pause(self):
        if not self.is_monitoring:
            return
            
        if self.monitoring_paused:
            self.monitoring_paused = False
            self.macro_paused = False
            self.pause_btn.config(text="⏸️ Pause", style='Secondary.TButton')
            self.status_lbl.config(text=self.t("status_active"), fg="#a6e3a1")
            self.log_event(self.t("log_monitoring_resumed"))
        else:
            self.monitoring_paused = True
            self.macro_paused = True
            self.pause_btn.config(text="▶️ Fortsetzen", style='Primary.TButton')
            self.status_lbl.config(text=self.t("status_paused"), fg="#f9e2af")
            self.log_event(self.t("log_monitoring_paused"))

    def toggle_monitoring(self):
        if self.is_monitoring:
            self.stop_monitoring()
        else:
            self.start_monitoring()

    def start_monitoring(self):
        # Default zone if none exists
        if not hasattr(self, 'zones') or not self.zones:
            self.zones = [{
                "name": "Zone 1",
                "x1": self.x1,
                "y1": self.y1,
                "x2": self.x2,
                "y2": self.y2,
                "target_color": self.target_color,
                "tolerance": self.tolerance.get(),
                "mode": self.mode.get(),
                "min_area_pct": self.min_area_pct.get(),
                "was_color_present": None
            }]
            self.selected_zone_idx = 0
            self.update_zones_listbox()
            self.zones_listbox.selection_set(0)

        # Validate all enabled zones
        active_zones_count = 0
        for zone in self.zones:
            if zone.get("enabled", True) is False:
                continue
            active_zones_count += 1
            w = abs(zone["x2"] - zone["x1"])
            h = abs(zone["y2"] - zone["y1"])
            if w < 1 or h < 1:
                messagebox.showerror(self.t("error"), self.t("invalid_region_msg", zone['name']), parent=self.root)
                return
                
        if active_zones_count == 0:
            messagebox.showwarning(self.t("zone_min_req"), self.t("zone_min_req_msg"), parent=self.root)
            return
            
        self.is_monitoring = True
        self.monitoring_paused = False
        self.macro_paused = False
        self.macro_aborted = False
        self.pause_btn.config(state="normal", text="⏸️ Pause", style='Secondary.TButton')
        
        # Reset runtime states for each zone
        for zone in self.zones:
            if zone.get("mode") == "Ziel-Farbe erscheint":
                zone["was_color_present"] = False
            elif zone.get("mode") == "Ziel-Farbe verschwindet":
                zone["was_color_present"] = True
            else:
                zone["was_color_present"] = None
            zone["baseline_img"] = None
            
            if zone["mode"] == "Generelle Farbänderung":
                try:
                    screen = ImageGrab.grab(bbox=(zone["x1"], zone["y1"], zone["x2"], zone["y2"]))
                    zone["baseline_img"] = np.array(screen)
                    if zone["baseline_img"].shape[-1] == 4:
                        zone["baseline_img"] = zone["baseline_img"][:, :, :3]
                except Exception as e:
                    self.log_event(self.t("log_baseline_error", zone['name'], str(e)))
                    self.is_monitoring = False
                    return
                    
        self.start_btn.config(text="⏹️ Stoppen", style='TButton')
        self.status_lbl.config(text=self.t("status_active"), fg="#a6e3a1")
        self.log_event(self.t("log_monitoring_started", len(self.zones)))
        
        self.check_loop()

    def stop_monitoring(self):
        self.is_monitoring = False
        self.monitoring_paused = False
        self.macro_paused = False
        self.macro_aborted = True
        self.start_btn.config(text="▶️ Starten", style='Primary.TButton')
        self.pause_btn.config(state="disabled", text="⏸️ Pause", style='Secondary.TButton')
        self.status_lbl.config(text=self.t("status_inactive"), fg="#7f849c")
        self.log_event(self.t("log_monitoring_stopped"))

    def restart_monitoring(self):
        if self.is_monitoring:
            self.stop_monitoring()
            self.root.after(100, self.start_monitoring)
        else:
            self.start_monitoring()


    def check_loop(self):
        if not self.is_monitoring:
            return
            
        try:
            # Update preview of the currently active editor zone
            self.update_live_preview()
            
            if self.monitoring_paused:
                self.root.after(int(self.interval.get() * 1000), self.check_loop)
                return
                
            triggered = False
            alert_msg = ""
            
            for zone in self.zones:
                if zone.get("enabled", True) is False:
                    continue
                img = ImageGrab.grab(bbox=(zone["x1"], zone["y1"], zone["x2"], zone["y2"]))
                arr = np.array(img)
                if arr.shape[-1] == 4:
                    arr = arr[:, :, :3]
                    
                total_pixels = arr.shape[0] * arr.shape[1]
                if total_pixels == 0:
                    continue
                    
                mode = zone.get("mode")
                tolerance = zone.get("tolerance", 30)
                min_area_pct = zone.get("min_area_pct", 1.0)
                target_color = zone.get("target_color", (255, 0, 0))
                
                if mode == "Generelle Farbänderung":
                    if "baseline_img" not in zone or zone["baseline_img"] is None:
                        zone["baseline_img"] = arr.copy()
                    elif zone["baseline_img"].shape == arr.shape:
                        diff = np.abs(arr.astype(np.int16) - zone["baseline_img"].astype(np.int16))
                        dist = np.linalg.norm(diff, axis=-1)
                        
                        changed_pixels = np.sum(dist > tolerance)
                        changed_percentage = (changed_pixels / total_pixels) * 100.0
                        
                        if changed_percentage >= min_area_pct:
                            triggered = True
                            alert_msg = f"Farbänderung von {changed_percentage:.1f}% in {zone['name']} erkannt."
                            zone["baseline_img"] = arr.copy()
                else:
                    target = np.array(target_color)
                    diff = np.abs(arr.astype(np.int16) - target)
                    dist = np.linalg.norm(diff, axis=-1)
                    
                    matching_pixels = np.sum(dist <= tolerance)
                    matching_percentage = (matching_pixels / total_pixels) * 100.0
                    
                    is_present = matching_percentage >= min_area_pct
                    
                    if mode == "Ziel-Farbe erscheint":
                        if zone.get("was_color_present") is None:
                            zone["was_color_present"] = is_present
                        elif is_present and not zone["was_color_present"]:
                            triggered = True
                            alert_msg = f"Ziel-Farbe in {zone['name']} erscheint ({matching_percentage:.1f}% Übereinstimmung)."
                        zone["was_color_present"] = is_present
                        
                    elif mode == "Ziel-Farbe verschwindet":
                        if zone.get("was_color_present") is None:
                            zone["was_color_present"] = is_present
                        elif not is_present and zone["was_color_present"]:
                            triggered = True
                            alert_msg = f"Ziel-Farbe in {zone['name']} verschwunden ({matching_percentage:.1f}% Übereinstimmung)."
                        zone["was_color_present"] = is_present

                    elif mode == "Ziel-Farbe vorhanden":
                        if is_present:
                            triggered = True
                            alert_msg = f"Ziel-Farbe in {zone['name']} vorhanden ({matching_percentage:.1f}% Übereinstimmung)."

                    elif mode == "Ziel-Farbe nicht vorhanden":
                        if not is_present:
                            triggered = True
                            alert_msg = f"Ziel-Farbe in {zone['name']} nicht vorhanden ({matching_percentage:.1f}% Übereinstimmung)."
                        
                if triggered:
                    break
                    
            if triggered:
                current_time = time.time()
                # Cooldown of 3 seconds between macro triggers
                if current_time - self.last_trigger_time > 3.0:
                    self.last_trigger_time = current_time
                    self.log_event(alert_msg)
                    self.run_macro()
                    
        except Exception as e:
            self.log_event(self.t("log_monitoring_error", str(e)))
            
        if self.is_monitoring:
            interval_ms = int(self.interval.get() * 1000)
            self.root.after(interval_ms, self.check_loop)

    # Macro management methods
    def add_action(self):
        ActionDialog(self, self.on_action_saved)

    def edit_action(self, event=None):
        if event:
            idx = self.macro_listbox.nearest(event.y)
            if idx >= 0 and idx < len(self.macro_actions):
                self.macro_listbox.selection_clear(0, "end")
                self.macro_listbox.selection_set(idx)
                self.macro_listbox.activate(idx)
        selected_idx = self.macro_listbox.curselection()
        if not selected_idx:
            messagebox.showinfo("Info", self.t("action_select_action_first"), parent=self.root)
            return
        idx = selected_idx[0]
        ActionDialog(self, lambda act: self.on_action_saved(act, idx), self.macro_actions[idx])

    def on_action_saved(self, action, idx=None):
        if idx is None:
            self.macro_actions.append(action)
            self.log_event(self.t("log_action_added", self._action_to_string(action)))
        else:
            self.macro_actions[idx] = action
            self.log_event(self.t("log_action_edited", idx+1, self._action_to_string(action)))
        self.update_macro_listbox()
        self.save_config()
        self.profile_modified = True

    def toggle_action_enabled(self, event=None):
        selected_idx = self.macro_listbox.curselection()
        if not selected_idx:
            return "break" if event else None
        idx = selected_idx[0]
        action = self.macro_actions[idx]
        action["enabled"] = not action.get("enabled", True)
        self.update_macro_listbox()
        self.macro_listbox.select_set(idx)
        self.save_config()
        self.profile_modified = True
        return "break"

    def delete_action(self):
        selected_idx = self.macro_listbox.curselection()
        if not selected_idx:
            messagebox.showinfo("Info", self.t("action_select_action_first"))
            return
        idx = selected_idx[0]
        action = self.macro_actions.pop(idx)
        self.log_event(self.t("log_action_removed", idx+1, self._action_to_string(action)))
        self.update_macro_listbox()
        self.save_config()
        self.profile_modified = True
        
        new_len = len(self.macro_actions)
        if new_len > 0:
            new_sel = min(idx, new_len - 1)
            self.macro_listbox.select_set(new_sel)

    def move_action_up(self):
        selected_idx = self.macro_listbox.curselection()
        if not selected_idx:
            return
        idx = selected_idx[0]
        if idx > 0:
            self.macro_actions[idx], self.macro_actions[idx-1] = self.macro_actions[idx-1], self.macro_actions[idx]
            self.update_macro_listbox()
            self.macro_listbox.select_set(idx-1)
            self.save_config()
            self.profile_modified = True

    def move_action_down(self):
        selected_idx = self.macro_listbox.curselection()
        if not selected_idx:
            return
        idx = selected_idx[0]
        if idx < len(self.macro_actions) - 1:
            self.macro_actions[idx], self.macro_actions[idx+1] = self.macro_actions[idx+1], self.macro_actions[idx]
            self.update_macro_listbox()
            self.macro_listbox.select_set(idx+1)
            self.save_config()
            self.profile_modified = True

    def _action_to_string(self, action):
        a_type = action["type"]
        if a_type == "wait":
            return self.t("act_wait", action['value'])
        elif a_type == "click":
            ct = action.get("click_type", "left")
            ct_name = self.t(ct + "_click")
            return self.t("act_click", ct_name, action['x'], action['y'])
        elif a_type == "key_combo":
            return self.t("act_key_combo", action.get('value', ''))
        elif a_type == "type_text":
            return self.t("act_type_text", action.get('value', ''))
        elif a_type == "play_sound":
            return self.t("act_play_sound")
        elif a_type == "ntfy":
            return self.t("act_ntfy", action.get('topic', ''))
        return self.t("act_unknown")

    def update_macro_listbox(self):
        self.macro_listbox.delete(0, tk.END)
        for idx, action in enumerate(self.macro_actions):
            prefix = "[✓] " if action.get("enabled", True) else "[ ] "
            self.macro_listbox.insert(tk.END, f"{idx+1}. {prefix}{self._action_to_string(action)}")

    def test_macro(self):
        if getattr(self, 'macro_running', False):
            self.log_event(self.t("macro_already_running"))
            return
        self._testing_macro = True
        self.macro_running = True
        threading.Thread(target=self._execute_macro_thread, daemon=True).start()

    def run_macro(self):
        if not self.macro_actions:
            self.log_event(self.t("macro_empty_warning"))
            return
        if getattr(self, 'macro_running', False):
            self.log_event(self.t("macro_already_running_trigger"))
            return
        self.macro_running = True
        self.macro_aborted = False
        threading.Thread(target=self._execute_macro_thread, daemon=True).start()

    def _highlight_macro_step(self, idx):
        """Highlights the active macro action row in the Listbox."""
        self.macro_listbox.select_clear(0, tk.END)
        self.macro_listbox.select_set(idx)
        self.macro_listbox.activate(idx)
        self.macro_listbox.see(idx)

    def _clear_macro_highlight(self):
        """Clears selection highlight from macro listbox."""
        self.macro_listbox.select_clear(0, tk.END)

    def _execute_macro_thread(self):
        self.log_event(self.t("log_macro_started"))
        # Update status bar visually
        self.safe_after(0, lambda: self.status_lbl.config(text=self.t("status_macro_running"), fg="#f9e2af"))
        
        try:
            for idx, action in enumerate(self.macro_actions):
                if action.get("enabled", True) is False:
                    continue
                # Stop if monitoring was turned off mid-execution or macro aborted (unless testing manually)
                if self.macro_aborted or (not self.is_monitoring and not self._testing_macro):
                    self.log_event(self.t("log_macro_aborted"))
                    break
                
                # Check for pause state
                while self.macro_paused and self.is_monitoring and not self._testing_macro:
                    time.sleep(0.05)
                    
                # Re-check abort after possible pause
                if self.macro_aborted or (not self.is_monitoring and not self._testing_macro):
                    self.log_event(self.t("log_macro_aborted"))
                    break
                
                # Highlight active step
                self.safe_after(0, lambda i=idx: self._highlight_macro_step(i))
                    
                a_type = action["type"]
                if a_type == "wait":
                    ms = action["value"]
                    self.log_event(self.t("log_macro_started") + f" Action {idx+1}: Wait {ms} ms")
                    
                    # Implement interruptible sleep with pause/abort checks
                    sleep_seconds = ms / 1000.0
                    step = 0.05
                    elapsed = 0.0
                    while elapsed < sleep_seconds:
                        if self.macro_aborted or (not self.is_monitoring and not self._testing_macro):
                            break
                        while self.macro_paused and self.is_monitoring and not self._testing_macro:
                            time.sleep(0.05)
                        time.sleep(step)
                        elapsed += step
                elif a_type == "click":
                    x, y = action["x"], action["y"]
                    ct = action.get("click_type", "left")
                    ct_name = CLICK_TYPE_MAP.get(ct, "Linksklick")
                    
                    self.log_event(f"Action {idx+1}: {ct_name} at X:{x}, Y:{y}")
                    self.mouse_controller.move_to(x, y)
                    
                    # Short interruptible sleep to allow mouse to move
                    step = 0.01
                    elapsed = 0.0
                    while elapsed < 0.05:
                        if self.macro_aborted or (not self.is_monitoring and not self._testing_macro):
                            break
                        time.sleep(step)
                        elapsed += step
                    
                    if ct == "left":
                        self.mouse_controller.click(button=1, double=False)
                    elif ct == "right":
                        self.mouse_controller.click(button=3, double=False)
                    elif ct == "double":
                        self.mouse_controller.click(button=1, double=True)
                    time.sleep(0.05) # Settle down
                elif a_type == "key_combo":
                    val = action.get("value", "")
                    self.log_event(f"Action {idx+1}: Keypress '{val}'")
                    self.mouse_controller.key_combo(val)
                    time.sleep(0.1)
                elif a_type == "type_text":
                    val = action.get("value", "")
                    self.log_event(f"Action {idx+1}: Type text '{val}'")
                    self.mouse_controller.type_text(val)
                    time.sleep(0.1)
                elif a_type == "play_sound":
                    self.log_event(f"Action {idx+1}: Play sound...")
                    self.play_alarm_sound()
                elif a_type == "ntfy":
                    topic = action.get("topic")
                    title = action.get("title", "")
                    message = action.get("message", "")
                    
                    self.log_event(f"Action {idx+1}: Ntfy push...")
                    
                    try:
                        import urllib.request
                        url = f"https://ntfy.sh/{topic}"
                        headers = {}
                        if title:
                            headers["Title"] = title.encode('utf-8')
                        
                        req = urllib.request.Request(url, data=message.encode('utf-8'), headers=headers, method="POST")
                        with urllib.request.urlopen(req) as resp:
                            resp.read()
                            
                        self.log_event(self.t("log_ntfy_sent", idx+1))
                    except Exception as ex:
                        self.log_event(self.t("log_ntfy_error", idx+1, str(ex)))
            
            self.log_event(self.t("log_macro_finished"))
        except Exception as e:
            self.log_event(self.t("log_macro_error", str(e)))
        finally:
            self.macro_running = False
            self._testing_macro = False
            # Clear highlight and restore status bar state
            self.safe_after(0, self._clear_macro_highlight)
            self.safe_after(0, lambda: self.status_lbl.config(text=self.t("status_active") if self.is_monitoring else self.t("status_inactive"), fg="#a6e3a1" if self.is_monitoring else "#7f849c"))

    def update_overlay_border_visibility(self):
        """Toggles or updates the position of the transparent red screen overlay border."""
        if hasattr(self, 'show_overlay_border') and self.show_overlay_border.get():
            self.overlay_border.show(self.x1, self.y1, self.x2, self.y2)
        else:
            self.overlay_border.hide()

    def update_always_on_top(self):
        """Sets the root window to be topmost or not."""
        if hasattr(self, 'always_on_top'):
            is_top = self.always_on_top.get()
            self.root.attributes("-topmost", is_top)
            self.save_config()

    def show_shortcuts_dialog(self):
        messagebox.showinfo(self.t("shortcuts_title"), self.t("shortcuts_content"))

    def show_about_dialog(self):
        messagebox.showinfo(self.t("about_title"), self.t("about_content"))

    def on_space_pressed(self, event):
        """Hotkey to toggle monitoring using the Spacebar, unless focused on an entry field."""
        focused = self.root.focus_get()
        if isinstance(focused, (tk.Entry, ttk.Entry)):
            return
        self.toggle_monitoring()

    def on_delete_pressed(self, event):
        """Hotkey to delete the selected macro action using the Delete key, unless focused on an entry field."""
        focused = self.root.focus_get()
        if isinstance(focused, (tk.Entry, ttk.Entry)):
            return
        selected = self.macro_listbox.curselection()
        if selected:
            idx = selected[0]
            del self.macro_actions[idx]
            self.update_macro_listbox()
            self.save_config()
            self.log_event(self.t("log_shortcut_deleted", idx+1))

    def play_alarm_sound(self):
        """Generates a short WAV alert sound if it doesn't exist and plays it using ALSA aplay, or falls back to system bell."""
        wav_path = os.path.join(SCRIPT_DIR, "beep.wav")
        if not os.path.exists(wav_path):
            try:
                import wave, math, struct
                sample_rate = 8000
                num_samples = int(sample_rate * 0.4) # 400ms duration
                with wave.open(wav_path, 'wb') as w:
                    w.setnchannels(1)
                    w.setsampwidth(2) # 16-bit
                    w.setframerate(sample_rate)
                    for i in range(num_samples):
                        t = float(i) / sample_rate
                        val = int(16000.0 * math.sin(2.0 * math.pi * 587.33 * t))
                        w.writeframesraw(struct.pack('<h', val))
            except Exception as e:
                print(f"Fehler beim Erzeugen der WAV-Datei: {e}", file=sys.stderr)
                
        if os.path.exists(wav_path):
            if sys.platform.startswith("win"):
                try:
                    import winsound
                    winsound.PlaySound(wav_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                except Exception as e:
                    print(f"Windows PlaySound Fehler: {e}", file=sys.stderr)
                    try:
                        self.root.bell()
                    except:
                        pass
            else:
                import subprocess
                try:
                    subprocess.Popen(["aplay", "-q", wav_path])
                except Exception:
                    try:
                        self.root.bell()
                    except:
                        pass
        else:
            try:
                self.root.bell()
            except:
                pass

    def refresh_profile_list(self):
        """Scans the profiles/ directory for JSON profile files and refreshes the Combobox."""
        profiles_dir = os.path.join(SCRIPT_DIR, "profiles")
        os.makedirs(profiles_dir, exist_ok=True)
        files = os.listdir(profiles_dir)
        profile_names = [os.path.splitext(f)[0] for f in files if f.endswith(".json")]
        if not profile_names:
            profile_names = ["default"]
            self.save_profile_to_file("default")
        
        self.profile_cb.config(values=profile_names)
        if self.profile_name_var.get() not in profile_names:
            self.profile_name_var.set(profile_names[0])

    def save_profile_to_file(self, name):
        """Saves current dashboard state and macros into a specific profile file."""
        profiles_dir = os.path.join(SCRIPT_DIR, "profiles")
        os.makedirs(profiles_dir, exist_ok=True)
        path = os.path.join(profiles_dir, f"{name}.json")
        try:
            serializable_zones = []
            if hasattr(self, 'zones'):
                for zone in self.zones:
                    sz = zone.copy()
                    if "target_color" in sz:
                        sz["target_color"] = list(sz["target_color"])
                    if "was_color_present" in sz:
                        sz.pop("was_color_present")
                    if "baseline_img" in sz:
                        sz.pop("baseline_img")
                    serializable_zones.append(sz)
            
            data = {
                "language": self.current_lang,
                "x1": self.x1,
                "y1": self.y1,
                "x2": self.x2,
                "y2": self.y2,
                "target_color": list(self.target_color),
                "tolerance": self.tolerance.get(),
                "mode": self.mode.get(),
                "interval": self.interval.get(),
                "min_area_pct": self.min_area_pct.get(),
                "hide_on_pick": self.hide_on_pick.get(),
                "show_overlay_border": self.show_overlay_border.get(),
                "always_on_top": self.always_on_top.get() if hasattr(self, 'always_on_top') else False,
                "macro_actions": self.macro_actions,
                "zones": serializable_zones,
                "selected_zone_idx": self.selected_zone_idx
            }
            
            try:
                geom = self.root.geometry()
                parts = geom.split('+')[0].split('x')
                w, h = int(parts[0]), int(parts[1])
                if w > 200 and h > 200:
                    data["window_geometry"] = geom
            except:
                pass
                
            if hasattr(self, 'paned'):
                try:
                    s_pos = self.paned.sashpos(0)
                    if s_pos > 100:
                        data["sash_position"] = s_pos
                except:
                    pass
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            self.profile_modified = False
            self.current_profile_name = name
        except Exception as e:
            self.log_event(f"Fehler beim Speichern des Profils: {e}")

    def save_profile_btn(self):
        """Prompt the user for a name and save the profile."""
        name = simpledialog.askstring(self.t("save_profile_title"), self.t("save_profile_prompt"), initialvalue=self.profile_name_var.get(), parent=self.root)
        if name:
            name = name.strip()
            if name:
                self.save_profile_to_file(name)
                self.profile_name_var.set(name)
                self.refresh_profile_list()
                self.log_event(self.t("log_profile_saved", name))

    def load_profile_btn(self):
        """Loads the selected profile with unsaved changes verification."""
        name = self.profile_name_var.get()
        if not name:
            return
            
        current = getattr(self, 'current_profile_name', 'default')
        if name == current:
            return
            
        if getattr(self, 'profile_modified', False):
            ans = messagebox.askyesnocancel(self.t("unsaved_changes"), self.t("unsaved_changes_switch_msg", current))
            if ans is True:
                self.save_profile_to_file(current)
            elif ans is None:
                self.profile_name_var.set(current)
                return
                
        self.load_profile_from_file(name)

    def load_profile_from_file(self, name):
        """Loads coordinates, target colors, and macros from a specific profile file."""
        path = os.path.join(SCRIPT_DIR, "profiles", f"{name}.json")
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            self.x1 = data.get("x1", self.x1)
            self.y1 = data.get("y1", self.y1)
            self.x2 = data.get("x2", self.x2)
            self.y2 = data.get("y2", self.y2)
            
            tc = data.get("target_color")
            if tc and len(tc) == 3:
                self.target_color = tuple(tc)
                
            self.tolerance.set(data.get("tolerance", self.tolerance.get()))
            self.mode.set(data.get("mode", self.mode.get()))
            self.interval.set(data.get("interval", self.interval.get()))
            self.min_area_pct.set(data.get("min_area_pct", self.min_area_pct.get()))
            self.hide_on_pick.set(data.get("hide_on_pick", self.hide_on_pick.get()))
            self.show_overlay_border.set(data.get("show_overlay_border", self.show_overlay_border.get()))
            
            if hasattr(self, 'always_on_top'):
                self.always_on_top.set(data.get("always_on_top", False))
                self.root.attributes("-topmost", self.always_on_top.get())
                
            win_geom = data.get("window_geometry")
            if win_geom:
                try:
                    parts = win_geom.split('+')[0].split('x')
                    w, h = int(parts[0]), int(parts[1])
                    if w > 200 and h > 200:
                        self.root.geometry(win_geom)
                except:
                    pass
            
            sash_pos = data.get("sash_position")
            if sash_pos is not None and hasattr(self, 'paned'):
                try:
                    if int(sash_pos) > 100:
                        self.root.after(100, lambda: self.paned.sashpos(0, int(sash_pos)))
                except:
                    pass
            
            # Legacy migrations (in case click_type was missing)
            actions = data.get("macro_actions", self.macro_actions)
            for act in actions:
                if act["type"] == "click" and "click_type" not in act:
                    act["click_type"] = "left"
            self.macro_actions = actions
            
            # Load zones
            zones_data = data.get("zones")
            if zones_data:
                self.zones = []
                for zd in zones_data:
                    zone = zd.copy()
                    if "target_color" in zone:
                        zone["target_color"] = tuple(zone["target_color"])
                    zone["was_color_present"] = None
                    self.zones.append(zone)
                self.selected_zone_idx = data.get("selected_zone_idx", 0)
                if self.selected_zone_idx >= len(self.zones):
                    self.selected_zone_idx = 0
            else:
                self.zones = [{
                    "name": "Zone 1",
                    "x1": self.x1,
                    "y1": self.y1,
                    "x2": self.x2,
                    "y2": self.y2,
                    "target_color": self.target_color,
                    "tolerance": self.tolerance.get(),
                    "mode": self.mode.get(),
                    "min_area_pct": self.min_area_pct.get(),
                    "was_color_present": None
                }]
                self.selected_zone_idx = 0
            
            # Populate listbox and load selected zone to editor
            self.update_zones_listbox()
            self.zones_listbox.selection_clear(0, "end")
            if 0 <= self.selected_zone_idx < len(self.zones):
                self.zones_listbox.selection_set(self.selected_zone_idx)
                self.load_zone_to_editor(self.selected_zone_idx)
            
            self.interval_val_lbl.config(text=f"{self.interval.get():.1f} s")
            
            self.update_macro_listbox()
            self.update_overlay_border_visibility()
            self.on_mode_change(None)
            
            if hasattr(self, 'profile_name_var'):
                self.profile_name_var.set(name)
            self.save_config()
            self.profile_modified = False
            self.current_profile_name = name
            self.log_event(self.t("log_profile_loaded", name))
        except Exception as e:
            self.log_event(f"Fehler beim Laden des Profils: {e}")
        finally:
            self._updating_editor = False

    def delete_profile_btn(self):
        """Deletes the selected profile from profiles/ (except default)."""
        name = self.profile_name_var.get()
        if name == "default":
            messagebox.showwarning(self.t("zone_min_req"), self.t("del_profile_default_warn"))
            return
        if messagebox.askyesno(self.t("del_profile_confirm"), self.t("del_profile_confirm_msg", name)):
            path = os.path.join(SCRIPT_DIR, "profiles", f"{name}.json")
            if os.path.exists(path):
                os.remove(path)
            self.profile_name_var.set("default")
            self.refresh_profile_list()
            self.load_profile_from_file("default")
            self.log_event(self.t("log_profile_deleted", name))

    def export_macro_btn(self):
        """Export current macro actions to a JSON file."""
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            title="Makro exportieren",
            parent=self.root
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self.macro_actions, f, indent=4, ensure_ascii=False)
                self.log_event(self.t("log_macro_exported"))
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Exportieren des Makros: {e}")

    def import_macro_btn(self):
        """Import macro actions from a JSON file."""
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            filetypes=[("JSON Files", "*.json")],
            title="Makro importieren",
            parent=self.root
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    actions = json.load(f)
                if isinstance(actions, list):
                    for act in actions:
                        if not isinstance(act, dict) or "type" not in act:
                            raise ValueError("Ungültiges Makro-Format.")
                    self.macro_actions = actions
                    self.update_macro_listbox()
                    self.save_config()
                    self.profile_modified = True
                    self.log_event(self.t("log_macro_imported"))
                else:
                    raise ValueError("Makro muss eine Liste von Aktionen sein.")
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Importieren des Makros: {e}")

    def export_log_btn(self):
        """Export event log messages to a TXT file."""
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Textdateien", "*.txt")],
            title="Protokoll exportieren",
            parent=self.root
        )
        if path:
            try:
                logs = self.log_list.get(0, tk.END)
                with open(path, "w", encoding="utf-8") as f:
                    for line in logs:
                        f.write(line + "\n")
                self.log_event(self.t("log_log_exported"))
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Exportieren des Protokolls: {e}")


if __name__ == "__main__":
    import sys
    # Enable high DPI awareness on Windows
    if sys.platform.startswith("win"):
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass
    root = tk.Tk()
    app = ColorMonitorApp(root)
    root.mainloop()
