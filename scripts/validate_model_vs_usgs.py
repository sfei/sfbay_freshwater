import utm
import os, sys
import geopandas as gpd
import numpy as np
import xarray as xr
import matplotlib.pylab as plt
from shapely.geometry import Point
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

########################################################################################
# the first step is to make some plots to help us match USGS stations with pour points
########################################################################################

# map usgs stations to pour poitns
usgs_to_pourpt = [[11458500 ,'SONOMA'],
                  [11458000 , 'NAPA'],
                  [11460000 , 'MARINS3'],
                  [11181040 , 'USANLORZ'],
                  [11181040 , 'EBAYCc3'],
                  [11179000 , 'UALAMEDA'],
                  [11164500 , 'SCLARAVW1'],
                  [11169025 , 'SCLARAVCc'],
                  [11169000 , 'SCLARAVCc'],
                  [11172175 , 'COYOTE']]

# list of zoom windows for plotting figurs
zoom_windows = [(518020.06212375907, 576204.087092947, 4185296.8007331635, 4261880.9019746585), 
 (569364.9726537764, 605009.7158758788, 4154220.8858074374, 4186030.598222632),
 (566055.3663127264, 589125.5497150281, 4136744.8453214155, 4156711.0404114076),
 (582551.7719804023, 605717.7425264334, 4129964.9462470612, 4149083.2914333506)
 ]

# station number to latitude, longitude
usgs_latlon = {11164500 : (37.42327257, -122.1894095, 'SAN FRANCISQUITO C A STANFORD UNIVERSITY CA'),
			   11169000 : (37.3343859, -121.8994, 'GUADALUPE R A SAN JOSE CA'),
			   11169025 : (37.3738296, -121.9330129, 'GUADALUPE R ABV HWY 101 A SAN JOSE CA'),
			   11172175 : (37.4221617, -121.9274577, 'COYOTE C AB HWY 237 A MILPITAS CA'),
			   11179000 : (37.58715679, -121.960793, 'ALAMEDA C NR NILES CA'),
			   11181040 : (37.6840977, -122.1399649, 'SAN LORENZO C A SAN LORENZO CA'),
			   11458000 : (38.3682457, -122.3033085, 'NAPA R NR NAPA CA'),
			   11458500 : (38.32324705, -122.4944258, 'SONOMA C A AGUA CALIENTE CA'),
			   11460000 : (37.96297947, -122.556922, 'CORTE MADERA C A ROSS CA')}
usgs_utm = {}
for station in usgs_latlon.keys():
	x1, y1, dum1, dum2 = utm.from_latlon(usgs_latlon[station][0],usgs_latlon[station][1])
	usgs_utm[station] = (x1,y1,usgs_latlon[station][2])


flow_dir=os.path.join("..","ModelforNutrient","BAHM Flow")

# load shapefiles
pour_points=gpd.read_file(os.path.join(flow_dir,
           							   "PourPointsforBAHydroModel",
           							   "Watershed2_CustomOutFlowPts.shp"))
watersheds=gpd.read_file(os.path.join(flow_dir,
           							   "PourPointsforBAHydroModel",
           							   "BAHM-WtrShds_custom.shp"))
streams=gpd.read_file(os.path.join(flow_dir,
           							   "PourPointsforBAHydroModel",
           							   "BAHM-streams_forslp_utm.shp"))

# fix pour point geometry -- lat and long are mixed up!
x = []
y = []
p = []
for lat, lon in zip(pour_points['Long'], pour_points['Lat']):
	x1, y1, dum1, dum2 = utm.from_latlon(lat,lon)
	p1 = Point(x1,y1)
	p.append(p1)
pour_points['geometry'] = p

# add centroids for other geometries
def add_centroid(gdf):
	x = []
	y = []
	p = gdf.centroid.values
	for p1 in p:
		x1,y1 = p1.xy
		x.append(x1[0])
		y.append(y1[0])
	gdf['xc'] = x
	gdf['yc'] = y
	return gdf
pour_points = add_centroid(pour_points)
watersheds = add_centroid(watersheds)


with PdfPages('../plots/compare_watershed_model_to_usgs.pdf') as pdf:

	# plot the pour points with the USGS gage station locations...
	
	for izoom, zoom in enumerate(zoom_windows):
	
		width=8.5
		height = (zoom[3]-zoom[2])/(zoom[1]-zoom[0])*width
		fig, ax = plt.subplots(figsize=(width,height))
		
		
		watersheds.plot(ax=ax,color='lightblue',edgecolor='b')
		streams.plot(ax=ax,color='r')
		
		nudge=200
		close=200
		for i in range(len(pour_points)):
		
		
		
			x = pour_points.iloc[i].xc
			y = pour_points.iloc[i].yc
			name = pour_points.iloc[i].immediatec
	
			if x>=zoom[0] and x<=zoom[1] and y>=zoom[2] and y<=zoom[3]:
		
				if name=='USANLORZ':
					nudge1 = nudge
				else:
					nudge1 = -nudge
			
				ax.plot(x,y,'bo')
				ax.text(x+nudge,y+nudge1,name,color='b')
		
		for station in usgs_utm.keys():
			x, y, name = usgs_utm[station]
	
			if x>=zoom[0] and x<=zoom[1] and y>=zoom[2] and y<=zoom[3]:
		
				ax.plot(x,y,'ko')
				ax.text(x+nudge,y+nudge,'USGS %d\n%s' % (station,name),color='k')
		
		ax.axis(zoom)
		pdf.savefig()

		plt.close('all')
	
	########################################################################################
	# the next step is to compare netcdf file with usgs stations
	########################################################################################
	
	
	ds = xr.open_dataset('../outputs/sfbay_freshwater.nc')
	
	
	for station_to_ppt in usgs_to_pourpt:
	
		station = station_to_ppt[0]
		ppt = station_to_ppt[1]
	
		# make a figure
		fig, ax = plt.subplots(figsize=(24,8.5))
	
		# plot pour point data first because it's farther downstream, and thus should be bigger
		ds1 = ds.sel(station=ppt)
		time_ppt = ds1.time.values
		flow_ppt = ds1.flow_cms.values
	
		ind = time_ppt <= np.datetime64('2017-12-31')
		ax.semilogy(time_ppt[ind], flow_ppt[ind], label='%s (BAHM)' % ppt, color='red')
	
		ind = np.logical_and(time_ppt >= np.datetime64('2018-01-01'),
			                 time_ppt <= np.datetime64('2019-12-31'))
		ax.semilogy(time_ppt[ind], flow_ppt[ind], label='%s (WDM from Tan)' % ppt, color='blue')
	
	
		ind = time_ppt >= np.datetime64('2021-08-01')
		ax.semilogy(time_ppt[ind], flow_ppt[ind], label='%s (WDM from Pedro)' % ppt, color='purple')
	
	
		# then add usgs station data
		data = pd.read_csv('../USGS_flow/%d.txt' % station, sep='\t', comment='#').iloc[1:]
		time_usgs = data['datetime'].values.astype('datetime64[ns]')
		for col in data.columns:
			if '_00060_' in col and not '_cd' in col:
				flow_col = col
		flow_usgs = data[flow_col].values.astype(float) * 0.0283168 # convert cfs to cms
		flow_usgs[flow_usgs<=0] = np.nan


		ax.semilogy(time_usgs, flow_usgs, label='USGS Station %d' % station, color='gold')
	
		ax.legend()
	
		ylim = ax.get_ylim()
	
		ax.set_ylim([0.01, ylim[1]])
	
		ax.set_ylabel('Flow (m3/s)')
	
		pdf.savefig()
	
		plt.close('all')
		
					