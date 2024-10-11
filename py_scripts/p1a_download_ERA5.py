#!/usr/bin/env python

import os
import sys
from datetime import datetime, timedelta
import calendar
import cdsapi


# Case study
case_name = sys.argv[1]
start_date = sys.argv[2]
tstop = sys.argv[3]
tspinup = sys.argv[4]

# Directory where the data will be downloaded at
root_dir="/projects/0/einf2224/paper1/data/gtsm/meteo_forcing/ERA5"
targetfile=f'{root_dir}/ERA5_{case_name}.nc'

'''
if os.path.exists(targetfile):
    print(f'ERA5 for {case_name} already downloaded')
else:
'''

# Obtain start and end dates
start_date_object = datetime.strptime(start_date, "%Y%m%d")
start_date_object_withspinup = start_date_object - timedelta(days=int(tspinup))
start_year = start_date_object_withspinup.year
start_month = start_date_object_withspinup.month
start_day = start_date_object_withspinup.day


end_date_object = start_date_object + timedelta(hours=int(tstop))
end_year = end_date_object.year
end_month = end_date_object.month
end_day = end_date_object.day

month_range = [str(month).zfill(2) for month in range(start_month, end_month + 1)]

# Select the months and years for which data should be downloaded
if len(month_range) > 1:
    mnth = month_range
else:
    mnth = month_range[0] #f"{month_range[0]:02}"

if start_year == end_year:
    yr=start_year
else:
    print("Start year differs from end year", flush=True)    # This still needs to be fixed
     
yr=int(yr)

print(f"Downloading ERA5 data for {case_name} for the year {yr} and month(s) {mnth}", flush=True)

# Monthly download
if os.path.isfile(targetfile)==False: 
    c = cdsapi.Client()
    c.retrieve('reanalysis-era5-single-levels',
        {'product_type':'reanalysis',
        'format':'netcdf',
        'variable':['10m_u_component_of_wind','10m_v_component_of_wind','mean_sea_level_pressure'],
        'year':yr,
        'month':mnth,
        'day': [
            '01', '02', '03',
            '04', '05', '06',
            '07', '08', '09',
            '10', '11', '12',
            '13', '14', '15',
            '16', '17', '18',
            '19', '20', '21',
            '22', '23', '24',
            '25', '26', '27',
            '28', '29', '30',
            '31',
        ],
        'time':['00:00','01:00','02:00','03:00','04:00','05:00',
                '06:00','07:00','08:00','09:00','10:00','11:00',
      	        '12:00','13:00','14:00','15:00','16:00','17:00',
                '18:00','19:00','20:00','21:00','22:00','23:00']
        },
        targetfile)


