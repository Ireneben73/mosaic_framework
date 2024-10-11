#import matplotlib.pyplot as plt
#import matplotlib.colors as colors
#import matplotlib.patches as patches
#import cartopy.crs as ccrs
#import cartopy.feature as cfeature
import numpy as np
import xarray as xr

import dfm_tools as dfmt
from scipy.interpolate import griddata


#------------------------------------------------------------------------------------------------------------------------------------------------------------------------
## Directories
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------

model_runs_dir="/projects/0/einf2224/paper1/scripts/model_runs/gtsm"

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------
## Functions
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def load_case(case, model_config):
    if model_config == "N1" or model_config == "N2" or model_config == "N3":
        gtsm_his = xr.open_dataset(f'{model_runs_dir}/{case}/{model_config}/local/output/gtsm_fine_local_0000_his.nc').load()
        gtsm_map = dfmt.open_partitioned_dataset(f'{model_runs_dir}/{case}/{model_config}/local/output/gtsm_fine_local_00*_map.nc')    
        gtsm_his_clipped = gtsm_his
        gtsm_map_clipped = gtsm_map    
    else:
        gtsm_his = xr.open_dataset(f'{model_runs_dir}/{case}/{model_config}/output/gtsm_fine_0000_his.nc').load()
        gtsm_map = dfmt.open_partitioned_dataset(f'{model_runs_dir}/{case}/{model_config}/output/gtsm_fine_00*_map.nc')       
        
        # clip per study area
        condition_his = (
            (gtsm_his['FlowElem_xcc'] >= min_lon) &
            (gtsm_his['FlowElem_xcc'] <= max_lon) &
            (gtsm_his['FlowElem_ycc'] >= min_lat) &
            (gtsm_his['FlowElem_ycc'] <= max_lat)
        )
        
        condition_map = (
            (gtsm_map['FlowElem_xcc'] >= min_lon) &
            (gtsm_map['FlowElem_xcc'] <= max_lon) &
            (gtsm_map['FlowElem_ycc'] >= min_lat) &
            (gtsm_map['FlowElem_ycc'] <= max_lat)
        ).compute()
        
        # Clip the dataset based on the condition
        gtsm_his_clipped = gtsm_his.where(condition_his, drop=True)
        gtsm_map_clipped = gtsm_map.where(condition_map, drop=True)

       
    # obtain the maximum waterlevel
    gtsm_his_max=gtsm_his_clipped.waterlevel.max(dim='time')
    gtsm_map_max=gtsm_map_clipped.s1.max(dim='time')

    # remove dry cells by masking stations/cells that have the maximum waterlevel equal to the bedlevel
    gtsm_his_msk = gtsm_his_max.where(gtsm_his_max != gtsm_his_clipped.bedlevel, drop=True)
    mask_bl = (gtsm_map_max != gtsm_map_clipped.FlowElem_bl).compute()
    gtsm_map_msk = gtsm_map_max.where(mask_bl, drop=True)     
    #gtsm_map_msk = gtsm_map_max.where(gtsm_map_max != gtsm_map_clipped.FlowElem_bl, drop=True) 
    print('Local model masked', flush=True)
    
    # If model_config is not 'G1', subtract gtsm_map for 'G1'
    if model_config != 'G1':
        #gtsm_map_bs = xr.open_dataset(f'{model_runs_dir}/{case}/BS/output/gtsm_map_max.nc')#.load()
        gtsm_map_bs = dfmt.open_partitioned_dataset(f'{model_runs_dir}/{case}/BS/output/gtsm_fine_00*_map.nc')   
        
        if model_config == "N1" or model_config == "N2" or model_config == "N3":
            # clip BS
            print('gtsm_map_msk:', gtsm_map_msk)
            print('gtsm_map_msk X min:', gtsm_map_msk.FlowElem_xcc.min().values)
            print('gtsm_map_msk X max:', gtsm_map_msk.FlowElem_xcc.max().values)
            print('gtsm_map_msk Y min:', gtsm_map_msk.FlowElem_ycc.min().values)
            print('gtsm_map_msk Y min:', gtsm_map_msk.FlowElem_ycc.max().values)
            
            condition_map_bs = (
                (gtsm_map_bs['FlowElem_xcc'] >= gtsm_map_msk.FlowElem_xcc.min().values) &
                (gtsm_map_bs['FlowElem_xcc'] <= gtsm_map_msk.FlowElem_xcc.max().values) &
                (gtsm_map_bs['FlowElem_ycc'] >= gtsm_map_msk.FlowElem_ycc.min().values) &
                (gtsm_map_bs['FlowElem_ycc'] <= gtsm_map_msk.FlowElem_ycc.max().values)
            ).compute()
            gtsm_map_bs_clipped = gtsm_map_bs.where(condition_map_bs, drop=True)
            print('gtsm_map_bs_clipped:', gtsm_map_bs_clipped, flush=True)
            print('Global model clipped', flush=True)
            # calculate the maximum s1 over time
            gtsm_map_bs_max=gtsm_map_bs_clipped.s1.max(dim='time')
            
            # mask dry cells!
            mask_bl_bs = (gtsm_map_bs_max != gtsm_map_bs_clipped.FlowElem_bl).compute()
            gtsm_map_bs_msk = gtsm_map_bs_max.where(mask_bl_bs, drop=True)
            print('Global model masked', flush=True)
            print('gtsm_map_bs S1:', gtsm_map_bs.s1, flush=True)
            
            # interpolate to the refined grid
            source_coords = np.column_stack((gtsm_map_bs_msk.FlowElem_xcc.values, gtsm_map_bs_msk.FlowElem_ycc.values))
            source_data = gtsm_map_bs_msk.values#.reshape((len(gtsm_map_bs.time), -1))
            print('source_coords:', source_coords, flush=True)
            print('source_data:', source_data, flush=True)
            target_coords = np.column_stack((gtsm_map_msk.FlowElem_xcc.values, gtsm_map_msk.FlowElem_ycc.values))
            print('target_coords:', target_coords, flush=True)
            
            interpolated_data = griddata(source_coords, source_data, target_coords, method='linear')
            print('Global model interpolated', flush=True)
            # make a data array out of the interpolated data
            gtsm_map_bs_max_interp = xr.DataArray(
                interpolated_data,
                dims=('nNetElem',),
                coords={'nNetElem': gtsm_map_msk.nNetElem,
                        'FlowElem_xcc': (('nNetElem',), gtsm_map_msk.FlowElem_xcc.values),
                        'FlowElem_ycc': (('nNetElem',), gtsm_map_msk.FlowElem_ycc.values)}
            )
            

            print('interpolated_data_interp:', gtsm_map_bs_max_interp)

            gtsm_map_bs_max_interp_ds = gtsm_map_bs_max_interp.to_dataset(name='s1')
            gtsm_map = gtsm_map_msk - gtsm_map_bs_max_interp_ds

        else:
            # clip BS map to have same region as other model config
            gtsm_map_bs_clipped = gtsm_map_bs.where(condition_map, drop=True)
            # calculate max water level
            gtsm_map_bs_max=gtsm_map_bs_clipped.s1.max(dim='time')
            # remove dry cells
            gtsm_map_bs_msk = gtsm_map_bs_max.where(mask_bl, drop=True) 
            # calculate the difference between the gtsm output of the model config and the gtsm output of BS        
            gtsm_map = gtsm_map_msk - gtsm_map_bs_msk                                                 
   
    else:
        #gtsm_map = gtsm_map_wl_msk.waterlevel
        gtsm_map = gtsm_map_msk

    if model_config == "N3":    
        return gtsm_his_msk, gtsm_map, gtsm_map_msk
    else:
        return gtsm_his_msk, gtsm_map
    

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------
## Postprocess GTSM output data
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------

