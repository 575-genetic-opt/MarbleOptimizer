from Optimizer import sort_array_by_col
import numpy as np
import matplotlib.pyplot as plt
import copy


class MultiObjectiveOptimizer:
    def __init__(self, x, fitness, n_generations=5, population_size=5, n_objectives=2, constraint=None,
                 generation_func=None, constraint_func_input="design"):
        """Initialize the optimizer
        x: list that contains a series of dictionaries that define the x values for the optimizer where
        type is either continuous or integer. and min and max are the minimum and maximum values of the variable this
        should follow the form [{'type': ('integer' or 'continuous'), 'bounds': (min, max)]] with a new dict for each
        x value

        fitness: function that accepts x array in the same order as given in the x input, and returns the fitness of
        each design.

        n_generations: the number of generations to carry out

        population_size: the number of members in the population at each generation

        n_objectives: the number of objectives that are returned by the fitness function

        constraint: function that accepts x array in the same order as given in x and returns a vector that contains
        the constraint violation state of each constraint where >0 suggests that the constraint is violated and <=0
        suggests that the constraint is satisfied.

        generation_func: function that is called with each passing generation.  calls the generation function with
        the current population of the algorithm.  This is useful for things like plotting the generation at each
        iteration of the algorithm, but could be used for other fun things

        constraint_func_input: string, either "design" or "full" if design the constraint function is called with just
        the design, if full the constraint function is called with a 1d array where the 0th value is the maximin fitness
        of the design, the next n values are the n objectives returned by the fitness function, and the last n values
        are the n values that define the design.  It is useful to define full if the fitness and constraints are based
        on the same values and they are somewhat expensive to obtain.
        """
        self.num_generations = n_generations
        self.num_population = np.trunc(population_size)
        if self.num_population % 2 != 0:
            self.num_population += 1
        self.num_population = int(self.num_population)
        self.num_x = len(x)
        self.fitness_func = fitness
        self.constraint_func = constraint
        self.x_def = x
        self.num_objectives = n_objectives
        self.generation_call = generation_func
        self.constraint_func_input = constraint_func_input

        self.tournament_size = 2
        self.crossover_prob = 0.5
        self.mutation_prob = 0.13
        self.cross_eta = 0.5
        self.mutation_beta = 0.13

        # initialize the parent array
        # stored in the form ([fitness, x1, x2, x3, ..., xn])
        self.population = np.zeros((self.num_population, self.num_x + n_objectives + 1))
        for i in range(self.num_population):
            x_new = np.zeros(self.num_x)
            for j, val in enumerate(x):
                if val['type'] == 'integer':
                    x_new[j] = np.random.randint(val['bounds'][0], val['bounds'][1] + 1)
                elif val['type'] == 'continuous':
                    x_new[j] = np.random.uniform(val['bounds'][0], val['bounds'][1])
                else:
                    print("error unknown variable type")
            self.population[i, 1:n_objectives+1] = self.fitness_func(x_new)
            self.population[i, n_objectives+1:] = x_new
        self.population = sort_array_by_col(self.population, 0)
        self.population = self.calc_maximin(self.population)
        self.population = self.apply_constraints(self.population)
        if self.generation_call is not None:
            self.generation_call(self.population)
        return

    def select_parents(self):
        """select the parents from the current population of the optimization"""
        # randomize the order of the population
        np.random.shuffle(self.population)
        # preallocate the array to hold the parents
        parents = np.zeros_like(self.population)
        # self.population = self.calc_maximin(self.population)
        # select random people from the population for tournament selection
        for row in range(parents.shape[0]):
            rand_indicies = np.random.randint(parents.shape[0], size=self.tournament_size)
            competitors = self.population[rand_indicies]
            sorted_competitors = sort_array_by_col(competitors, 0)
            parents[row, :] = sorted_competitors[0]
        return parents

    def calc_maximin(self, population):
        """calculates the maximin values for each point of the supplied population.  Uses a bunch of information stored
        in the class, so probably not a good idea to pass in random populations, unless you know what you're doing."""
        for idx in range(population.shape[0]):
            # get function values
            fVals = copy.deepcopy(population[:, 1:self.num_objectives+1])
            for col_idx in range(self.num_objectives):
                test_val = fVals[idx, col_idx]
                fVals[:, col_idx] = -(fVals[:, col_idx] - test_val)
            fVals = np.delete(fVals, idx, 0)
            population[idx, 0] = np.nanmax(np.nanmin(fVals, 1))
        return population

    def apply_constraints(self, population):
        """ applies appropriate penalties for designs that are outside of the permissible bounds.  Requires that a
        constraint function be defined that returns the constraints in a row vector"""
        if self.constraint_func is None:
            return population
        max_fitness = np.nanmax(population[:, 0])
        for row in population:
            design = row[self.num_objectives+1:]
            if self.constraint_func_input == "design":
                cons = self.constraint_func(design)
            elif self.constraint_func_input == "full":
                cons = self.constraint_func(row)
            else:
                print("unrecognized constraint input term check constraint_func_input argument at initialization")
                quit()
            if np.max(cons) > 0:
                row[0] = max_fitness + np.max(cons)
        return population


    def find_min(self):
        generations = []
        for generation in range(self.num_generations):
            # select reproducing parents
            parents = self.select_parents()
            children = np.zeros_like(parents)
            # for each set of parents
            for idx in range(0, parents.shape[0], 2):
                child1 = copy.deepcopy(parents[idx, self.num_objectives+1:])
                child2 = copy.deepcopy(parents[idx+1, self.num_objectives+1:])
                for x_idx in range(len(child1)):
                    crossover = np.random.random()
                    mutate1 = np.random.random()
                    mutate2 = np.random.random()
                    if crossover < self.crossover_prob:
                        # perform the crossover
                        self.crossover(child1, child2, x_idx)
                    if mutate1 < self.mutation_prob:
                        child1 = self.mutate(child1, x_idx, self.x_def[x_idx]['bounds'],
                                             self.x_def[x_idx]['type'], generation)
                    if mutate2 < self.mutation_prob:
                        child2 = self.mutate(child2, x_idx, self.x_def[x_idx]['bounds'],
                                             self.x_def[x_idx]['type'], generation)
                # put the children into the children array
                child1_fitness = self.fitness_func(child1)
                child2_fitness = self.fitness_func(child2)
                children[idx, 1:self.num_objectives+1] = child1_fitness
                children[idx, self.num_objectives+1:] = child1
                children[idx + 1, 1:self.num_objectives+1] = child2_fitness
                children[idx + 1, self.num_objectives+1:] = child2
            # perform elitism
            population_pool = np.append(parents, children, axis=0)
            population_pool = self.calc_maximin(population_pool)
            population_pool = self.apply_constraints(population_pool)
            sorted_pool = sort_array_by_col(population_pool, 0)
            self.population = sorted_pool[0:self.num_population]
            # generations.append(copy.deepcopy(self.population))
            print(generation)
            if self.generation_call is not None:
                self.generation_call(self.population)
        return self.population

    def crossover(self, child1, child2, x_idx):
        """
        Performs crossover between the two children at the specifiec index.  The children must be numpy arrays or
        some other object that is mutable so that the changes persist
        :param child1: Child 1 to be crossed a numpy array of the values
        :param child2: Child 2 to be crossed a numpy array of the values
        :param x_idx: Index location for the crossover.
        :return: none
        """
        r = np.random.random()
        if r <= 0.5:
            a = ((2 * r) ** (1 / self.cross_eta)) / 2
        else:
            a = 1 - ((2 - 2 * r) ** (1 / self.cross_eta)) / 2
        child1_val = child1[x_idx]
        child2_val = child2[x_idx]
        y1 = a * child1_val + (1 - a) * child2_val
        y2 = (1 - a) * child1_val + a * child2_val
        child1[x_idx] = y1
        child2[x_idx] = y2
        # truncate the values if needed
        if self.x_def[x_idx]['type'] == 'integer':
            child1[x_idx] = int(np.round(child1[x_idx]))
            child2[x_idx] = int(np.round(child2[x_idx]))

    def mutate(self, child, idx, bounds, type, generation):
        """
        Perform a mutation on the child at the specified location
        :param child: array of values that represent the child to be mutated
        :param idx: the index where the mutation should occur
        :param bounds: bound of the value that is being mutated
        :param type: Type of the variable
        :param generation: generation number for the mutation.
        :return: the mutated child
        """
        min = bounds[0]
        max = bounds[1]
        r = np.random.uniform(min, max)
        alpha = (1 - (generation) / self.num_generations) ** self.mutation_beta
        if r <= child[idx]:
            child[idx] = min + (r - min) ** alpha * (child[idx] - min) ** (1 - alpha)
        else:
            child[idx] = max - (max - r) ** alpha * (max - child[idx]) ** (1 - alpha)
        if type == 'integer':
            child[idx] = np.round(child[idx])
        return child

