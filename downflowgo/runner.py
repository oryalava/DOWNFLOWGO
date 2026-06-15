import os
import downflowgo.downflowcpp as downflowcpp
import downflowgo.txt_to_shape as txt_to_shape
# import downflowgo.run_flowgo as run_flowgo
import downflowgo.all_for_grid as all_for_grid
import downflowgo.check_files as check_files
import shutil
import json
import pyflowgo.run_outs as run_outs
import numpy as np
import pandas as pd

import pyflowgo.run_flowgo_effusion_rate_array as run_flowgo_effusion_rate_array
import pyflowgo.run_flowgo as run_flowgo
import pyflowgo.plot_flowgo_results as plot_flowgo_results


class Runner:
    def __init__(self, config: object):
        self.config = config

    def run_flowgo_no_gridmode(self, flow_id: str, path_to_folder: str, map_folder: str, sim_layers: dict):
        """Run FLOWGO without gridmode and make the map for donwflowgo results"""
        print("************************ Start FLOWGO for FLOW ID =", flow_id, '*********')
        path_to_flowgo_results = os.path.join(path_to_folder, 'results_flowgo')
        if not os.path.exists(path_to_flowgo_results):
            os.makedirs(path_to_flowgo_results)

        # get LoSD from DOWNFLOW and clean it if necessary
        slope_file = sim_layers['losd_file']
        df = pd.read_csv(slope_file, sep=r'\s+')
        df = df.dropna()
        df_cleaned = df[df['L'].diff().fillna(1) > 0]
        assert all(df_cleaned['L'].diff().dropna() > 0), "L is still not strictly increasing"
        df_cleaned.to_csv(slope_file, sep="\t", index=False)

        # Run FLOWGO using the json defined effusion rate
        if self.config.effusion_rates_tuple is None:
            # when effusion rate = 0,  flowgo calculates the effusion rate based on the channel dimensions
            json_file_new = os.path.join(path_to_flowgo_results, f'parameters_{flow_id}.json')
            with open(self.config.json_input, "r") as data_file:
                read_json_data = json.load(data_file)
            read_json_data["slope_file"] = slope_file
            read_json_data["effusion_rate_init"] = 0.0
            read_json_data["lava_name"] = flow_id

            with open(json_file_new, "w") as data_file:
                json.dump(read_json_data, data_file)

            flowgo = run_flowgo.RunFlowgo()
            flowgo.run(json_file_new, path_to_flowgo_results)
            filename = flowgo.get_file_name_results(path_to_flowgo_results, json_file_new)
            filename_array = [filename]
            plot_flowgo_results.plot_all_results(path_to_flowgo_results, filename_array, json_file_new)

            with open(json_file_new, "r") as data_file:
                data = json.load(data_file)
            lava_name = data["lava_name"]
            run_outs.get_run_outs(path_to_flowgo_results, filename_array, slope_file, lava_name)
            print('****** FLOWGO results are saved:', filename, '***********')

        else:
            # Run FLOWGO for several effusion rates
            simulation = run_flowgo_effusion_rate_array.StartFlowgo()
            json_file_new = os.path.join(path_to_flowgo_results, f'parameters_{flow_id}.json')
            simulation.make_new_json(self.config.json_input, flow_id, slope_file, json_file_new)
            simulation.run_flowgo_effusion_rate_array(json_file_new, path_to_flowgo_results, slope_file,
                                                      self.config.effusion_rates_tuple)
        # Save the run_outs results
        run_outs_file = os.path.join(path_to_flowgo_results, f'run_outs_{flow_id}.csv')
        shp_runouts = os.path.join(map_folder, f'runouts_{flow_id}.shp')
        txt_to_shape.get_runouts_shp(run_outs_file, shp_runouts, self.config.epsg_code)
        # move(losd_file)
        os.rename(sim_layers['losd_file'], os.path.join(map_folder, f'losd_{flow_id}_profile_00000.txt'))

        print('*********** FLOWGO executed and results stored in:', path_to_flowgo_results, '***********')
        shp_30pct = os.path.join(map_folder, f'30pct_{self.config.name_vent}.shp')
        txt_to_shape.cut_lines_losd_30pct(sim_layers["shp_losd_file"], shp_runouts, shp_30pct)

        # Make the map
        sim_layers["shp_runouts"] = shp_runouts
        sim_layers["shp_30pct"] = shp_30pct

    def run_flowgo_gridmode(self, path_to_folder: str, map_folder: str, pathfinder_slope_file_shp: str, grid_dict: dict, lon_intersect,
                            lat_intersect, sim_multi_n):
        """ Run FLOWGO with gridmode, for the slope that passes through the edge coordianates
         and make the map for donwflowgo results"""
        if self.config.mode == "downflowgo":
            # initialize headers for FLOWGO data
            eff_dict = {'X': [], 'Y': []}
            start = self.config.effusion_rates_tuple["first_eff_rate"]
            stop = self.config.effusion_rates_tuple["last_eff_rate"]
            step = self.config.effusion_rates_tuple["step_eff_rate"]

            for eff in range(start, stop + step, step):
                eff_dict[f'Run_out_{eff:.1f}'] = []
                eff_dict[f'X_run_out_{eff:.1f}'] = []
                eff_dict[f'Y_run_out_{eff:.1f}'] = []
                eff_dict[f'X_init_{eff:.1f}'] = []
                eff_dict[f'Y_init_{eff:.1f}'] = []

            # find which paths go through edge coordinate
            # n = 0
            # Look for all the values in the grid dict (amoung all the n1 raster)
            # to find the X and Y that match X and Y edge
            for value in grid_dict.values():
                Y = value['Coords'][0]
                X = value['Coords'][1]
                flow_id = f'{X}_{Y}'
                raster = value['Raster']
                latitude = value["Latitude"]
                longitude = value['Longitude']

                # #### DEBUGGING #####
                # lon_diff = np.amin(abs(lon_intersect-longitude))
                # lat_diff = np.amin(abs(lat_intersect-latitude))
                # if lon_diff < dem_resolution and lat_diff < dem_resolution:
                #     print(f'{n}. lat_diff:{lat_diff:.1f}  lon_diff:{lon_diff:.1f}')
                #     n += 1

                try:
                    row = np.where(latitude == lat_intersect)[0][0]
                except IndexError:
                    # comment on this step : Find the closest point
                    lat_diff = np.amin(abs(lat_intersect - latitude))
                    if lat_diff < 0.001:
                        row = np.argmin(latitude == lat_intersect)
                    else:
                        # os.remove(f'{path_to_results}{flow_id}/profile_{flow_id}_{X}_{Y}.txt')
                        continue

                try:
                    col = np.where(longitude == lon_intersect)[0][0]
                except IndexError:
                    # comment on this step
                    lon_diff = np.amin(abs(lon_intersect - longitude))
                    if lon_diff < 0.001:
                        col = np.argmin(abs(lon_intersect - longitude))
                    else:
                        # os.remove(f'{path_to_results}{flow_id}/profile_{flow_id}_{X}_{Y}.txt')
                        continue
                prob = raster[row, col]
                if prob != 0:
                    # if the probility of this X and Y are the same as X and Y edge and not zero, we run flowgo
                    # 1) Build the path to the vent folder
                    path_to_flowgo_results = os.path.join(path_to_folder, f"vents_{flow_id}")

                    # Create the directory if it doesn't exist
                    os.makedirs(path_to_flowgo_results, exist_ok=True)

                    # Move the profile file into the vent folder
                    old_profile = os.path.join(path_to_folder, f"profile_{flow_id}.txt")
                    new_profile = os.path.join(path_to_flowgo_results, f"profile_{flow_id}.txt")

                    if os.path.exists(old_profile):
                        os.makedirs(path_to_flowgo_results, exist_ok=True)
                        shutil.move(old_profile, new_profile)  # safer than os.rename for cross-filesystem moves
                    else:
                        print(f"Profile file not found: {old_profile}")
                    # Define slopefile and output_file paths
                    # slopefile = new_profile
                    # output_file = os.path.join(path_to_flowgo_results, f"json_{X}_{Y}.json")
                    # sys.exit()
                    simulation_flowgo = run_flowgo_effusion_rate_array.StartFlowgo()
                    json_file_new = os.path.join(path_to_flowgo_results, f'parameters_{flow_id}.json')
                    simulation_flowgo.make_new_json(self.config.json_input, flow_id, new_profile, json_file_new)

                    # Run FLOWGO for several effusion rates
                    simulation_flowgo.run_flowgo_effusion_rate_array(json_file_new, path_to_flowgo_results,
                                                                     new_profile,
                                                                     self.config.effusion_rates_tuple)

                    # flowgo.run_flowgo_effusion_rate_array(output_file, path_to_flowgo, slopefile, {'first_eff_rate': start, 'last_eff_rate': stop, 'step_eff_rate': step}, lava_name=flow_id)

                    run_outs_file = os.path.join(path_to_flowgo_results, f'run_outs_{flow_id}.csv')
                    df = pd.read_csv(run_outs_file)
                    for i in range(len(df)):
                        eff = df['Effusion_rate'][i]
                        eff_dict[f'Run_out_{eff:.1f}'].append(df['Distance_run_out'][i])
                        eff_dict[f'X_run_out_{eff:.1f}'].append(df['X_run_out'][i])
                        eff_dict[f'Y_run_out_{eff:.1f}'].append(df['Y_run_out'][i])
                        eff_dict[f'X_init_{eff:.1f}'].append(df['X_init'][i])
                        eff_dict[f'Y_init_{eff:.1f}'].append(df['Y_init'][i])

                    eff_dict['X'].append(X)
                    eff_dict['Y'].append(Y)

                else:
                    pass
                    # os.remove(f'{path_to_results}{flow_id}/profile_{flow_id}_{X}_{Y}.txt')

            # save the output into one single run_outs file
            output_csv = os.path.join(path_to_folder, 'run_outs.csv')
            new_df = pd.DataFrame.from_dict(eff_dict)
            new_df.to_csv(output_csv, index=False)
            # Calculates the average runouts of all the paths along the pathfinder_slope_file_shp
            average_run_outs = all_for_grid.get_average_run_outs(path_to_folder, self.config.name_vent, start, stop,
                                                                 step, pathfinder_slope_file_shp)

            effusion_rate_array = np.arange(start, stop + step, step)

        # Make the map layers and the map
        shp_vent_file = os.path.join(map_folder, f'vents_{self.config.name_vent}.shp')
        txt_to_shape.get_vent_shp(self.config.csv_vent_file, shp_vent_file, self.config.epsg_code)
        if self.config.mode == "downflowgo":
            shp_runouts = os.path.join(map_folder, f'runouts_{self.config.name_vent}.shp')
            txt_to_shape.get_runouts_grid_shp(average_run_outs, shp_runouts, self.config.epsg_code)
            shp_vents_runouts = os.path.join(map_folder, f'vents_runouts_{self.config.name_vent}.shp')
            txt_to_shape.get_vents_runouts_shp(output_csv, shp_vents_runouts, self.config.epsg_code)
            shp_iqr = os.path.join(map_folder, f'interquartiles_{self.config.name_vent}.shp')
            txt_to_shape.cut_lines_losd(pathfinder_slope_file_shp, shp_runouts, shp_iqr)

            sim_layers = {
                'shp_losd_file': pathfinder_slope_file_shp,
                'shp_vent_file': shp_vent_file,
                'cropped_geotiff_file': sim_multi_n,
                'shp_runouts': shp_runouts,
                'shp_iqr': shp_iqr
            }
        else:
            sim_layers = {
                'shp_losd_file': pathfinder_slope_file_shp,
                'shp_vent_file': shp_vent_file,
                'cropped_geotiff_file': sim_multi_n
            }
        return sim_layers

    def run_gridmode_origin(self, grid):
        """
        Run grid algorithm
        Pathstacker + Pathfinder
        et run flowgo_grid mode
        """

        # 1) first stack all the rasters and obtain a mastergrid with all the multi path into one file and
        # stack all the raster LoSD into a dictionnary containing all the raster n1_sim.tif (grid_dict)
        mastergrid, lon_X, lat_Y, grid_dict = all_for_grid.path_stacker_helper(grid,
                                                                               self.config.name_vent,
                                                                               self.path_to_folder,
                                                                               self.config.dem_resolution,
                                                                               self.config.epsg_code)

        sim_Losd_n1 = os.path.join(self.path_to_folder, f'{self.config.name_vent}_ventgrid_sim_n1.tif')
        sim_multi_n = os.path.join(self.path_to_folder, f'{self.config.name_vent}_ventgrid_sim_multi_n.tif')
        print("**************** Path stacking done *********")
        # caterpillar
        # Find the pathfinder and the lon_intersect, lat_intersect that are edge coordinate : X and Y edge
        # And save is as a slope file txt as well as a shape file pathfinder_slope_file_shp
        lon_intersect, lat_intersect, pathfinder_slope_file_shp = all_for_grid.pathfinder(
            ventgrid_resolution=self.config.ventgrid_resolution,
            dem_resolution=self.config.dem_resolution,
            grid=grid,
            path_to_results=self.path_to_folder,
            flow_id=self.config.name_vent, dem=self.config.dem,
            epsg_code=self.config.epsg_code, filename=sim_Losd_n1,
            edge=True, flowgo=True)

        # pathfinder_slope = os.path.join(path_to_folder, f'{self.config.name_vent}_pathfinder.txt')

        print("**************** Path finder done :" f'{pathfinder_slope_file_shp} *********')

        self.sim_layers = self.run_flowgo_gridmode(self.path_to_folder, pathfinder_slope_file_shp, grid_dict,
                                                   lon_intersect, lat_intersect, sim_multi_n)

    def run_pathstacking(self, grid):
        """
        Stack all grid rasters into a mastergrid
        """

        mastergrid, lon_X, lat_Y, grid_dict = all_for_grid.path_stacker_helper(
            grid,
            self.config.name_vent,
            self.path_to_folder,
            self.config.dem_resolution,
            self.config.epsg_code
        )

        sim_Losd_n1 = os.path.join(
            self.path_to_folder,
            f"{self.config.name_vent}_ventgrid_sim_n1.tif"
        )
        sim_multi_n = os.path.join(
            self.path_to_folder,
            f"{self.config.name_vent}_ventgrid_sim_multi_n.tif"
        )

        print("**************** Path stacking done *********")

        return {
            "mastergrid": mastergrid,
            "lon_X": lon_X,
            "lat_Y": lat_Y,
            "grid_dict": grid_dict,
            "sim_Losd_n1": sim_Losd_n1,
            "sim_multi_n": sim_multi_n,
        }

    def run_pathfinding(self, grid, sim_Losd_n1):
        """
        Run pathfinder on stacked grid
        """
        lon_intersect, lat_intersect, pathfinder_slope_file_shp = all_for_grid.pathfinder(
            #ventgrid_resolution=self.config.ventgrid_resolution,
            dem_resolution=self.config.dem_resolution,
            grid=grid,
            path_to_results=self.path_to_folder,
            flow_id=self.config.name_vent,
            dem=self.config.dem,
            epsg_code=self.config.epsg_code,
            filename=sim_Losd_n1,
            edge=True,
            flowgo=True
        )

        print(
            "**************** Path finder done : "
            f"{pathfinder_slope_file_shp} *********"
        )

        return lon_intersect, lat_intersect, pathfinder_slope_file_shp

    def run_flowgo_from_pathfinder(self, pathfinder_slope_file_shp, grid_dict,lon_intersect,lat_intersect, sim_multi_n):
        """
        Run FlowGO grid mode from pathfinder output
        """
        self.sim_layers = self.run_flowgo_gridmode(
            self.path_to_folder,
            self.map_folder,
            pathfinder_slope_file_shp,
            grid_dict,
            lon_intersect,
            lat_intersect,
            sim_multi_n
        )
    def run_model(self, data: dict, main_id: str):
        """
        Run downflow from 'flow_id', 'long' and 'lat' in data
        and if downflowgo run flowgo no grid mode

        Parameters
        ----------
        data : dict
        Contains vent parameters
        """
        flow_id = str(data['flow_id'])  # self.config.name_vent
        long = str(data['X'])
        lat = str(data['Y'])

        # If grid mode, hence the csv file considered is the grid file, skip making individual folders
        if self.config.grid_mode == 'yes':
            # save the files into the main folder
            self.path_to_folder = os.path.join(self.config.path_to_grid_folder, main_id)
        else:
            # Create individual folders for each row of the csv file and a map folder
            self.path_to_folder = os.path.join(self.config.path_to_eruptions, flow_id)

            check_files.overwrite_check_files(self.config.delete_existing, self.path_to_folder)

        os.chdir(self.path_to_folder)  # Change the current directory

        # Create map folder
        self.map_folder = os.path.join(self.path_to_folder, "map")
        check_files.overwrite_check_files(delete_existing=True, path_to_folder=self.map_folder)

        # Run downflow in 3 steps
        # 1) Returns an asc file with new (filled) DEM
        downflowcpp.get_downflow_filled_dem(long, lat, self.config.dem,
                                            self.config.path_to_downflow, self.config.parameters_file_downflow)
        print("************************ DOWNFLOW filled DEM done *********")

        # 2) Returns the profile.txt obtained from filled DEM
        filled_dem = 'dem_filled_DH0.001_N1000.asc'
        filled_dem = os.path.join(self.path_to_folder, filled_dem)
        downflowcpp.get_downflow_losd(long, lat, filled_dem, self.config.path_to_downflow,
                                      self.config.parameters_file_downflow, self.config.slope_step)

        if self.config.grid_mode == 'yes':
            # if grid mode the profile is also saved as a raster (cropped to dimensions),
            profile_name = os.path.join(self.path_to_folder, f'profile_{flow_id}.txt')
            os.replace(os.path.join(self.path_to_folder, "profile_00000.txt"), profile_name)
            profile_asc = os.path.join(self.path_to_folder, "sim.asc")
            cropped_file = os.path.join(self.path_to_folder, f'profile_{flow_id}_dH001_n1_sim.tif')
            txt_to_shape.crop_and_convert_to_tif(profile_asc, cropped_file, self.config.epsg_code)
            os.remove(profile_asc)
        else:
            # if not the LoSd and vent are converted here into shape files
            losd_file = os.path.join(self.path_to_folder, "profile_00000.txt")
            shp_losd_file = os.path.join(self.map_folder, f'losd_{flow_id}.shp')
            txt_to_shape.get_path_shp(losd_file, shp_losd_file, self.config.epsg_code)
            shp_vent_file = os.path.join(self.map_folder, f'vents_{flow_id}.shp')
            # txt_to_shape.get_vent_shp(csv_vent_file, shp_vent_file, epsg_code)
            txt_to_shape.write_single_vent_shp(flow_id, long, lat, shp_vent_file, self.config.epsg_code)

        print("************************ DOWNFLOW LoSD done *********")

        os.remove(filled_dem)

        # 3) Returns a raster (cropped to dimensions) with the lava flow path probabilities using the given DH and n
        downflowcpp.get_downflow_probabilities(long, lat, self.config.dem, self.config.path_to_downflow,
                                               self.config.parameters_file_downflow,
                                               self.config.DH,
                                               self.config.n)

        print("************************ DOWNFLOW probabilities done *********")

        sim_asc = os.path.join(self.path_to_folder, "sim.asc")
        cropped_geotiff_file = os.path.join(self.path_to_folder, f'sim_{flow_id}.tif')
        txt_to_shape.crop_and_convert_to_tif(sim_asc, cropped_geotiff_file, self.config.epsg_code)
        os.remove(sim_asc)
        print('*********** Simulation paths done and saved in:', cropped_geotiff_file, '*********')

        print("**************** End of DOWNFLOW ", flow_id, '*********')

        if self.config.grid_mode == 'no':
            # Define the map_layers dictionary initially
            # Make the map for donwflow results
            self.sim_layers = {
                'losd_file': losd_file,
                'shp_losd_file': shp_losd_file,
                'shp_vent_file': shp_vent_file,
                'cropped_geotiff_file': cropped_geotiff_file,
            }

            if self.config.mode == "downflowgo":
                self.run_flowgo_no_gridmode(flow_id, self.path_to_folder, self.map_folder, self.sim_layers)

    def init_results_folder(self, flow_id=None):
        """
        Initialize results folder without running run_model
        """
        if flow_id is None:
            flow_id = self.config.name_vent

        if not hasattr(self, "path_to_folder"):
            self.path_to_folder = self.make_result_folder(flow_id)

    def make_result_folder(self, flow_id):
        """
        Create and return result folder path
        """
        base = self.config.path_to_results

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = f"{flow_id}_{timestamp}"

        path = os.path.join(base, folder_name)
        os.makedirs(path, exist_ok=True)

        return path