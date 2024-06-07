import tkinter as tk
from tkinter import filedialog
import os
import csv
import downflowgo.downflowcpp as downflowcpp
from tkinter import ttk
import subprocess
import downflowgo.mapping as mapping
import datetime


if __name__ == "__main__":

    def get_folder():
        folder_path = filedialog.askdirectory()
        if folder_path:
            entry_path_to_results_var.set(folder_path)
    def get_file_name(entry_var):
        file_path = filedialog.askopenfilename()
        if file_path:
            entry_var.set(file_path)
    def get_values_and_create_csv():
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
        #print("csv_vent_file created under:", csv_vent_file)

    # Global variable to store the loaded CSV file path
    loaded_csv_file_path = None
    def load_csv_file():
        global loaded_csv_file_path
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
        global loaded_csv_file_path
        path_to_results = entry_path_to_results_var.get()
        dem = os.path.join(os.path.abspath('DEM'), entry_dem_name_var.get())
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
                    'dem': dem
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
                'dem': dem
            }
            return values

    def open_run_window():
        run_window = tk.Toplevel(root)
        run_window.title("Run Downflow")
        tk.Label(run_window, text="Check selected files:").pack()
        get_values_and_create_csv()
        values = get_values()

        # Afficher les résultats dans la fenêtre
        results_text = tk.Text(run_window, height=7, width=100)
        results_text.pack()
        results_text.tag_configure("bold", font=("arial", 12, "bold"))
        results_text.insert(tk.END, "Name of the vent: ", "bold", f"{values['name']}\n")
        results_text.insert(tk.END, "Path to Results:", "bold", f"{values['path_to_results']}/{values['name']}\n")
        results_text.insert(tk.END, "VENT:", "bold", f" {values['csv_vent_file']}\n")
        results_text.insert(tk.END, "DEM:", "bold", f" {values['dem']}\n")

        # Bouton lancer Downflow
        button_frame = tk.Frame(run_window)
        button_frame.pack()
        style = ttk.Style()
        style.configure("Volcano.TButton", font=('Helvetica', 12, 'bold'))
        style.map("Volcano.TButton",
                  foreground=[('active', 'red'), ('pressed', 'orange')],
                  background=[('active', 'orange'), ('pressed', 'red')])

        volcano_button = ttk.Button(button_frame, text="RUN DOWNFLOW", command=lambda: run_downflow(values,run_window),
                                    style="Volcano.TButton")
        volcano_button.pack()

    def run_downflow(values,run_window):
        path_to_results = values['path_to_results']
        dem = values['dem']
        csv_vent_file = values['csv_vent_file']
        downflowcpp.run_downflow_simple(path_to_results,dem,csv_vent_file)
        open_create_map_window(run_window, dem)

    def open_create_map_window(run_window,dem):
        map_window = tk.Toplevel(root)
        map_window.title("Create Map")
        map_window_width = 900  # Définir la largeur souhaitée
        map_window_height = 300  # Définir la hauteur souhaitée
        map_window.geometry(f"{map_window_width}x{map_window_height}")
        values = get_values()

        #  Make button to browse layers for the map
        ## TODO:  change path to prefered Background
        file1_var = tk.StringVar(value="/Users/chevrel/Documents/DOWNFLOWGO_PDF_OVPF/mapping_data/layers/IGN-map-Background/IGN_SCAN25_2020_enclos_img.tif")
        file2_var = tk.StringVar(value="0")
        file3_var = tk.StringVar(value="0")
        ##TODO:  change path to prefered logos
        file4_var = tk.StringVar(value="/Users/chevrel/Documents/DOWNFLOWGO_PDF_OVPF/mapping_data/map/accessoires/all_logo.png")

        file1_frame = tk.Frame(map_window)
        file1_frame.pack(anchor=tk.W)
        label_file1 = tk.Label(file1_frame, text="Background Map (.tif):")
        label_file1.pack(side=tk.LEFT)
        entry_file1 = tk.Entry(file1_frame, textvariable=file1_var, width=40)
        entry_file1.pack(side=tk.LEFT)
        button_browse1 = tk.Button(file1_frame, text="Browse", command=lambda: get_file_name(file1_var))
        button_browse1.pack(side=tk.LEFT)

        file2_frame = tk.Frame(map_window)
        file2_frame.pack(anchor=tk.W)
        label_file2 = tk.Label(file2_frame, text="OVPF stations (.shp): (0 if not)")
        label_file2.pack(side=tk.LEFT)
        entry_file2 = tk.Entry(file2_frame, textvariable=file2_var, width=40)
        entry_file2.pack(side=tk.LEFT)
        button_browse2 = tk.Button(file2_frame, text="Browse", command=lambda: get_file_name(file2_var))
        button_browse2.pack(side=tk.LEFT)

        file3_frame = tk.Frame(map_window)
        file3_frame.pack(anchor=tk.W)
        label_file3 = tk.Label(file3_frame, text="LavaFlow outline (.shp): (0 if not)")
        label_file3.pack(side=tk.LEFT)
        entry_file3 = tk.Entry(file3_frame, textvariable=file3_var, width=40)
        entry_file3.pack(side=tk.LEFT)
        button_browse3 = tk.Button(file3_frame, text="Browse", command=lambda: get_file_name(file3_var))
        button_browse3.pack(side=tk.LEFT)

        file4_frame = tk.Frame(map_window)
        file4_frame.pack(anchor=tk.W)
        label_file4 = tk.Label(file4_frame, text="Logo(s) (.png): (0 if not)")
        label_file4.pack(side=tk.LEFT)
        entry_file4 = tk.Entry(file4_frame, textvariable=file4_var, width=40)
        entry_file4.pack(side=tk.LEFT)
        button_browse4 = tk.Button(file4_frame, text="Browse", command=lambda: get_file_name(file4_var))
        button_browse4.pack(side=tk.LEFT)

        # Bouton Create Map
        button_frame = tk.Frame(map_window)
        button_frame.pack()
        style = ttk.Style()
        style.configure("Volcano.TButton", font=('Helvetica', 12, 'bold'))
        style.map("Volcano.TButton",
                  foreground=[('active', 'red'), ('pressed', 'orange')],
                  background=[('active', 'orange'), ('pressed', 'red')])

        volcano_button = ttk.Button(button_frame, text="CREATE MAP",
                                    command=lambda: process_and_create_mapping(values, file1_var.get(), file2_var.get(),
                                                                               file3_var.get(),file4_var.get(),
                                                                               map_window, run_window, dem),
                                    style="Volcano.TButton")
        volcano_button.pack(side=tk.LEFT)

        no_button = ttk.Button(button_frame, text="NO", command=lambda: close_all_windows(map_window, run_window, root))
        no_button.pack(side=tk.LEFT)

    def process_and_create_mapping(values, file1_path, file2_path, file3_path, file4_path, map_window, run_window, dem):
        map_layers = process_files(file1_path, file2_path, file3_path, file4_path)
        if loaded_csv_file_path:
            with open(loaded_csv_file_path, 'r') as csvfile:
                csvreader = csv.DictReader(csvfile, delimiter=';')
                for row in csvreader:
                    flow_id = str(row['flow_id'])
                    path_to_results = entry_path_to_results_var.get() + '/' + flow_id
                    mapping.create_map_downflow(path_to_results, dem, flow_id, map_layers)
                    print(path_to_results, flow_id)
            close_all_windows(map_window, run_window, root)
        else:
            path_to_results = values['path_to_results'] +"/"+values['name']
            flow_id = values['name']
            mapping.create_map_downflow(path_to_results, dem, flow_id, map_layers)
            close_all_windows(map_window, run_window, root)

    def process_files(file1_path, file2_path, file3_path, file4_path):
        map_layers = {
            'tiff_file': file1_path,
            'station_ovpf_path': file2_path,
            'lava_flow_outline_path': file3_path,
            'logo': file4_path
        }
        return map_layers

    def close_all_windows(*windows):
        for window in windows:
            window.destroy()

    # Création de la fenêtre principale
    root = tk.Tk()
    root.title("Enter Coordinates and File Names")
    folder_frame = tk.Frame(root)
    folder_frame.pack(anchor=tk.W)

    # Ajuster la largeur de la fenêtre
    window_width = 1000  # Définir la largeur souhaitée
    window_height = 200  # Définir la hauteur souhaitée
    root.geometry(f"{window_width}x{window_height}")


    # Select main folder
    label_path_to_results = tk.Label(folder_frame, text="Path to Eruption Results:")
    label_path_to_results.pack(side=tk.LEFT) # Aligner à gauche
    ## TODO: change path to prefered folder
    entry_path_to_results_var = tk.StringVar(value="/Users/chevrel/GoogleDrive/Eruption_PdF/test")
    entry_path_to_results = tk.Entry(folder_frame, textvariable=entry_path_to_results_var, width=50)
    entry_path_to_results.pack(side=tk.LEFT)
    button_browse = tk.Button(folder_frame, text="Browse", command=get_folder)
    button_browse.pack(side=tk.LEFT)

    # Nom
    name_frame = tk.Frame(root)
    name_frame.pack(anchor=tk.W)
    label_name = tk.Label(name_frame, text="Name of the vent:")
    label_name.pack(side=tk.LEFT)
    entry_name_var = tk.StringVar(value="Main_vent")
    entry_name = tk.Entry(name_frame, textvariable=entry_name_var, width=20)
    entry_name.pack(side=tk.LEFT)