def calc_fitness(x):
    width = x[0]
    height = x[1]

    length = 20
    force = 10
    modulus = 39000000
    density = 4.65 / 16

    max_weight = 200
    max_defl = 2

    deflection = (force * length**3) / (3 * modulus * (width * height**3)/12)
    # deflection = saturate(deflection, max_defl)/max_defl
    weight = length * width * height * density
    # weight = saturate(weight, max_weight)/max_weight
    return [deflection, weight]

def calc_fitness2(x):
    width = x[0]
    height = x[1]

    length = 20
    force = 10
    modulus = 39000000
    density = 4.65 / 16

    max_weight = 200
    max_defl = 2

    deflection = (force * length**3) / (3 * modulus * (width * height**3)/12)
    # deflection = saturate(deflection, max_defl)/max_defl
    weight = length * width * height * density
    # weight = saturate(weight, max_weight)/max_weight
    return [deflection]

def calc_constraints(x):
    width = x[0]
    height = x[1]

    length = 20
    force = 10
    modulus = 39000000
    density = 4.65 / 16

    max_deflection = 0.04
    max_weight = 10
    max_stress = 36000

    moment = length * force
    I = (width * height ** 3) / 12
    stress = moment * (height / 2) / I
    stress_constraint = (stress - max_stress) / max_stress

    deflection = (force * length ** 3) / (3 * modulus * (width * height ** 3) / 12)
    deflection_constraint = (deflection - max_deflection) / max_deflection

    weight = length * width * height * density
    weight_constraint = (weight - max_weight) / max_weight
    return [deflection_constraint, weight_constraint, stress_constraint]

