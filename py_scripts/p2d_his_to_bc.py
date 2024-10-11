import os
import xarray as xr
from pathlib import Path
import pandas as pd
from scipy.spatial import KDTree
import numpy as np
import matplotlib.pyplot as plt
plt.close('all')
import contextily as ctx
import dfm_tools as dfmt
import hydrolib.core.dflowfm as hcdfm
import sys

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
## Input
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------

case_name = sys.argv[3]

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
## Directories
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------

model_dir = sys.argv[2]
case_dir = sys.argv[1]
global_dir = f'{model_dir}/global'
local_dir = f'{model_dir}/local'

#file_pli_list = [Path(f'{model_dir}/local/{case_name}.pli'),]
file_pli_list = []
# Add all files ending with '.pli' in the specified folder
folder_path = Path(f'{model_dir}/local/')
file_pli_list.extend(folder_path.glob('*.pli'))
print('file_pli_list:', file_pli_list)

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
## Converting the his.nc waterlevel data from the global model into the .bc (boundary conditions) data for the local model
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------

for file_pli in file_pli_list:
    print('file_pli:', file_pli)
    kdtree_k = 4
    file_his = f'{global_dir}/output/gtsm_fine_0000_his.nc'
    data_xr_his = xr.open_mfdataset(file_his,preprocess=dfmt.preprocess_hisnc)
    data_xr_his_selvars = data_xr_his[['waterlevel']]#,'velocity_magnitude']]
    #data_xr_his_selvars = data_xr_his[['waterlevel','velocity_magnitude']]
    
    
    data_interp = dfmt.interp_hisnc_to_plipoints(data_xr_his=data_xr_his_selvars,file_pli=file_pli,kdtree_k=kdtree_k)

    #if npoints is not None:
    #    data_interp = data_interp.isel(node=range(npoints))
    
    rename_dict = {'waterlevel':'waterlevelbnd'}#
    data_interp = data_interp.rename(rename_dict)
    
    ForcingModel_object = dfmt.plipointsDataset_to_ForcingModel(plipointsDataset=data_interp)
    file_bc_out = file_pli.name.replace('.pli','.bc')
    ForcingModel_object.save(filepath=local_dir + '/' + file_bc_out) #TODO REPORT: writing itself is fast, but takes quite a while to start writing (probably because of conversion)
    print('done')


    '''
    rename_dict = {'waterlevel':'waterlevelbnd'}#
    data_interp=data_interp.rename(rename_dict)
    
    
 
    ForcingModel_object = dfmt.plipointsDataset_to_ForcingModel(plipointsDataset=data_interp)
    file_bc_out=f'{local_dir}/{case_name}_waterlevel_global.bc'
    
    print('saving bc file')
    ForcingModel_object.save(filepath=file_bc_out) 
    print('done')
    
    
    data_xr_his_selvars_wl = data_xr_his[['waterlevel']]#,'velocity_magnitude']]
    data_xr_his_selvars_vl = data_xr_his[['velocity_magnitude']]#,'velocity_magnitude']]
    data_interp_wl = dfmt.interp_hisnc_to_plipoints(data_xr_his=data_xr_his_selvars_wl,file_pli=file_pli,kdtree_k=kdtree_k)
    data_interp_vl = dfmt.interp_hisnc_to_plipoints(data_xr_his=data_xr_his_selvars_vl,file_pli=file_pli,kdtree_k=kdtree_k)

    rename_dict_wl = {'waterlevel':'waterlevelbnd'}#,
    rename_dict_vl = {'velocity_magnitude':'velocitybnd'}#,

    data_interp_wl=data_interp_wl.rename(rename_dict_wl)
    ForcingModel_object_wl = dfmt.plipointsDataset_to_ForcingModel(plipointsDataset=data_interp_wl)
    file_bc_out_wl=f'{local_dir}/{case_name}_waterlevel_global.bc'
    print('saving bc file')
    ForcingModel_object_wl.save(filepath=file_bc_out_wl) 
    print('done')
    
    data_interp_vl=data_interp_vl.rename(rename_dict_vl)
    ForcingModel_object_vl = dfmt.plipointsDataset_to_ForcingModel(plipointsDataset=data_interp_vl)
    file_bc_out_vl=f'{local_dir}/{case_name}_velocity_global.bc'
    print('saving bc file')
    ForcingModel_object_vl.save(filepath=file_bc_out_vl) 
    print('done')
    

    '''