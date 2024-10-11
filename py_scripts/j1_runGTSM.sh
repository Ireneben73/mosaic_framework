#!/bin/bash
#Set job requirements
#SBATCH --nodes=1
#SBATCH --ntasks=32
#SBATCH --cpus-per-task=1
#SBATCH --partition=rome
#SBATCH --time=15:00:00

echo $OMP_NUM_THREADS


#------------------------------------------------------------------------------------------------------------------------------------------------------
## Directories
#------------------------------------------------------------------------------------------------------------------------------------------------------
singularitydir=/projects/0/einf2224/dflowfm_2022.04_fix20221108/delft3dfm_2022.04
pyscripts_dir="/projects/0/einf2224/paper1/scripts/py_scripts/"
gtsm_model_runsdir="/projects/0/einf2224/paper1/scripts/model_runs/gtsm/"
meteo_dir="/projects/0/einf2224/paper1/data/gtsm/meteo_forcing/"

#------------------------------------------------------------------------------------------------------------------------------------------------------
## Models setup
#------------------------------------------------------------------------------------------------------------------------------------------------------

# Case studies with their bboxes for which gridded data will be saved at
cases=('irma' 'haiyan' 'xynthia')

# Start dates                          
declare -A start_date
start_date['irma']="20170909"      # Date 2 days before passing near Jacksonville (11 Sept. 2017)
start_date['haiyan']="20131106"    # Date 2 days before landfall (8th Nov. 2013)
start_date['xynthia']="20100226"   # Date 2 days before landfall 
tstop=96                           # Hours that the event lasts
tspinup=10                         # Days of spinup

# Meteorological forcing
declare -A meteo_forcing
# Specify the kind of meteorological forcing to use. In our case, Irma and Haiyan couple ERA5 and Holland model output, and Xynthia uses ERA5 alone
meteo_forcing['irma']="ERA5" #"ERA5-Holland" 
meteo_forcing['haiyan']="ERA5-Holland"
meteo_forcing['xynthia']="ERA5"

# Model configurations 
model_configs=('G1' 'G2' 'G3' 'N2' 'N3')                #G1 (Default configuration), G2 (Refined temporal output resolution), G3 (Refined spatial output), N2 (Dynamic downscaling (Refined grid + Updated bathymetry)), N3 (Fully refined configuration)

# bounding box for the local model on the IB
declare -A bbox                                    # lon min, lon max, lat min, lat max  
bbox['irma']=-85.6,-79.4,24.4,34.0
bbox['haiyan']=124.0,139.7,7.3,13.0
bbox['xynthia']=-30.1,1,30,48.0 # test

