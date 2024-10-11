#! /usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 20 17:25:23 2023
@author: benitoli
"""

import sys
sys.path.insert(0, '/projects/0/einf2224/paper2/scripts/gtsm_template/')
import numpy as np
import os
import shutil
import fnmatch
#import datetime
from datetime import datetime, timedelta
import templates
from distutils.dir_util import copy_tree
import glob 
import pandas as pd
import shutil

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
## Input settings from the bash script
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

case_name=sys.argv[1]
model_config=sys.argv[2]
tstart=sys.argv[3]
tstop=sys.argv[4]
tspinup = sys.argv[5]
tstart_spinup = datetime.strptime(tstart, "%Y%m%d") - timedelta(days=int(tspinup))
tstart_spinup_str = tstart_spinup.strftime("%Y%m%d")
meteo_forcing=sys.argv[6]

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
## Directories
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

root_dir="/projects/0/einf2224/paper1/scripts"
templatedir=f"{root_dir}/gtsm41_template/model_input_template"
modelfilesdir=f"{root_dir}/gtsm41_template/model_files_common"
meteodir="/projects/0/einf2224/paper1/data/gtsm/meteo_forcing/ERA5"
#if model_config=="IB":
if model_config == "IB" or model_config == "RC":
    newdir=f"{root_dir}/model_runs/gtsm/{case_name}/{model_config}/global" # directory where each gtsm model will be ran
else:
    newdir=f"{root_dir}/model_runs/gtsm/{case_name}/{model_config}"
spwdir="/projects/0/einf2224/paper1/data/gtsm/meteo_forcing/spiderwebs"

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
## Copy GTSM files to each model folder
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# copy template files to newdir
print("copying ",templatedir," to ",newdir)
copy_tree(templatedir,newdir)#,symlinks=False,ignore=None)
    
# copy static model files to newdir
copy_tree(modelfilesdir, newdir)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
## Modify template GTSM files according to Case Study and Model Configuration
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# define settings based on meteorological forcing
if meteo_forcing=="ERA5":
    shutil.copy2(f'{meteodir}/ERA5_4GTSM_u10_{case_name}.nc',f'{newdir}/ERA5_4GTSM_u10_{case_name}.nc')
    shutil.copy2(f'{meteodir}/ERA5_4GTSM_v10_{case_name}.nc',f'{newdir}/ERA5_4GTSM_v10_{case_name}.nc')
    shutil.copy2(f'{meteodir}/ERA5_4GTSM_msl_{case_name}.nc',f'{newdir}/ERA5_4GTSM_msl_{case_name}.nc')
    ext_file='gtsm_fine_ERA5.ext.template'
    keywords_EXT={'METEOFILE_ERA5_WX':f'ERA5_4GTSM_u10_{case_name}.nc', 'METEOFILE_ERA5_WY':f'ERA5_4GTSM_v10_{case_name}.nc', 'METEOFILE_ERA5_P':f'ERA5_4GTSM_msl_{case_name}.nc'}
elif meteo_forcing=="ERA5-Holland":
    # copy ERA5 files to the model folder
    shutil.copy2(f'{meteodir}/ERA5_4GTSM_u10_{case_name}.nc',f'{newdir}/ERA5_4GTSM_u10_{case_name}.nc')
    shutil.copy2(f'{meteodir}/ERA5_4GTSM_v10_{case_name}.nc',f'{newdir}/ERA5_4GTSM_v10_{case_name}.nc')
    shutil.copy2(f'{meteodir}/ERA5_4GTSM_msl_{case_name}.nc',f'{newdir}/ERA5_4GTSM_msl_{case_name}.nc')
    shutil.copy2(f'{spwdir}/{case_name}.spw',f'{newdir}/{case_name}.spw')
    ext_file='gtsm_fine_ERA5-Holland.ext.template'
    keywords_EXT={'METEOFILE_ERA5_WX':f'ERA5_4GTSM_u10_{case_name}.nc', 'METEOFILE_ERA5_WY':f'ERA5_4GTSM_v10_{case_name}.nc', 'METEOFILE_ERA5_P':f'ERA5_4GTSM_msl_{case_name}.nc','HOLLAND_SPW':f'{case_name}.spw'}
else:
    print('EXTERNAL FORCING FILE NOT DEFINED!')

# define settings based on model configuration
#if model_config=="TR":
if model_config == "TR" or model_config == "RC":
    #hisinterval="600." # 172800.  777600."
    hisinterval=600. # 172800.  777600."
else:
    #hisinterval="3600."#  172800.  777600."
    hisinterval=3600. #  172800.  777600."

if model_config=="OR":
    shutil.copy2(f"{root_dir}/model_configs_setups/OR_refinement/observation_locations_snapped_1p25eu/selected_output_OR_" + str(case_name) + "_snapped_1p25eu_unique_obs.xyn",f'{newdir}/selected_output_OR_' + str(case_name) + '_snapped_1p25eu_unique_obs.xyn')
    obsfile=f"selected_output_OR_{case_name}_snapped_1p25eu_unique_obs.xyn"
    
#elif model_config=="IB":
elif model_config == "IB" or model_config == "RC":
    #obsfile=f"{newdir}/{case_name}_obs.xyn"
    obsfile=f"{case_name}_obs.xyn"
    
else:
    obsfile="selected_output_new_unique_noreg.xyn"

# Map file saving depending on spinup times
tmap_start = int(tspinup) * 24 *  3600                # tspinup is in days. Multiply by 3600 to have seconds
tmap_stop = (int(tstop) + int(tspinup)*24) * 3600     # tstop is in hours. Multiply by 24 * 3600 to have seconds
mapinterval = f"{hisinterval} {tmap_start}. {tmap_stop}."

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
## Modify template GTSM files according to Case Study and Model Configuration
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

## Modify model config file
#---------------------------
keywords_MDU={'REFDATE':tstart_spinup_str,'TSTART':str(0),'TSTOP':str(int(tstop) + int(tspinup)*24), 'OBSFILE':obsfile , 'HISINT':f'{hisinterval}', 'MAPINT':mapinterval} 
templates.replace_all(os.path.join(newdir,"gtsm_fine.mdu.template"), os.path.join(newdir,"gtsm_fine.mdu"),keywords_MDU,'%')


mdu_template_files=glob.glob(os.path.join(newdir,"gtsm_fine_00*.mdu.template"))
for mdu_template_file in mdu_template_files:
    # Construct the output file name with the .mdu extension
    mdu_file = os.path.splitext(mdu_template_file)[0] #+ ".mdu"
    # Replace the keywords in the input file and write to the output file
    templates.replace_all(os.path.join(newdir,mdu_template_file), os.path.join(newdir,mdu_file), keywords_MDU, '%')

## Modify external forcings file
#--------------------------------
templates.replace_all(os.path.join(newdir,ext_file),os.path.join(newdir,'gtsm_fine.ext'),keywords_EXT,'%') 
