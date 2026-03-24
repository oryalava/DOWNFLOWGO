import os
import sys
import configparser
import editor_configuration_file_downflowgo


class Config:
    def __init__(self):
        self.abspath = os.path.abspath('')
        self.path_to_downflow = os.path.join(self.abspath, 'downflowgo')
        self.parameter_file_downflow = os.path.join(self.path_to_downflow, 'DOWNFLOW', 'parameters_range.txt')
        self.from_vent = False

        # [config_general]
        self.use_gui = None
        self.grid_mode = None
        self.mode = None
        self.mapping_display = None
        self.map_layers = None

        # [paths]
        self.path_to_eruptions = None
        self.dem = None
        self.csv_vent_file = None
        self.delete_existing = None

        # [downflow]
        self.name_vent = None
        self.easting = None
        self.northing = None
        self.dh = None
        self.n_path = None
        self.slope_step = None
        self.epsg_code = None

        # [pyflowgo]
        self.json_input = None
        self.effusion_rates_input = None

        # [grid_parameters]
        self.ventgrid_size = None
        self.ventgrid_resolution = None
        self.grid_csv = None

        # [mapping]
        self.img_tif_map_background_path = None
        self.monitoring_network_path = None
        self.lava_flow_outline_path = None
        self.logo_path = None
        self.source_img_tif_map_background = None
        self.unverified_data = None

        # [language]
        self.language = None

    def _make_absolute(self, path: str):  # Tristan 21/10
        """
        Returns an absolute path from a relative path.
        if path == '0', the file doesn't exist.

        """
        if path == '0':
            return path
        if not os.path.isabs(path):
            return os.path.join(self.abspath, path.replace('./', ''))
        return path

    def validate_path(self):
        """
        validates paths and makes them absolute.
        """
        if self.path_to_eruptions is None:
            raise ValueError("path_to_eruptions undefined")

        if self.dem is None:
            raise ValueError("dem path undefined")

        if self.csv_vent_file is None:
            raise ValueError("csv_vent_file path undefined")

        if self.grid_mode == "yes" and self.grid_csv is None:
            raise ValueError("grid mode is activate but grid_csv path undefined")

        if self.json_input is None:
            print("No .json file.")

        self.path_to_eruptions = self._make_absolute(self.path_to_eruptions)
        self.dem = self._make_absolute(self.dem)
        self.csv_vent_file = self._make_absolute(self.csv_vent_file)
        if self.grid_mode == "yes":
            self.grid_csv = self._make_absolute(self.grid_csv)
        self.json_input = self._make_absolute(self.json_input)

    def check_arg(self, cmd_arg: str):
        if len(cmd_arg) < 2:
            print("Usage:  python main_downflowgo.py config_downflowgo.ini")
            sys.exit(1)
        return sys.argv[1]

    def load_config(self, config_file: str):
        """Load the INI configuration file"""
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

        if not self.config.sections():
            print(f"Error : Impossible to read '{config_file}'")
            sys.exit(1)

        # Check if GUI is enabled in the config
        self.use_GUI = self.config['config_general']['use_gui']

        # Check if grid
        self.grid_mode = self.config.get('config_general', 'grid_mode', fallback='no')

        # Launch GUI if enabled
        if self.use_GUI == 'yes':
            gui_option = 1
        elif self.use_GUI == 'short':
            gui_option = 2
        else:  # use_GUI == 'no'
            return self.config

        modified_config = editor_configuration_file_downflowgo.launch_editor(config_file=config_file, grid_mode=self.grid_mode, gui_option=gui_option)
        # Reload the updated config if a new one was saved
        self.config.read(modified_config)
        config_file = modified_config  # Update path to point to new config
        self.grid_mode = self.config.get('config_general', 'grid_mode', fallback='no')

        return self.config

    def read_dem_resolution(self):
        with open(self.dem, 'r') as file:
            for i in range(4):
                file.readline()
            dem_resolution = float(file.readline().split()[-1])
        return dem_resolution

    def set_map_layers(self):
        # Define the map_layers dictionary for the mapping
        if self.mapping_display:
            self.map_layers = {
                "img_tif_map_background": self._make_absolute(self.img_tif_map_background_path),
                "monitoring_network_path": self._make_absolute(self.monitoring_network_path),
                "lava_flow_outline_path": self._make_absolute(self.lava_flow_outline_path),
                "logo_path": self._make_absolute(self.logo_path),
                "source_img_tif_map_background": self.source_img_tif_map_background,
                "unverified_data": self.unverified_data
            }
        else:
            self.map_layers = None
        return self.map_layers

    def set_path_to_grid_folder(self) -> str:
        return os.path.join(self.path_to_eruptions, self.name_vent)

    def set_json_input(self):
        return self._make_absolute(self.config["pyflowgo"]["json"])

    def set_effusion_rate(self, effusion_rates_input) -> None:
        if effusion_rates_input == "0":
            self.effusion_rates_tuple = None
            print("Effusion rates input is taken from channel dimension in json")
        else:
            try:
                rates = [int(r.strip()) for r in effusion_rates_input.split(',')]
                if len(rates) == 1:
                    self.effusion_rates_tuple = {"first_eff_rate": rates[0], "last_eff_rate": rates[0],
                                                 "step_eff_rate": rates[0]}
                elif len(rates) == 3:
                    self.effusion_rates_tuple = {
                        "first_eff_rate": rates[0], "last_eff_rate": rates[1], "step_eff_rate": rates[2]}
                else:
                    raise ValueError
            except ValueError:
                raise ValueError(
                    " Effusion rates input should be '0', or a single integer, "
                    "or three comma-separated integers (e.g., '5' or '5,20,5').")
        return self.effusion_rates_tuple

    def use_config(self):
        # ------------>    load downflow and the parameter file  <------------

        # General Config
        self.mode = self.config.get('config_general', 'mode', fallback='downfowgo')
        self.language = self.config.get('language', 'language', fallback='En')

        # Specify if you want to overwrite existing folder
        # delete_existing = config.getboolean('config_general', 'delete_existing_folder', fallback=False) new mais je vois pas dans config Tristan 24/10
        self.delete_existing = self.config['paths'].get('delete_existing_results', 'yes').lower() == 'yes'
        # Check if grid
        self.grid_mode = self.config.get('config_general', 'grid_mode', fallback='no')
        self.mapping_display = self.config.get('config_general', 'mapping_display', fallback='no')

        self.img_tif_map_background_path = self._make_absolute(
            self.config.get("mapping", "img_tif_map_background_path", fallback=None))
        self.monitoring_network_path = self._make_absolute(
            self.config.get("mapping", "monitoring_network_path", fallback=None))
        self.lava_flow_outline_path = self._make_absolute(
            self.config.get("mapping", "lava_flow_outline_path", fallback=None))
        self.logo_path = self._make_absolute(self.config.get("mapping", "logo_path", fallback=None))
        self.source_img_tif_map_background = self.config.get("mapping", "source_img_tif_map_background", fallback=None)
        self.unverified_data = self.config.get("mapping", "unverified_data", fallback=None)
        self.set_map_layers()

        ########
        # Config DOWNFLOW
        self.name_vent = self.config["downflow"]["name_vent"]  # *
        self.easting = self.config["downflow"]["easting"]  # *
        self.northing = self.config["downflow"]["northing"]  # *
        self.DH = self.config["downflow"]["DH"]
        self.n = self.config["downflow"]["n_path"]
        self.slope_step = self.config["downflow"]["slope_step"]
        self.epsg_code = self.config["downflow"]["epsg_code"]

        # Paths
        self.path_to_eruptions = self.config["paths"]["eruptions_folder"]  # *
        self.path_to_eruptions = self._make_absolute(self.path_to_eruptions)  # *
        self.csv_vent_file = self.config["paths"]["csv_vent_file"]  # *
        self.csv_vent_file = self._make_absolute(self.csv_vent_file)  # *
        if self.mode == "downflowgo":
            self.json_input = self.set_json_input()
        self.dem = self.config["paths"]["dem"]
        self.dem = self._make_absolute(self.dem)
        if self.grid_mode == 'yes':
            self.path_to_grid_folder = self.set_path_to_grid_folder()

        # For FLOWGO
        # Parse effusion rates
        if self.mode == "downflowgo":
            self.effusion_rates_input = self.config["pyflowgo"]["effusion_rates_input"].strip()
            self.set_effusion_rate(self.effusion_rates_input)

        if self.grid_mode == 'yes':
            self.ventgrid_size = float(self.config["grid_parameters"]["ventgrid_size"])
            self.ventgrid_resolution = float(self.config["grid_parameters"]["ventgrid_resolution"])
            self.dem_resolution = self.read_dem_resolution()

    def save_config(self, main_id: str, name_config_file='saved_config.ini'):
        save_config = configparser.ConfigParser()
        # General Config
        save_config['config_general'] = {
            'mode': self.mode,
            'grid_mode': self.grid_mode,
            'mapping_display': self.mapping_display,
            'use_gui': f"{self.use_gui if self.use_gui else 'no'}"}

        # Paths
        save_config['paths'] = {
            'eruptions_folder': self.path_to_eruptions,
            'dem': self.dem,
            'csv_vent_file': self.csv_vent_file}

        # Config DOWNFLOW
        save_config['downflow'] = {}
        ########
        save_config["downflow"]["name_vent"] = self.name_vent
        save_config["downflow"]["easting"] = self.easting
        save_config["downflow"]["northing"] = self.northing
        save_config["downflow"]["dh"] = self.DH
        save_config["downflow"]["n_path"] = self.n
        save_config["downflow"]["slope_step"] = self.slope_step
        save_config["downflow"]["epsg_code"] = self.epsg_code

        # pyflowgo
        if self.mode == "downflowgo":
            save_config['pyflowgo'] = {
                'json': self.json_input,
                'effusion_rates_input': self.effusion_rates_input
            }

        if self.grid_mode == 'yes':
            save_config['grid_parameters'] = {}
            save_config["grid_parameters"]["ventgrid_size"] = str(self.ventgrid_size)
            save_config["grid_parameters"]["ventgrid_resolution"] = str(self.ventgrid_resolution)
            save_config["grid_parameters"]["grid_csv"] = self.csv_vent_file
            save_config["grid_parameters"]["dem_resolution"] = str(self.dem_resolution)

        # mapping
        save_config['mapping'] = {
            'img_tif_map_background_path': self.img_tif_map_background_path,
            'monitoring_network_path': self.monitoring_network_path,
            'lava_flow_outline_path': self.lava_flow_outline_path,
            'logo_path': self.logo_path,
            'source_img_tif_map_background': self.source_img_tif_map_background,
            'unverified_data': self.unverified_data}

        # language
        save_config['language'] = {'language': self.language}

        if self.grid_mode == 'yes':
            save_path = self.set_path_to_grid_folder()
        else:
            save_path = self.path_to_eruptions

        with open(os.path.join(save_path, main_id, name_config_file), 'w') as configfile:
            save_config.write(configfile)

    def show(self, a_dict: dict):
        for key, item in a_dict.items():
            print(f"{key}: {item}")

    def grid_mode_summary(self):
        return {
            "mode": self.mode,
            "grid_mode": self.grid_mode,
            # "path_to_grid_folder": self.path_to_grid_folder,
            "dem": self.dem,
            "ventgrid_size": self.ventgrid_size,
            "ventgrid_resolution": self.ventgrid_resolution,
            "grid_csv": self.grid_csv,
            "dem_resolution": self.dem_resolution
        }

    def summary(self) -> dict:
        return {"path_to_downflow": self.path_to_downflow,
                "parameter_file_downflow": self.parameter_file_downflow,
                "use_gui": self.use_gui,
                "grid_mode": self.grid_mode,
                "mode": self.mode,
                "mapping_display": self.mapping_display,
                "map_layers": self.map_layers,
                "eruptions_folder": self.eruptions_folder,
                "delete_existing_results": self.delete_existing_results,
                "dem": self.dem,
                "csv_vent_file": self.csv_vent_file,
                "name_vent": self.name_vent,
                "easting": self.easting,
                "northing": self.northing,
                "dh": self.dh,
                "slope_step": self.slope_step,
                "epsg_code": self.epsg_code,
                "json_input": self.json_input,
                "effusion_rates_input": self.effusion_rates_input,
                "ventgrid_size": self.ventgrid_size,
                "ventgrid_resolution": self.ventgrid_resolution,
                "grid_csv": self.grid_csv,
                "dem_resolution": self.dem_resolution,
                "img_tif_map_background_path": self.img_tif_map_background_path,
                "monitoring_network_path": self.monitoring_network_path,
                "lava_flow_outline_path": self.lava_flow_outline_path,
                "logo_path": self.logo_path,
                "source_img_tif_map_background": self.source_img_tif_map_background,
                "unverified_data": self.unverified_data,
                "language": self.language
                }
