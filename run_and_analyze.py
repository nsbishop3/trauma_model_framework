# from sugarscape_cg.model_control import SugarscapeCg as ssc
from trauma_model_framework.model import SugarscapeTMF as stmf
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

# max step count of simulation
step_count = 2500
# number of monte-carlo simulation runs
mc_iters = 10

# post trauma event average trauma levels
post_te_avg_tl = []
# average trauma level (over entire simulation)
avg_tl = []

# loop over monte-carlo runs with the iteration number as the seed for each run
for mc_iter in tqdm(range(mc_iters),smoothing=0):
    m = stmf(initial_population=100,seed=mc_iter)
    m.run_model(step_count=step_count)
    
    famine_end = m.te_end
    
    pop = m.datacollector.model_vars['SsAgent']
    trauma = m.datacollector.model_vars['Trauma']
    
    # vv line below will allow for plotting all trauma values after trauma event ends
    post_te_avg_tl.append(trauma[famine_end:])
    # vv line below will allow for plotting all trauma values (not used in model framework)
    avg_tl.append(trauma)

    
#%% plot aggregated statistics of post-trauma event average trauma levels

steps_to_plot = range(max([len(xx) for xx in post_te_avg_tl]))
processed_data = []
num_run_data = []
for step in steps_to_plot:
    # this list comprehension allows for error-free plotting if one or more
    # of the lines being plotted has less x-values than the others
    vals = [avg_tl[step] for avg_tl in post_te_avg_tl if len(avg_tl) > step]
    num_runs = len(vals)
    quantiles = np.quantile(vals,[0,0.1,.25,0.5,.75,0.9,1])
    
    processed_data.append(quantiles)
    num_run_data.append(num_runs)

# data bookends
q000 = [xx[0] for xx in processed_data]
q100 = [xx[-1] for xx in processed_data]
# 10th and 90th percentiles
q010 = [xx[1] for xx in processed_data]
q090 = [xx[-2] for xx in processed_data]
# 25th and 75th percentiles
q025 = [xx[2] for xx in processed_data]
q075 = [xx[-3] for xx in processed_data]
# median
q050 = [xx[3] for xx in processed_data]

fig_tr, ax_tr_agg = plt.subplots(nrows=1,figsize=(16,6))
fig_tr.suptitle('No Trauma Features Active')
ax_tr_agg.set_ylim(0,0.6)
ax_tr_agg.set_xlim(0,800)
ax_tr_agg.set_title('Aggregated Post-Trauma Event Trauma Levels')

ax_tr_agg.plot(steps_to_plot,q100,linestyle='-',label='Q 1.00',color='black',alpha=0.5)
ax_tr_agg.plot(steps_to_plot,q090,linestyle='-',label='Q 0.90',color='black')
ax_tr_agg.plot(steps_to_plot,q075,linestyle='-',label='Q 0.75',color='orange')

ax_tr_agg.plot(steps_to_plot,q050,label='Median',color='r')

ax_tr_agg.plot(steps_to_plot,q025,linestyle='-',label='Q 0.25',color='orange')
ax_tr_agg.plot(steps_to_plot,q010,linestyle='-',label='Q 0.10',color='black')
ax_tr_agg.plot(steps_to_plot,q000,linestyle='-',label='Q 0.00',color='black',alpha=0.5)


ax_tr_agg.set_ylabel('Average Trauma Level')
ax_tr_agg.set_xlabel('Steps After Trauma Event Ends')
plt.tight_layout()
ax_tr_agg.grid()
ax_tr_agg.legend(fontsize='medium',ncols=1)


#%% plot last mc run pop and trauma vs sim steps
fig, ax = plt.subplots(nrows=2,figsize=(16,6))
x = np.arange(m.schedule.steps+1)
yvars = [pop,trauma]
titles = ['pop','trauma levels']

for i in range(2):
    ax[i].set_title(titles[i])
    ax[i].plot(x,yvars[i])
    ax[i].grid()
    ax[i].set_xticks(np.arange(0,len(x),100))