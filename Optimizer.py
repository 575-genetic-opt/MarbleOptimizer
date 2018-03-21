import numpy as np
import matplotlib.pyplot as plt
import copy

class Optimizer:
    def __init__(self, x, fitness, n_generations=5, population_size=5, constraint=None):
        """Initialize the optimizer
        x: list that contains a series of dictionaries that define the x values for the optimizer where
        type is either continuous or integer. and min and max are the minimum and maximum values of the variable this
        should follow the form [{'type': ('integer' or 'continuous'), 'bounds': (min, max)]] with a new dict for each
        x value

        fitness: function that accepts x array in the same order as given in the x input, and returns the fitness of
        each design.

        n_generations: the number of generations to carry out

        population_size: the number of members in the population at each generation

        constraint: function that accepts x array in the same order as given in x and returns a vector that contains
        the constraint violation state of each constraint where >0 suggests that the constraint is violated and <=0
        suggests that the constraint is satisfied.
        """
        self.num_generations = n_generations
        self.num_population = np.trunc(population_size)
        if self.num_population % 2 != 0:
            self.num_population += 1
        self.num_population = int(self.num_population)
        self.num_x = len(x)
        self.fitness_func = fitness
        self.x_def = x
        # self.variable_types = np.zeros(self.num_x)

        self.tournament_size = 1
        self.crossover_prob = 0.7
        self.mutation_prob = 0.2
        self.cross_eta = 0.5
        self.mutation_beta = 0.01

        # initialize the parent array
        # stored in the form ([fitness, x1, x2, x3, ..., xn])
        self.population = np.zeros((self.num_population, self.num_x + 1))
        for i in range(self.num_population):
            x_new = np.zeros(self.num_x)
            for j, val in enumerate(x):
                if val['type'] == 'integer':
                    x_new[j] = np.random.randint(val['bounds'][0], val['bounds'][1]+1)
                elif val['type'] == 'continuous':
                    x_new[j] = np.random.uniform(val['bounds'][0], val['bounds'][1])
                else:
                    print("error unknown variable type")
            self.population[i, 0] = self.fitness_func(x_new)
            self.population[i, 1:] = x_new
        self.population = sort_array_by_col(self.population, 0)
        return


    def select_parents(self):
        """select the parents from the current population of the optimization"""
        # randomize the order of the population
        np.random.shuffle(self.population)
        # preallocate the array to hold the parents
        parents = np.zeros_like(self.population)
        # select random people from the population for tournament selection
        for row in range(parents.shape[0]):
            rand_indicies = np.random.randint(parents.shape[0], size=self.tournament_size)
            competitors = self.population[rand_indicies]
            sorted_competitors = sort_array_by_col(competitors, 0)
            parents[row, :] = sorted_competitors[-1]
        return parents


    def find_max(self):
        generations = []
        for generation in range(self.num_generations):
            # select reproducing parents
            parents = self.select_parents()
            children = np.zeros_like(parents)
            # for each set of parents
            for idx in range(0, parents.shape[0], 2):
                child1 = copy.deepcopy(parents[idx, 1:])
                child2 = copy.deepcopy(parents[idx+1, 1:])
                for x_idx in range(len(child1)):
                    crossover = np.random.random()
                    mutate1 = np.random.random()
                    mutate2 = np.random.random()
                    if crossover < self.crossover_prob:
                        # perform the crossover
                        r = np.random.random()
                        if r <= 0.5:
                            a = ((2 * r) ** (1/self.cross_eta)) / 2
                        else:
                            a = 1 - ((2 - 2 * r)**(1/self.cross_eta)) / 2
                        child1_val = child1[x_idx]
                        child2_val = child2[x_idx]
                        y1 = a * child1_val + (1-a) * child2_val
                        y2 = (1-a) * child1_val + a * child2_val
                        child1[x_idx] = y1
                        child2[x_idx] = y2
                        # truncate the values if needed
                        if self.x_def[x_idx]['type'] == 'integer':
                            child1[x_idx] = np.round(child1[x_idx])
                            child2[x_idx] = np.round(child2[x_idx])

                    if mutate1 < self.mutation_prob:
                        child1 = self.mutate(child1, x_idx, self.x_def[x_idx]['bounds'],
                                             self.x_def[x_idx]['type'], generation)

                    if mutate2 < self.mutation_prob:
                        child2 = self.mutate(child2, x_idx, self.x_def[x_idx]['bounds'],
                                             self.x_def[x_idx]['type'], generation)
                # put the children into the children array
                child1_fitness = self.fitness_func(child1)
                child2_fitness = self.fitness_func(child2)
                children[idx, 0] = child1_fitness
                children[idx, 1:] = child1
                children[idx+1, 0] = child2_fitness
                children[idx+1, 1:] = child2
            # perform elitism
            population_pool = np.append(parents, children, axis=0)
            sorted_pool = sort_array_by_col(population_pool, 0)
            self.population = sorted_pool[self.num_population:]
            generations.append(copy.deepcopy(self.population))
        return generations


    def mutate(self, child, idx, bounds, type, generation):
        min = bounds[0]
        max = bounds[1]
        r = np.random.uniform(min, max)
        alpha = (1 - (generation - 1) / self.num_generations) ** self.mutation_beta
        if r <= child[idx]:
            child[idx] = min + (r - min) ** alpha * (child[idx] - min) ** (1 - alpha)
        else:
            child[idx] = max - (max - r) ** alpha * (max - child[idx]) ** (1 - alpha)
        if type == 'integer':
            child[idx] = np.round(child[idx])
        return child


