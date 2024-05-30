# import requires packages
import csv
import downflowcpp
import run_flowgo_effusion_rate_array
import run_flowgo
import run_outs
import os
import txt_to_shape
import plot_flowgo_results
import json


if __name__ == "__main__":

    # ------------>   TODO : choose the path to the working folder   <------------
    path_to_results = "/Users/chevrel/GoogleDrive/Eruption_PdF/020723"
    #path_to_results = "/Users/chevrel/Documents/iceland-simu/Iceland_Nov2023"

    # ------------>   TODO : choose the path to the DEM (asc format  <------------

    #  The DEM must be .asc format with UTM in WGS84, with header :
    #      ncols        3193
    #      nrows        2305
    #      xllcorner    361622.6
    #      yllcorner    7644294.2
    #      cellsize     5.00
    #      NODATA_value  0

    dem = os.path.abspath('') + '/DEM/MNT-post-20220919_5m.asc'
    #dem = "/Users/chevrel/Documents/iceland-simu/DEM_Grindavik_5m.asc"

    # --------->   TODO : choose csv file width the name of the lava flow (flow_id) and the X, Y coordinates <----------
    csv_vent_file = "/Users/chevrel/GoogleDrive/Eruption_PdF/020723/vent_MSI_SWIR.csv"
    #csv_vent_file = "/Users/chevrel/Documents/iceland-simu/Fissure-test.csv"

    # ------------>    TODO : define parameter file and N and Dh for DOWNFLOW  <------------
    n_path = '10000'
    DH = '2'

    path = os.path.abspath('')
    parameter_file_downflow = path + '/DOWNFLOW/parameters_range.txt'

    # ----->>  TODO : choose json file for FLOWGO <------------
    template_json_file = path + "/PdF_template.json"
    #template_json_file ="/Users/chevrel/Documents/iceland-simu/Iceland_Nov2023/Parametre_FLOWGO_template.json"

    # ----->>  TODO : Choose if run FLOWGO FOR one json or several effusion rates (5,10,15,20,25,30 etc..  <------------
    # FLOWGO for one json : flowgo = 0,
    # FLOWGO for several effusion rates (5,10,15,20,25,30): flowgo = 1
    flowgo = 1

    with open(csv_vent_file, 'r') as csvfile:
        csvreader = csv.DictReader(csvfile, delimiter=';')

        for row in csvreader:

            flow_id = str(row['flow_id'])
            lat = str(row['X'])
            long = str(row['Y'])

            name_folder = path_to_results + '/' + flow_id + '_' + str(flowgo)
            path_to_folder = name_folder + '/'
            os.mkdir(name_folder)
            os.chdir(name_folder)

            with open(parameter_file_downflow) as f:
                l = list(f)
            with open(parameter_file_downflow, 'w') as output:
                for line in l:
                    if line.startswith('DH'):
                        output.write('DH ' + DH + '\n')
                    elif line.startswith('n_path'):
                        output.write('n_path ' + n_path + '\n')
                    else:
                        output.write(line)

            # Returns an asc file with the lava flow path probabilities
            downflowcpp.get_downflow_probabilities(lat, long, dem, path, parameter_file_downflow)
            print("******************* DOWNFLOW probability executed: sim.asc created **************************")

            # Returns an asc file with new (filled) DEM
            downflowcpp.get_downflow_filled_dem(lat, long, dem, path, parameter_file_downflow)
            print("************************ DOWNFLOW filled DEM done *********")

            # Returns the profile.txt
            filled_dem = 'dem_filled_DH0.001_N1000.asc'
            downflowcpp.get_downflow_losd(lat, long, filled_dem, path, parameter_file_downflow)
            print("************************ DOWNFLOW LoSD done *********")

            os.remove(path_to_folder + "/dem_filled_DH0.001_N1000.asc")

            # create map folder
            map = path_to_folder + 'map'
            os.mkdir(map)

            # crop asc file
            sim_asc = path_to_folder + '/sim.asc'
            txt_to_shape.crop_asc_file(sim_asc, path_to_folder, flow_id)
            # convert .asc to tiff
            cropped_asc_file = path_to_folder + '/map/sim_' + flow_id + '.asc'
            txt_to_shape.convert_to_tiff(cropped_asc_file, path_to_folder, flow_id)
            os.remove(path_to_folder + 'sim.asc')
            # convert profile to shape line
            slope_file = path_to_folder + "profile_00000.txt"
            txt_to_shape.get_path_shp(slope_file, path_to_folder, flow_id)
            print("**************** DOWNFLOW executed for FLOW ID =", flow_id, '*********')
            print('*********** simulation paths saved in:', path_to_folder + 'map/'+'sim_' + flow_id + '.tif', '***********')
            print('*********** shape file is saved in:', map, '/path_'+flow_id+'.shp', '***********')

            print("************************ Start FLOWGO for FLOW ID =", flow_id, '*********')

            # Run FLOWGO for json defined effusion rate
            if flowgo == 0:
                simulation = run_flowgo_effusion_rate_array.StartFlowgo()
                json_file_new = path_to_folder + 'parameters_' + flow_id + ".json"
                simulation.make_new_json(template_json_file, flow_id, slope_file, json_file_new)
                flowgo = run_flowgo.RunFlowgo()
                flowgo.run(json_file_new, path_to_folder)
                filename = flowgo.get_file_name_results(path_to_folder, json_file_new)
                filename_array = [filename]
                plot_flowgo_results.plot_all_results(path_to_folder, filename_array)
                with open(json_file_new, "r") as data_file:
                    data = json.load(data_file)
                lava_name = data["lava_name"]
                run_outs.get_run_outs(path_to_folder, filename_array, slope_file, lava_name)

                print('****** FLOWGO results are saved:', filename, '***********')

            elif flowgo == 1:
                # Run FLOWGO for several effusion rates
                simulation = run_flowgo_effusion_rate_array.StartFlowgo()
                json_file_new = path_to_folder + 'parameters_' + flow_id + ".json"
                simulation.make_new_json(template_json_file, flow_id, slope_file, json_file_new)
                simulation.run_flowgo_effusion_rate_array(json_file_new, path_to_folder, slope_file)

            else:
                print('define FLOWGO for one json or effusion rate array')

            run_outs = path_to_folder + 'run_outs_' + flow_id + '.csv'
            txt_to_shape.get_runouts_shp(run_outs, path_to_folder, flow_id)
            txt_to_shape.get_vent_shp(run_outs, path_to_folder, flow_id)
            print('*********** runouts file is saved in:', map, '/run_outs_' + flow_id + '.shp', '***********')

            print('*********** FLOWGO executed and results stored in:', path_to_folder, '***********')

    print("************************************** THE END *************************************")

