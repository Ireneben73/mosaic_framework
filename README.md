# mosaic_framework
**MOdelling Sea Level And Inundation for Cyclones (MOSAIC) modelling framework**

This repository contains the code for the reproduction of the paper:

_Benito, I., Aerts, J.C.J.H., Ward, P.J., Eilander, D., and Muis, S., 2024. A multiscale modelling framework of coastal flooding events for global to local flood hazard assessments._ 

In this study we introduce a novel modelling framework to dynamically simulate tropical and extratropicalcyclone induced total water levels using the Global Tide and Surge Model (GTSM), and the hydrodynamic flood model Super-Fast INundation of CoastS (SFINCS). MOSAIC allows to choose between gridded meteorological forcing or track data, and provides the possibility to modify the model resolution. The resolution can be modified spatially and temporally, and provides a multiscale modelling approach where local high-resolution models (Delft3D FM based) can be nested within a global hydrodynamic model (GTSM).

The code consists of the following files and directories:
* **py_environments:** folder containing the environments necessary to run the scripts
   * **j1_environment.yml:** environment file to run the general scripts within j1_run_GTSM.sh bash script
   * **j1b_environment.yml:** environment file to run the local high-resolution model scripts within j1_run_GTSM.sh bash script
   * **j2_environment.yml:** environment file to run the j2_run_SFINCS.sh bash script
 
* **py_scripts:** folder containing the main scripts to execute the modelling framework 
   * **p1_holland_model:** folder containing the scripts to run the Holland model
     * **p1a_create_single_spw.py:** script to define the settings for the spiderweb file output from the Holland model
     * **p1b_holland_model.py:** script to run the Holland model
     * **p1c_write_spw_file.py:** script to define the spiderweb file output from the Holland model
 
   * **j1_run_GTSM.sh:** bash script to execute GTSM and run its pre- and postprocess
     * **p1a_download_ERA5.py:** script to download ERA5 data from CDS
     * **p1b_ERA5_process4GTSM.py:** script to preprocess the ERA5 data for GTSM
     * **p2a_preprocess_GTSM.py:** script to prepare the model files of GTSM
     * **p2b_create_localGTSM_v2.py:** script to generate a local high-resolution grid using Delft3D FM and define its model boundaries
     * **p2c_pli_to_xyn.py:** script to translate the local high-resolution model boundaries into output locations for GTSM
     * **p2d_his_to_bc.py:** script to convert the output of GTSM into boundary conditions for the local high-resolution model
     * **p2e_generate_local_model_v2.py:** script to generate the model files for the local high-resolution model
     * **p3_postprocess_GTSM.py:** script to postprocess the GTSM and/or nested model
       
   * **j2_run_SFINCS.sh:** bash script to execute SFINCS, run its pre- and postprocess 
     * **p5_build_SFINCS_model.py:** script to build the SFINCS model
     * **p6_postprocess_SFINCS.py:** script to postprocess the SFINCS model
 

