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
        runner = Runner(config)
        if config.mode == "downflowgo":
            if config.grid_mode == 'yes':
                # Make a new csv file with the location of each new vent
                grid = grid_maker_reader(data, config)
                grid_csv_data = file_opener.csv_vent_reader()
                # Start the loop to run downflowgo for each row in the csv file

                for grid_data in grid_csv_data:
                    runner.run_model(grid_data, main_id)

                #stack the rasters into mastergrids
                stack = runner.run_pathstacking(grid)

                # Pathfinding on the most frequently travelled corridor and return X and Y intercect
                lon_intersect, lat_intersect, shp = runner.run_pathfinding(grid, stack["mastergrid_n1_file"])

                # Find contributing vents
                contributing_vents = runner.find_contributing_vents(lon_intersect,lat_intersect,stack["grid_dict"])

                # Run FLOWGO only for contributing vents
                sim_layers = runner.run_flowgo_contributing_vents(runner.path_to_folder,shp,contributing_vents,
                    stack["mastergrid_multi_n_file"])

            else:
                runner.run_model(data, main_id)
                # Run FLOWGO only for one vent or one csv file
                sim_layers = runner.run_flowgo_no_gridmode(runner.path_to_folder)
        else:
            sim_layers = runner.run_model(data, main_id)

        config.save_config(name_config_file='saved_config.ini', main_id=main_id)

        # Make the map
        mapping = Mapping(path_to_folder=runner.path_to_folder,
                          dem=config.dem,
                          flow_id=main_id,
                          map_layers=config.map_layers,
                          sim_layers=sim_layers,
                          mode=config.mode,
                          language=config.language,
                          grid_mode=config.grid_mode)
        mapping.create_map(display=config.mapping_display)
    print("************************************** THE END *************************************")

    runtime(start_time, time.time())
