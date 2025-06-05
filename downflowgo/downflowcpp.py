#import requires packages
import os.path
import csv
#import downflowgo.run_flowgo_effusion_rate_array as run_flowgo_effusion_rate_array
import os
import downflowgo.txt_to_shape as txt_to_shape
import numpy as np

#def run_downflowgo(path_to_results,dem,csv_vent_file,template_json_file, crs):
#
#    path = os.path.abspath('')+"/downflowgo"
#    print('path',path)
#
#    # ------------>    define parameter file and N and Dh for DOWNFLOW  <------------
#
#    parameter_file_downflow = path +'/DOWNFLOW/parameters_range.txt'
#    n_path = '10000'
#    DH = '2'
#
#    with open(csv_vent_file, 'r') as csvfile:
#        csvreader = csv.DictReader(csvfile, delimiter=';')
#
#        for row in csvreader:
#
#            flow_id = str(row['flow_id'])
#            long = str(row['X'])
#            lat = str(row['Y'])
#
#            name_folder = path_to_results + '/' + flow_id
#            path_to_folder = name_folder + '/'
#            os.mkdir(name_folder)
#            os.chdir(name_folder)
#
#            with open(parameter_file_downflow) as f:
#                l = list(f)
#            with open(parameter_file_downflow, 'w') as output:
#                for line in l:
#                    if line.startswith('DH'):
#                        output.write('DH ' + DH + '\n')
#                    elif line.startswith('n_path'):
#                        output.write('n_path ' + n_path + '\n')
#                    else:
#                        output.write(line)
#
#            # this returns an asc file with the lava flow path probabilities
#            get_downflow_probabilities(long,lat,  dem, path, parameter_file_downflow)
#            print('get_downflow_probabilities', get_downflow_probabilities)
#
#            print("******************* DOWNFLOW probability executed: sim.asc created **************************")
#
#            get_downflow_filled_dem(long,lat,  dem, path, parameter_file_downflow)
#            # this returns an asc file with new (filled) DEM
#            print("************************ DOWNFLOW filled DEM done *********")
#
#            filled_dem = 'dem_filled_DH0.001_N1000.asc'
#            get_downflow_losd( long, lat,filled_dem, path, parameter_file_downflow)
#            # this returns the profile.txt
#            os.remove(path_to_folder + "dem_filled_DH0.001_N1000.asc")
#            # create map folder
#            map = path_to_folder + 'map'
#            os.mkdir(map)
#
#            # crop asc file
#            sim_asc = path_to_folder + '/sim.asc'
#            txt_to_shape.crop_asc_file(sim_asc, path_to_folder, flow_id)
#            # convert .asc to tiff
#            cropped_asc_file = path_to_folder + '/map/sim_' + flow_id + '.asc'
#            txt_to_shape.convert_to_tiff(cropped_asc_file, path_to_folder, flow_id)
#            os.remove(path_to_folder + 'sim.asc')
#            print('*********** simulation paths saved in:', path_to_folder + 'map/'+'sim_' + flow_id + '.tif', '***********')
#            slope_file = path_to_folder + "profile_00000.txt"
#
#            # convert profile to shape line
#            txt_to_shape.get_path_shp(slope_file, path_to_folder, flow_id, crs)
#            print('*********** shape file is saved in:', map, '/path_'+flow_id+'.shp', '***********')
#
#            print("**************** DOWNFLOW slope profile executed for FLOW ID =", flow_id, '*********')
#
#            print("************************ Start FLOWGO for FLOW ID =", flow_id, '*********')
#            # Run FLOWGO
#            simulation = run_flowgo_effusion_rate_array.StartFlowgo()
#            json_file_new = path_to_folder + 'parameters_' + flow_id + ".json"
#            simulation.make_new_json(template_json_file, flow_id, slope_file, json_file_new)
#            simulation.run_flowgo_effusion_rate_array(json_file_new, path_to_folder, slope_file)
#            print('*********** FLOWGO executed and results stored in:', path_to_folder, '***********')
#
#            # convert profile to shape line
#            run_outs = path_to_folder + 'run_outs_'+flow_id+'.csv'
#            txt_to_shape.get_runouts_shp(run_outs, path_to_folder, flow_id, crs)
#            txt_to_shape.get_vent_shp(path_to_folder, flow_id, csv_vent_file, crs)
#            print('*********** run outs file is saved in:', map, '/run_outs_'+flow_id+'.shp', '***********')
#
#            # Make the MAP
#            #mapping.create_map(path_to_folder, flow_id, tiff_file, station_ovpf_path, logo, dem)
#    print("************************************** THE END *************************************")


