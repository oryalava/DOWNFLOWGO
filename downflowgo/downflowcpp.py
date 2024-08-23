#import requires packages
import os.path
import csv
import downflowgo.run_flowgo_effusion_rate_array as run_flowgo_effusion_rate_array
import os
import downflowgo.txt_to_shape as txt_to_shape

def run_downflowgo(path_to_results,dem,csv_vent_file,template_json_file, crs):

    path = os.path.abspath('')+"/downflowgo"
    print('path',path)

    # ------------>    define parameter file and N and Dh for DOWNFLOW  <------------

    parameter_file_downflow = path +'/DOWNFLOW/parameters_range.txt'
    n_path = '10000'
    DH = '2'

    with open(csv_vent_file, 'r') as csvfile:
        csvreader = csv.DictReader(csvfile, delimiter=';')

        for row in csvreader:

            flow_id = str(row['flow_id'])
            lat = str(row['X'])
            long = str(row['Y'])

            name_folder = path_to_results + '/' + flow_id
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

            # this returns an asc file with the lava flow path probabilities
            get_downflow_probabilities(lat, long, dem, path, parameter_file_downflow)
            print('get_downflow_probabilities', get_downflow_probabilities)

            print("******************* DOWNFLOW probability executed: sim.asc created **************************")

            get_downflow_filled_dem(lat, long, dem, path, parameter_file_downflow)
            # this returns an asc file with new (filled) DEM
            print("************************ DOWNFLOW filled DEM done *********")

            filled_dem = 'dem_filled_DH0.001_N1000.asc'
            get_downflow_losd(lat, long, filled_dem, path, parameter_file_downflow)
            # this returns the profile.txt
            os.remove(path_to_folder + "dem_filled_DH0.001_N1000.asc")
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
            print('*********** simulation paths saved in:', path_to_folder + 'map/'+'sim_' + flow_id + '.tif', '***********')
            slope_file = path_to_folder + "profile_00000.txt"

            # convert profile to shape line
            txt_to_shape.get_path_shp(slope_file, path_to_folder, flow_id, crs)
            print('*********** shape file is saved in:', map, '/path_'+flow_id+'.shp', '***********')

            print("**************** DOWNFLOW slope profile executed for FLOW ID =", flow_id, '*********')

            print("************************ Start FLOWGO for FLOW ID =", flow_id, '*********')
            # Run FLOWGO
            simulation = run_flowgo_effusion_rate_array.StartFlowgo()
            json_file_new = path_to_folder + 'parameters_' + flow_id + ".json"
            simulation.make_new_json(template_json_file, flow_id, slope_file, json_file_new)
            simulation.run_flowgo_effusion_rate_array(json_file_new, path_to_folder, slope_file)
            print('*********** FLOWGO executed and results stored in:', path_to_folder, '***********')

            # convert profile to shape line
            run_outs = path_to_folder + 'run_outs_'+flow_id+'.csv'
            txt_to_shape.get_runouts_shp(run_outs, path_to_folder, flow_id, crs)
            txt_to_shape.get_vent_shp(path_to_folder, flow_id, csv_vent_file, crs)
            print('*********** run outs file is saved in:', map, '/run_outs_'+flow_id+'.shp', '***********')

            # Make the MAP
            #mapping.create_map(path_to_folder, flow_id, tiff_file, station_ovpf_path, logo, dem)
    print("************************************** THE END *************************************")


def run_downflow_simple(path_to_results,dem,csv_vent_file, crs):

    path = os.path.abspath('') + "/downflowgo"
    print('path', path)

    # ------------>    define parameter file and N and Dh for DOWNFLOW  <------------

    parameter_file_downflow = path + '/DOWNFLOW/parameters_range.txt'
    n_path = '10000'
    DH = '2'

    with open(csv_vent_file, 'r') as csvfile:
        csvreader = csv.DictReader(csvfile, delimiter=';')

        for row in csvreader:

            flow_id = str(row['flow_id'])
            lat = str(row['X'])
            long = str(row['Y'])

            name_folder = path_to_results + '/' + flow_id
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

            # this returns an asc file with the lava flow path probabilities
            get_downflow_probabilities(lat, long, dem, path, parameter_file_downflow)
            print('get_downflow_probabilities', get_downflow_probabilities)

            print("******************* DOWNFLOW probability executed: sim.asc created **************************")

            get_downflow_filled_dem(lat, long, dem, path, parameter_file_downflow)
            # this returns an asc file with new (filled) DEM
            print("************************ DOWNFLOW filled DEM done *********")

            filled_dem = 'dem_filled_DH0.001_N1000.asc'
            get_downflow_losd(lat, long, filled_dem, path, parameter_file_downflow)
            # this returns the profile.txt
            os.remove(path_to_folder + "dem_filled_DH0.001_N1000.asc")
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
            print('*********** simulation paths saved in:', path_to_folder + 'map/'+'sim_' + flow_id + '.tif', '***********')
            slope_file = path_to_folder + "profile_00000.txt"

            # convert profile to shape line
            txt_to_shape.get_path_shp(slope_file, path_to_folder, flow_id, crs)
            txt_to_shape.get_vent_shp(path_to_folder, flow_id, csv_vent_file, crs)
            print('*********** shape file is saved in:', map, '/path_'+flow_id+'.shp', '***********')

            print("**************** DOWNFLOW slope profile executed for FLOW ID =", flow_id, '*********')

    print("************************************** THE END *************************************")
