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

    def _run_flowgo_single_vent(self, flow_id: str, path_to_folder: str, path_to_flowgo_results: str,  profile_file: str):

        """
        Run FLOWGO for a single flow_id using an existing DOWNFLOW profile.

        Parameters
        ----------
        flow_id : str  #ID of the flow/vent.
        path_to_folder : str  #Main simulation folder.
        path_to_flowgo_results : str # Folder where FLOWGO results are written.
      profile_file : str  # Profile/LoSD file used by FLOWGO.

    Returns
    -------
    str Path to the FLOWGO run_outs CSV file.
        """
        os.makedirs(path_to_flowgo_results, exist_ok=True)
        # ---------------------------------------------------------
        # Check profile
        # ---------------------------------------------------------

        if not os.path.exists(profile_file):
            print(f"Profile not found: {profile_file}")
            return None

        # ---------------------------------------------------------
        # Clean profile if necessary
        # ---------------------------------------------------------

        df = pd.read_csv(profile_file,sep=r'\s+')
        df = df.dropna()
        df_cleaned = df[df["L"].diff().fillna(1) > 0]
        assert all(df_cleaned["L"].diff().dropna() > 0), "L is still not strictly increasing"
        df_cleaned.to_csv(profile_file,sep="\t",index=False)

        # ---------------------------------------------------------
        # Run FLOWGO
        # ---------------------------------------------------------
        #run flowgo using defined effusion rate in json
        if self.config.effusion_rates_tuple is None:
            #when effusion rate = 0, flowgo calculates the effusion rate based on the channel dimensions
            json_file = os.path.join(path_to_flowgo_results, f"parameters_{flow_id}.json" )
            with open(self.config.json_input, "r") as data_file:
                json_data = json.load(data_file)
            json_data["slope_file"] = profile_file
            json_data["effusion_rate_init"] = 0.0
            json_data["lava_name"] = flow_id

            with open(json_file, "w") as data_file:
                json.dump(json_data, data_file)
            flowgo = run_flowgo.RunFlowgo()
            flowgo.run(json_file,path_to_flowgo_results)
            filename = flowgo.get_file_name_results(path_to_flowgo_results,json_file)
            filename_array = [filename]
            plot_flowgo_results.plot_all_results(path_to_flowgo_results,filename_array,json_file)

            with open(json_file, "r") as data_file:
                data = json.load(data_file)
            lava_name = data["lava_name"]
            run_outs.get_run_outs(path_to_flowgo_results, filename_array, profile_file,lava_name)

            print( f"****** FLOWGO results saved for {flow_id}: {filename} ******")

        else:
            # FLOWGO for several effusion rates
            simulation = (run_flowgo_effusion_rate_array.StartFlowgo())
            json_file = os.path.join(path_to_flowgo_results,f"parameters_{flow_id}.json")
            simulation.make_new_json(self.config.json_input,flow_id, profile_file,json_file)
            simulation.run_flowgo_effusion_rate_array(json_file, path_to_flowgo_results,profile_file,self.config.effusion_rates_tuple)

        # ---------------------------------------------------------
        # FLOWGO output
        # ---------------------------------------------------------

        run_outs_file = os.path.join(path_to_flowgo_results,f"run_outs_{flow_id}.csv")

        if not os.path.exists(run_outs_file):
            print(f"Missing FLOWGO output: {run_outs_file}")
            return None

        return run_outs_file

    def run_pathstacking(self, grid):
        """
        Stack all grid rasters into a mastergrid

        Returns:
            Mastergrid_n1 for the single path staking   : occurrence count
            Mastergrid_multi_n for the multi paths staking : probability sum
        """

        stack_results = all_for_grid.path_stacker_helper(
            grid, self.config.name_vent, self.path_to_folder, self.config.dem_resolution, self.config.epsg_code)

        sim_stack = stack_results["sim"]
        n1_stack = stack_results["n1"]

        mastergrid = sim_stack["mastergrid"]
        lon_X = sim_stack["lon_X"]
        lat_Y = sim_stack["lat_Y"]
        grid_dict = sim_stack["grid_dict"]

        sim_multi_n = os.path.join(self.path_to_folder, f"{self.config.name_vent}_mastergrid_multi_n.tif")
        sim_Losd_n1 = os.path.join(self.path_to_folder, f"{self.config.name_vent}_mastergrid_n1.tif")


        print("**************** Path stacking done *********")
        return {
            "sim": sim_multi_n,
            "n1": sim_Losd_n1,
            "mastergrid_multi_n_file": os.path.join(self.path_to_folder,
                                                    f"{self.config.name_vent}_mastergrid_multi_n.tif"),
            "mastergrid_n1_file": os.path.join(self.path_to_folder,
                                               f"{self.config.name_vent}_mastergrid_n1.tif"),
            "grid_dict": n1_stack["grid_dict"], }

    def run_pathfinding(self, grid, mastergrid_n1_file):
        """
        Run pathfinder on stacked grid of single path
        """
        lon_intersect, lat_intersect, pathfinder_slope_file_shp = all_for_grid.pathfinder(
            #ventgrid_resolution=self.config.ventgrid_resolution,
            dem_resolution=self.config.dem_resolution,
            grid=grid,
            path_to_results=self.path_to_folder,
            flow_id=self.config.name_vent,
            dem=self.config.dem,
            epsg_code=self.config.epsg_code,
            filename=mastergrid_n1_file,
            edge=True,
            flowgo=True)

        print("**************** Pathfinder done : "
            f"{pathfinder_slope_file_shp} *********" )

        return lon_intersect, lat_intersect, pathfinder_slope_file_shp

    def find_contributing_vents(self, lon_intersect, lat_intersect, losd_dict, window_size=0):
        """
        Find vents whose individual LOSD passes through the Pathfinder
        drainage point.

        Parameters
        ----------
        lon_intersect: float
            X coordinate of the Pathfinder intersection point.
        lat_intersect : float
            Y coordinate of the Pathfinder intersection point.
        losd_dict : dict
            Dictionary containing individual LOSD rasters from path_stacker.
            Each entry must contain:
                - "Raster"
                - "Longitude"
                - "Latitude"
        window_size : int, optional
            Number of pixels around the closest pixel to search.

        Returns
        -------
        contributing_vents : dict
            Subset of losd_dict containing only vents contributing to the
            Pathfinder corridor.
        """

        contributing_vents = {}

        for vent_key, vent_data in losd_dict.items():

            raster = vent_data["Raster"]
            longitude = vent_data["Longitude"]
            latitude = vent_data["Latitude"]

            # Vérifier que le point Pathfinder est dans l'emprise du raster
            xmin = longitude.min()
            xmax = longitude.max()
            ymin = latitude.min()
            ymax = latitude.max()

            # Attention : latitude peut être décroissante
            if not (xmin <= lon_intersect <= xmax and
                    min(ymin, ymax) <= lat_intersect <= max(ymin, ymax)):
                continue

            # Find closest pixel to the Pathfinder intersection point
            col = np.argmin(np.abs(longitude - lon_intersect))
            row = np.argmin(np.abs(latitude - lat_intersect))

            # Define search window around this pixel
            r0 = max(0, row - window_size)
            r1 = min(raster.shape[0], row + window_size + 1)

            c0 = max(0, col - window_size)
            c1 = min(raster.shape[1], col + window_size + 1)

            window = raster[r0:r1, c0:c1]

            # If the LOSD crosses this area, the vent contributes
            if np.any(window > 0):
                contributing_vents[vent_key] = vent_data

        print( f"{len(contributing_vents)} contributing vents identified "
            f"at drainage point ({lon_intersect:.2f}, {lat_intersect:.2f})" )
        # Export to csv and shape
        all_for_grid.export_contributing_vents(contributing_vents,self.path_to_folder, self.config.name_vent,
            self.config.epsg_code)


        return contributing_vents

    def run_model(self, data: dict, main_id: str):
        """
        Run downflow from 'flow_id', 'long' and 'lat' in data

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
            # if no grid; the LoSd and vent are converted here into shape files
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

        if self.config.mode == "downflow":
            sim_layers = {
                "cropped_geotiff_file": cropped_geotiff_file,
                "shp_vent_file": shp_vent_file,
                "shp_losd_file": shp_losd_file}
            return sim_layers

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

    def run_flowgo_contributing_vents(self,path_to_folder: str, pathfinder_slope_file_shp: str,
            contributing_vents: dict,mastergrid_multi_n_file):
        """
        Run FLOWGO only for vents contributing to the main drainage corridor.

        Each contributing vent already has a DOWNFLOW profile generated during
        the grid simulations. This function simply reuses these profiles to run
        FLOWGO and then aggregates all runnout statistics.

        Parameters
        ----------
        path_to_folder : str
            Main simulation folder.

        map_folder : str
            Folder where GIS layers are written.

        pathfinder_slope_file_shp : str
            Pathfinder shapefile.

        contributing_vents : dict
            Dictionary returned by find_contributing_vents().

        sim_multi_n : str
            Mastergrid raster used for mapping.

        Returns
        -------
        dict
            Dictionary containing the map layers.
        """

        if self.config.mode == "downflowgo":

            # ---------------------------------------------------------
            # Initialize FLOWGO output table
            # ---------------------------------------------------------

            eff_dict = {"X": [], "Y": []}

            start = self.config.effusion_rates_tuple["first_eff_rate"]
            stop = self.config.effusion_rates_tuple["last_eff_rate"]
            step = self.config.effusion_rates_tuple["step_eff_rate"]

            for eff in np.arange(start, stop + step, step):
                eff_dict[f"Run_out_{eff:.1f}"] = []
                eff_dict[f"X_run_out_{eff:.1f}"] = []
                eff_dict[f"Y_run_out_{eff:.1f}"] = []
                eff_dict[f"X_init_{eff:.1f}"] = []
                eff_dict[f"Y_init_{eff:.1f}"] = []

            valid_vents = []

            print(f"Running FLOWGO for {len(contributing_vents)} contributing vents...")

            # ---------------------------------------------------------
            # Loop over contributing vents only
            # ---------------------------------------------------------

            for vent_key, vent_data in contributing_vents.items():
                lat, lon = vent_data["Coords"]
                flow_id = f"{lon}_{lat}"
                valid_vents.append({"flow_id": flow_id,"X": lon, "Y": lat})
                path_to_flowgo_results = os.path.join( path_to_folder, f"vents_{flow_id}")
                os.makedirs(path_to_flowgo_results, exist_ok=True)

                # ---------------------------------------------------------
                # Copy profile generated during DOWNFLOW
                # ---------------------------------------------------------
                old_profile = os.path.join(path_to_folder, f"profile_{flow_id}.txt")
                new_profile = os.path.join(path_to_flowgo_results,f"profile_{flow_id}.txt")
                if not os.path.exists(old_profile):
                    print(f"Profile not found: {old_profile}")
                    continue
                shutil.copy2(old_profile, new_profile)


                # ---------------------------------------------------------
                # Run FLOWGO
                # ---------------------------------------------------------

                run_outs_file = self._run_flowgo_single_vent(flow_id, path_to_folder,path_to_flowgo_results,new_profile)
                if run_outs_file is None:
                    continue

                # ---------------------------------------------------------
                # Read FLOWGO results
                # ---------------------------------------------------------

                if not os.path.exists(run_outs_file):
                    print(f"Missing FLOWGO output: {run_outs_file}")
                    continue

                df = pd.read_csv(run_outs_file)

                for i in range(len(df)):
                    eff = df["Effusion_rate"][i]
                    eff_dict[f"Run_out_{eff:.1f}"].append(df["Distance_run_out"][i])
                    eff_dict[f"X_run_out_{eff:.1f}"].append(df["X_run_out"][i])
                    eff_dict[f"Y_run_out_{eff:.1f}"].append(df["Y_run_out"][i])
                    eff_dict[f"X_init_{eff:.1f}"].append(df["X_init"][i])
                    eff_dict[f"Y_init_{eff:.1f}"].append(df["Y_init"][i])

                eff_dict["X"].append(lon)
                eff_dict["Y"].append(lat)

            # ---------------------------------------------------------
            # Save merged FLOWGO outputs
            # ---------------------------------------------------------

            output_csv = os.path.join(path_to_folder, "run_outs.csv")
            pd.DataFrame.from_dict(eff_dict).to_csv(output_csv, index=False)

            valid_vents_csv = os.path.join(
                path_to_folder,
                "contributing_vents.csv"
            )

            pd.DataFrame(valid_vents).to_csv( valid_vents_csv, index=False)

            # ---------------------------------------------------------
            # Average runouts
            # ---------------------------------------------------------

            average_run_outs = all_for_grid.get_average_run_outs(
                path_to_folder,
                self.config.name_vent,
                start,
                stop,
                step,
                pathfinder_slope_file_shp
            )

        # ---------------------------------------------------------
        # GIS layers
        # ---------------------------------------------------------
        map_folder = os.path.join(path_to_folder,"map")
        shp_vent_file = os.path.join( map_folder, f"vents_{self.config.name_vent}.shp")
        txt_to_shape.get_vent_shp(self.config.csv_vent_file,shp_vent_file,self.config.epsg_code)
        shp_valid_vent_file = os.path.join(map_folder,f"contributing_vents_{self.config.name_vent}.shp")

        txt_to_shape.get_vent_shp(valid_vents_csv,shp_valid_vent_file,self.config.epsg_code)

        if self.config.mode == "downflowgo":

            shp_runouts = os.path.join(map_folder,f"runouts_{self.config.name_vent}.shp")
            txt_to_shape.get_runouts_grid_shp(average_run_outs,shp_runouts, self.config.epsg_code)
            shp_vents_runouts = os.path.join(map_folder, f"vents_runouts_{self.config.name_vent}.shp" )
            txt_to_shape.get_vents_runouts_shp( output_csv,shp_vents_runouts,self.config.epsg_code)
            shp_iqr = os.path.join( map_folder,f"interquartiles_{self.config.name_vent}.shp" )

            txt_to_shape.cut_lines_losd(pathfinder_slope_file_shp,shp_runouts,shp_iqr)

            sim_layers = {
                "shp_losd_file": pathfinder_slope_file_shp,
                "shp_vent_file": shp_vent_file,
                "shp_contributing_vent_file": shp_valid_vent_file,
                "cropped_geotiff_file": mastergrid_multi_n_file,
                "shp_runouts": shp_runouts,
                "shp_iqr": shp_iqr,
            }

        else:

            sim_layers = {
                "shp_losd_file": pathfinder_slope_file_shp,
                "shp_vent_file": shp_vent_file,
                "shp_contributing_vent_file": shp_valid_vent_file,
                "cropped_geotiff_file": mastergrid_multi_n_file,
            }

        return sim_layers
    def run_flowgo_no_gridmode(self,path_to_folder: str):

        """
        Run FLOWGO for a single vent without gridmode.
        """
        flow_id = self.config.name_vent
        print("**************** Start FLOWGO for FLOW ID =",flow_id, "****************" )

        map_folder = os.path.join(path_to_folder,"map")
        path_to_flowgo_results = os.path.join(path_to_folder,"results_flowgo")
        os.makedirs(path_to_flowgo_results, exist_ok=True)


        # ---------------------------------------------------------
        # get cropped sim and profile and define the vent
        # ---------------------------------------------------------
        cropped_geotiff_file = os.path.join(path_to_folder,f"sim_{flow_id}.tif")
        slope_file = os.path.join(path_to_folder,"profile_00000.txt")

        df_profile = pd.read_csv(slope_file, sep=r"\s+")
        x_vent = df_profile.iloc[0]["x"]
        y_vent = df_profile.iloc[0]["y"]


        # ---------------------------------------------------------
        # Run FLOWGO
        # ---------------------------------------------------------
        run_outs_file = self._run_flowgo_single_vent(flow_id, path_to_folder, path_to_flowgo_results, slope_file)

        if run_outs_file is None:
            print("FLOWGO failed or run_outs file is missing")
            return None

        # ---------------------------------------------------------
        # GIS outputs
        # ---------------------------------------------------------
        shp_vent_file = os.path.join(map_folder, f"vents_{flow_id}.shp")
        txt_to_shape.write_single_vent_shp(flow_id, x_vent, y_vent, shp_vent_file, self.config.epsg_code)
        shp_losd_file = os.path.join(self.map_folder, f'losd_{flow_id}.shp')
        txt_to_shape.get_path_shp(slope_file, shp_losd_file, self.config.epsg_code)

        if self.config.mode == "downflowgo":
            shp_runouts = os.path.join(map_folder, f"runouts_{self.config.name_vent}.shp")
            txt_to_shape.get_runouts_shp(run_outs_file, shp_runouts, self.config.epsg_code)
            shp_30pct = os.path.join(map_folder, f"30pct_{self.config.name_vent}.shp")
            txt_to_shape.cut_lines_losd_30pct(shp_losd_file, shp_runouts, shp_30pct)

            sim_layers = {
                "cropped_geotiff_file": cropped_geotiff_file,
                "shp_vent_file": shp_vent_file,
                "shp_losd_file": shp_losd_file,
                "shp_runouts": shp_runouts,
                "shp_30pct": shp_30pct}

        else:
            sim_layers = {
                "cropped_geotiff_file": cropped_geotiff_file,
                "shp_vent_file": shp_vent_file,
                "shp_losd_file": shp_losd_file}

        print( "**************** FLOWGO executed and results stored in:",path_to_flowgo_results,"****************" )

        return sim_layers
