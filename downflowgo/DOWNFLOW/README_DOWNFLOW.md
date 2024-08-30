# Welcome to the folder DOWNFLOW

This is a README file for this folder containing the stochastic model DOWNFLOW of [Favalli et al. 2005](https://doi.org/10.1029/2004gl021718).
DOWNFLOW provides the most likely lava flow paths, including the LoSD and area of coverage, from a point vent. 
DOWNFLOW must be calibrated (dh and N parameters) for your volcano.

This is not the original release of DOWNFLOW but a version provided by Massimiliano Favalli who will hopefully soon release it.

To use DOWNFLOW you must cite :
Favalli, M. et al. (2005). “Forecasting lava flow paths by a stochastic approach”. Geophysical Research Letters 32(3). 
issn: 0094- 8276. https://doi.org/10.1029/2004gl021718.**


## Description of the package 
This folder includes:

-> the source code in c++ of [DOWNFLOW](https://doi.org/10.1029/2004gl021718) 
provided by Massimiliano Favalli (hopefully soon officially available on github).

-> the makefile to compile the c++ code into an executable program.

-> parameters_range_template.txt that contains the input parameters needed for DOWNFLOW.

## Actions:

### 1) Run the Makefile to compile DOWNFLOW.cpp on your system

Unix system:

Open your terminal, go into the folder DOWNFLOW, delete the executable file (DOWNFLOW) and the code object (DOWNFLOW.o),
and then simply type : ```make```
this function will actually use the makefile and the DOWNFLOW.cpp to make the executable program. 
Now you hence should have the new DOWNFLOW executable Unix file and the code object (DOWNFLOW.o)

Windows:

Use some compiler software to compile the c++ code.

### 2) Run DOWNFLOW

Requiered file types:

1) The DEM must be  ```.asc ``` format with UTM in WGS84, with the following header :
```
ncols        3193
nrows        2305
xllcorner    361622.6
yllcorner    7644294.2
cellsize     5.00
NODATA_value  0
 ```
NODATA_value can be 0 or what ever value (like -99999) but avoid « nan » or any letters.

2) The parameters_range_template.txt must contain the path to the DEM and the required parameters.




In your terminal :
 ```
 ../DOWNFLOW/DOWNFLOW parameters_range_template.txt
 ```

python function:

 ```
 import os
 
 parameters_range = '/path/to/parameters_range_template.txt'
 path = '/path/to/DOWNFLOW/'
 
 def run_downflow(parameters_range, path):
       os.system(path + '/DOWNFLOW ' + parameters_range)
 
 run_downflow(parameters_range, path)
 ```

## Output files

The following files will be produced :
  1) ```sim.asc ```(a raster with the flow path probabilities)
  2) ```profile_00000.txt``` (coordinates every xx m of the line of steepest descent)

 # Licence:
Not fully open, you must contact Massimiliano Favalli.



 # Authors of this readme:
 Dr. Magdalena Oryaëlle Chevrel (oryaelle.chevrel@ird.fr) - Laboratoire Magmas et Volcans
