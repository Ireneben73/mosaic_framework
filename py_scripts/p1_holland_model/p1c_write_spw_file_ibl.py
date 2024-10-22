# -*- coding: utf-8 -*-
"""
Created on Wed Apr 08 14:10:05 2020
@author:    Job Dullaart
@institute: IVM - VU Amsterdam
"""

## IMPORT MODULES
import numpy as np
import pandas as pd
import os

## FUNCTION THAT WRITES THE SPIDERWEB FILE
def write_spw_file(filename,n_cols,n_rows,tc_radius,startdate,nodata_array_wind,nodata_array_pressure,time_out,windfield,winddir,Pdrop_mesh,rmaxslice,j,lon0,lat0, tspinup):
    name=os.path.splitext(filename)[0]
    #if storm == 1 and j == 1:
    if j == 1:
        ## WRITE INFORMATION TO TOP OF SPIDERWEB FILE
        print('number of timesteps' ,len(rmaxslice))
        f = open(str(name)+'.spw','a')
        f.write("FileVersion    = 1.03\n")
        f.write("filetype       = meteo_on_spiderweb_grid\n")
        f.write("NODATA_value   = -999.0\n")
        f.write("n_cols         = " + str(n_cols) + "\n")
        f.write("n_rows         = " + str(n_rows) + "\n")
        f.write("grid_unit      = degree\n")
        f.write("spw_radius     = " + str(int(tc_radius*1000)) + "\n")
        f.write("spw_merge_frac = 0.75\n") #f.write("spw_merge_frac = 0.333\n")
        f.write("spw_rad_unit   = m\n")
        f.write("n_quantity     = 3\n")
        f.write("quantity1      = wind_speed\n")
        f.write("quantity2      = wind_from_direction\n")
        f.write("quantity3      = p_drop\n")
        f.write("unit1          = m s-1\n")
        f.write("unit2          = degree\n")
        f.write("unit3          = Pa\n")
        
        ### EXPLANATION
        # We write zeros to Canada before and after the TC is active.
        # This coordinate is far away from any GTSM output location to make sure no forcing is applied
        # The TC is moved quickly from Canada to its starting position to make sure the 'zeros' are not interpolated spatially
        
        ## WRITE ZEROS TO CANADA AT T = 0.0
        f.write("TIME           = " + str(float(startdate.hour - int(tspinup)*24))+ " hours since "+str(startdate.date())+" 00:00:00 +00:00\n")
        if lon0 > 180:
            lon_out = np.around((lon0 - 360), decimals=2)
        else:
            lon_out = np.around(lon0, decimals=2)
        f.write("x_spw_eye      = " + str(lon_out) + "\n")
        f.write("y_spw_eye      = " + str(lat0) + "\n")
        f.write("p_drop_spw_eye = " + str(0) + "\n")
        for line in np.transpose(np.around(nodata_array_wind,decimals=2)):                                    # print windspeed
            for number in line:
                f.write("{:>9}".format(str(number)))
            f.write("\n")
        for line in np.transpose(np.around(nodata_array_wind,decimals=2)):                                    # print winddirection (0 degrees means wind comes from the north)
            for number in line:
                f.write("{:>9}".format(str(number)))
            f.write("\n")
        for line in np.transpose(np.around(nodata_array_pressure,decimals=2)):                                # print pressure drop
            for number in line:
                f.write("{:>9}".format(str(number)))
            f.write("\n")
        f.close()
        
        f = open(str(name)+'.spw','a')
        f.write("TIME           = " + str(float(startdate.hour - 24))+ " hours since "+str(startdate.date())+" 00:00:00 +00:00\n")
        if lon0 > 180:
            lon_out = np.around((lon0 - 360), decimals=2)
        else:
            lon_out = np.around(lon0, decimals=2)
        f.write("x_spw_eye      = " + str(lon_out) + "\n")
        f.write("y_spw_eye      = " + str(lat0) + "\n")
        f.write("p_drop_spw_eye = " + str(0) + "\n")
        for line in np.transpose(np.around(nodata_array_wind,decimals=2)):                                    # print windspeed
            for number in line:
                f.write("{:>9}".format(str(number)))
            f.write("\n")
        for line in np.transpose(np.around(nodata_array_wind,decimals=2)):                                    # print winddirection (0 degrees means wind comes from the north)
            for number in line:
                f.write("{:>9}".format(str(number)))
            f.write("\n")
        for line in np.transpose(np.around(nodata_array_pressure,decimals=2)):                                # print pressure drop
            for number in line:
                f.write("{:>9}".format(str(number)))
            f.write("\n")
        f.close()

    '''
    f = open(str(name)+'.spw','a')
    f.write("TIME           = " + str(float(startdate.hour))+ " hours since "+str(startdate.date())+" 00:00:00 +00:00\n")
    #f.write("TIME           = " + str(np.around((startdate.hour+time_out+1),decimals=5))+ " hours since "+str(startdate.date())+" 00:00:00 +00:00\n")
    #f.write("TIME           = " + str(np.around((startdate.hour+time_out),decimals=5))+ " hours since "+str(startdate.date())+" 00:00:00 +00:00\n")
    
    if lon0 > 180:
        lon_out = np.around((lon0 - 360), decimals=2)
    else:
        lon_out = np.around(lon0, decimals=2)
    
    f.write("x_spw_eye      = " + str(lon_out) + "\n")                                                       # print longitude
    f.write("y_spw_eye      = " + str(lat0) + "\n")                                                          # print latitude
    f.write("p_drop_spw_eye = " + str(np.around(np.max(Pdrop_mesh),decimals=2)) + "\n")                      # print maximum pressure drop of this timestep
    for line in np.transpose(np.around(windfield,decimals=2)):                                               # print windspeed
        for number in line:
            f.write("{:>9}".format(str(number)))
        f.write("\n")
    for line in np.transpose(np.around(winddir,decimals=2)):                                                 # print winddirection (0 degrees means wind comes from the north)
        for number in line:
            f.write("{:>9}".format(str(number)))
        f.write("\n")
    for line in np.transpose(np.around(Pdrop_mesh,decimals=2)):                                              # print pressure drop
        for number in line:
            f.write("{:>9}".format(str(number)))
        f.write("\n")
    f.close()
    '''
    '''    
    if j == 1:
        ## WRITE INFORMATION TO TOP OF SPIDERWEB FILE
        print('number of timesteps' ,len(rmaxslice))
        f = open(str(name)+'.spw','a')
        f.write("FileVersion    = 1.03\n")
        f.write("filetype       = meteo_on_spiderweb_grid\n")
        f.write("NODATA_value   = -999.0\n")
        f.write("n_cols         = " + str(n_cols) + "\n")
        f.write("n_rows         = " + str(n_rows) + "\n")
        f.write("grid_unit      = degree\n")
        f.write("spw_radius     = " + str(int(tc_radius*1000)) + "\n")
        f.write("spw_merge_frac = 0.333\n")
        f.write("spw_rad_unit   = m\n")
        f.write("n_quantity     = 3\n")
        f.write("quantity1      = wind_speed\n")
        f.write("quantity2      = wind_from_direction\n")
        f.write("quantity3      = p_drop\n")
        f.write("unit1          = m s-1\n")
        f.write("unit2          = degree\n")
        f.write("unit3          = Pa\n")
        
        ### EXPLANATION
        # We write zeros to Canada before and after the TC is active.
        # This coordinate is far away from any GTSM output location to make sure no forcing is applied
        # The TC is moved quickly from Canada to its starting position to make sure the 'zeros' are not interpolated spatially
        
        ## WRITE ZEROS TO CANADA AT T = 0.0
        f.write("TIME           = " + str(float(startdate.hour))+ " hours since "+str(startdate.date())+" 00:00:00 +00:00\n")
        if lon0 > 180:
            lon_out = np.around((lon0 - 360), decimals=2)
        else:
            lon_out = np.around(lon0, decimals=2)
        f.write("x_spw_eye      = " + str(lon_out) + "\n")
        f.write("y_spw_eye      = " + str(lat0) + "\n")
        f.write("p_drop_spw_eye = " + str(0) + "\n")
        for line in np.transpose(np.around(nodata_array_wind,decimals=2)):                                    # print windspeed
            for number in line:
                f.write("{:>9}".format(str(number)))
            f.write("\n")
        for line in np.transpose(np.around(nodata_array_wind,decimals=2)):                                    # print winddirection (0 degrees means wind comes from the north)
            for number in line:
                f.write("{:>9}".format(str(number)))
            f.write("\n")
        for line in np.transpose(np.around(nodata_array_pressure,decimals=2)):                                # print pressure drop
            for number in line:
                f.write("{:>9}".format(str(number)))
            f.write("\n")
        f.close()
    '''
    '''    
    if j == 1:
        ## WRITE ZEROS TO CANADA AT T = START HOUR STORM - 0.00001
        f = open(str(name)+'.spw','a')
        f.write("TIME           = " + str(np.around((startdate.hour+time_out-0.00001+1),decimals=5))+ " hours since "+str(startdate.date())+" 00:00:00 +00:00\n")
        f.write("x_spw_eye      = " + str(lon_out) + "\n")
        f.write("y_spw_eye      = " + str(lat0) + "\n")
        f.write("p_drop_spw_eye = " + str(0) + "\n")
        for line in np.transpose(np.around(nodata_array_wind,decimals=2)):                                    # print windspeed
            for number in line:
                f.write("{:>9}".format(str(number)))
            f.write("\n")
        for line in np.transpose(np.around(nodata_array_wind,decimals=2)):                                    # print winddirection (0 degrees means wind comes from the north)
            for number in line:
                f.write("{:>9}".format(str(number)))
            f.write("\n")
        for line in np.transpose(np.around(nodata_array_pressure,decimals=2)):                                # print pressure drop
            for number in line:
                f.write("{:>9}".format(str(number)))
            f.write("\n")
        f.close()
    '''
    
    ### EXPLANATION    
    # The spiderweb values are interpolated between from 0 to the actual values between t1 and t2
    # This is to make sure the spiderweb is already on the move when wind speeds are linearly increasing and the pressure is decreasing
    # When doing this before the TC starts moving, a surge could be generated which would be incorrect
    # It also helps to prevent a shock wave -> caused by an instant pressure decrease or increase
    # We replicate the described methodology for the last timestep
    
    ## REPLACE VALUES WITH ZEROS AT FIRST AND LAST TIMESTEP
    
    #The first timestep is already defined above with all 0s 
    #if j == 1:                                                                                                # print zeros at t = 1
    #    windfield = nodata_array_wind
    #    winddir = nodata_array_wind
    #    Pdrop_mesh = nodata_array_pressure
    
    if j == (len(rmaxslice)-1):  
   # if j == (len(rmaxslice)):                                                                             # print zeros at t = -1
        windfield = nodata_array_wind
        winddir = nodata_array_wind
        Pdrop_mesh = nodata_array_pressure
    
    ## WRITE VALUES TO STORM XY AT T = TIME
    f = open(str(name)+'.spw','a')
    f.write("TIME           = " + str(np.around((startdate.hour+time_out),decimals=5))+ " hours since "+str(startdate.date())+" 00:00:00 +00:00\n")
    #f.write("TIME           = " + str(np.around((startdate.hour+time_out+1),decimals=5))+ " hours since "+str(startdate.date())+" 00:00:00 +00:00\n")
    #f.write("TIME           = " + str(np.around((startdate.hour+time_out),decimals=5))+ " hours since "+str(startdate.date())+" 00:00:00 +00:00\n")
    
    if lon0 > 180:
        lon_out = np.around((lon0 - 360), decimals=2)
    else:
        lon_out = np.around(lon0, decimals=2)
    
    f.write("x_spw_eye      = " + str(lon_out) + "\n")                                                       # print longitude
    f.write("y_spw_eye      = " + str(lat0) + "\n")                                                          # print latitude
    f.write("p_drop_spw_eye = " + str(np.around(np.max(Pdrop_mesh),decimals=2)) + "\n")                      # print maximum pressure drop of this timestep
    for line in np.transpose(np.around(windfield,decimals=2)):                                               # print windspeed
        for number in line:
            f.write("{:>9}".format(str(number)))
        f.write("\n")
    for line in np.transpose(np.around(winddir,decimals=2)):                                                 # print winddirection (0 degrees means wind comes from the north)
        for number in line:
            f.write("{:>9}".format(str(number)))
        f.write("\n")
    for line in np.transpose(np.around(Pdrop_mesh,decimals=2)):                                              # print pressure drop
        for number in line:
            f.write("{:>9}".format(str(number)))
        f.write("\n")
    f.close()
    '''
    if j == (len(rmaxslice)-1):  
    ## WRITE VALUES TO STORM XY AT T = TIME + 48hours (2days) for the flood modelling
        f = open(str(name)+'.spw','a')
        f.write("TIME           = " + str(np.around((startdate.hour+time_out+1+48),decimals=5))+ " hours since "+str(startdate.date())+" 00:00:00 +00:00\n")
        #f.write("TIME           = " + str(np.around((startdate.hour+time_out),decimals=5))+ " hours since "+str(startdate.date())+" 00:00:00 +00:00\n")
        
        if lon0 > 180:
            lon_out = np.around((lon0 - 360), decimals=2)
        else:
            lon_out = np.around(lon0, decimals=2)
        
        f.write("x_spw_eye      = " + str(lon_out) + "\n")                                                       # print longitude
        f.write("y_spw_eye      = " + str(lat0) + "\n")                                                          # print latitude
        f.write("p_drop_spw_eye = " + str(np.around(np.max(Pdrop_mesh),decimals=2)) + "\n")                      # print maximum pressure drop of this timestep
        for line in np.transpose(np.around(windfield,decimals=2)):                                               # print windspeed
            for number in line:
                f.write("{:>9}".format(str(number)))
            f.write("\n")
        for line in np.transpose(np.around(winddir,decimals=2)):                                                 # print winddirection (0 degrees means wind comes from the north)
            for number in line:
                f.write("{:>9}".format(str(number)))
            f.write("\n")
        for line in np.transpose(np.around(Pdrop_mesh,decimals=2)):                                              # print pressure drop
            for number in line:
                f.write("{:>9}".format(str(number)))
            f.write("\n")
        f.close()  
        '''
        