#------------------------------------------------------------------------------------------------------------------------------------------------------
## Model execution
#------------------------------------------------------------------------------------------------------------------------------------------------------
case_nr="$1"
model_nr="$2"
# Run GTSM for each case study and each model configuration
for case_name in "${cases[$case_nr]}"; do
    cd "$pyscripts_dir" || exit                      # go to the python scripts directory
    echo "CASE STUDY: $case_name"
    case_folder="$gtsm_model_runsdir/$case_name"
    mkdir -p "$case_folder"                          # make a directory for the case study

    #--------------------------------------------------------------------------------------------------------------------------------------------------
    ## Prepare meteo forcing for the case studies
    #--------------------------------------------------------------------------------------------------------------------------------------------------
    
    ## ERA5
    #--------------------------------------------
    era5_file="$meteo_dir/ERA5/ERA5_$case_name.nc"
    if [ -e "$era5_file" ]; then
        # If the file exists, do not download ERA5 again
        echo "File ERA5_$case_name.nc already exists."
    else
        echo "File ERA5_$case_name.nc does not exist."
        # download ERA5 data from CDS
        echo "Downloading ERA5 data"
        conda run -n gtsm_paper1 python p1a_download_ERA5.py "$case_name" "${start_date[$case_name]}" "$tstop" "$tspinup"                                                   
        # modify ERA5 data to be used by GTSM
        echo "Modifying ERA5 data"
        conda run -n gtsm_paper1 python p1b_ERA5_process4GTSM.py "$case_name"
    fi
    
    ## Holland model                                                                                                                    
    #--------------------------------------------                                                                                       

    forcing="${meteo_forcing[$case_name]}"
    if [[ $forcing == *Holland* ]]; then
      echo "Track data is being used. Holland model necessary to convert to wind and pressure fields"
      
      spw_file="$meteo_dir/spiderwebs/$case_name.spw"
      # Run the Holland model only if the $forcing_file does not exist
      if [ ! -f "$spw_file" ]; then
        echo "Spiderweb file $case_name.spw does not exist. Start running Holland model"
        conda run -n dfm_tools python /projects/0/einf2224/paper1/scripts/py_scripts/p1_holland_model/p1a_create_single_spw_ibl.py "$case_name" "${start_date[$case_name]}" "$tspinup" &&
        touch "holland_$case_name.done"
        if [ ! -f "holland_$case_name.done" ]; then
          echo "$case_name FAILED!" >> holland_log.txt
        else
          echo "Finished running Holland model"
          rm "holland_$case_name.done"
        fi
      else
          echo "Spiderweb file $case_name.spw already exits."
      fi
    fi
    
    #--------------------------------------------------------------------------------------------------------------------------------------------------
    ## Iterate through each model configuration for each case study
    #--------------------------------------------------------------------------------------------------------------------------------------------------
    
    echo "Iterating over model configurations"
    #for model_config in "${model_configs[@]}"; do
    for model_config in "${model_configs[$model_nr]}"; do
        cd "$pyscripts_dir" || exit                 # go to the python scripts directory
        echo "MODEL CONFIGURATION: $model_config"
        
        # Make a directory for each model configuration
        model_folder="$case_folder/$model_config"
        mkdir -p "$model_folder"                    # make a directory for the model configuration
        
        # If model configuration is N2 or N3, then first the local model needs to be generated
        if [ "$model_config" == "N2" ] || [ "$model_config" == "N3" ]; then
            local_dir="$model_folder/local"
            #mkdir -p "$local_dir"
            echo "Generating .pli file and net.nc file for the local GTSM model"
            conda run -n dfm_tools python p2b_create_localGTSM_v2.py "$model_folder" "$case_name" "${bbox[$case_name]}"
            # The .pli file from the local model is converted to the .xyn observations file, where the Global GTSM model will store the data at
            global_dir="$model_folder/global"
            mkdir -p "$global_dir"
            conda run -n dfm_tools python p2c_pli_to_xyn.py "$case_folder" "$model_folder" "$case_name"
            echo "Convert the .pli file of the local model into .xyn file"

        fi
        
        # Preprocess GTSM to modify the case study, model configuration characteristics and start/end dates
        echo "Editing GTSM mdu" 
        conda run -n dfm_tools python p2a_preprocess_GTSM.py "$case_name" "$model_config" "${start_date[$case_name]}" "$tstop" "$tspinup" "${meteo_forcing[$case_name]}" &&                       
        
        # Run global GTSM
        if [ "$model_config" == "N2" ] || [ "$model_config" == "N3" ]; then
            cd "$model_folder/global" || exit           # move into the global model folder within the model_config directory
        else
            cd "$model_folder" || exit                  # move into the model_config directory  
        fi      
        mdufile=gtsm_fine.mdu

        # Execute GTSM
        echo "Running GTSM"
        srun $singularitydir/execute_singularity_snellius.sh -p 1 run_dflowfm.sh $mdufile 
        
        cd "$pyscripts_dir" || exit
        if [ "$model_config" == "N2" ] || [ "$model_config" == "N3" ]; then
            # Convert .his file from the global GTSM model to boundary conditions (.bc) file for the local model
            conda run -n dfm_tools python p2d_his_to_bc.py "$case_folder" "$model_folder" "$case_name"
            # Generate the model configuration file for the local GTSM model
            conda run -n dfm_tools python p2e_generate_local_model_v2.py "$model_config" "$model_folder" "$case_name" "${meteo_forcing[$case_name]}" "${start_date[$case_name]}" "$tstop" "${bbox[$case_name]}"
            # Run local model
            cd "$model_folder/local" || exit  
            mdufile_local=gtsm_fine_local.mdu
            echo "Partitioning GTSM"
            nPart=32                                    # number of partitions of the model
            srun -n 1 $singularitydir/execute_singularity_snellius.sh -p 1 run_dflowfm.sh --partition:ndomains=$nPart:icgsolver=6:genpolygon=1:contiguous=0  $mdufile_local
            echo "Running GTSM"
            srun $singularitydir/execute_singularity_snellius.sh -p 1 run_dflowfm.sh $mdufile_local 

        fi
    done
done




