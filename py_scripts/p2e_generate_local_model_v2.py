import os
import matplotlib.pyplot as plt
plt.close('all')
import dfm_tools as dfmt
from dfm_tools import modelbuilder as mb
import hydrolib.core.dflowfm as hcdfm
import xarray as xr
import pandas as pd
import contextily as ctx
import getpass
import sys
import glob
from distutils.dir_util import copy_tree
import shutil
from datetime import datetime, timedelta
sys.path.insert(0, '/projects/0/einf2224/paper2/scripts/gtsm41_template/')
import templates


#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
## Input
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
model_config = sys.argv[1]
model_dir = sys.argv[2]
case_name = sys.argv[3]
meteo_forcing = sys.argv[4]
tstart=sys.argv[5]
tstop=sys.argv[6]
bbox = sys.argv[7].split(',')

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
## Directories
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
local_dir = f'{model_dir}/local'
global_dir = f'{model_dir}/global'
root_dir="/projects/0/einf2224/paper1/scripts"
modelfilesdir=f"{root_dir}/gtsm41_template/model_files_common"
templatedir=f"{root_dir}/gtsm41_template/model_input_template"

# Move to the local directory
os.chdir(local_dir)

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
## Files
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------

if model_config=="N3":
    shutil.copy2(f"{root_dir}/model_configs_setups/OR_refinement/observation_locations_snapped_1p25eu/selected_output_OR_" + str(case_name) + "_snapped_1p25eu_unique_obs.xyn",f'{local_dir}/selected_output_OR_' + str(case_name) + '_snapped_1p25eu_unique_obs.xyn')
    obsfile=f"selected_output_OR_{case_name}_snapped_1p25eu_unique_obs.xyn"
    
else:
    obsfile="selected_output_new_unique_noreg.xyn"
    
#obsfile = "selected_output_new_unique_noreg.xyn"
netfile  = f'{case_name}_net.nc'
extfile_new = f'{case_name}_new.ext'
extfile_old = 'gtsm_fine.ext'
poly_file = f'{case_name}.pli'

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
## Fix times
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------

tspinup=3 # days of spinup for the local model
tstart_spinup = datetime.strptime(tstart, "%Y%m%d") - timedelta(days=int(tspinup))
tstart_spinup_str = tstart_spinup.strftime("%Y%m%d")
tstop_spinup_str = str(int(tstop) + int(tspinup)*24)

if model_config == "N3":
    timeinterval=600. # 172800.  777600."
else:
    timeinterval=3600. #  172800.  777600."

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
## Get model configuration file .mdu
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------

shutil.copy2(f'{templatedir}/gtsm_fine_local.mdu.template',f'{local_dir}/gtsm_fine_local.mdu.template')

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
## External forcing file definitions
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## Old external forcings file
#----------------------------

# Copy old external forcing file from the global model to the local. Frictions are the same.
shutil.copy2(f'{global_dir}/{extfile_old}',f'{local_dir}/{extfile_old}')

# Copy meteo files from the global model to the local. Meteo forcings are the same.
if meteo_forcing=="ERA5":
    shutil.copy2(f'{global_dir}/ERA5_4GTSM_u10_{case_name}.nc',f'{local_dir}/ERA5_4GTSM_u10_{case_name}.nc')
    shutil.copy2(f'{global_dir}/ERA5_4GTSM_v10_{case_name}.nc',f'{local_dir}/ERA5_4GTSM_v10_{case_name}.nc')
    shutil.copy2(f'{global_dir}/ERA5_4GTSM_msl_{case_name}.nc',f'{local_dir}/ERA5_4GTSM_msl_{case_name}.nc')
elif meteo_forcing=="ERA5-Holland":
    shutil.copy2(f'{global_dir}/ERA5_4GTSM_u10_{case_name}.nc',f'{local_dir}/ERA5_4GTSM_u10_{case_name}.nc')
    shutil.copy2(f'{global_dir}/ERA5_4GTSM_v10_{case_name}.nc',f'{local_dir}/ERA5_4GTSM_v10_{case_name}.nc')
    shutil.copy2(f'{global_dir}/ERA5_4GTSM_msl_{case_name}.nc',f'{local_dir}/ERA5_4GTSM_msl_{case_name}.nc')
    shutil.copy2(f'{global_dir}/{case_name}.spw',f'{local_dir}/{case_name}.spw')
else:
    print('EXTERNAL FORCING FILE NOT DEFINED!')


## New external forcings file
#----------------------------

# Create new external forcings file for the water level boundary conditions
ext_new = hcdfm.ExtModel()
poly_files = f"{case_name}_*.pli"
# Loop over each matching file
for poly_file in glob.glob(poly_files):
    print('poly_file:', poly_file)

    file_number = os.path.splitext(os.path.basename(poly_file))[0].split('_')[-1]
    print('file_number:', file_number)
    
    forcing_file = f'{case_name}_{file_number}.bc'
    boundary_object = hcdfm.Boundary(quantity='waterlevelbnd',
                                     locationfile=poly_file,
                                     forcingfile=forcing_file)
    ext_new.boundary.append(boundary_object)
ext_new.save(filepath=extfile_new)

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
## Clip observations file from the global model
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Load the global observation points file
global_obs = f'{global_dir}/selected_output_new_unique_noreg.xyn'
global_obs_df = pd.read_csv(global_obs, sep='\t', names=['x', 'y', 'id'])

# Coordinates of the local model to which the observation points file will be clipped to
x_min, x_max, y_min, y_max = float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])

# Observation points for the local model
local_obs_df = global_obs_df[(global_obs_df['x'] >= x_min) & (global_obs_df['x'] <= x_max) & (global_obs_df['y'] >= y_min) & (global_obs_df['y'] <= y_max)]
local_obs_df.to_csv(obsfile, sep=' ', header=False, index=False, float_format='%.6f')

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
## Copy static model files to the local model 
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------

source_dir = modelfilesdir
destination_dir = local_dir

for filename in os.listdir(source_dir):
    # Check if the filename contains "step11"
    if "step11" not in filename:
        # If it does not contain "step11", copy the file to the destination directory
        source_path = os.path.join(source_dir, filename)
        destination_path = os.path.join(destination_dir, filename)
        shutil.copy2(source_path, destination_path)

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
## Model config file modifications (.mdu) - Modify templates
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# His and Map file saving depending on spinup times
tmap_start = int(tspinup) * 24 *  3600              # tspinup is in days. Multiply by 3600 to have seconds
tmap_stop = (int(tstop) + int(tspinup)*24) * 3600   # tstop is in hours. Multiply by 24 * 3600 to have seconds
hisinterval=f"{timeinterval} {tmap_start}. {tmap_stop}."
mapinterval=f"{timeinterval} {tmap_start}. {tmap_stop}."

## Modify model config file
#---------------------------
keywords_MDU={'NETFILE':f'{case_name}_net.nc', 'REFDATE':pd.Timestamp(tstart_spinup_str).strftime('%Y%m%d'),'TSTART':str(0),'TSTOP':tstop_spinup_str, 'EXTFORCEFILENEW':extfile_new, 'OBSFILE':obsfile , 'HISINT':hisinterval, 'MAPINT':mapinterval} 
templates.replace_all(os.path.join(local_dir,"gtsm_fine_local.mdu.template"), os.path.join(local_dir,"gtsm_fine_local.mdu"),keywords_MDU,'%')



