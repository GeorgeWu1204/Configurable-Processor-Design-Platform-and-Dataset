import matplotlib.pyplot as plt
import numpy as np
import matplotlib
# matplotlib.rcParams['font.family'] = 'Times New Roman'
matplotlib.rcParams['font.size'] = 12.5

# Data
name = ["Baseline Framework W/O Acceleration", "Standard BO", "Hill Climbing", "BOOM-Explorer"]
IS = {
    'Dhrystone': [21, 25, 8, 28],
    'qsort': [25, 23, 9, 27],
    'mt-matmul': [29, 32, 9, 31],
    'median': [26, 26, 10, 30]
}
ADRS = {
    'Dhrystone': [90.48, 95.33, 97.33, 91.64],
    'qsort': [88.83, 95.57, 98.62, 90.17],
    'mt-matmul': [56.48, 82.35, 88.53, 73.43],
    'median': [66.07, 77.33, 93.21, 68.22]
}


for i in range(4):
    print("Name: ", name[i])
    avg = 0
    for j in ADRS.keys():
        avg += ADRS[j][i]
    print("Average: ", 100 - avg/4)
    if i == 1 or i == 3:
        is_avg = 0
        for j in IS.keys():
            is_avg += IS[j][0]/IS[j][i]
        print("IS Average: ", 1 - is_avg/4)

# Prepare data for plotting
labels = list(IS.keys())
is_values = np.array(list(IS.values()))
adrs_values = np.array(list(ADRS.values()))
x = np.arange(len(labels))  # the label locations
width = 0.15  # the width of the bars

turq = (40, 161, 151)
darkblue = (18, 67, 109)
dark_pink = (128, 22, 80)
orange = (244, 106, 37)
turq = tuple([i / 255 for i in turq])
darkblue = tuple([i / 255 for i in darkblue])
dark_pink = tuple([i / 255 for i in dark_pink])
orange = tuple([i / 255 for i in orange])
colors = [darkblue, orange, turq, dark_pink]

# Plotting IS
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 4))
for i in range(len(name)):
    ax1.bar(x + i * width, is_values[:, i], width, label=name[i], color=colors[i])

# Add some text for labels, title and custom x-axis tick labels, etc.

ax1.set_ylabel('IC', fontweight='bold')
ax1.set_title('IC in Four Benchmarks', fontweight='bold')
ax1.set_xticks(x + width * 1.5)
ax1.set_xticklabels(labels)


# Plotting ADRS
for i in range(len(name)):
    ax2.bar(x + i * width, adrs_values[:, i], width, label=name[i], color=colors[i])

# Add some text for labels, title and custom x-axis tick labels, etc.

ax2.set_ylabel('ETR', fontweight='bold')
ax2.set_title('ETR in Four Benchmarks', fontweight='bold')
ax2.set_xticks(x + width * 1.5)
ax2.set_xticklabels(labels)
ax2.set_ylim(50, 100)

handles, labels = ax2.get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, -0.01), fancybox=True, shadow=False, ncol=6, fontsize='large')

fig.tight_layout()
plt.subplots_adjust(bottom=0.2)
plt.savefig('../plot_results/RocketChip_FPGA_1.pdf')
# plt.show()
