import utm
import os, sys
import geopandas as gpd
import numpy as np
import xarray as xr
import matplotlib.pylab as plt
from shapely.geometry import Point
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

ymax = 1e4
ymin = 1e-2


outfile = '../plots/sfbay_freshwater_data_compare.pdf'


flow_data_directories = ['../ModelforNutrient/BAHM Flow', 
                         '../TanModel_v1_Flow', 
                         '../Flow4BayModel_08012021_10012022']
flow_data_labels = ['BAHM', 
                    'WDM from Tan', 
                    'WDM from Pedro']
flow_data_colors = ['red','blue','purple']

# optional netcdf dataset for comparison...
ds=None
#ds = xr.open_dataset("../outputs/sfbay_freshwater.nc")
#ds = xr.open_dataset("/hpcvol2/open_bay/Hydro_model/Full_res/WY2018/wy2018/sfb_dfm/sfbay_freshwater/outputs/sfbay_freshwater.nc")

all_stations = ['MARINS1', 'MARINS3', 'MARINS2', 'MARINN', 'PETALUMA', 'SONOMA',
       'NAPA', 'SOLANOWa', 'SOLANOWb', 'SOLANOWc', 'CCOSTAC2', 'CCOSTAC3',
       'CCOSTAC1', 'CCOSTAC4', 'CCOSTAW2', 'CCOSTAW3', 'CCOSTAW1',
       'EBAYN1', 'EBAYN4', 'EBAYN2', 'EBAYN3', 'EBAYCc6', 'EBAYCc1',
       'EBAYCc5', 'EBAYCc4', 'EBAYCc3', 'UALAMEDA', 'EBAYS', 'COYOTE',
       'SCLARAVCc', 'SCLARAVW5', 'SCLARAVW4', 'SCLARAVW3', 'SCLARAVW2',
       'SCLARAVW1', 'PENINSULb1', 'PENINSULb3', 'PENINSULb4',
       'PENINSULb6', 'PENINSULb2', 'PENINSULb7', 'PENINSULb5', 'EBAYCc2',
       'USANLORZ']

# map usgs stations to pour poitns
station_to_usgs ={'SONOMA'   : [11458500],
                  'NAPA'     : [11458000],
                  'MARINS3'  : [11460000],
                  'USANLORZ' : [11181040],
                  'EBAYCc3'  : [11181040],
                  'UALAMEDA' : [11179000],
                  'SCLARAVW1': [11164500],
                  'SCLARAVCc': [11169025,11169000],
                  'COYOTE'   : [11172175]}

with PdfPages(outfile) as pdf:


	for station in all_stations:

		

		fig, ax = plt.subplots(figsize=(24,12))
	
		for idir in range(len(flow_data_directories)):

			directory = flow_data_directories[idir]
			label = flow_data_labels[idir]
			color = flow_data_colors[idir]

			src_fn = os.path.join(directory, '%s.txt' % station)

			if label=='BAHM':
				df=pd.read_fwf(src_fn,
                   colspecs=[ (0,4), (5,7), (8,10),(10,23) ],
                   skiprows=5,
                   names=['year','month','day','flow_cfs'],
                   parse_dates={'date': [0,1,2] } )
			else:

				df = pd.read_csv(src_fn, sep='\t')
				df.columns = ['date', 'flow_cfs']
				df['date'] = pd.DatetimeIndex(df['date'])

			ax.semilogy(df['date'], df['flow_cfs'], label='%s (%s)' % (station, label), color=color)
	
		# check if there's one or more usgs stations upstream
		if station in station_to_usgs.keys():

			usgs_colors = ['gold','black']

			for iusgs, usgs_station in enumerate(station_to_usgs[station]):

				color = usgs_colors[iusgs]

				data = pd.read_csv('../USGS_flow/%d.txt' % usgs_station, sep='\t', comment='#').iloc[1:]
				time_usgs = data['datetime'].values.astype('datetime64[ns]')
				for col in data.columns:
					if '_00060_' in col and not '_cd' in col:
						flow_col = col
				flow_usgs = data[flow_col].values.astype(float)
				flow_usgs[flow_usgs<=0] = np.nan

				ax.semilogy(time_usgs, flow_usgs, label='USGS Station %d' % usgs_station, color=color)


		if not (ds is None):
		    ds1 = ds.sel(station=station)
		    ax.semilogy(ds1['time'], ds1['flow_cfs'], '--', color='lightgray', label='sfbay_freshwater.nc')

		ax.legend()
	
		ax.set_ylabel('Flow (cfs)')
		ax.grid()
		ax.set_ylim((ymin,ymax))
	



		pdf.savefig()
	

		plt.close('all')
		
					