cases = ['irma', 'haiyan', 'xynthia']

study_areas = {
    'irma': {'min_lon': -85.6, 'max_lon': -79.4, 'min_lat': 23, 'max_lat': 34},
    'haiyan': {'min_lon': 124, 'max_lon': 128, 'min_lat': 8, 'max_lat': 12},  # Define actual values
    'xynthia': {'min_lon': -7, 'max_lon': 1, 'min_lat': 43.0, 'max_lat': 51.5},  # Define actual values
}

model_configs = ['G1', 'G2', 'G3', 'N1', 'N2', 'N3']

# loop over each case study
for i, case in enumerate(cases):

    # Get study area boundaries
    min_lon = study_areas[case]['min_lon']
    max_lon = study_areas[case]['max_lon']
    min_lat = study_areas[case]['min_lat']
    max_lat = study_areas[case]['max_lat']
    
    # loop over each model configuration
    for j, model_config in enumerate(model_configs):
        print('MODEL CONFIG:', model_config)
        
        # Save the datasets
        if model_config == 'N1' or model_config == "N2":
            his, gtsm_map = load_case(case, model_config)
            his.to_netcdf(f'{model_runs_dir}/{case}/{model_config}/local/output/gtsm_his_max.nc')
            gtsm_map.to_netcdf(f'{model_runs_dir}/{case}/{model_config}/local/output/gtsm_map_max.nc')
        elif model_config == 'N3':
            his, gtsm_map, gtsm_map_msk = load_case(case, model_config)
            his.to_netcdf(f'{model_runs_dir}/{case}/{model_config}/local/output/gtsm_his_max.nc')
            gtsm_map.to_netcdf(f'{model_runs_dir}/{case}/{model_config}/local/output/gtsm_map_max.nc')
            gtsm_map_msk.to_netcdf(f'{model_runs_dir}/{case}/{model_config}/local/output/gtsm_map_max_absolute.nc')
        else:
            his, gtsm_map = load_case(case, model_config)
            his.to_netcdf(f'{model_runs_dir}/{case}/{model_config}/output/gtsm_his_max.nc')
            gtsm_map.to_netcdf(f'{model_runs_dir}/{case}/{model_config}/output/gtsm_map_max.nc')
        
