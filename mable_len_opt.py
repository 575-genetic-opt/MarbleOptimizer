from marble_coaster import calc_cost, calc_length
from MultiObjectiveOptimizer import MultiObjectiveOptimizer
from numpy import random
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import sys
# sys.setrecursionlimit(200)

plt.ion()
max_lengths = []
min_lengths = []
length_range = []
fig = plt.figure(1)
# fig = plt.figure(2)
ax = fig.add_subplot(211)
ax2 = fig.add_subplot(212)
# ax2 = fig.add_subplot(122)
ax.autoscale_view(True, True, True)
# ax2.autoscale_view(True, True, True)
plt.show()

def plot_progression(generation):
    plt.ion()
    # if len(ax.lines) > 4:
    #     del ax.lines[0]
    max_len = -np.min(generation[:, 1])
    min_len = -np.max(generation[:, 1])
    max_lengths.append(max_len)
    min_lengths.append(min_len)
    length_range.append(max_len - min_len)
    if len(max_lengths) % 1 == 0:
        ax.clear()
        ax2.clear()
        ax.plot(range(len(max_lengths)), max_lengths, 'b', label='max length')
        ax.plot(range(len(min_lengths)), min_lengths, 'r', label='min length')
        ax2.plot(range(len(length_range)), length_range, 'g', label='length range')
        ax.legend()
        ax2.legend()
        # ax.plot(generation[:, 1], generation[:, 2], 'o')
        # ax.set_xlabel('Generation')
        ax2.set_xlabel('Generation')
        plt.ylabel('Length')
        # plt.title('Genetic Optimizer Progression')
        # ax.relim()
        plt.pause(0.1)
        plt.show()

def check_design(design):

    # try:
    design = design.astype(int)
    length = -calc_length(design)
    # cost = calc_cost(design)

    return [length]



if __name__ == "__main__":
    # thread = threading.Thread(target=opt_coaster)
    # thread.start()
    design_space = []
    for i in range(10**3):
        design_space.append({'type': 'integer', 'bounds': (1, 5)})
        design_space.append({'type': 'integer', 'bounds': (0, 4)})
    optimizer = MultiObjectiveOptimizer(design_space, check_design, n_generations=2000, population_size=300,
                                        n_objectives=1, generation_func=plot_progression)
    opts = optimizer.find_min()
    print(-np.min(opts[:, 1]))


    # np.savetxt('optmimum_coasters.csv', opts, delimiter=',')
    # plt.savefig("pareto_front.pdf")