def fitt(x):
    if x[1] > 5:
        ret = x[0]**2 - x[1] - x[2]
    else:
        ret = x[0]**3 + x[1] - x[2]
    ret_val = abs(ret) ** np.random.random()
    # ret = x[1]
    return ret_val


def sort_array_by_col(array, sort_col=0):
    """take an array and sort it by the specified column"""
    new_array = array[np.argsort(array[:, sort_col])]
    return new_array

def hw5(x):
    f = 2 + 0.2 * x[0] ** 2 + 0.2 * x[1]**2 - np.cos(np.pi * x[0]) - np.cos(np.pi * x[1])
    return -f


if __name__ == "__main__":
    # z = [{'type': 'integer', 'bounds': (2, 7)},
    #      {'type': 'continuous', 'bounds': (1, 11)},
    #      {'type': 'continuous', 'bounds': (1, 9)}]
    hw_types = [{'type': 'continuous', 'bounds': (-5, 5)},
                {'type': 'continuous', 'bounds': (-5, 5)}]

    opt = Optimizer(hw_types, hw5, n_generations=10, population_size=10)
    generations = opt.find_max()
    sorted_pop = sort_array_by_col(opt.population)
    print(opt.population)
    print(sorted_pop[-1])
    x = np.linspace(-5, 5, 500)
    y = np.linspace(-5, 5, 500)

    xx, yy = np.meshgrid(x, y)
    zz = hw5([xx, yy])
    plt.contour(xx, yy, zz, 20)

    colors = ['bo', 'go', 'ro', 'co', 'mo']
    labels = ['generation 1', 'generation 2', 'generation 3', 'generation 4', 'generation 5']
    for color, generation, label in zip(colors, (generations[0::2]), labels):
        fitness = generation[:, 0]
        mean_fitness = np.average(fitness)
        max_fitness = np.max(fitness)
        x_vals = generation[:, 1]
        y_vals = generation[:, 2]
        plt.plot(x_vals, y_vals, color, label=label + '\nAvg. Fit: ' + str(mean_fitness)[0:5] + '\nMax Fit: ' + str(max_fitness)[0:5], alpha=0.7)
    plt.legend()
    plt.show()
