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
# make some plots to help us match USGS stations with pour points
########################################################################################

outfile = '../plots/sfbay_freshwater_usgs_locations_vs_pourpoints.pdf'

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


with PdfPages(outfile) as pdf:

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
	