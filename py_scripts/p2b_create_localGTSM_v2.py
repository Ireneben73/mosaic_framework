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
import geopandas as gpd

# input
model_dir = sys.argv[1]
case_name = sys.argv[2]
bbox = sys.argv[3]
print('bbox:', bbox)
print('case_name:', case_name)

dir_output = f'{model_dir}/local'
path_style = 'unix' # windows / unix
overwrite = False # used for downloading of forcing data. Always set to True when changing the domain
is_geographic = True
crs = 'EPSG:4326'

# domain and resolution
bbox_refinement=sys.argv[3].split(',')
print('bbox_refinement:', bbox_refinement[0])
lon_min, lon_max, lat_min, lat_max = float(bbox_refinement[0]), float(bbox_refinement[1]), float(bbox_refinement[2]), float(bbox_refinement[3])
dxy = 0.25 #this is a bit more than the 2.5km grid resolution that GTSM has near the coasts Used for Irma and Haiyan. For Xynthia testing lower as the global model is more refined there..

#dates that are a dummy in this case
date_min = '2022-11-01'
date_max = '2022-11-02'
ref_date = '2022-01-01'


# make dirs and list all files
os.makedirs(dir_output, exist_ok=True)
os.listdir(dir_output)

#generate spherical regular grid
mk_object = dfmt.make_basegrid(lon_min, lon_max, lat_min, lat_max, dx=dxy, dy=dxy, crs=crs)

# generate plifile from grid extent and coastlines
bnd_gdf = dfmt.generate_bndpli_cutland(mk=mk_object, res='h', buffer=0.01)
    
for i, row in bnd_gdf.iterrows():
    print('I:', i)
    
    #bnd_gdf_i = gpd.GeoDataFrame((bnd_gdf.iloc[[i]])#.reset_index(drop=True))
    bnd_gdf_i = gpd.GeoDataFrame([row])
    bnd_gdf_i.at[i, 'name'] = f'{case_name}_bnd_{i}'
    bnd_gdf_i.index = [0]

    bnd_gdf_interp = dfmt.interpolate_bndpli(bnd_gdf_i, res=0.03)

    poly_file = os.path.join(dir_output, f'{case_name}_{i}.pli')
    pli_polyfile = dfmt.geodataframe_to_PolyFile(bnd_gdf_interp)
    pli_polyfile.save(poly_file)


# bathymetry to define the grid with
bathymetry_dir = '/projects/0/einf2224/paper1/data/gtsm/bathymetry'
file_gebco = f'{bathymetry_dir}/GEBCO_2023.nc' 
data_bathy = xr.open_dataset(file_gebco)
#data_bathy_sel = data_bathy.sel(lon=slice(lon_min - 1, lon_max + 1), lat=slice(lat_min - 1, lat_max + 1)).elevation
data_bathy_sel_grid = data_bathy.sel(lon=slice(lon_min + 0.3, lon_max - 0.3), lat=slice(lat_min + 0.3, lat_max - 0.3)).elevation # 0.3 works for Xynthia but not for Irma
data_bathy_sel = data_bathy.sel(lon=slice(lon_min - 1, lon_max + 1), lat=slice(lat_min - 1, lat_max + 1)).elevation

#refine grid
min_edge_size = 450 #in meters, GEBCO 2023 has moreless that resolution
dfmt.refine_basegrid(mk=mk_object, data_bathy_sel=data_bathy_sel_grid, min_edge_size=min_edge_size)      

# remove land with GSHHS coastlines
#dfmt.meshkernel_delete_withcoastlines(mk=mk_object, res='h', min_area = 70)                      # TO DO - remove this later on!

# merge circumcentres
mk_object.mesh2d_delete_small_flow_edges_and_small_triangles(0.1, 10.0)

#convert to xugrid, interpolate z-values and write to netcdf
xu_grid_uds = dfmt.meshkernel_to_UgridDataset(mk=mk_object, crs=crs)

#interp bathy
data_bathy_interp = data_bathy_sel.interp(lon=xu_grid_uds.obj.mesh2d_node_x, lat=xu_grid_uds.obj.mesh2d_node_y).reset_coords(['lat','lon'])
xu_grid_uds['mesh2d_node_z'] = data_bathy_interp.elevation.clip(max=10)

#write xugrid grid to netcdf
netfile  = os.path.join(dir_output, f'{case_name}_net.nc')
xu_grid_uds.ugrid.to_netcdf(netfile)
