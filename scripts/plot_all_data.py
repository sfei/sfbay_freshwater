import utm
import os, sys
import geopandas as gpd
import numpy as np
import xarray as xr
import matplotlib.pylab as plt
from shapely.geometry import Point
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.gridspec as gridspec

ymax = 1e4
ymin = 1e-2

figsize = (11,11)
subplot_ratio = 1.3
linewidth = 0.25
markersize = 4
fdpi = 150

outfile = '../plots/sfbay_freshwater_data_compare.pdf'

# list of datasets to compare
flow_data_directories = ['../Flow4BayModel_1994_2022',
                         '../TanModel_v1_Flow', 
                         '../Flow4BayModel_08012021_10012022',
                         '../ModelforNutrient/BAHM Flow']
flow_data_labels = ['WDM 1994-2022 from Pedro, v2',
                    'WDM 2018-2019 from Tan', 
                    'WDM WY2022 from Pedro, v1',
                    'BAHM']
flow_data_colors = ['blue','purple','limegreen','red']


# one special dataset for inter-comparison
base_dir = '../Flow4BayModel_1994_2022'
base_label = 'WDM 1994-2022'


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


# load shapefiles and fix pourpoint geometry (lat/lon are mixed up)
flow_dir=os.path.join("..","ModelforNutrient","BAHM Flow")
pour_points=gpd.read_file(os.path.join(flow_dir,"PourPointsforBAHydroModel","Watershed2_CustomOutFlowPts.shp"))
watersheds=gpd.read_file(os.path.join(flow_dir,"PourPointsforBAHydroModel","BAHM-WtrShds_custom.shp"))
streams=gpd.read_file(os.path.join(flow_dir,"PourPointsforBAHydroModel","BAHM-streams_forslp_utm.shp"))
x = []
y = []
p = []
for lat, lon in zip(pour_points['Long'], pour_points['Lat']):
	x1, y1, dum1, dum2 = utm.from_latlon(lat,lon)
	p1 = Point(x1,y1)
	p.append(p1)
pour_points['geometry'] = p
pour_points['immediatec'] = pour_points['immediatec'].str.replace(' ','') # remove whitespace
x = []
y = []
for ipp in range(len(pour_points)):
	x1, y1 = pour_points.iloc[ipp]['geometry'].xy
	x.append(x1[0])
	y.append(y1[0])
pour_points['xutm'] = x
pour_points['yutm'] = y



with PdfPages(outfile) as pdf:


	for station in all_stations:

		
		fig = plt.figure(tight_layout=True, figsize=figsize)
		gs = gridspec.GridSpec(2, 2, width_ratios=(subplot_ratio,1)) 
		ax1 = fig.add_subplot(gs[0, :])
		ax2 = fig.add_subplot(gs[1,0])
		ax3 = fig.add_subplot(gs[1,1])


		# first load the base data
		src_fn = os.path.join(base_dir, '%s.txt' % station)
		df_base = pd.read_csv(src_fn, sep='\t')
		df_base.columns = ['date', 'flow_cfs']
		df_base['date'] = pd.DatetimeIndex(df_base['date'])
		df_base['numtime'] = (df_base['date'] - np.datetime64('1994-01-01'))/np.timedelta64(1,'s')

		colors_vs_base = []

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

			ax1.semilogy(df['date'], df['flow_cfs'], label='%s (%s)' % (station, label), 
				color=color, linewidth=linewidth, 
				    rasterized=True)
	
			# interpolate onto base time
			if not label==base_label:
				df['numtime'] = (df['date'] - np.datetime64('1994-01-01'))/np.timedelta64(1,'s')
				flow_cfs_interp = np.interp(df_base['numtime'].values, df['numtime'].values, df['flow_cfs'].values, left=np.nan, right=np.nan)
				df_base[label] = flow_cfs_interp
				colors_vs_base.append(color)

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

				ax1.semilogy(time_usgs, flow_usgs, label='USGS Station %d' % usgs_station, 
					color=color, linewidth=linewidth, 
				    rasterized=True)

				# interpolate onto base time
				numtime_usgs = (time_usgs - np.datetime64('1994-01-01'))/np.timedelta64(1,'s')
				flow_cfs_interp = np.interp(df_base['numtime'].values, numtime_usgs, flow_usgs, left=np.nan, right=np.nan)
				df_base[usgs_station] = flow_cfs_interp
				colors_vs_base.append(color)

		if not (ds is None):
		    ds1 = ds.sel(station=station)
		    ax1.semilogy(ds1['time'], ds1['flow_cfs'], '--', color='lightgray', 
		    	label='sfbay_freshwater.nc', 
				    rasterized=True)

		ax1.legend()
	
		ax1.set_ylabel('Flow (cfs)')
		ax1.grid()
		ax1.set_ylim((ymin,ymax))

		# add correlations between model and data
		colors_vs_base.reverse()
		for icol, col in enumerate(df_base.columns[3:][::-1]):

			ax2.loglog(df_base['flow_cfs'], df_base[col], '.', 
				    markersize=markersize, label=col, color=colors_vs_base[icol], 
				    rasterized=True)
		ax2.set_xlabel('%s (cfs)' % base_label)
		ax2.set_ylabel('comparison dataset (cfs)')

		ax2.grid()
		ax2.legend()

		watersheds.plot(ax=ax3,color='lightblue',edgecolor='b', linewidth=linewidth, 
				    rasterized=True)
		streams.plot(ax=ax3,color='r',linewidth=linewidth, 
				    rasterized=True)
		ax3.axis((535640.22844051, 605073.2099276104, 4139672.1691559376, 4229417.9909717105))
		pp = pour_points.loc[pour_points['immediatec'].values == station]
		ax3.plot(pp['xutm'], pp['yutm'], 'o', color='red', markersize=8)
		#ax3.text(pp['xutm']+2000, pp['yutm'], station, fontsize=20)
		ax3.axis('off')

		fig.suptitle(station)

		pdf.savefig(dpi=fdpi)
	

		plt.close('all')
		
					