#def run_downflow_simple(path_to_results,dem,csv_vent_file, crs):
#
#    path = os.path.abspath('') + "/downflowgo"
#    print('path', path)
#
#    # ------------>    define parameter file and N and Dh for DOWNFLOW  <------------
#
#    parameter_file_downflow = path + '/DOWNFLOW/parameters_range.txt'
#    n_path = '10000'
#    DH = '2'
#
#    with open(csv_vent_file, 'r') as csvfile:
#        csvreader = csv.DictReader(csvfile, delimiter=';')
#
#        for row in csvreader:
#
#            flow_id = str(row['flow_id'])
#            long = str(row['X'])
#            lat = str(row['Y'])
#
#            name_folder = path_to_results + '/' + flow_id
#            path_to_folder = name_folder + '/'
#            os.mkdir(name_folder)
#            os.chdir(name_folder)
#
#            with open(parameter_file_downflow) as f:
#                l = list(f)
#            with open(parameter_file_downflow, 'w') as output:
#                for line in l:
#                    if line.startswith('DH'):
#                        output.write('DH ' + DH + '\n')
#                    elif line.startswith('n_path'):
#                        output.write('n_path ' + n_path + '\n')
#                    else:
#                        output.write(line)
#
#            # this returns an asc file with the lava flow path probabilities
#            get_downflow_probabilities(long,lat,  dem, path, parameter_file_downflow)
#            print('get_downflow_probabilities', get_downflow_probabilities)
#
#            print("******************* DOWNFLOW probability executed: sim.asc created **************************")
#
#            get_downflow_filled_dem(long, lat, dem, path, parameter_file_downflow)
#            # this returns an asc file with new (filled) DEM
#            print("************************ DOWNFLOW filled DEM done *********")
#
#            filled_dem = 'dem_filled_DH0.001_N1000.asc'
#            get_downflow_losd(long,lat,  filled_dem, path, parameter_file_downflow)
#            # this returns the profile.txt
#            os.remove(path_to_folder + "dem_filled_DH0.001_N1000.asc")
#            # create map folder
#            map = path_to_folder + 'map'
#            os.mkdir(map)
#
#            # crop asc file
#            sim_asc = path_to_folder + '/sim.asc'
#            txt_to_shape.crop_asc_file(sim_asc, path_to_folder, flow_id)
#            # convert .asc to tiff
#            cropped_asc_file = path_to_folder + '/map/sim_' + flow_id + '.asc'
#            txt_to_shape.convert_to_tiff(cropped_asc_file, path_to_folder, flow_id)
#            os.remove(path_to_folder + 'sim.asc')
#            print('*********** simulation paths saved in:', path_to_folder + 'map/'+'sim_' + flow_id + '.tif', '***********')
#            slope_file = path_to_folder + "profile_00000.txt"
#
#            # convert profile to shape line
#            txt_to_shape.get_path_shp(slope_file, path_to_folder, flow_id, crs)
#            txt_to_shape.get_vent_shp(path_to_folder, flow_id, csv_vent_file, crs)
#            print('*********** shape file is saved in:', map, '/path_'+flow_id+'.shp', '***********')
#
#            print("**************** DOWNFLOW slope profile executed for FLOW ID =", flow_id, '*********')
#
#    print("************************************** THE END *************************************")
def run_downflow(parameter_file_downflow, path):
    # Run DOWNFLOW
    os.system(path + '/DOWNFLOW/DOWNFLOW ' + parameter_file_downflow)
