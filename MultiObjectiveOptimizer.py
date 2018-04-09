import numpy as np
import copy


class MultiObjectiveOptimizer:
    def __init__(self, x, fitness, n_generations=5, population_size=5, n_objectives=2, constraint=None,
                 generation_func=None, constraint_func_input="design", crossover_type="uniform",
                 mutation_type="unifom", use_genocide=False):
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

        crossover_type: string, either "transitional" or "uniform" if transitional a transitional crossover is performed
        if uniform a uniform crossover, meaning that the values are simply swapped is performed

        mutation_type: string, either "uniform" or "dynamic" this defines the type of mutation that will occur.
        dynamic mutation changes more at the beginning of the optimization and less toward the end. Uniform mutation
        randomly selects a value in the bounds.
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
        self.constraint_func_input = constraint_func_input.lower()
        self.crossover_type = crossover_type.lower()
        self.mutation_type = mutation_type.lower()
        self.use_genocide = use_genocide

        self.tournament_size = 2
        self.crossover_prob = 0.5
        self.mutation_prob = 0.13
        self.cross_eta = 0.5
        self.mutation_beta = 0.13

        self.no_diversity_counter = 0
        self.population = self.generate_population()

        return

    def generate_population(self):
        # initialize population array
        # stored in the form ([fitness, objective values, x1, x2, x3, ..., xn])
        population = np.zeros((self.num_population, self.num_x + self.num_objectives + 1))
        for i in range(self.num_population):
            x_new = np.zeros(self.num_x)
            for j, val in enumerate(self.x_def):
                if val['type'] == 'integer':
                    x_new[j] = np.random.randint(val['bounds'][0], val['bounds'][1] + 1)
                elif val['type'] == 'continuous':
                    x_new[j] = np.random.uniform(val['bounds'][0], val['bounds'][1])
                # else:
                #     print("error unknown variable type")
            population[i, 1:self.num_objectives + 1] = self.fitness_func(x_new)
            population[i, self.num_objectives + 1:] = x_new
        population = sort_array_by_col(population, 0)
        population = self.calc_fitness(population)
        population = self.apply_constraints(population)
        if self.generation_call is not None:
            self.generation_call(population)
        return population

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

    def calc_fitness(self, population):
        """calculates the maximin values for each point of the supplied population.  Uses a bunch of information stored
        in the class, so probably not a good idea to pass in random populations, unless you know what you're doing."""
        if self.num_objectives > 1:
            for idx in range(population.shape[0]):
                # get function values
                fVals = copy.deepcopy(population[:, 1:self.num_objectives+1])
                for col_idx in range(self.num_objectives):
                    test_val = fVals[idx, col_idx]
                    fVals[:, col_idx] = -(fVals[:, col_idx] - test_val)
                fVals = np.delete(fVals, idx, 0)
                population[idx, 0] = np.nanmax(np.nanmin(fVals, 1))
        else:
            population[:, 0] = population[:, 1]
        return population

    def check_diversity(self, population):
        """
        Checks that a population is diverse. If it is not the best members of the population are kept and the rest
        of the population is randomly regenerated.
        :param population: the population whose diversity is to be checked.
        :return: the new population
        """
        fitness_vals = population[:, 0]
        num_unique = len(np.unique(fitness_vals))
        if num_unique == 1:
            self.no_diversity_counter += 1
            if self.no_diversity_counter > 20:
                self.no_diversity_counter = 0
                num_to_save = int(self.num_population * 0.2)
                # sort the designs
                population = sort_array_by_col(population, 0)
                # save the best 10% of designs
                best_designs = copy.deepcopy(population[0:num_to_save, :])
                # regenerate the population
                new_population = self.generate_population()
                # replace the best designs
                new_population[0:num_to_save, :] = best_designs
                np.random.shuffle(new_population)
                return new_population
        else:
            self.no_diversity_counter = 0
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
            # else:
                # print("unrecognized constraint input term check constraint_func_input argument at initialization")
                # quit()
            if np.max(cons) > 0:
                row[0] = max_fitness + np.max(cons)
        return population

    def find_min(self):
        """
        Runs the optimizer.
        :return: the population at the end of the optimization routine.
        """
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
                        if self.crossover_type == "transitional":
                            self.crossover_transitional(child1, child2, x_idx)
                        else:
                            self.crossover_uniform(child1, child2, x_idx)
                    if mutate1 < self.mutation_prob:
                        if self.mutation_type == "dynamic":
                            child1 = self.mutate_dynamic(child1, x_idx, self.x_def[x_idx]['bounds'],
                                                         self.x_def[x_idx]['type'], generation)
                        else:
                            child1 = self.mutate_uniform(child1, x_idx, self.x_def[x_idx]['bounds'],
                                                         self.x_def[x_idx]['type'])
                    if mutate2 < self.mutation_prob:
                        if self.mutation_type == "dynamic":
                            child2 = self.mutate_dynamic(child2, x_idx, self.x_def[x_idx]['bounds'],
                                                         self.x_def[x_idx]['type'], generation)
                        else:
                            child1 = self.mutate_uniform(child1, x_idx, self.x_def[x_idx]['bounds'],
                                                         self.x_def[x_idx]['type'])
                # put the children into the children array
                child1_fitness = self.fitness_func(child1)
                child2_fitness = self.fitness_func(child2)
                children[idx, 1:self.num_objectives+1] = child1_fitness
                children[idx, self.num_objectives+1:] = child1
                children[idx + 1, 1:self.num_objectives+1] = child2_fitness
                children[idx + 1, self.num_objectives+1:] = child2
            # perform elitism
            population_pool = np.append(parents, children, axis=0)
            population_pool = self.calc_fitness(population_pool)
            population_pool = self.apply_constraints(population_pool)
            sorted_pool = sort_array_by_col(population_pool, 0)
            self.population = sorted_pool[0:self.num_population]
            # generations.append(copy.deepcopy(self.population))
            # print(generation)
            if self.use_genocide:
                self.population = self.check_diversity(self.population)
            if self.generation_call is not None:
                self.generation_call(self.population)
        return self.population

    def crossover_transitional(self, child1, child2, x_idx):
        """
        Performs a transitional crossover from uniform to blend between the two children at the specifiec index.
        The children must be numpy arrays or some other object that is mutable so that the changes persist
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

    def crossover_uniform(self, child1, child2, x_idx):
        """
        Performs a uniform crossover between the children at the specified x index
        :param child1: design 1 to be crossed
        :param child2: design 2 to be crossed
        :param x_idx: Index location for the crossover
        :return: none
        """
        r = np.random.random()
        if r <= 0.5:
            temp = child1[x_idx]
            child1[x_idx] = child2[x_idx]
            child2[x_idx] = temp

    def mutate_dynamic(self, child, idx, bounds, type, generation):
        """
        Perform a dynamic mutation on the child at the specified location
        meaning that the mutation amount decreases as the generation number increases
        :param child: array of values that represent the child to be mutated
        :param idx: the index where the mutation should occur
        :param bounds: tuple of the bounds of the value that is being mutated
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

    def mutate_uniform(self, child, idx, bounds, type):
        """
        Perform a mutation of the child at the specified index. The mutation is uniform meaning that it will
        be randomly assigned in the bounds of the value.
        :param child: the design that is to be mutated
        :param idx: the index of the value where the mutation should occur
        :param bounds: tuple of the bounds on the variable that we are mutating
        :param type: the type of the variable
        :return: the mutated child
        """
        min = bounds[0]
        max = bounds[1]
        if type == 'integer':
            child[idx] = np.random.randint(min, max+1)
        else:
            child[idx] = np.random.uniform(min, max+0.000001)
        return child

def sort_array_by_col(array, sort_col=0):
    """take an array and sort it by the specified column"""
    new_array = array[np.argsort(array[:, sort_col])]
    return new_array

