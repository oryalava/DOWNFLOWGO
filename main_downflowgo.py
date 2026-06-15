import sys
import time

import downflowgo.datamanager as datamanager
from downflowgo.all_for_grid import grid_maker_reader
from downflowgo.config_loader import Config
from downflowgo.perf_timer import runtime
from downflowgo.runner import Runner
from downflowgo.mapping import Mapping
from downflowgo.check_files import check_vent_in_dem

if __name__ == "__main__":
    # Start the timer
    start_time = time.time()

    # Création de la config
    config = Config()

    # Check argument
    config_file = config.check_arg(sys.argv)
    # Charge la config
    config.load_config(config_file)
    config.use_config()

    file_opener = datamanager.DataManager(config)
    # Writes a csv file with the position of the vent in the config file
    file_opener.csv_vent_writer(config.name_vent, config.easting, config.northing)

    csv_data = file_opener.csv_vent_reader()

    # Start the loop to run downflowgo for each row in the csv file
    for data in csv_data:
        # First check that each vent of csv file is within DEM
        check_vent_in_dem(data['X'], data['Y'], config.dem)
        main_id = data["flow_id"]
        if config.grid_mode == 'yes':
            # Make a new csv file with the location of each new vent
            grid = grid_maker_reader(data, config)

            grid_csv_data = file_opener.csv_vent_reader()
            # Start the loop to run downflowgo for each row in the csv file
            runner = Runner(config)
            for grid_data in grid_csv_data:
                runner.run_model(grid_data, main_id)

            stack = runner.run_pathstacking(grid)
            lon_i, lat_i, shp = runner.run_pathfinding(grid, stack["sim_Losd_n1"])
            runner.run_flowgo_from_pathfinder(
                shp,
                stack["grid_dict"],
                lon_i,
                lat_i,
                stack["sim_multi_n"]
            )
        else:
            runner = Runner(config)
            runner.run_model(data, main_id)

        config.save_config(name_config_file='saved_config.ini', main_id=main_id)

        # Make the map
        mapping = Mapping(path_to_folder=runner.path_to_folder,
                          dem=config.dem,
                          flow_id=main_id,
                          map_layers=config.map_layers,
                          sim_layers=runner.sim_layers,
                          mode=config.mode,
                          language=config.language,
                          grid_mode=config.grid_mode)
        mapping.create_map(display=config.mapping_display)
    print("************************************** THE END *************************************")

    runtime(start_time, time.time())
