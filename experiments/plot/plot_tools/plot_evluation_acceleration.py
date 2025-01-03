import matplotlib.pyplot as plt
import numpy as np
import matplotlib
# matplotlib.rcParams['font.family'] = 'Times New Roman'
matplotlib.rcParams['font.size'] = 12.5

frame_work_name = ["Framework without acceleration", "Framework without config matcher", "Our framework"]
avg_rocket_chip_eval = [45.4, 25.7, 20.1]
avg_boom_eval = [61.2, 41.2, 34.1]
x_labels = ['RocketChip', 'BOOM']

# Number of categories (CPU types)
n_categories = 2
# Number of frameworks
n_frameworks = len(frame_work_name)

# Width of each bar
bar_width = 0.15

# Create figure and axis objects with a specific size
fig, ax = plt.subplots(figsize=(8, 4))  # 10 inches wide by 6 inches tall

# Calculating the index for each set of bars
index = np.arange(n_categories) * (n_frameworks * bar_width + 0.1)  # Smaller gap between groups

turq = (40, 161, 151)
darkblue = (18, 67, 109)
dark_pink = (128, 22, 80)
orange = (244, 106, 37)
turq = tuple([i / 255 for i in turq])
darkblue = tuple([i / 255 for i in darkblue])
dark_pink = tuple([i / 255 for i in dark_pink])
orange = tuple([i / 255 for i in orange])
colors = [darkblue, orange, turq, dark_pink]

# Plotting data
for i in range(n_frameworks):
    bar_positions = index + i * bar_width
    ax.bar(bar_positions, [avg_rocket_chip_eval[i], avg_boom_eval[i]], bar_width, label=frame_work_name[i], color=colors[i])

# Adding labels, title, and axes ticks
# ax.set_xlabel('CPU Type')
ax.set_ylabel('Average Evaluation Time (mins)')
# ax.set_title('Comparison of Average Evaluation Times by CPU Type')
ax.set_xticks(index + bar_width * (n_frameworks - 1) / 2)
ax.set_xticklabels(x_labels)

# Adjust the axis to shrink the bar chart area
ax.set_position([0.1, 0.1, 0.5, 0.8])  # [left, bottom, width, height]

# Adding a legend to the right of the plot, making it larger
ax.legend(loc='center left', bbox_to_anchor=(1, 0.1, 0.3, 0.8), title='Evaluation Frameworks', shadow=False, frameon=False)

plt.savefig('../plot_results/Average_Evaluation_Times.pdf')
