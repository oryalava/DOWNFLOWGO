import tkinter as tk
from tkinter import filedialog, ttk
import os
import csv
import subprocess
import datetime
import time
import json
import downflowgo.mapping as mapping
import downflowgo.downflowcpp as downflowcpp
import downflowgo.txt_to_shape as txt_to_shape

import pyflowgo.run_flowgo_effusion_rate_array as run_flowgo_effusion_rate_array
import pyflowgo.run_flowgo as run_flowgo
import pyflowgo.run_outs as run_outs
import pyflowgo.plot_flowgo_results as plot_flowgo_results

if __name__ == "__main__":
    # Start the timer
    start_time = time.time()

    path_to_resources = "/Users/chevrel/Documents/DOWNFLOWGO_PDF_OVPF"
    path_to_eruptions = "/Users/chevrel/GoogleDrive/Eruption_PdF"
    path = os.path.abspath('') + "/downflowgo"
    print('path', path)
    
    def get_folder():
        folder_path = filedialog.askdirectory()
        if folder_path:
            entry_path_to_results_var.set(folder_path)
    def open_editor():
        subprocess.Popen(["python", "edit_json_gui.py"])
    def get_file_name(entry_var):
        file_path = filedialog.askopenfilename()
        if file_path:
            entry_var.set(file_path)
    def get_values_and_create_csv():
        ''' this is to create a vent_csv file from the UTM coordinate '''
        path_to_results = entry_path_to_results_var.get()
        name = entry_name_var.get()
        easting = float(entry_easting_var.get())
        northing = float(entry_northing_var.get())
        csv_vent_file = os.path.join(path_to_results, 'csv_vent_file.csv')
        if os.path.exists(csv_vent_file):
            os.remove(csv_vent_file)
        with open(csv_vent_file, 'a', newline='') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=';')
            if os.path.getsize(csv_vent_file) == 0:
                csvwriter.writerow(['flow_id', 'X', 'Y'])
            csvwriter.writerow([name, easting, northing])

    # Global variable to store the loaded CSV file path
    loaded_csv_file_path = None
    def load_csv_file():
        ''' this is to load the data from a vent_csv file '''
        loaded_csv_file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if loaded_csv_file_path:
            with open(loaded_csv_file_path, newline='') as csvfile:
                csvreader = csv.reader(csvfile, delimiter=';')
                next(csvreader)  # Skip header
                row = next(csvreader)  # Get first row
                entry_name_var.set(row[0])
                entry_easting_var.set(row[1])
                entry_northing_var.set(row[2])

    def get_values():
        ''' this is to load the values from the window to run downflow, this includes
                 the dem, the DH, n and epsg code
                 and the vent_csv file that is either created from the coordinate or from the loaded csv'''
        global loaded_csv_file_path
        path_to_results = entry_path_to_results_var.get()
        dem = os.path.join(os.path.abspath('DEM'), entry_dem_name_var.get())
        DH =entry_DH_var.get()
        n_path = entry_n_path_var.get()
        epsg_code = entry_epsg_code.get()
        json_file = os.path.abspath(entry_json_file_var.get())
        effusion_rates_input = entry_effusion_rates_var.get()

        if effusion_rates_input:
            # Split the input by commas
            rates = effusion_rates_input.split(',')

            if len(rates) == 1:
                # If there is only one value, use it for all three parameters
                try:
                    single_value = int(rates[0])
                    effusion_rates = {
                        "first_eff_rate": single_value,
                        "last_eff_rate": single_value,
                        "step_eff_rate": single_value
                    }
                except ValueError:
                    print("Invalid input. Effusion rates input should have 1 or 3 comma-separated values.")
                    
            elif len(rates) == 3:
                # If there are three values, use them for the parameters
                try:
                    effusion_rates = {
                        "first_eff_rate": int(rates[0]),
                        "last_eff_rate": int(rates[1]),
                        "step_eff_rate": int(rates[2])
                    }
                except ValueError:
                    print("Invalid input. Effusion rates input should have 1 or 3 comma-separated values.")
                    
            else:
                # If the number of values is incorrect
                print("Effusion rates input should have 1 or 3 comma-separated values.")
        else:
            # Handle the case where no input is provided
            print("Effusion rates input is taken from json")
            effusion_rates = 0

        # Use the loaded CSV file if available, otherwise use the default csv_vent_file path
        if loaded_csv_file_path:
            with open(loaded_csv_file_path, newline='') as csvfile:
                csvreader = csv.reader(csvfile, delimiter=';')
                next(csvreader)  # Skip header
                row = next(csvreader)  # Get first row
                name = entry_name_var.set(row[0])
                values = {
                    'name': name,
                    'path_to_results': path_to_results,
                    'csv_vent_file': loaded_csv_file_path,
                    'json_file': json_file,
                    'dem': dem,
                    'DH': DH,
                    'n_path': n_path,
                    'epsg_code': epsg_code,
                    'effusion_rates': effusion_rates
                    }
                return values
        else:
            path_to_results = entry_path_to_results_var.get()
            csv_vent_file = os.path.join(path_to_results, 'csv_vent_file.csv')
            name = entry_name_var.get()
            values = {
                'name': name,
                'path_to_results': path_to_results,
                'csv_vent_file': csv_vent_file,
                'json_file': json_file,
                'dem': dem,
                'DH': DH,
                'n_path': n_path,
                'epsg_code': epsg_code,
                'effusion_rates': effusion_rates
            }
            return values

    def open_run_window():
        ''' this open the window with to check the selected files to run DOWNFLOW'''
        run_window = tk.Toplevel(root)
        run_window.title("Run Downflowgo")
        tk.Label(run_window, text="Check selected files:").pack()
        get_values_and_create_csv()
        values = get_values()

        # Show results in a new window
        results_text = tk.Text(run_window, height=7, width=100)
        results_text.pack()
        results_text.tag_configure("bold", font=("arial", 12, "bold"))
        results_text.insert(tk.END, "Name of the vent: ", "bold", f"{values['name']}\n")
        results_text.insert(tk.END, "Path to Results:", "bold", f"{values['path_to_results']}/{values['name']}\n")
        results_text.insert(tk.END, "VENT:", "bold", f" {values['csv_vent_file']}\n")
        results_text.insert(tk.END, "DEM:", "bold", f" {values['dem']}\n")
        results_text.insert(tk.END, "JSON:", "bold", f" {values['json_file']}\n")

        # Activate Downflowgo button
        button_frame = tk.Frame(run_window)
        button_frame.pack()
        style = ttk.Style()
        style.configure("Volcano.TButton", font=('Helvetica', 12, 'bold'))
        style.map("Volcano.TButton",
                  foreground=[('active', 'red'), ('pressed', 'orange')],
                  background=[('active', 'orange'), ('pressed', 'red')])

        volcano_button = ttk.Button(button_frame, text="RUN DOWNFLOWGO", command=lambda: run_downflowgo(values, run_window),
                                    style="Volcano.TButton")
        volcano_button.pack()
    def run_downflowgo(values,run_window):
        ''' this function will run downflow from downflowcpp.py '''
        path_to_results = values['path_to_results']
        dem = values['dem']
        template_json_file = values['json_file']
        csv_vent_file = values['csv_vent_file']
        DH = values['DH']
        n = values['n_path']
        epsg_code = values['epsg_code']
        effusion_rates = values['effusion_rates']


        # ------------>    load the parameter file  <------------

        parameter_file_downflow = path + '/DOWNFLOW/parameters_range.txt'


        # ------------>  open the csv file with the vent coordinates
        with open(csv_vent_file, 'r') as csvfile:
            csvreader = csv.DictReader(csvfile, delimiter=';')

            for row in csvreader:
                flow_id = str(row['flow_id'])
                long = str(row['X'])
                lat = str(row['Y'])
                name_folder = path_to_results + '/' + flow_id
                path_to_folder = name_folder + '/'
                os.mkdir(name_folder)
                os.chdir(name_folder)

            # Returns an asc file with new (filled) DEM
            downflowcpp.get_downflow_filled_dem(long, lat, dem, path, parameter_file_downflow)
            print("************************ DOWNFLOW filled DEM done *********")

            # Returns the profile.txt
            filled_dem = 'dem_filled_DH0.001_N1000.asc'
            downflowcpp.get_downflow_losd(long, lat, filled_dem, path, parameter_file_downflow)
            print("************************ DOWNFLOW LoSD done *********")
            os.remove(path_to_folder + "/dem_filled_DH0.001_N1000.asc")

            # Returns an asc file with the lava flow path probabilities using the given DH and n
            downflowcpp.get_downflow_probabilities(long, lat, dem, path, parameter_file_downflow, DH, n)
            print("******************* DOWNFLOW probability executed: sim.asc created **************************")

            # create map folder with layers in it
            map = path_to_folder + 'map'
            os.mkdir(map)
            sim_asc = path_to_folder + 'sim.asc'
            cropped_geotiff_file = path_to_folder + 'map/sim_' + flow_id + '.tif'
            txt_to_shape.crop_and_convert_to_tif(sim_asc, cropped_geotiff_file, epsg_code)
            os.remove(sim_asc)
            print('*********** simulation paths saved in:', cropped_geotiff_file, '*********')

            losd_file = path_to_folder + "profile_00000.txt"
            shp_losd_file = path_to_folder + 'map/losd_' + flow_id + '.shp'
            txt_to_shape.get_path_shp(losd_file, shp_losd_file, epsg_code)
            shp_vent_file = path_to_folder + 'map/vent_' + flow_id + '.shp'
            txt_to_shape.get_vent_shp(csv_vent_file, shp_vent_file, epsg_code)
            print("**************** End of DOWNFLOW ", flow_id, '*********')

            print("************************ Start FLOWGO for FLOW ID =", flow_id, '*********')
            path_to_flowgo_results = path_to_folder+'/results_flowgo/'
            os.mkdir(path_to_flowgo_results)
            # Run FLOWGO for json defined effusion rate
            if effusion_rates["first_eff_rate"] == 0:
                #it will calculate the effusion rate basedo n the channel dimensions
                
                json_file_new = path_to_flowgo_results + 'parameters_' + flow_id + ".json"
                slope_file = losd_file
                with open(template_json_file, "r") as data_file:
                    read_json_data = json.load(data_file)
                read_json_data["slope_file"] = slope_file
                read_json_data["effusion_rate_init"] = 0
                read_json_data["lava_name"] = flow_id
                
                with open(json_file_new, "w") as data_file:
                    json.dump(read_json_data, data_file)
                    
                flowgo = run_flowgo.RunFlowgo()
                flowgo.run(json_file_new, path_to_flowgo_results)
                filename = flowgo.get_file_name_results(path_to_flowgo_results, json_file_new)
                filename_array = [filename]
                plot_flowgo_results.plot_all_results(path_to_flowgo_results, filename_array)
                plot_flowgo_results.plt.show()
                plot_flowgo_results.plt.close()
                
                with open(json_file_new, "r") as data_file:
                    data = json.load(data_file)
                lava_name = data["lava_name"]
                run_outs.get_run_outs(path_to_flowgo_results, filename_array, slope_file, lava_name)

                print('****** FLOWGO results are saved:', filename, '***********')
            
            elif effusion_rates != 0:
                # Run FLOWGO for several effusion rates
                first_eff_rate, last_eff_rate, step_eff_rate = effusion_rates  # Unpack the tuple
                simulation = run_flowgo_effusion_rate_array.StartFlowgo()
                json_file_new = path_to_flowgo_results + 'parameters_' + flow_id + ".json"
                slope_file = losd_file
                simulation.make_new_json(template_json_file, flow_id, slope_file, json_file_new)
                simulation.run_flowgo_effusion_rate_array(json_file_new, path_to_flowgo_results, slope_file, effusion_rates)
                
            else:
                print('define effusion rate in effusion_rate or provide an effusion rate array')

            run_outs_file = path_to_flowgo_results + 'run_outs_' + flow_id + '.csv'
            shp_runouts = path_to_folder + 'map/runouts_' + flow_id + '.shp'
            txt_to_shape.get_runouts_shp(run_outs_file, shp_runouts, epsg_code)

            print('*********** FLOWGO executed and results stored in:', path_to_flowgo_results, '***********')

            sim_layers = {
                'losd_file': losd_file,
                'shp_losd_file': shp_losd_file,
                'shp_vent_file': shp_vent_file,
                'cropped_geotiff_file': cropped_geotiff_file,
                'shp_runouts': shp_runouts
            }
            print("************************************** THE END *************************************")
        # Close the run_window after running Downflowgo
        run_window.destroy()
        root.withdraw()
        open_create_map_window(root, dem, sim_layers)


    def open_create_map_window(root, dem, sim_layers):

        ''' this opens the windows to load all the layers to create the map'''

        map_window = tk.Toplevel(root)
        map_window.title("Create Map")
        map_window_width = 900  # Définir la largeur souhaitée
        map_window_height = 300  # Définir la hauteur souhaitée
        map_window.geometry(f"{map_window_width}x{map_window_height}")
        values = get_values()

        # Initialize StringVars for the layers
        ## TODO:  change default path to prefered path
        img_tif_var = tk.StringVar(
            value=path_to_resources + "/mapping_data/map_layers/IGN-map-Background/IGN_SCAN25_2020_enclos_img.tif")
        monitoring_network_var = tk.StringVar(value=path_to_resources + "/mapping_data/map_layers/stations_OVPF/All_Stations_Ovpf_update_2022.shp")
        lava_flow_outline_var = tk.StringVar(value="0")
        logo_var = tk.StringVar(value=path_to_resources + "/mapping_data/map_layers/accessoires/all_logo.png")

        # Define the map_layers dictionary initially
        map_layers = {
            'img_tif_path': img_tif_var.get(),
            'monitoring_network_path': monitoring_network_var.get(),
            'lava_flow_outline_path': lava_flow_outline_var.get(),
            'logo_path': logo_var.get()
        }

        # Frame for Background Map (.tif)
        img_tif_frame = tk.Frame(map_window)
        img_tif_frame.pack(anchor=tk.W)
        label_img_tif = tk.Label(img_tif_frame, text="Background Map (.tif):")
        label_img_tif.pack(side=tk.LEFT)
        entry_img_tif = tk.Entry(img_tif_frame, textvariable=img_tif_var, width=60)
        entry_img_tif.pack(side=tk.LEFT)
        button_browse_img_tif = tk.Button(img_tif_frame, text="Browse",
                                          command=lambda: [img_tif_var.set(filedialog.askopenfilename()),
                                                           map_layers.update({'img_tif_path': img_tif_var.get()})])
        button_browse_img_tif.pack(side=tk.LEFT)

        # Frame for monitoring_network (.shape)
        monitoring_network_frame = tk.Frame(map_window)
        monitoring_network_frame.pack(anchor=tk.W)
        label_monitoring_network = tk.Label(monitoring_network_frame, text="Monitoring Network (.shp): (0 if not)")
        label_monitoring_network.pack(side=tk.LEFT)
        entry_monitoring_network = tk.Entry(monitoring_network_frame, textvariable=monitoring_network_var, width=60)
        entry_monitoring_network.pack(side=tk.LEFT)
        button_browse_monitoring_network = tk.Button(monitoring_network_frame, text="Browse",
                                                     command=lambda: [
                                                         monitoring_network_var.set(filedialog.askopenfilename()),
                                                         map_layers.update({
                                                                               'monitoring_network_path': monitoring_network_var.get()})])
        button_browse_monitoring_network.pack(side=tk.LEFT)

        # Frame for lava_flow_outline (.shape)
        lava_flow_outline_frame = tk.Frame(map_window)
        lava_flow_outline_frame.pack(anchor=tk.W)
        label_lava_flow_outline = tk.Label(lava_flow_outline_frame, text="LavaFlow outline (.shp): (0 if not)")
        label_lava_flow_outline.pack(side=tk.LEFT)
        entry_lava_flow_outline = tk.Entry(lava_flow_outline_frame, textvariable=lava_flow_outline_var, width=60)
        entry_lava_flow_outline.pack(side=tk.LEFT)
        button_browse_lava_flow_outline = tk.Button(lava_flow_outline_frame, text="Browse",
                                                    command=lambda: [
                                                        lava_flow_outline_var.set(filedialog.askopenfilename()),
                                                        map_layers.update(
                                                            {'lava_flow_outline_path': lava_flow_outline_var.get()})])
        button_browse_lava_flow_outline.pack(side=tk.LEFT)

        # Frame for lava_flow_outline (.png)
        logo_frame = tk.Frame(map_window)
        logo_frame.pack(anchor=tk.W)
        label_logo = tk.Label(logo_frame, text="Logo(s) (.png): (0 if not)")
        label_logo.pack(side=tk.LEFT)
        entry_logo = tk.Entry(logo_frame, textvariable=logo_var, width=60)
        entry_logo.pack(side=tk.LEFT)
        button_browse_logo = tk.Button(logo_frame, text="Browse",
                                       command=lambda: [logo_var.set(filedialog.askopenfilename()),
                                                        map_layers.update({'logo_path': logo_var.get()})])
        button_browse_logo.pack(side=tk.LEFT)

        # Button to create Map
        button_frame = tk.Frame(map_window)
        button_frame.pack()
        style = ttk.Style()
        style.configure("Volcano.TButton", font=('Helvetica', 12, 'bold'))
        style.map("Volcano.TButton",
                  foreground=[('active', 'red'), ('pressed', 'orange')],
                  background=[('active', 'orange'), ('pressed', 'red')])

        map_layers = {
            'img_tif_path': img_tif_var.get(),
            'monitoring_network_path': monitoring_network_var.get(),
            'lava_flow_outline_path': lava_flow_outline_var.get(),
            'logo_path': logo_var.get()
        }
        volcano_button = ttk.Button(button_frame, text="CREATE MAP",
                                    command=lambda: process_and_create_mapping(values, map_layers, map_window, root, dem, sim_layers),
                                    style="Volcano.TButton")
        volcano_button.pack(side=tk.LEFT)

        no_button = ttk.Button(button_frame, text="NO", command=lambda: close_all_windows(map_window, root))
        no_button.pack(side=tk.LEFT)

    def process_and_create_mapping(values, map_layers, map_window, run_window, dem, sim_layers):

        if loaded_csv_file_path:
            with open(loaded_csv_file_path, 'r') as csvfile:
                csvreader = csv.DictReader(csvfile, delimiter=';')
                for row in csvreader:
                    flow_id = str(row['flow_id'])
                    path_to_results = entry_path_to_results_var.get() + '/' + flow_id
                    mapping.create_map(path_to_results, dem, flow_id, map_layers, sim_layers, mode='downflowgo')
                    print(path_to_results, flow_id)
            close_all_windows(map_window, root)
        else:
            path_to_results = values['path_to_results'] +"/"+values['name']
            flow_id = values['name']
            mapping.create_map(path_to_results, dem, flow_id, map_layers, sim_layers, mode='downflowgo')
            close_all_windows(map_window, root)

    def close_all_windows(*windows):
        for window in windows:
            window.destroy()

    # Create main window
    root = tk.Tk()
    root.title("Enter Coordinates and File Names")
    folder_frame = tk.Frame(root)
    folder_frame.pack(anchor=tk.W)

    # Adjust size window
    window_width = 1000  # Définir la largeur souhaitée
    window_height = 250  # Définir la hauteur souhaitée
    root.geometry(f"{window_width}x{window_height}")


    # Select main folder
    label_path_to_results = tk.Label(folder_frame, text="Path to Eruption Results:")
    label_path_to_results.pack(side=tk.LEFT)
    entry_path_to_results_var = tk.StringVar(value=path_to_eruptions+"/test")
    entry_path_to_results = tk.Entry(folder_frame, textvariable=entry_path_to_results_var, width=50)
    entry_path_to_results.pack(side=tk.LEFT)
    button_browse = tk.Button(folder_frame, text="Browse", command=get_folder)
    button_browse.pack(side=tk.LEFT)

    # Name of the vent
    name_frame = tk.Frame(root)
    name_frame.pack(anchor=tk.W)
    label_name = tk.Label(name_frame, text="Name of the vent:")
    label_name.pack(side=tk.LEFT)
    entry_name_var = tk.StringVar(value="Main_vent")
    entry_name = tk.Entry(name_frame, textvariable=entry_name_var, width=20)
    entry_name.pack(side=tk.LEFT)

    # Define Easting and Northing
    easting_northing_frame = tk.Frame(root)
    easting_northing_frame.pack(anchor=tk.W)
    # Easting
    label_easting = tk.Label(easting_northing_frame, text="Easting (UTM):")
    label_easting.pack(side=tk.LEFT)
    entry_easting_var = tk.StringVar(value="369082.7")
    entry_easting = tk.Entry(easting_northing_frame, textvariable=entry_easting_var, width=15)
    entry_easting.pack(side=tk.LEFT)
    #  Northing
    label_northing = tk.Label(easting_northing_frame, text="Northing (UTM):")
    label_northing.pack(side=tk.LEFT)
    entry_northing_var = tk.StringVar(value="7647204.29")
    entry_northing = tk.Entry(easting_northing_frame, textvariable=entry_northing_var, width=15)
    entry_northing.pack(side=tk.LEFT)

    #CSV file
    csv_frame = tk.Frame(root)
    csv_frame.pack(anchor=tk.W)
    label_csv = tk.Label(csv_frame, text="Or Load Coordinates from CSV:")
    label_csv.pack(side=tk.LEFT)
    button_load_csv = tk.Button(csv_frame, text="Load CSV", command=load_csv_file)
    button_load_csv.pack(side=tk.LEFT)

    # Define DEM
    dem_frame = tk.Frame(root)
    dem_frame.pack(anchor=tk.W)
    label_dem_name = tk.Label(dem_frame, text="DEM:")
    label_dem_name.pack(side=tk.LEFT)  # Aligner à gauche
    ##TODO:  change path to prefered DEM
    entry_dem_name_var = tk.StringVar(value=path_to_resources+"/DEM/DEM-20240411-net-5m.asc")
    entry_dem_name = tk.Entry(dem_frame, textvariable=entry_dem_name_var, width=80)
    entry_dem_name.pack(side=tk.LEFT)
    button_browse = tk.Button(dem_frame, text="Browse", command=lambda: get_file_name(entry_dem_name_var))
    button_browse.pack(side=tk.LEFT)

    # Define N and DH and EPSG
    N_DH_EPSG_frame = tk.Frame(root)
    N_DH_EPSG_frame.pack(anchor=tk.W)
    # DH
    label_DH = tk.Label(N_DH_EPSG_frame, text="DH:")
    label_DH.pack(side=tk.LEFT)
    entry_DH_var = tk.StringVar(value="2")
    entry_DH = tk.Entry(N_DH_EPSG_frame, textvariable=entry_DH_var, width=4)
    entry_DH.pack(side=tk.LEFT)
    #  N
    label_n_path = tk.Label(N_DH_EPSG_frame, text="N:")
    label_n_path.pack(side=tk.LEFT)
    entry_n_path_var = tk.StringVar(value="10000")
    entry_n_path = tk.Entry(N_DH_EPSG_frame, textvariable=entry_n_path_var, width=8)
    entry_n_path.pack(side=tk.LEFT)
    #  EPSG
    label_epsg_code = tk.Label(N_DH_EPSG_frame, text="EPSG:")
    label_epsg_code.pack(side=tk.LEFT)
    entry_epsg_code_var = tk.StringVar(value="32740")
    entry_epsg_code = tk.Entry(N_DH_EPSG_frame, textvariable=entry_epsg_code_var, width=8)
    entry_epsg_code.pack(side=tk.LEFT)

    # JSON File
    json_frame = tk.Frame(root)
    json_frame.pack(anchor=tk.W)
    label_json_file = tk.Label(json_frame, text="JSON File:")
    label_json_file.pack(side=tk.LEFT)  # Aligner à gauche
    ##TODO:  change path to prefered json
    entry_json_file_var = tk.StringVar(value=path_to_resources+"/PdF_template.json")
    entry_json_file = tk.Entry(json_frame, textvariable=entry_json_file_var, width=80)
    entry_json_file.pack(side=tk.LEFT)
    button_browse = tk.Button(json_frame, text="Browse", command=lambda: get_file_name(entry_json_file_var))
    button_browse.pack(side=tk.LEFT)
    edit_button = tk.Button(json_frame, text="Edit Json", command=open_editor)
    edit_button.pack(side=tk.LEFT)
    
    #  Effusion rates
    effusion_rates_frame = tk.Frame(root)
    effusion_rates_frame.pack(anchor=tk.W)
    label_effusion_rates = tk.Label(effusion_rates_frame, text="Effusion rate or effusion rate range (first, last, step):")
    label_effusion_rates.pack(side=tk.LEFT)
    entry_effusion_rates_var = tk.StringVar(value="5,65,5")
    entry_effusion_rates = tk.Entry(effusion_rates_frame, textvariable=entry_effusion_rates_var, width=10)
    entry_effusion_rates.pack(side=tk.LEFT)

    # Button to open Downflowgo window
    style = ttk.Style()
    style.configure("Volcano.TButton", font=('Helvetica', 12, 'bold'))
    style.map("Volcano.TButton",
              foreground=[('active', 'red'), ('pressed', 'orange')],
              background=[('active', 'orange'), ('pressed', 'red')])

    volcano_button = ttk.Button(root, text="DOWNFLOWGO", command=lambda:open_run_window(), style="Volcano.TButton")
    volcano_button.pack()

    # Start main loop
    root.mainloop()

    # End the timer
    end_time = time.time()

    # Calculate the duration
    execution_time = end_time - start_time

    # Format the execution time
    if execution_time >= 60:
        minutes = int(execution_time // 60)
        seconds = int(execution_time % 60)
        print(f"The code took {minutes} minutes and {seconds} seconds to execute.")
    else:
        print(f"The code took {int(execution_time)} seconds to execute.")