#    # Easting and Northing
    easting_northing_frame = tk.Frame(root)
    easting_northing_frame.pack(anchor=tk.W)
#    # Easting
    label_easting = tk.Label(easting_northing_frame, text="Easting (UTM):")
    label_easting.pack(side=tk.LEFT)
    entry_easting_var = tk.StringVar(value="369082.7")
    entry_easting = tk.Entry(easting_northing_frame, textvariable=entry_easting_var, width=15)
    entry_easting.pack(side=tk.LEFT)
#
#    #  Northing
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

    # Nom du MNT (DEM)
    dem_frame = tk.Frame(root)
    dem_frame.pack(anchor=tk.W)
    label_dem_name = tk.Label(dem_frame, text="DEM:")
    label_dem_name.pack(side=tk.LEFT)  # Aligner à gauche
    ## TODO: change path to prefered DEM
    entry_dem_name_var = tk.StringVar(value="/Users/chevrel/Documents/DOWNFLOWGO_PDF_OVPF_2023/DEM/DEM-20240411-net-5m.asc")
    entry_dem_name = tk.Entry(dem_frame, textvariable=entry_dem_name_var, width=80)
    entry_dem_name.pack(side=tk.LEFT)
    button_browse = tk.Button(dem_frame, text="Browse", command=lambda: get_file_name(entry_dem_name_var))
    button_browse.pack(side=tk.LEFT)


    # Bouton ouvrir fenetre Downflowgo
    style = ttk.Style()
    style.configure("Volcano.TButton", font=('Helvetica', 12, 'bold'))
    style.map("Volcano.TButton",
              foreground=[('active', 'red'), ('pressed', 'orange')],
              background=[('active', 'orange'), ('pressed', 'red')])

    volcano_button = ttk.Button(root, text="DOWNFLOW", command=lambda:open_run_window(),style="Volcano.TButton")
    volcano_button.pack()

    # Lancement de la boucle principale
    root.mainloop()




