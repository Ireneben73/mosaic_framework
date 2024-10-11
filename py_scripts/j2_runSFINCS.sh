#!/bin/bash
#SBATCH -p thin
#SBATCH -n 1
#SBATCH -t 00:20:00
#SBATCH --mem=40G

#------------------------------------------------------------------------------------------------------------------------------------------------------
## Directories
#------------------------------------------------------------------------------------------------------------------------------------------------------
scripts_dir="/projects/0/einf2224/paper1/scripts"
sfincs_templatedir="$scripts_dir/sfincs_template"
sfincs_model_runsdir="$scripts_dir/model_runs/sfincs"
tmp_model_runsdir="$TMPDIR"
gtsm_model_runsdir="$scripts_dir/model_runs/gtsm"
sfincsdata_dir="/projects/0/einf2224/paper1/data/sfincs"

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
tspinup=10                          # Days of spinup


# Model configurations 
model_configs=('G1' 'G2' 'G3' 'N2' 'N3')                #G1 (Default configuration), G2 (Refined temporal output resolution), G3 (Refined spatial output), N2 (Dynamic downscaling (Refined grid + Updated bathymetry)), N3 (Fully refined configuration)

# bounding box for the SFINCS model
declare -A bbox_sfincs                                    # lon min, lon max, lat min, lat max  
bbox_sfincs['irma']=-82.2,-80.2,30.0,32.0
bbox_sfincs['haiyan']=124.8,125.3,11.0,11.5
bbox_sfincs['xynthia']=-1.8,-0.8,45.5,46.5

#------------------------------------------------------------------------------------------------------------------------------------------------------
## Model execution
#------------------------------------------------------------------------------------------------------------------------------------------------------
case_nr="$1"
model_nr="$2"
# Run SFINCS for each case study and each model configuration
for case_name in "${cases[$case_nr]}"; do
    echo "CASE STUDY: $case_name"
    case_folder="$sfincs_model_runsdir/$case_name"
    mkdir -p "$case_folder"  
    
    for model_config in "${model_configs[$model_nr]}"; do
        echo "MODEL CONFIGURATION: $model_config"
        conda run -n hydromt-sfincs_latest python test_p5_build_SFINCS_model.py "$case_name" "$model_config" "${start_date[$case_name]}" "$tstop" "${bbox_sfincs[$case_name]}" "$sfincs_templatedir" "$sfincs_model_runsdir" "$gtsm_model_runsdir" "$sfincsdata_dir" "$TMPDIR"
            
        # Go to the temporary scratch folder where SFINCS will be run
        cd "$TMPDIR/$case_name/$model_config"
        echo "Temporary directory: $tmp_model_runsdir/$case_name/$model_config"
        
        echo "Starting SFINCS"
        # Run Singularity container and redirect output logs to sfincs_log.txt
        singularity run /gpfs/work2/0/einf2224/flood_modelling/hydromt-sfincs/sfincs-cpu_latest.sif > sfincs_log.txt
        
        # Postprocess to calculate the hmax
        cd "$scripts_dir/py_scripts"                                                                                          
        conda run -n hydromt-sfincs_latest python p6_postprocess_SFINCS.py "$TMPDIR/$case_name" "$model_config" "$sfincs_templatedir" "$sfincs_model_runsdir" "$case_name"

        # Copy the SFINCS model already executed to the model runs directory        
        if [ -d "$tmp_model_runsdir/$case_name/$model_config" ]; then
            mkdir -p "$case_folder/$model_config"
            cp -r "$tmp_model_runsdir/$case_name/$model_config"/* "$case_folder/$model_config"
            echo "Files copied successfully to $case_folder/$model_config."
        else
            echo "Source directory does not exist: $tmp_model_runsdir/$case_name/$model_config"
        fi

    done
done