def get_downflow_probabilities(long,lat, dem, path, parameter_file_downflow,DH,n):
    """    # Run DOWNFLOW and create a raster file 'sim.asc' with the probability of trajectories for a given dem (dem)
    and a given parameter file"""

    with open(parameter_file_downflow) as f:
        l = list(f)
    with open(parameter_file_downflow, 'w') as output:
        for line in l:
            if line.startswith('input_DEM'):
                output.write('input_DEM '+dem+'\n')
            elif line.startswith('Xorigine'):
                output.write('Xorigine ' + long + '\n')
            elif line.startswith('Yorigine'):
                output.write('Yorigine ' + lat + '\n')
            elif line.startswith('DH'):
                output.write('DH ' + DH + '\n')
            elif line.startswith('n_path'):
                output.write('n_path ' + n + '\n')
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
def get_downflow_filled_dem(long, lat, dem, path, parameter_file_downflow):

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
                output.write('Xorigine ' + long + '\n')
            elif line.startswith('Yorigine'):
                output.write('Yorigine ' + lat + '\n')
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

def get_downflow_losd(long, lat, filled_dem, path,parameter_file_downflow):
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
                output.write('Xorigine ' + long + '\n')
            elif line.startswith('Yorigine'):
                output.write('Yorigine ' + lat + '\n')
            elif line.startswith('DH'):
                output.write('DH ' + DH + '\n')
            elif line.startswith('n_path'):
                output.write('n_path ' + n_path +'\n')
            elif line.startswith('#output_L_grid_name '):
                output.write('output_L_grid_name sim.asc' + '\n')
            elif line.startswith('New_h_grid_name'):
                output.write('#New_h_grid_name  dem_filled_DH0.001_N1000.asc' + '\n')
            elif line.startswith('#write_profile'):
                output.write('write_profile 10' + '\n')
            else:
                output.write(line)
    # Run DOWNFLOW
    os.system(path + '/DOWNFLOW/DOWNFLOW ' + parameter_file_downflow)


def check_dem(long, lat, dem):
    """ to check dem headers and data lines as well as vent position within the dem"""
    long = float(long)
    lat = float(lat)
    expected_headers = ['ncols', 'nrows', 'xllcorner', 'yllcorner', 'cellsize', 'nodata_value']

    with open(dem) as file:
        header_lines = [next(file) for _ in range(6)]
        # Check that header keys match expected ones
        for i, line in enumerate(header_lines):
            key = line.split()[0].strip().lower()
            if key != expected_headers[i]:
                raise ValueError(
                    f"Unexpected header at line {i + 1} in your DEM '{dem}': got '{key}', expected "
                    f"'{expected_headers[i]}'")

        ncols = int(header_lines[0].split()[1])
        nrows = int(header_lines[1].split()[1])
        xllcorner = float(header_lines[2].split()[1])
        yllcorner = float(header_lines[3].split()[1])
        cellsize = float(header_lines[4].split()[1])
        nodata_value = float(header_lines[5].split()[1])

        # Read the values from the ASC file
        data_lines = [line.strip().split() for line in file]
        data = np.array(data_lines, dtype=float)

        # Check that the data exists
        if data.size == 0:
            raise ValueError(f"The ASC file '{dem}' contains no data after the header.")

        # Check that the data shape matches the header info
        if data.shape != (nrows, ncols):
            raise ValueError(
                f"Inconsistent dimensions in the dem :'{dem}': expected {nrows}x{ncols}, got {data.shape}.")

        # Check that (long, lat) is inside the DEM extent
        x_max = xllcorner + ncols * cellsize
        y_max = yllcorner + nrows * cellsize

        if not (xllcorner <= long <= x_max and yllcorner <= lat <= y_max):
            raise ValueError(
                f"The coordinates of the vent (long={long}, lat={lat}) is outside the DEM extent:\n"
                f"x: [{xllcorner}, {x_max}], y: [{yllcorner}, {y_max}]")

    # Optional: return useful values if needed
    return True
