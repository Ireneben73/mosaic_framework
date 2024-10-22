import os
import numpy as np
import pandas as pd
import sys
#sys.path.insert(1, r'/gpfs/home4/benitoli/papers/paper2/case_studies/storm2/models/holland')
import p1b_holland_model_ibl as hm
import math
from datetime import datetime
import p1c_write_spw_file_ibl as spw


#%%

# Case study
case_name = sys.argv[1]
tstart = sys.argv[2]
tspinup = sys.argv[3]

# Directory where the TC tracks are
root_dir="/projects/0/einf2224/paper1/data/gtsm/meteo_forcing/TC_tracks"
filename = f"{root_dir}/{case_name}.atcf"



# Directory where the resulting spiderweb will be saved at
outputdest="/projects/0/einf2224/paper1/data/gtsm/meteo_forcing/spiderwebs/"


data = np.loadtxt(filename, delimiter=',', dtype='str', encoding='utf-8')
unique_indices = np.unique(data[:, 2], return_index=True)[1]
data_unique = data[unique_indices]

# Extracting date strings from the data
dateall = data_unique[:, 2]

# Convert the filter date string "20170910" to a datetime object
#filter_date = datetime.strptime(tstart, "%Y%m%d")

# Convert the date strings to datetime objects
dateall_datetime = [datetime.strptime(date.lstrip(), "%Y%m%d%H") for date in dateall]

# Boolean indexing to filter rows based on date
#filtered_indices = [i for i, date in enumerate(dateall_datetime) if date >= filter_date]
#filtered_indices = [i for i, date in enumerate(dateall_datetime) if date >= filter_date and date.hour % 6 == 0]
filtered_indices = [i for i, date in enumerate(dateall_datetime) if date.hour % 6 == 0]
filtered_data_unique = data_unique[filtered_indices]
#print(filtered_data_unique)

# Extracting required arrays
dateall = filtered_data_unique[:, 2]
latall = filtered_data_unique[:, 6]
lonall = filtered_data_unique[:, 7]
presall = filtered_data_unique[:, 9]             # Original unit comes in hPa
windall = filtered_data_unique[:, 8].astype(float) / 1.94384           # Original unit comes in kts. Divide by 1.94384 to convert to m/s
rmaxall = filtered_data_unique[:, 19].astype(float) * 1.852            # Original unit comes in nautic miles. Multily by 1.852 to convert to km


startdate_str=dateall[0]
startdate_str_without_spaces = startdate_str.lstrip()  # Remove leading spaces
startdate = datetime.strptime(startdate_str_without_spaces, "%Y%m%d%H")

#%%
#=============================================================================
# Constants from literature
#=============================================================================
alpha=0.55              # Deceleration of surface background wind - Lin & Chavas 2012
beta_bg=20.             # Angle of background wind flow - Lin & Chavas 2012
SWRF=0.85               # Empirical surface wind reduction factor (SWRF) - Powell et al 2005 
CF=0.915                # Wind conversion factor from 1 minute average to 10 minute average - Harper et al (2012)
Patm=101325.            # Atmospheric pressure

#==============================================================================
# Spyderweb specifications 
#==============================================================================
tc_radius=350 #500           # Radius of the tropical cyclone, in km                                                                                            TO CHECK!!! What would happen if I use this value as a variable???
n_cols=36               # Number of gridpoints in angular direction
n_rows=375              # Number of gridpoints in radial direction

#==============================================================================
# Create spiderweb file with the parametric wind model of Holland
#==============================================================================


if os.path.exists(outputdest + str(case_name) + '.spw'):
  os.remove(outputdest + str(case_name) + '.spw')
  print("Original file has been deleted")
else:
  print("The file does not exist")



latslice = np.array([float(lat.replace(' ', '').rstrip('NS')) * (1 if 'N' in lat else -1) / 10 for lat in latall])
#lonslice = np.array([float(lon.replace(' ', '').rstrip('EW')) * (1 if 'E' in lon else -1) / 10 for lon in lonall])
lonslice = np.array([(float(lon.replace(' ', '').rstrip('EW')) * (1 if 'E' in lon else -1)) /10 + 360 for lon in lonall])



windslice = windall #np.array([float(wind.replace(' ', '')) for wind in windall])
presslice = np.array([float(press.replace(' ', '')) for press in presall])
timeslice = np.arange(len(rmaxall))

#rmaxslice = np.array([float(rmax.replace(' ', '')) for rmax in rmaxall])
rmaxslice = rmaxall #np.array([float(rmax.replace(' ', '')) for rmax in rmaxall])

