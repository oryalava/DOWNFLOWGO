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