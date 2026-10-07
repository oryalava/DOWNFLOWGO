import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import configparser
import subprocess
import tempfile
import threading
import queue
import sys
import os
from pathlib import Path


APP_DIR = Path(__file__).resolve().parent
MAIN_SCRIPT = APP_DIR / "main_downflowgo.py"


class DownflowGoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DOWNFLOWGO")
        self.root.geometry("1100x820")
        self.root.minsize(850, 620)

        self.config = configparser.ConfigParser()
        self.config_file = None
        self.process = None
        self.log_queue = queue.Queue()

        self.vars = {
            "eruptions_folder": tk.StringVar(),
            "name_vent": tk.StringVar(),
            "easting": tk.StringVar(),
            "northing": tk.StringVar(),
            "csv_vent_file": tk.StringVar(value="0"),
            "dem": tk.StringVar(),
            "dh": tk.StringVar(),
            "n_path": tk.StringVar(),
            "slope_step": tk.StringVar(),
            "epsg_code": tk.StringVar(value="32740"),
            "json": tk.StringVar(),
            "effusion_rates_input": tk.StringVar(),
            "mode": tk.StringVar(value="downflowgo"),
            "grid_mode": tk.StringVar(value="no"),
            "language": tk.StringVar(value="EN"),
            "mapping_display": tk.StringVar(value="no"),
            "use_gui": tk.StringVar(value="no"),
            "delete_existing_results": tk.StringVar(value="yes"),
            "parameters_file_downflow": tk.StringVar(),
            "ventgrid_size": tk.StringVar(),
            "ventgrid_resolution": tk.StringVar(),
            "grid_csv": tk.StringVar(value="0"),
            "dem_resolution": tk.StringVar(),
            "img_tif_map_background_path": tk.StringVar(),
            "monitoring_network_path": tk.StringVar(value="0"),
            "lava_flow_outline_path": tk.StringVar(value="0"),
            "logo_path": tk.StringVar(value="0"),
            "source_img_tif_map_background": tk.StringVar(value="0"),
            "unverified_data": tk.StringVar(value="0"),
        }

        self.build_ui()
        self.root.after(100, self.poll_log_queue)


    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def build_ui(self):
        container = ttk.Frame(self.root)
        container.pack(fill="both", expand=True)
        canvas = tk.Canvas(container, highlightthickness=0)
        scroll = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        outer = ttk.Frame(canvas, padding=12)
        win = canvas.create_window((0,0), window=outer, anchor="nw")
        outer.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(win, width=e.width))

        # Configuration
        config_frame = ttk.LabelFrame(outer, text="DOWNFLOWGO configuration", padding=10)
        config_frame.pack(fill="x", pady=(0, 8))

        self.ini_label = ttk.Label(config_frame, text="No INI configuration loaded")
        self.ini_label.grid(row=0, column=0, sticky="w", padx=(0, 10))

        ttk.Button(
            config_frame, text="Load INI", command=self.choose_ini
        ).grid(row=0, column=1, padx=4)

        ttk.Button(
            config_frame, text="Save INI As...", command=self.save_ini_as
        ).grid(row=0, column=2, padx=4)

        # Main inputs
        inputs = ttk.LabelFrame(outer, text="Simulation", padding=10)
        inputs.pack(fill="x", pady=8)
        inputs.columnconfigure(1, weight=1)

        row = 0
        row = self.add_path_row(
            inputs, row, "Eruption results folder:",
            self.vars["eruptions_folder"], folder=True
        )
        row = self.add_entry_row(inputs, row, "Name of the vent:", self.vars["name_vent"])

        coord = ttk.Frame(inputs)
        coord.grid(row=row, column=0, columnspan=3, sticky="ew", pady=3)
        ttk.Label(coord, text="Easting (UTM):", width=24).pack(side="left")
        ttk.Entry(coord, textvariable=self.vars["easting"], width=18).pack(side="left", padx=(0, 12))
        ttk.Label(coord, text="Northing (UTM):").pack(side="left")
        ttk.Entry(coord, textvariable=self.vars["northing"], width=18).pack(side="left", padx=(4, 12))
        ttk.Label(coord, text="EPSG:").pack(side="left")
        ttk.Entry(coord, textvariable=self.vars["epsg_code"], width=10).pack(side="left", padx=4)
        row += 1

        row = self.add_path_row(
            inputs, row, "Vent CSV (0 = use coordinates):",
            self.vars["csv_vent_file"],
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        row = self.add_path_row(
            inputs, row, "DEM:",
            self.vars["dem"],
            filetypes=[("DEM / raster", "*.asc *.tif *.tiff"), ("All files", "*.*")]
        )

        params = ttk.Frame(inputs)
        params.grid(row=row, column=0, columnspan=3, sticky="ew", pady=3)
        ttk.Label(params, text="DH:", width=24).pack(side="left")
        ttk.Entry(params, textvariable=self.vars["dh"], width=10).pack(side="left")
        ttk.Label(params, text="N paths:").pack(side="left", padx=(15, 4))
        ttk.Entry(params, textvariable=self.vars["n_path"], width=10).pack(side="left")
        ttk.Label(params, text="Slope step:").pack(side="left", padx=(15, 4))
        ttk.Entry(params, textvariable=self.vars["slope_step"], width=10).pack(side="left")
        row += 1

        # Mode / grid / language
        options = ttk.Frame(inputs)
        options.grid(row=row, column=0, columnspan=3, sticky="w", pady=(7, 3))

        ttk.Label(options, text="Mode:", width=24).pack(side="left")
        ttk.Radiobutton(
            options, text="DOWNFLOWGO", variable=self.vars["mode"], value="downflowgo",
            command=self.update_mode_state
        ).pack(side="left")
        ttk.Radiobutton(
            options, text="DOWNFLOW only", variable=self.vars["mode"], value="downflow",
            command=self.update_mode_state
        ).pack(side="left", padx=(8, 18))

        ttk.Label(options, text="Grid mode:").pack(side="left")
        ttk.Radiobutton(options, text="No", variable=self.vars["grid_mode"], value="no").pack(side="left")
        ttk.Radiobutton(options, text="Yes", variable=self.vars["grid_mode"], value="yes").pack(side="left")
        row += 1

        # Additional INI parameters
        extra = ttk.LabelFrame(outer, text="Additional DOWNFLOW parameters", padding=10)
        extra.pack(fill="x", pady=8)
        extra.columnconfigure(1, weight=1)
        self.add_path_row(extra, 0, "DOWNFLOW parameters file:", self.vars["parameters_file_downflow"],
                          filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        opts = ttk.Frame(extra)
        opts.grid(row=1, column=0, columnspan=3, sticky="w", pady=3)
        ttk.Label(opts, text="Delete existing results:", width=28).pack(side="left")
        ttk.Combobox(opts, textvariable=self.vars["delete_existing_results"],
                     values=["yes","no"], width=7, state="readonly").pack(side="left", padx=(0,18))
        ttk.Label(opts, text="use_gui:").pack(side="left")
        ttk.Combobox(opts, textvariable=self.vars["use_gui"],
                     values=["yes","no"], width=7, state="readonly").pack(side="left", padx=5)

        # PyFLOWGO
        self.flowgo_frame = ttk.LabelFrame(outer, text="PyFLOWGO (DOWNFLOWGO mode)", padding=10)
        self.flowgo_frame.pack(fill="x", pady=8)
        self.flowgo_frame.columnconfigure(1, weight=1)

        self.add_path_row(
            self.flowgo_frame, 0, "PyFLOWGO JSON:",
            self.vars["json"],
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        self.add_entry_row(
            self.flowgo_frame, 1,
            "Effusion rates (first,last,step):",
            self.vars["effusion_rates_input"]
        )

        # Grid parameters
        grid = ttk.LabelFrame(outer, text="Grid parameters", padding=10)
        grid.pack(fill="x", pady=8)
        grid.columnconfigure(1, weight=1)
        self.add_entry_row(grid, 0, "Vent grid size (m):", self.vars["ventgrid_size"])
        self.add_entry_row(grid, 1, "Vent grid resolution (m):", self.vars["ventgrid_resolution"])
        self.add_path_row(grid, 2, "Grid CSV (0 = create grid):", self.vars["grid_csv"],
                          filetypes=[("CSV files","*.csv"),("All files","*.*")])
        self.add_entry_row(grid, 3, "DEM resolution (m):", self.vars["dem_resolution"])

        # Mapping
        mapping = ttk.LabelFrame(outer, text="Mapping", padding=10)
        mapping.pack(fill="x", pady=8)
        mapping.columnconfigure(1, weight=1)
        r=0
        r=self.add_path_row(mapping,r,"Background map TIFF:",self.vars["img_tif_map_background_path"],
                            filetypes=[("TIFF","*.tif *.tiff"),("All files","*.*")])
        r=self.add_path_row(mapping,r,"Monitoring network:",self.vars["monitoring_network_path"],
                            filetypes=[("Shapefile","*.shp"),("All files","*.*")])
        r=self.add_path_row(mapping,r,"Lava flow outline:",self.vars["lava_flow_outline_path"],
                            filetypes=[("Shapefile","*.shp"),("All files","*.*")])
        r=self.add_path_row(mapping,r,"Logo:",self.vars["logo_path"],
                            filetypes=[("Images","*.png *.jpg *.jpeg *.tif *.tiff"),("All files","*.*")])
        r=self.add_entry_row(mapping,r,"Background image source:",self.vars["source_img_tif_map_background"])
        self.add_entry_row(mapping,r,"Unverified data:",self.vars["unverified_data"])

        # Display options
        display = ttk.Frame(outer)
        display.pack(fill="x", pady=(3, 8))
        ttk.Label(display, text="Map language:").pack(side="left")
        ttk.Combobox(
            display, textvariable=self.vars["language"],
            values=["EN", "FR"], width=6, state="readonly"
        ).pack(side="left", padx=(5, 18))
        ttk.Label(display, text="Display map:").pack(side="left")
        ttk.Combobox(
            display, textvariable=self.vars["mapping_display"],
            values=["no", "yes"], width=6, state="readonly"
        ).pack(side="left", padx=5)

        # Run controls
        controls = ttk.Frame(outer)
        controls.pack(fill="x", pady=6)

        self.run_button = ttk.Button(
            controls, text="RUN DOWNFLOWGO", command=self.start_run
        )
        self.run_button.pack(side="left")

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(controls, textvariable=self.status_var).pack(side="left", padx=15)

        # Console
        console_frame = ttk.LabelFrame(outer, text="Console — last output lines", padding=6)
        console_frame.pack(fill="both", expand=True, pady=(6, 0))

        self.console = tk.Text(console_frame, height=10, wrap="word", state="disabled")
        scrollbar = ttk.Scrollbar(console_frame, orient="vertical", command=self.console.yview)
        self.console.configure(yscrollcommand=scrollbar.set)
        self.console.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.update_mode_state()

    def add_entry_row(self, parent, row, label, variable):
        ttk.Label(parent, text=label, width=28).grid(row=row, column=0, sticky="w", pady=3)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, columnspan=2, sticky="ew", pady=3)
        return row + 1

    def add_path_row(self, parent, row, label, variable, folder=False, filetypes=None):
        ttk.Label(parent, text=label, width=28).grid(row=row, column=0, sticky="w", pady=3)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=3, padx=(0, 6))

        def browse():
            if folder:
                value = filedialog.askdirectory()
            else:
                value = filedialog.askopenfilename(filetypes=filetypes or [("All files", "*.*")])
            if value:
                variable.set(value)

        ttk.Button(parent, text="Browse", command=browse).grid(row=row, column=2, sticky="e", pady=3)
        return row + 1

    # ------------------------------------------------------------------
    # INI handling
    # ------------------------------------------------------------------
    @staticmethod
    def get_option(config, candidates, fallback=""):
        for section, option in candidates:
            if config.has_option(section, option):
                return config.get(section, option)
        return fallback

    def set_option(self, candidates, value, preferred):
        # Update an existing key first, so older/newer INI layouts both work.
        for section, option in candidates:
            if self.config.has_option(section, option):
                self.config.set(section, option, str(value))
                return

        section, option = preferred
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, option, str(value))

    def choose_ini(self):
        filename = filedialog.askopenfilename(
            filetypes=[("INI configuration", "*.ini"), ("All files", "*.*")]
        )
        if filename:
            self.load_ini(Path(filename))

    def load_ini(self, filename):
        cfg = configparser.ConfigParser()
        read_files = cfg.read(filename, encoding="utf-8")
        if not read_files:
            messagebox.showerror("Configuration", f"Unable to read:\n{filename}")
            return

        self.config = cfg
        self.config_file = Path(filename)
        self.ini_label.config(text=str(self.config_file))

        self.vars["eruptions_folder"].set(self.get_option(cfg, [
            ("paths", "eruptions_folder")
        ]))
        self.vars["name_vent"].set(self.get_option(cfg, [
            ("downflow", "name_vent"), ("paths", "name_vent")
        ]))
        self.vars["easting"].set(self.get_option(cfg, [("downflow", "easting")]))
        self.vars["northing"].set(self.get_option(cfg, [("downflow", "northing")]))
        self.vars["csv_vent_file"].set(self.get_option(cfg, [
            ("paths", "csv_vent_file")
        ], "0"))
        self.vars["dem"].set(self.get_option(cfg, [("paths", "dem")]))
        self.vars["dh"].set(self.get_option(cfg, [
            ("downflow", "dh"), ("downflow", "DH")
        ]))
        self.vars["n_path"].set(self.get_option(cfg, [("downflow", "n_path")]))
        self.vars["slope_step"].set(self.get_option(cfg, [("downflow", "slope_step")]))
        self.vars["epsg_code"].set(self.get_option(cfg, [("downflow", "epsg_code")], "32740"))
        self.vars["json"].set(self.get_option(cfg, [("pyflowgo", "json")]))
        self.vars["effusion_rates_input"].set(self.get_option(cfg, [
            ("pyflowgo", "effusion_rates_input")
        ]))
        self.vars["mode"].set(self.get_option(cfg, [
            ("config_general", "mode")
        ], "downflowgo").lower())
        self.vars["grid_mode"].set(self.get_option(cfg, [
            ("config_general", "grid_mode")
        ], "no").lower())
        self.vars["mapping_display"].set(self.get_option(cfg, [
            ("config_general", "mapping_display")
        ], "no").lower())
        self.vars["language"].set(self.get_option(cfg, [
            ("language", "language"), ("config_general", "language")
        ], "EN").upper())

        for key, section, option, default in [
            ("use_gui","config_general","use_gui","no"),
            ("delete_existing_results","paths","delete_existing_results","yes"),
            ("parameters_file_downflow","downflow","parameters_file_downflow",""),
            ("ventgrid_size","grid_parameters","ventgrid_size",""),
            ("ventgrid_resolution","grid_parameters","ventgrid_resolution",""),
            ("grid_csv","grid_parameters","grid_csv","0"),
            ("dem_resolution","grid_parameters","dem_resolution",""),
            ("img_tif_map_background_path","mapping","img_tif_map_background_path",""),
            ("monitoring_network_path","mapping","monitoring_network_path","0"),
            ("lava_flow_outline_path","mapping","lava_flow_outline_path","0"),
            ("logo_path","mapping","logo_path","0"),
            ("source_img_tif_map_background","mapping","source_img_tif_map_background","0"),
            ("unverified_data","mapping","unverified_data","0"),
        ]:
            self.vars[key].set(self.get_option(cfg, [(section, option)], default))

        self.update_mode_state()
        self.status_var.set(f"Loaded: {self.config_file.name}")

    def apply_gui_to_config(self):
        self.set_option(
            [("paths", "eruptions_folder")],
            self.vars["eruptions_folder"].get(),
            ("paths", "eruptions_folder")
        )
        self.set_option(
            [("downflow", "name_vent"), ("paths", "name_vent")],
            self.vars["name_vent"].get(),
            ("downflow", "name_vent")
        )
        self.set_option([("downflow", "easting")], self.vars["easting"].get(), ("downflow", "easting"))
        self.set_option([("downflow", "northing")], self.vars["northing"].get(), ("downflow", "northing"))
        self.set_option([("paths", "csv_vent_file")], self.vars["csv_vent_file"].get() or "0",
                        ("paths", "csv_vent_file"))
        self.set_option([("paths", "dem")], self.vars["dem"].get(), ("paths", "dem"))
        self.set_option([("downflow", "dh"), ("downflow", "DH")], self.vars["dh"].get(), ("downflow", "dh"))
        self.set_option([("downflow", "n_path")], self.vars["n_path"].get(), ("downflow", "n_path"))
        self.set_option([("downflow", "slope_step")], self.vars["slope_step"].get(), ("downflow", "slope_step"))
        self.set_option([("downflow", "epsg_code")], self.vars["epsg_code"].get(), ("downflow", "epsg_code"))
        self.set_option([("config_general", "mode")], self.vars["mode"].get(), ("config_general", "mode"))
        self.set_option([("config_general", "grid_mode")], self.vars["grid_mode"].get(),
                        ("config_general", "grid_mode"))
        self.set_option([("config_general", "mapping_display")], self.vars["mapping_display"].get(),
                        ("config_general", "mapping_display"))
        self.set_option([("language", "language"), ("config_general", "language")],
                        self.vars["language"].get(), ("language", "language"))

        for key, section, option in [
            ("use_gui","config_general","use_gui"),
            ("delete_existing_results","paths","delete_existing_results"),
            ("parameters_file_downflow","downflow","parameters_file_downflow"),
            ("ventgrid_size","grid_parameters","ventgrid_size"),
            ("ventgrid_resolution","grid_parameters","ventgrid_resolution"),
            ("grid_csv","grid_parameters","grid_csv"),
            ("dem_resolution","grid_parameters","dem_resolution"),
            ("img_tif_map_background_path","mapping","img_tif_map_background_path"),
            ("monitoring_network_path","mapping","monitoring_network_path"),
            ("lava_flow_outline_path","mapping","lava_flow_outline_path"),
            ("logo_path","mapping","logo_path"),
            ("source_img_tif_map_background","mapping","source_img_tif_map_background"),
            ("unverified_data","mapping","unverified_data"),
        ]:
            value = self.vars[key].get()
            if key in ("grid_csv","monitoring_network_path","lava_flow_outline_path","logo_path",
                       "source_img_tif_map_background","unverified_data") and not value:
                value = "0"
            self.set_option([(section, option)], value, (section, option))

        if self.vars["mode"].get() == "downflowgo":
            self.set_option([("pyflowgo", "json")], self.vars["json"].get(), ("pyflowgo", "json"))
            self.set_option([("pyflowgo", "effusion_rates_input")],
                            self.vars["effusion_rates_input"].get(),
                            ("pyflowgo", "effusion_rates_input"))

    def save_ini_as(self):
        if not self.config.sections():
            messagebox.showwarning("Configuration", "Load an INI configuration first.")
            return
        self.apply_gui_to_config()
        filename = filedialog.asksaveasfilename(
            defaultextension=".ini",
            filetypes=[("INI configuration", "*.ini")]
        )
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                self.config.write(f)
            self.status_var.set(f"Saved: {Path(filename).name}")

    # ------------------------------------------------------------------
    # Running
    # ------------------------------------------------------------------
    def update_mode_state(self):
        mode = self.vars["mode"].get()
        self.run_button.config(text="RUN DOWNFLOWGO" if mode == "downflowgo" else "RUN DOWNFLOW")

        state = "normal" if mode == "downflowgo" else "disabled"
        for child in self.flowgo_frame.winfo_children():
            try:
                child.configure(state=state)
            except tk.TclError:
                pass

    def validate(self):
        required = [
            ("Eruption results folder", self.vars["eruptions_folder"].get()),
            ("Name of the vent", self.vars["name_vent"].get()),
            ("DEM", self.vars["dem"].get()),
            ("DH", self.vars["dh"].get()),
            ("N paths", self.vars["n_path"].get()),
            ("Slope step", self.vars["slope_step"].get()),
            ("EPSG", self.vars["epsg_code"].get()),
        ]
        if self.vars["csv_vent_file"].get().strip() in ("", "0"):
            required.extend([
                ("Easting", self.vars["easting"].get()),
                ("Northing", self.vars["northing"].get()),
            ])
        if self.vars["mode"].get() == "downflowgo":
            required.append(("PyFLOWGO JSON", self.vars["json"].get()))

        missing = [name for name, value in required if not str(value).strip()]
        if missing:
            messagebox.showwarning("Missing information", "Please provide:\n- " + "\n- ".join(missing))
            return False

        if not Path(self.vars["dem"].get()).expanduser().is_file():
            messagebox.showerror("DEM", "The selected DEM does not exist.")
            return False

        if self.vars["mode"].get() == "downflowgo":
            if not Path(self.vars["json"].get()).expanduser().is_file():
                messagebox.showerror("JSON", "The selected PyFLOWGO JSON does not exist.")
                return False

        csv_path = self.vars["csv_vent_file"].get().strip()
        if csv_path not in ("", "0") and not Path(csv_path).expanduser().is_file():
            messagebox.showerror("Vent CSV", "The selected vent CSV does not exist.")
            return False

        return True

    def start_run(self):
        if not self.config.sections():
            messagebox.showwarning("Configuration", "Load an INI configuration first.")
            return
        if not self.validate():
            return
        if not MAIN_SCRIPT.is_file():
            messagebox.showerror("DOWNFLOWGO", f"main_downflowgo.py not found:\n{MAIN_SCRIPT}")
            return

        self.apply_gui_to_config()

        # Use a temporary INI. The user's original INI is never overwritten.
        fd, temp_name = tempfile.mkstemp(prefix="downflowgo_", suffix=".ini")
        os.close(fd)
        self.temp_ini = Path(temp_name)
        with open(self.temp_ini, "w", encoding="utf-8") as f:
            self.config.write(f)

        self.clear_console()
        self.run_button.config(state="disabled")
        self.status_var.set("DOWNFLOWGO is running...")

        thread = threading.Thread(target=self.run_process, daemon=True)
        thread.start()

    def run_process(self):
        try:
            # Copy the current environment
            env = os.environ.copy()

            # Do not force a PROJ database.
            # Let Fiona / GDAL use their compatible PROJ installation.
            env.pop("PROJ_DATA", None)
            env.pop("PROJ_LIB", None)

            self.process = subprocess.Popen(
                [sys.executable, "-u", str(MAIN_SCRIPT), str(self.temp_ini)],
                cwd=str(APP_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env
            )

            for line in self.process.stdout:
                self.log_queue.put(("line", line.rstrip()))

            return_code = self.process.wait()
            self.log_queue.put(("done", return_code))

        except Exception as exc:
            self.log_queue.put(("error", str(exc)))

    def poll_log_queue(self):
        try:
            while True:
                kind, value = self.log_queue.get_nowait()

                if kind == "line":
                    self.append_console(value)

                elif kind == "done":
                    self.finish_run(value)

                elif kind == "error":
                    self.run_button.config(state="normal")
                    self.status_var.set("Error")
                    messagebox.showerror("DOWNFLOWGO", value)
        except queue.Empty:
            pass

        self.root.after(100, self.poll_log_queue)

    def finish_run(self, return_code):
        self.run_button.config(state="normal")

        try:
            self.temp_ini.unlink(missing_ok=True)
        except Exception:
            pass

        if return_code != 0:
            self.status_var.set(f"DOWNFLOWGO failed (code {return_code})")
            messagebox.showerror(
                "DOWNFLOWGO",
                "The simulation failed.\nSee the console output for details."
            )
            return

        self.status_var.set("DOWNFLOWGO finished successfully.")

        output_folder = (
            Path(self.vars["eruptions_folder"].get()).expanduser()
            / self.vars["name_vent"].get()
        )
        map_file = output_folder / f"map_{self.vars['name_vent'].get()}.png"

        if map_file.is_file():
            messagebox.showinfo(
                "DOWNFLOWGO",
                f"Simulation finished successfully.\n\nMap:\n{map_file}"
            )
        else:
            messagebox.showinfo(
                "DOWNFLOWGO",
                f"Simulation finished successfully.\n\nResults:\n{output_folder}"
            )

    # ------------------------------------------------------------------
    # Console helpers
    # ------------------------------------------------------------------
    def append_console(self, line):
        self.console.configure(state="normal")
        self.console.insert("end", line + "\n")

        # Keep only approximately the last 20 lines.
        lines = int(self.console.index("end-1c").split(".")[0])
        if lines > 21:
            self.console.delete("1.0", f"{lines - 20}.0")

        self.console.see("end")
        self.console.configure(state="disabled")

    def clear_console(self):
        self.console.configure(state="normal")
        self.console.delete("1.0", "end")
        self.console.configure(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    app = DownflowGoGUI(root)
    root.mainloop()