for j in range(1,len(rmaxslice)):  
    ## DATA PER TIMESTEP
    lat0,lat1,lon0,lon1,t0,t1=latslice[j-1],latslice[j],lonslice[j-1],lonslice[j],timeslice[j-1],timeslice[j]
    U10,Rmax,P=windslice[j-1],rmaxslice[j-1],presslice[j-1]
    dt=3600*(t1-t0)*6
    
    ## HOLLAND MODEL
    ## STEP 1: GENERATE THE SPIDERWEB MESH
    rlist,thetalist,xlist,ylist=hm.Generate_Spyderweb_mesh(n_cols,n_rows,tc_radius,lat0) # rlist = distance in km from eye, thetalist = wind angle, xlist = zonal distance in km, ylist = meridional distance in km
    latlist,lonlist=hm.Generate_Spyderweb_lonlat_coordinates(xlist,ylist,lat1,lon1)      # xlist and ylist converted to lon/lat coordinates
    
    ## STEP 2: CALCULATE THE BACKGROUND WIND
    [bg,ubg,vbg]=hm.Compute_background_flow(lon0,lat0,lon1,lat1,dt)                      # bg = translational speed (m/s), ubg/vbg are zonal/meridional components of bg

    ## STEP 3: SUBTRACT THE BACKGROUND FLOW FROM U10 (TROPICAL CYCLONE'S 10-METER WIND SPEED)
    Ugrad=(U10/SWRF)-(bg*alpha)                                                          # 10-minute maximum sustained surface wind (conversts surface wind to gradient level, and subtracts the background wind multiplied with a reduction factor alpha)
    P_mesh=np.zeros((xlist.shape))
    Pdrop_mesh=np.zeros((xlist.shape))
    up=np.zeros((xlist.shape))
    vp=np.zeros((xlist.shape))
    winddir=np.zeros((xlist.shape))
    
    ## STEP 4: CALCULATE WIND AND PRESSURE PROFILE USING THE HOLLAND MODEL
    for l in range(0,n_rows):
        r=rlist[0][l]                                                                     # Distance in km from the eye
        Vs,Ps=hm.Holland_model(lat0,P,Ugrad,Rmax,r)                                       # Calculate wind speed and pressure for this radius
        Vs=Vs*SWRF                                                                        # Convert back to 10-min surface wind speed
        
        P_mesh[:,l].fill(Ps)                                                              # Fill the circle with the computed pressure at the given radius
        Pdrop_mesh[:,l].fill((Patm-Ps))                                                   # Convert pressure to drop in pressure
        
        beta=hm.Inflowangle(r,Rmax,lat0)                                                  # Inflow angle, depends on the distance from the eye (r)
        for k in range(0,n_cols):                                                         # Compute wind components: wind speed at this radius + background windspeed + inflow angle
            ubp=alpha*(ubg*math.cos(math.radians(beta_bg))-np.sign(lat0)*vbg*math.sin(math.radians(beta_bg)))
            vbp=alpha*(vbg*math.cos(math.radians(beta_bg))+np.sign(lat0)*ubg*math.sin(math.radians(beta_bg)))
            
            up[k,l]=-Vs*math.sin(thetalist[:,0][k]+beta)+ubp
            vp[k,l]=-Vs*math.cos(thetalist[:,0][k]+beta)+vbp
            winddir[k,l]=np.degrees(np.arctan2(up[k,l],vp[k,l]))+180                      # Wind direction in degrees, with 0/360 wind coming from the North

    u10=CF*up                                                                             # Convert zonal wind componenet from 1-minute average to 10-minute average
    v10=CF*vp                                                                             # Convert meridional wind componenet from 1-minute average to 10-minute average
    windfield=np.sqrt(u10**2.+v10**2.)                                                    # Calculate wind speed with Pythagoras

    time_out = t0*6                                                                       # ATCF timestep is six hourly
    
    ## ARRAY WITH ZEROS OF SIMILAR SIZE AS THE SPIDERWEB
    nodata_array_wind = np.zeros((windfield.shape))
    nodata_array_pressure = np.zeros((windfield.shape))
    
    ## WRITE TIMESTEP TO SPIDERWEB FILE
    spw.write_spw_file(outputdest + str(case_name),n_cols,n_rows,tc_radius,startdate,nodata_array_wind,nodata_array_pressure,time_out,windfield,winddir,Pdrop_mesh,rmaxslice,j,lon0,lat0, tspinup)

## MOVE FILES TO DEDICATED SUBFOLDER
#os.rename(filename,filename)