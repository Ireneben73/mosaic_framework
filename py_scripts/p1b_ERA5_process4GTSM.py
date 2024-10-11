# -*- coding: utf-8 -*-
"""
Created on Wed Jun 29 13:36:11 2022

@author: ibe202
"""

from netCDF4 import num2date, Dataset, date2num
from shutil import copy
from os.path import split, join
import numpy as np
#import xarray as xr
#from datetime import datetime, timedelta
import datetime as dt
from p1b_ERA5_maps import EraMaps
import pandas as pd
import xarray as xr
import sys


# Case study
case_name=sys.argv[1]

# Directory where the data will be downloaded at
root_dir="/projects/0/einf2224/paper1/data/gtsm/meteo_forcing/ERA5"

# Input ERA5 file downloaded from CDS
input_file = f'{root_dir}/ERA5_{case_name}.nc'
maps=EraMaps(input_file,'NETCDF4','r')

var_ncvarnames = ('u10', 'v10', 'msl')

for var_ncvarname in var_ncvarnames:
    # Output ERA5 file after being processed
    dest = EraMaps(f'{root_dir}/ERA5_4GTSM_{var_ncvarname}_{case_name}.nc', 'NETCDF4', 'w')
    
    # Dates
    reftime=dt.datetime(1900,1,1) #imposed  
    #date_start = dt.datetime(2017,9,1,0,0)  # TO DO
    era5=xr.open_dataset(input_file)
    print('times:', era5.time)
    start_time_value = era5.time.values[0]
    date_start = dt.datetime.utcfromtimestamp(start_time_value.astype(int) * 1e-9)  
    end_time_value = era5.time.values[-1]  
    print('end_time_value:', end_time_value)
    date_end = dt.datetime.utcfromtimestamp(end_time_value.astype(int) * 1e-9) 
    print('date_start:', date_start) 
    print('date_end:', date_end)
    tstep_h=1
    dates_fileoutreal = pd.date_range(start=date_start, end=date_end, freq='%iH'%(tstep_h))
    
    #%%
    lon_varname= 'longitude'
    lat_varname= 'latitude'
    lon_dimname = maps._ds.variables[lon_varname].dimensions[0]
    lat_dimname = maps._ds.variables[lat_varname].dimensions[0]
    lon_vals = maps._ds.variables['longitude'][:]
    lat_vals = maps._ds.variables['latitude'][:]
    
    #create new dest dimensions (without lat/lon/time)
    dest.copyGlobalDataFrom(maps,skipDims=[lat_dimname,lon_dimname,'time'])
    
    # create correct new dimension for longitude (with overlap on edges)
    #x=maps._ds.variables[lon_varname][:]
    nx=len(lon_vals)
    part1=(lon_vals>178) #move 180:360 part to -180:0 so field now runs from longitute -180 to 180
    part2=(lon_vals<182) #take a bit of overlap to avoid interpolation issues at edge
    lon_vals_new=np.hstack((lon_vals[part1]-360,lon_vals[part2]))
    nx=len(lon_vals_new)
    
    dest.createDim(lon_dimname,nx) #def createDim(self,dim_name,value)
    longitude_type=maps.getVariableType(lon_varname)
    new_longitude=dest.createVariable(lon_varname,longitude_type,(lon_dimname)) #def createVariable(self,variable_name,variable_type,variable_dims=())
    dest.copyVariableAttributesFrom(maps,lon_varname)
    dest.createVariableAttribute(lon_varname,'standard_name','longitude') #overwrite standard name
    new_longitude[:]=lon_vals_new;
    #new_longitude[:]=lon_vals;
    
    # create dimension for latitude
    nx=len(lat_vals)
    dest.createDim(lat_dimname,nx) #def createDim(self,dim_name,value)
    latitude_type=maps.getVariableType(lat_varname)
    new_latitude=dest.createVariable(lat_varname,latitude_type,(lat_dimname)) #def createVariable(self,variable_name,variable_type,variable_dims=())
    dest.copyVariableAttributesFrom(maps,lat_varname)
    dest.createVariableAttribute(lat_varname,'standard_name','latitude') #overwrite standard name
    new_latitude[:]=lat_vals;
    
    #make time UNLIMITED. don't copy time!
    dest._ds.createDimension('time',None)
    tim_type=maps.getVariableType('time')
    dest.createVariable('time',tim_type,('time'))
    dest.copyVariableAttributesFrom(maps,'time')
    if (dest._ds.variables['time'].calendar == '360_day') or (dest._ds.variables['time'].calendar == '365_day'):
        dest._ds.variables['time'].calendar = 'standard' #overwrite for 360_day calendar in netcdf time variable
    #reformat timeunit to standard format
    t_reftime=maps.getReferenceTime()
    tunit_unit = dest._ds.variables['time'].units.split(' ')[0]
    dest._ds.variables['time'].units = '%s since %s'%(tunit_unit, t_reftime.strftime('%Y-%m-%d %H:%M:%S'))
    
    #create variables
    #var_ncvarname = 'sp'
    var_ncvarname = var_ncvarname #'u10' # 'u10', 'v10', 'msl'
    var_standard_name = 'eastward_wind' #  'eastward_wind', 'northward_wind', 'air_pressure'
    param_type=maps.getVariableType(var_ncvarname)
    maps_var_attrlist = maps._ds.variables[var_ncvarname].ncattrs()
    dest.createVariable(var_ncvarname,param_type,('time',lat_dimname,lon_dimname))
    dest.copyVariableAttributesFrom(maps,var_ncvarname)
    dest.createVariableAttribute(var_ncvarname,'standard_name',var_standard_name)
    dest.createVariableAttribute(var_ncvarname,'coordinates','lon lat')
    dest_var_attrlist = dest._ds.variables[var_ncvarname].ncattrs()
    
    #fill in data
    t=maps.getRelativeTimes()
    #print('t',t)
    t_reftime=maps.getReferenceTime() #datetime object
    for iT, filein_time in enumerate(t): #loop over timesteps in current input file
        var=maps._ds.variables[var_ncvarname][iT,:,:]
        nc_timevar = maps._ds.variables['time']
        if 'hours' in nc_timevar.units:
            filein_time_h = filein_time
        elif 'days' in nc_timevar.units:
            filein_time_h = filein_time*24
        elif 'minutes' in nc_timevar.units:
            filein_time_h = filein_time/60
        elif 'seconds' in nc_timevar.units:
            filein_time_h = filein_time/3600
        else:
            err_line = 'ERROR: no known time unit (days/hours/minutes/seconds since...)'
            file_err.write('%s\n'%(err_line))
            raise Exception(err_line)
        #print('filein_time_h:', filein_time_h)
    
        datei = num2date(filein_time,units=nc_timevar.units,calendar=nc_timevar.calendar)
        fileout_time_h = filein_time_h
        datei_all = []
        datei_all.append(datei)
        #print('datei_all',datei_all)
        #print('datei', datei)
        #print('dates_fileoutreal', dates_fileoutreal)
        #if datei in dates_fileoutreal:
        tid_fileout = list(dates_fileoutreal).index(datei)
        #print('tid_fileout:', tid_fileout)
        #if iR==0: #fill in time array only for first variable
        dest.setNewRelativeTimes(reftime,[fileout_time_h],t_reftime,tid_fileout)
        #move 180:360 part to -180:0 so field now runs from longitute -180 to 180
        new_var=np.hstack((var[:,part1],var[:,part2]))
        dest._ds.variables[var_ncvarname][tid_fileout,:,:]=new_var
        #print(dest._ds.variables[var_ncvarname])
        
maps.close()