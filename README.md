 # Welcome to DOWNFLOWGO

A number of numerical models exist to support lava flow modeling (see review by Dietterich et al. [2017]). 
Here, we combine the stochastic model DOWNFLOW [Favalli et al. 2005](https://doi.org/10.1029/2004gl021718) with the deterministic model FLOWGO [Harris and Rowland 2001](https://doi.org/10.1007/s004450000120) to support hazard assessment at Piton de la Fournaise , mainly.

DOWNFLOW provides the most likely lava flow paths, including the LoSD and area of coverage. 
For responding to current crises at Piton de la Fournaise, this model was calibrated by fitting the output flow coverage 
to the actual areas of all flow fields since 2016 [Chevrel et al. 2021](https://doi.org/10.5194/nhess-21-2355-2021). DOWNFLOW must be calibrated (dh and N parameters) for you volcano.

FLOWGO calculates the runout distance of a lava flow along a slope line for a given effusion rate [Harris and Rowland 2001](https://doi.org/10.1007/s004450000120). 
It is 1-D model adapted for **cooling-limited basaltic lava flow in a channel of uniform depth** that, once calibrated with a suitable models and input parameters, 
only needs the slope from the vent along the steepest descent line and a discharge rate as its source terms.
The code is now an open access python library : [PyFLOwGO](https://github.com/pyflowgo/pyflowgo.git) presented in [Chevrel et al. 2018](https://doi.org/10.1016/j.cageo.2017.11.009). 

FLOWGO source terms must be adapted accordingly to your lava flow. 
See exemples on Earth: Hawaiʻi, (Harris et al., 2022; Harris & Rowland, 2001, 2015; Mossoux et al., 2016; Riker et al., 2009; Robert et al., 2014; Rowland et al., 2005; Chevrel et al., 2018; Thompson and Ramsey, 2021), 
Italy (Harris et al., 2007, 2011; Wright et al., 2008) ; Kamchatka (Ramsey et al. 2019); Mt Cameroon (Wantim et al. 2013); D.R. Congo (Mossoux et al. 2016), Galapagos (Rowland et al. 2003) 
La Reunion  (Chevrel et al., 2018, 2022; Harris et al., 2016, 2019; Peltier et al., 2022; Rhéty et al., 2017) 
and on other planets (see also next session): Mars (Flynn et al., 2022; Rowland et al., 2004) Mercury (Vetere et al. 2017) ; 
Moon (Lev et al. 2021) and Venus Flynn et al. (2023). 

To use this package you must cite [Chevrel et al. 2022](https://doi.org/10.30909/vol.05.02.313334), [Favalli 2005](https://doi.org/10.1029/2004gl021718) and [Harris and Rowland 2001](https://doi.org/10.1007/s004450000120):

**Chevrel MO, Harris A, Peltier A, Villeneuve N, Coppola D, Gouhier M, Drenne S. (2022) 
Volcanic crisis management supported by near real time lava flow hazard assessment at Piton de la Fournaise, 
Volcanica 5(2), pp. 313–334. https://doi.org/10.30909/vol.05.02.313334

Harris, A. J. L. and S. Rowland (2001). “FLOWGO: a kinematic thermo-rheological model for lava flowing in a channel”. 
Bulletin of Volcanology 63(1), pages 20–44. issn: 1432-0819. https://doi.org/10.1007/s004450000120.

Favalli, M. et al. (2005). “Forecasting lava flow paths by a stochastic approach”. Geophysical Research Letters 32(3). 
issn: 0094- 8276. https://doi.org/10.1029/2004gl021718.**


## Description of the package 
This folder includes :

1) a folder **DOWNFLOW** containing the code in c++ of DOWNFLOW [Favalli et al. 2005](https://doi.org/10.1029/2004gl021718) 
provided by Massimiliano Favalli (hopefully soon available on github).

To install **DOWNFLOW** follow the instruction in the **DOWNFLOW** folder: **README_DOWNFLOW.md** 


2) the following scripts :

- scripts to execute :

``` main_downflow.py  ``` (or ``` main_downflow_GUI.py  ```)  to run **DOWNFLOW** alone.

 ``` main_downflowgo.py  ```(or ``` main_downflowgo_GUI.py  ```)   to run in sequence **DOWNFLOW + FLOWGO**. 


- scripts for various functions amoung which the important ones are:
```
  downflowcpp.py
  mapping.py
  txt_to_shape.py
  ```

3) the configuration file, the requirements and environment

## Actions

### 1) Python packages to install before running

To run these scripts, you will need :

--> Built-in Python 3.8 Packages (included in the standard installation): math, os, sys


--> install the following environment:

```conda env create -f environment.yml```

or requirements :

```pip install -r requirements.txt```

--> install the [PyFLOwGO](https://github.com/pyflowgo/pyflowgo.git) library from github:

```pip install git+https://github.com/pyflowgo/pyflowgo.git   ```


### 2) Requiered file types and configuration

1) The DEM must be  ```.asc ``` format with UTM in WGS84, with the following header :
```
ncols        3193
nrows        2305
xllcorner    361622.6
yllcorner    7644294.2
cellsize     5.00
NODATA_value  0
 ```

2) The configuration file: ```config_downflowgo.ini```:
use this file to write your prefered paths by default
```
[paths]
eruptions_folder = /Users/path/to your folder
dem = /Users/path/to/your_dem.asc
json = /Users/path/to/your_json.json

#For mapping
img_tif_map_background = /Users/path/to_your_background_for_mapping.tif
monitoring_network = /Users/path/to_your_moniroting_station.shp (point geometry)
lava_flow_outline = /Users/path/to_the_lava_flow_outline.shp (line geometry)
logo = Users/path/to_the_logos.png 

[notes]
# Credit for background image
source_img_tif_map_background =  © whatever credit
# Set motion about data, e.g 'UNVERIFIED DATA - NOT FOR DISTRIBUTION' or 'DONNEES NON VALIDES - NE PAS DIFFUSER' or 0 for nothing
unverified_data = UNVERIFIED DATA - NOT FOR DISTRIBUTION

[language]
# Set the language to EN (English) or FR (French)
language = EN 

```
3) The ```.json``` file for PyFLOWGO:
For more info go to ```https://github.com/pyflowgo/pyflowgo.git ```

### 3) Run the GUIS

To run DOWNFLOW :
 ``` python main_downflow_GUI.py config_downflowgo.ini ```

To run DOWNFLOWGO :
 ``` python main_downflowgo_GUI.py config_downflowgo.ini ```

## Output files

In the dedicated folder define in 2.1 (```eruptions_folder```) you will find:
* A folder named **results_flowgo** with all the results from pyflowgo and associated plots
* The map of the simulation that uses the above layers: ```map.png```
* A new folder named **map** that contains the following files so you can create your own map with any GIS system:

  1) ```vent.shp```(the vent point)
  2) ```sim.asc ```(a raster with the flow path probabilities)
  3) ```losd_profile.txt``` (the line of steepest descent as text file)
  4) ```losd.shp``` (the line of steepest descent as shape file)
  5) ```runouts.shp``` (the runout points for the given effusion rates along the main path)

    
#  Authors
 Dr. Magdalena Oryaëlle Chevrel (oryaelle.chevrel@ird.fr) - Laboratoire Magmas et Volcans

Please do not hesitate the contact me for any further information or assistance

# Licence
The current license of the software is GPL v3.0.