def saturate(val, max_val):
    if val > max_val:
        val = max_val
    return val

if __name__ == "__main__":
    z = [{'type': 'continuous', 'bounds': (0, 2)},
         {'type': 'continuous', 'bounds': (0, 2)}]
    n_gen = 100
    opt = MultiObjectiveOptimizer(z, calc_fitness2, n_objectives=1, population_size=10, n_generations=n_gen,
                                  constraint=calc_constraints)
    # opt.calc_maximin(opt.population)
    generations = opt.find_min()

    # x_start = generations[0][:, 1]
    # y_start = generations[0][:, 2]
    #
    # x_middle = generations[int(n_gen/2)-1][:, 1]
    # y_middle = generations[int(n_gen/2)-1][:, 2]
    #
    # x_end = generations[-1][:, 1]
    # y_end = generations[-1][:, 2]

    # plt.plot(x_start, y_start, 'o', label='1st generation')
    # plt.plot(x_middle, y_middle, 'o', label='middle generation', alpha=0.5)
    # plt.plot(x_end, y_end, 'o', label='last generation', alpha=0.5)
    # plt.xlabel('deflection')
    # plt.ylabel('weight')
    # plt.title('weight vs. deflection pareto front')
    # # plt.xlim((0, 0.025))
    # # plt.ylim((0, 10))
    # plt.legend()
    # plt.show()

    plt.ion()
    for i, generation in enumerate(generations):
        # if i > 5:
        #     points.clear()
        points = plt.plot(generation[:, 1], generation[:, 2], 'o')
        plt.xlim((0, 0.05))
        plt.ylim((0, 3))
        plt.xlabel('deflection')
        plt.ylabel('weight')
        plt.title('weight vs. deflection pareto front')
        # plt.xlim((0, 1))
        # plt.ylim((0, 1))
        plt.pause(0.5)

