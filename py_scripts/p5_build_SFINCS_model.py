import sys
import geopandas as gpd
from hydromt_sfincs import SfincsModel
from hydromt.log import setuplog
import xarray as xr
import numpy as np
import geopandas as gpd
import pandas as pd
from datetime import datetime, timedelta


case=sys.argv[1]
model_config=sys.argv[2]
tref=sys.argv[3]
tstart=sys.argv[3]
tstop=sys.argv[4]

tstart_datetime = datetime.strptime(tstart, "%Y%m%d")
tend = tstart_datetime + timedelta(hours=(int(tstop))) 

# Format the end datetime object to the desired format
tstart_str =  tstart_datetime.strftime("%Y%m%d %H%M%S")
tend_str = tend.strftime("%Y%m%d %H%M%S")

event_bbox=[float(coord) for coord in sys.argv[5].split(',')]

sfincs_templatedir=sys.argv[6]
sfincs_model_runsdir=sys.argv[7]
gtsm_model_runsdir=sys.argv[8]
sfincsdata_dir=sys.argv[9]
temporary_dir=sys.argv[10]

path_to_yml=f'{sfincs_templatedir}/data_catalog.yml'

root = f'{temporary_dir}/{case}/{model_config}' 
print('ROOT:', root)
mod = SfincsModel(root, mode='w+', data_libs=path_to_yml)

mod.setup_grid_from_region(region = {'geom': f"{sfincsdata_dir}/{case}_region.geojson"}, res=200, rotated=False)

mod.setup_config(
    tref = tstart_str,
    tstart = tstart_str,
    tstop = tend_str,
    dtmaxout = 99999.0,
    dtout = 3600.0,
    dtwnd = 600.0,
    alpha = 0.5,
    zsini = 0.5,
    advection = 0, # before I had 0.0
    huthresh = 0.05,
)

#datasets_dep = [{"elevtn":f"fabdem_{case}", "zmin":-5}, {"elevtn": "gebco"}]
if case == 'xynthia': 
    datasets_dep = [{"elevtn":f"ign_dem_{case}", "zmin":-5}, {"elevtn": "gebco"}]
else:
    datasets_dep = [{"elevtn":f"fabdem_{case}", "zmin":-5}, {"elevtn": "gebco"}]

mod.setup_dep(datasets_dep = datasets_dep)

mod.setup_mask_active(
    zmin = -5,                    # minimum elevation for valid cells
    #exclude_mask = "osm_coastlines",
    #drop_area = 1, # drops areas that are smaller than 1km2
)

mod.setup_mask_bounds(
    btype = "waterlevel",
    zmax = -5,
)

datasets_rgh = [{"lulc": "vito"}]

mod.setup_subgrid(
    datasets_dep = datasets_dep,
    datasets_rgh=datasets_rgh,
    nr_subgrid_pixels=8, 
    write_dep_tif=True,
    write_man_tif=True,
)
 
mod.setup_cn_infiltration("gcn250", antecedent_moisture="avg")



## Total water levels (GTSM)
# Import GTSM
#if model_config == 'IB':
if model_config == "IB" or model_config == "N1" or model_config == "RC":
    gtsm_file=f'{gtsm_model_runsdir}/{case}/{model_config}/local/output/gtsm_fine_local_0000_his.nc' 
else:
    gtsm_file=f'{gtsm_model_runsdir}/{case}/{model_config}/output/gtsm_fine_0000_his.nc'
    
region_data = gpd.read_file(f"{sfincsdata_dir}/{case}_region.geojson")
gtsm = xr.open_dataset(gtsm_file)#.vector.clip_geom(region)#.load()

# Extract the bounds of the region geometry
region_geometry = region_data.geometry.values[0]
min_x, min_y, max_x, max_y = region_geometry.bounds

# Clip the gtsm dataset using boolean indexing
station_x = gtsm['station_x_coordinate']
station_y = gtsm['station_y_coordinate']
clipped_gtsm = gtsm.where((station_x > min_x) & (station_x < max_x) & (station_y > min_y) & (station_y < max_y), drop=True)

# Mask dry cells
max_waterlevel = clipped_gtsm.waterlevel.max(dim='time')
mask_bl = (max_waterlevel != clipped_gtsm.bedlevel)#.compute()  # we could do the masking for the max WL over time..
gtsm_msk = clipped_gtsm.where(mask_bl, drop=True)

# Optain the boundary point coordinates from GTSM
bnd = gpd.GeoDataFrame(
    index=np.atleast_1d(gtsm_msk['stations'].values),
    geometry=gpd.points_from_xy(
        np.atleast_1d(gtsm_msk['station_x_coordinate'].values), 
        np.atleast_1d(gtsm_msk['station_y_coordinate'].values)
    ),
    crs=4326
).to_crs(mod.crs)

# Create a pandas dataframe to create the water level forcing   
df_timeseries=pd.DataFrame(index=gtsm_msk.time, columns=bnd.index, data=gtsm_msk.waterlevel)
#print('df_timeseries:', df_timeseries)

mod.setup_waterlevel_forcing(
    timeseries=df_timeseries,
    locations=bnd,
    offset="dtu10mdt",
    merge=False,
)

mod.setup_observation_points(
    locations=f"{sfincsdata_dir}/obs_points_{case}.geojson", merge=True
)

mod._write_gis = True
mod.write()
