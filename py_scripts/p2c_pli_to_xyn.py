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
import glob


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

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------
## Conversion from .pli file from the local model to the observations .xyn file for the global model
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# Open global grid file
file_net = f'{case_dir}/BS/output/gtsm_fine_0*_map.nc'        # Ideally _net.nc files could be used for this
print('FILE NET:', file_net)
crs_net = 'EPSG:4326'
data_xr = dfmt.open_partitioned_dataset(file_net)

# Obtain the coordinates at the face of the grid cells
#face_coords_np = data_xr.grid.face_coordinates
#tree_nest1 = KDTree(face_coords_np)
face_coords_pd = pd.DataFrame(dict(x=data_xr.FlowElemContour_x.mean(dim='nFlowElemContourPts'),y=data_xr.FlowElemContour_y.mean(dim='nFlowElemContourPts')))
tree_nest1 = KDTree(face_coords_pd)


#get and plot pli coordinates
#file_pli_list = [Path(f'{model_dir}/local/{case_name}.pli'),]

file_pli_list = []

# Add all files ending with '.pli' in the specified folder
folder_path = Path(f'{model_dir}/local/')
file_pli_list.extend(folder_path.glob('*.pli'))

''' 
for file_pli in file_pli_list:
    polyfile_object = hcdfm.PolyFile(file_pli)
    data_pol_pd_list = [dfmt.pointlike_to_DataFrame(polyobj) for polyobj in polyfile_object.objects]
    data_pol_pd = pd.concat(data_pol_pd_list)
    
    #get and plot unique cell center coordinates
    plicoords_distance1, plicoords_cellidx = tree_nest1.query(data_pol_pd,k=4) #TODO: do on spherical globe (like gtsm obs snapping procedure)
    cellidx_uniq = np.unique(plicoords_cellidx)
    cellcoords = face_coords_np[cellidx_uniq,:]
    #ax.plot(cellcoords[:,0],cellcoords[:,1],'x',label=f'{file_pli.name}_cellcenters')
    maxnumlen = max(4, len(str(len(cellcoords))))
    pli_name = os.path.splitext(file_pli.name)[0]
    cellcoords_names = [f'nestpoint_{pli_name}_{x+1:0{maxnumlen}d}' for x in range(len(cellcoords))]
    
    #write nesting obspoints to file
    basename = file_pli.name.replace('.pli','')
    #file_obs = os.path.join(global_dir,f'{case_name}_obs.xyn')
    file_obs = os.path.join(global_dir,f'{basename}_obs.xyn')
    # generate xyn file #TODO: make more convenient to initialize
    xynpoints = [hcdfm.XYNPoint(x=x,y=y,n=n) for x,y,n in zip(cellcoords[:,0], cellcoords[:,1], cellcoords_names)]
    xynmodel = hcdfm.XYNModel(points=xynpoints)
    xynmodel.save(file_obs)
    #print('xynmodel:', xynmodel)
    #xynmodel.to_csv(file_obs,sep='\t',index=False,header=False, float_format='%11.6f') 
'''    


for file_pli in file_pli_list:
    polyfile_object = hcdfm.PolyFile(file_pli)
    data_pol_pd_list = [dfmt.pointlike_to_DataFrame(polyobj) for polyobj in polyfile_object.objects]
    data_pol_pd = pd.concat(data_pol_pd_list)
    
    #get and plot unique cell center coordinates
    plicoords_distance1, plicoords_cellidx = tree_nest1.query(data_pol_pd,k=4) #TODO: do on spherical globe (like gtsm obs snapping procedure)
    cellidx_uniq = np.unique(plicoords_cellidx)
    cellcoords = face_coords_pd.iloc[cellidx_uniq]
    cellcoords = cellcoords.reset_index() #revert from face numbers to 0-based, prevents SettingWithCopyWarning
    maxnumlen = cellcoords.index.astype(str).str.len().max()
    pli_name = os.path.splitext(file_pli.name)[0]
    cellcoords['name'] = pd.Series(cellcoords.index).apply(lambda x: f'nestpoint_{pli_name}_{x+1:0{maxnumlen}d}')
    cellcoords=cellcoords.drop('index', axis=1)
    
    #write nesting obspoints to file
    file_obs = os.path.join(global_dir,f'{case_name}_obs.xyn')
    cellcoords.to_csv(file_obs,sep='\t',index=False,header=False, float_format='%11.6f', mode='a') 

