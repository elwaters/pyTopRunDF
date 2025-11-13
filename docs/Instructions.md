# Instruction
The user can define various scenarios that are simulated one after the other. These can be either individual events per scenario or scenarios of the same event for sensitivity analysis of the input parameters.  
However each scenario needs to be defined in the folder Scenarios/Scenario<#>
## Preprocessing for each scenario

Before starting a simulation with pyTopRunDF the following steps and procedures have to be accomplished and considered by the user. The main input parameters are:

**A volume of the debris-flow event to be simulated -** $V$

The volume must correspond to the unit of length measurement used for the projection of the digital terrain input model [topofan.asc](topofan.asc). In the example the volume is given in $m^3$.

***input.json***: $V=5000 m^3$\
`"volume": 5000,`

**A mobility coefficient -** $k_B$

The mobility coefficient $k_B$ is a dimensionless parameter and has to be defined by the user. For back calculation it is recommended to estimate $k_{obs}$ using the empirical relation:

$k_{obs}=B_{obs}V_{obs}^{-2/3}$ (1)

In equation (1), $B_{obs}$ is the planimetric deposition area $[L^2]$ and $V_{obs}$ the observed volume $[L^3]$. In order to perform a forward analysis, $k_{Bpred}$ a mobility coefficient based on the average slope of the channel $S_c$ as well as the average slope of the fan $S_f$, can bei estimated [(Scheidl and Rickenmann, 2009)](https://onlinelibrary.wiley.com/doi/abs/10.1002/esp.1897).

$k_{Bpred}=5.07S_f^{-0.10}S_c^{-1.68}$ (2)

If $k_{Bpred}$ is used, an uncertainty of a factor of two must be considered. See [Rickenmann et al. (2009)](https://www.e-periodica.ch/digbib/view?pid=wel-004%3A2010%3A102%3A%3A42) (in german), [Scheidl and Rickenmann, 2009](https://onlinelibrary.wiley.com/doi/abs/10.1002/esp.1897) for more details.

***input.json***: $k_B=20$\
`"coefficient": 20`

**A start point of the simulation -** $X | Y$

The user needs to declare a starting point of the simulation in $X$ (easting) and $Y$ (northing) coordinates. Those coordinates must lay within the applied digital terrain model and have to be defined in the same projection.\
Starting point can be a distinct change within the longitudinal flow-profile (significant change in slope gradient at fan apex) or obstacles forcing the debris flow to deposit. pyTopRunDF reacts sensitively to the starting point, which is why the program changes the starting point after each single flow path and randomly sets a new one in a buffer around the initial starting cell (default maximum buffer = 3 cells). However, the user might need to accomplish maybe several simulations to achieve plausible results.

***input.json***: $X=672724: Y= 152145$\
`"X_coord": 672724,`\
`"Y_coord": 152145,`

**A digital terrain model**

The digital terrain model (DTM) has to be provided in ASCII-format to assure being independent from any commercial GIS program. The file with the fixed name *topofan.asc* has to be placed in the ./DEM/ folder.\
pyTopRunDF was tested with LiDAR based digital terrain data showing a level of detail of 2.5 x 2.5 m.

To convert a geotif into an ascii grid you can use the [geotiff2ascii](../helper/geotiff2ascii.py) function.

``` bash
python .\helper\geotiff2ascii.py your_input.tif ./DEM/topofan.asc
```
## Postprocessing for each scenario
There are currently no postprocessing tools. The program writes an output for each scenario.  
This consists of the simulated deposition heights and a map of these.  
The results can be found after simulation of each scenario in Outputs/Scenario<#>