import sys
import os
from os.path import join

import numpy as np
import xarray as xr
import pandas as pd
import netCDF4 as nc

from hydromt_sfincs import SfincsModel, utils
import hydromt

#--------------------------------------------------------------------------------------------------------------------------------------------------------------
## POSTPROCESS SFINCS
#--------------------------------------------------------------------------------------------------------------------------------------------------------------


sfincs_root = sys.argv[1]
model_config = sys.argv[2]
sfincs_templatedir = sys.argv[3] 
sfincs_model_runsdir = sys.argv[4]
case = sys.argv[5]

print('sfincs_root:', sfincs_root)

os.chdir(sfincs_root)

mod = SfincsModel(
    data_libs=[f'{sfincs_templatedir}/data_catalog.yml'],
    root=model_config,
    mode="r",
)

mod.read_results()

# get max water levels
#zsmax = mod.results["hmax"]
zsmax = mod.results["zsmax"]
# compute the maximum over all time steps
zsmax = zsmax.max(dim='timemax')

# mask minimum flood depth
hmin = 0.05

# GSWO dataset used to mask permanent water 
# permanent water where water occurence > 5%
#gswo = mod.data_catalog.get_rasterdataset("gswo", geom=mod.region, buffer=10)
#gswo_mask = gswo.raster.reproject_like(mod.grid, method="max") <= 5
# get overland flood depth with GSWO and set minimum flood depth
zsmax_fld = zsmax#.where(gswo_mask).where(zsmax > hmin)                                          # TO DO: I have changed this!!
gdf_osm = mod.data_catalog.get_geodataframe("osm_landareas", geom=mod.region)

# downscale the floodmap to the submodel predefined grid (based on original fabdem)
#depfile = join(sfincs_root + "/" + model_config, "subgrid", "dep_subgrid.tif")
depfile = join(sfincs_root + "/" + model_config, "gis", "dep.tif")
da_dep = mod.data_catalog.get_rasterdataset(depfile)
hmax = utils.downscale_floodmap(
    zsmax=zsmax_fld,
    dep=da_dep,
    #dep=dep_subgrid,
    hmin=hmin,
    gdf_mask=gdf_osm,
    #floodmap_fn=join(sfincs_root, "submodel_" + sfincs_submodel + "_maxfloodmap.tif") 
)

#hmax = hmax.where(gswo_mask).where(hmax > hmin)       
# Create a new NetCDF file
#outfile = join(sfincs_model_runsdir, f"{case}/{model_config}/hmax.nc") 
outfile = join(sfincs_root + "/" + model_config, f"hmax.nc") 
print('OUTFILE:', outfile)
variable_name="flood_depth"
hmax_dataset=hmax.to_dataset(name=variable_name)
hmax_reproj=hmax_dataset.raster.reproject('EPSG:4326')
print('hmax_dataset:', hmax_reproj)
#hmax_stormid=hmax_stormid.drop('band')
encoding={variable_name:{'dtype': 'int16', 'scale_factor': 0.001, 'complevel': 3, 'zlib': True}}

#print('hmax_stormid:', hmax_stormid)
hmax_reproj.to_netcdf(outfile, encoding=encoding, mode='a')