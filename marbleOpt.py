from marble_coaster import calc_cost, calc_length, solve_track
from MultiObjectiveOptimizer import MultiObjectiveOptimizer
from numpy import random
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import sys
sys.setrecursionlimit(200)

plt.ion()
fig = plt.figure(1)
# fig = plt.figure(2)
ax = fig.add_subplot(111)
# ax2 = fig.add_subplot(122)
ax.autoscale_view(True, True, True)
# ax2.autoscale_view(True, True, True)
plt.show()

def plot_front(generation):
    plt.ion()
    if len(ax.lines) > 4:
        del ax.lines[0]
    ax.plot(-generation[:, 1], generation[:, 2], 'o')
    plt.xlabel('Length')
    plt.ylabel('Cost')
    plt.title('Marble Coaster Pareto Front')
    ax.relim()
    plt.pause(0.01)
    plt.show()

def check_design(design):
    gene_per_section = 2

    num_div_x = 3
    num_div_y = 3
    num_div_z = 3

    # try:

    design = design.astype(int)
    t_length, t_cost, p_list, p_loc, r_list, e_list = solve_track(design)

    return [-t_length, t_cost]



if __name__ == "__main__":
    # thread = threading.Thread(target=opt_coaster)
    # thread.start()
    design_space = []
    for i in range(10**3):
        design_space.append({'type': 'integer', 'bounds': (0, 5)})
        design_space.append({'type': 'integer', 'bounds': (0, 4)})
    optimizer = MultiObjectiveOptimizer(design_space, check_design, n_generations=1000, population_size=20,
                                        n_objectives=2, generation_func=plot_front)
    opts = optimizer.find_min()

    np.savetxt('optmimum_coasters.csv', opts, delimiter=',')
    plt.savefig("pareto_front.pdf")