def run_downflow(parameter_file_downflow, path):
    # Run DOWNFLOW
    os.system(path + '/DOWNFLOW/DOWNFLOW ' + parameter_file_downflow)
def get_downflow_probabilities(lat, long, dem, path, parameter_file_downflow):
    """    # Run DOWNFLOW and create a raster file 'sim.asc' with the probability of trajectories for a given dem (dem)
    and a given parameter file"""

    with open(parameter_file_downflow) as f:
        l = list(f)
    with open(parameter_file_downflow, 'w') as output:
        for line in l:
            if line.startswith('input_DEM'):
                output.write('input_DEM '+dem+'\n')
            elif line.startswith('Xorigine'):
                output.write('Xorigine ' + lat + '\n')
            elif line.startswith('Yorigine'):
                output.write('Yorigine ' + long + '\n')
            elif line.startswith('New_h_grid_name'):
                output.write('#New_h_grid_name ' + '\n')
            elif line.startswith('write_profile'):
                output.write('#write_profile ' + '\n')
            elif line.startswith('#output_L_grid_name '):
                output.write('output_L_grid_name sim.asc' + '\n')
            else:
                output.write(line)
    # Run DOWNFLOW
    os.system(path + '/DOWNFLOW/DOWNFLOW ' + parameter_file_downflow)
def get_downflow_filled_dem(lat, long, dem, path, parameter_file_downflow):

    """ Execute DOWNFLOW and create a new DEM where the pit are filled with a thin layer of 1 mm"""

    n_path = "1000"
    DH= "0.001"

    with open(parameter_file_downflow) as f:
        l = list(f)
    with open(parameter_file_downflow, 'w') as output:
        for line in l:
            if line.startswith('input_DEM'):
                output.write('input_DEM '+dem+'\n')
            elif line.startswith('Xorigine'):
                output.write('Xorigine ' + lat + '\n')
            elif line.startswith('Yorigine'):
                output.write('Yorigine ' + long + '\n')
            elif line.startswith('DH'):
                output.write('DH ' + DH + '\n')
            elif line.startswith('n_path'):
                output.write('n_path ' + n_path +'\n')
            elif line.startswith('output_L_grid_name '):
                output.write('#output_L_grid_name  sim.asc' + '\n')
            elif line.startswith('#New_h_grid_name'):
                output.write('New_h_grid_name  dem_filled_DH0.001_N1000.asc' + '\n')
            elif line.startswith('write_profile'):
                output.write('#write_profile' + '\n')
            else:
                output.write(line)
    # Run DOWNFLOW
    os.system(path + '/DOWNFLOW/DOWNFLOW ' + parameter_file_downflow)
def get_downflow_losd(lat, long, filled_dem, path,parameter_file_downflow):
    """ Execute DOWNFLOW and create the profile.txt """
    n_path = "1"
    DH= "0.001"

    with open(parameter_file_downflow) as f:
        l = list(f)
    with open(parameter_file_downflow, 'w') as output:
        for line in l:
            if line.startswith('input_DEM'):
                output.write('input_DEM '+filled_dem+'\n')
            elif line.startswith('Xorigine'):
                output.write('Xorigine ' + lat + '\n')
            elif line.startswith('Yorigine'):
                output.write('Yorigine ' + long + '\n')
            elif line.startswith('DH'):
                output.write('DH ' + DH + '\n')
            elif line.startswith('n_path'):
                output.write('n_path ' + n_path +'\n')
            elif line.startswith('output_L_grid_name '):
                output.write('#output_L_grid_name  sim.asc' + '\n')
            elif line.startswith('New_h_grid_name'):
                output.write('#New_h_grid_name  dem_filled_DH0.001_N1000.asc' + '\n')
            elif line.startswith('#write_profile'):
                output.write('write_profile 10' + '\n')
            else:
                output.write(line)
    # Run DOWNFLOW
    os.system(path + '/DOWNFLOW/DOWNFLOW ' + parameter_file_downflow)
