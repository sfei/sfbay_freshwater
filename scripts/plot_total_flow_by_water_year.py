import matplotlib.pylab as plt
import xarray as xr
import numpy as np
import pandas as pd 

# load model output
data = xr.open_dataset('../outputs/sfbay_freshwater.nc')
time = data.time
flow = data.flow_cfs.values.sum(axis=0)



# load delta inflows from usgs (rio vista and jersey poitn) as well
data = pd.read_csv('../USGS_flow/11455420.txt', sep='\t', comment='#').iloc[1:]
time_rio = data['datetime'].values.astype('datetime64[ns]')
for col in data.columns:
	if '_72137_' in col and not '_cd' in col:
		flow_col = col
flow_rio = pd.to_numeric(data[flow_col].values,errors='coerce')
data = pd.read_csv('../USGS_flow/11337190.txt', sep='\t', comment='#').iloc[1:]
time_jer = data['datetime'].values.astype('datetime64[ns]')
for col in data.columns:
	if '_72137_' in col and not '_cd' in col:
		flow_col = col
flow_jer = pd.to_numeric(data[flow_col].values,errors='coerce')
				
WYs = np.arange(1995,2023)
WYflow = np.zeros(np.shape(WYs))

for iwy in range(len(WYs)):
	WY = WYs[iwy]
	ind = np.logical_and(time>=np.datetime64('%d-10-01' % (WY-1)), time<np.datetime64('%d-10-01' % WY))
	WYflow[iwy] = np.mean(flow[ind])



time_step = []
flow_step = []
for iwy, WY in enumerate(WYs):

	time_step.append(np.datetime64('%d-10-01' % (WY-1)))
	time_step.append(np.datetime64('%d-10-01' % WY))

	flow_step.append(WYflow[iwy])
	flow_step.append(WYflow[iwy])


# make plot
fig, ax = plt.subplots(2,1, figsize=(16,8))

ax1 = ax[0]
ax1.plot(time, flow, 'r')
ax1.set_ylabel('Daily Average Flow (cfs)', color='r')
ax1.tick_params(axis='y', labelcolor='r')

ax1.set_xlim((time_step[0],time_step[-1]))

ax2=ax1.twinx()
ax2.plot(time_step, flow_step,'b',linewidth=2)
ax2.set_ylabel('Yearly Average Flow (cfs)', color='b')
ax2.tick_params(axis='y', labelcolor='b')

ax1.set_ylim((0,140000))
ax2.set_ylim((0,7000))


ax2.grid()

ax3 = ax[1]
ax3.plot(time_rio, flow_rio, 'r', label = 'Sacramento River')
ax3.plot(time_jer, flow_jer, 'b', label = 'San Joaquin River')
ax3.set_ylabel('Daily Delta Inflow (cfs)')
ax3.set_xlim((time_step[0],time_step[-1]))
ax3.grid()
ax3.legend()

fig.savefig('../plots/net_flow_WDM-1994-2022.png', dpi=300)


