 # DOWNFLOWGO

 ## Description of the package 
This folder contains :

1) a folder **DOWNFLOW** containing the code in c++ of [DOWNFLOW](https://github.com/) _a link to github will be added one day by Massi Favalli_

2) the following scripts :
- scripts of the functions :
```
  downflowcpp.py
  run_flowgo_effusion_rate_array.py
  txt_to_shape.py
  run_flowgo.py
  plot_flowgo_results.py
  run_outs.py
  mapping.py
  ```
- scripts to execute :

The script   ``` main_downflow.py  ``` (or ``` main_downflow_GUI.py  ```) is a Python program designed to run **DOWNFLOW**.

The script   ``` main_downflowgo.py  ```(or ``` main_downflowgo_GUI.py  ```)  is a Python program designed to run in sequence **DOWNFLOW** and **FLOWGO**. 



## Actions:

### 1) Python packages to install before running

To run these scripts, you will need :

--> Built-in Python 3.8 Packages (included in the standard installation): math, os, sys

--> install the following envorinment:

```conda env create -f environment.yml```

or requirements :

```pip install -r requirements.txt```

--> install the pyflowgo library from github:

```pip install git+https://github.com/pyflowgo/pyflowgo.git   ```


### File types:

1) The DEM must be  ```.asc ``` format with UTM in WGS84, with the following header :
```
ncols        3193
nrows        2305
xllcorner    361622.6
yllcorner    7644294.2
cellsize     5.00
NODATA_value  0
 ```


### Run the guiS:

To run DOWNFLOW :
 ``` python3 main_downglow_GUI.py ```

To run DOWNFLOWGO :
 ``` python3 main_downglowgo_GUI.py ```



###  In main_downflowgo.py

1) write the link to the result folder of your choice (in general it is the date of the eruption)

```
path_to_results = "Users/Documents/Eruptions/030523"
```

2) write the link to DEM of your choice:

```
dem = path + '/DEM/MNT-post-20220919_5m.asc'
```

3) write a short name for your DEM (this will be used to name your output files)
```
dem_name = '_MNT2022_'
```
4) write the path to the ```.csv``` file containing separated by ";"the vent coordinates (in UTM) – possibility of having various points
```
csv_vent_file = "./vent_coordinate.csv"
```
 Coordinate must be in UTM and you can add lines for new vent
```
flow_id;X;Y
Vent1;369142.0;7647368.0
Vent2;367303.0;7651654.0
```

5) write the path to the json input file
```
template_json_file = path +"/PdF_template.json"
```

 6)  run main_downflowgo.py

## Output files

In the dedicated folder chosen in step 1) you will find:
* all the results from pyflowgo and associated plots
* A folder named **map** has been created and contains the following files :
  1) ```vent.shp```(the vent point)
  2) ```Sim.asc ```(a raster with the flow path probabilities)
  3) ```Path.shp``` (the line of steepest descent)
  4) ```Run-outs.shp``` (the runout points for the given effusion rates along the main path)
  5) ```map.png``` (the map of the simulation that uses the above layers with the IGN 2020 background)

You can either use the files to create your own map with any GIS system or directly use the map.png