import random
import math
import sys

sys.setrecursionlimit(200)
gene_per_section = 2

num_div_x = 10
num_div_y = 10
num_div_z = 10

maximum_length = 0
corresponding_cost = 0

parts = [{'cost': 1., 'length': 10., 'cool': 90, 'in': 'top', 'out': 'bottom'},
         {'cost': 3., 'length': 7.5, 'cool': 50, 'in': 'top', 'out': 1},
         {'cost': 1., 'length': 10., 'cool': 70, 'in': 1, 'out': 3},
         {'cost': 3., 'length': 7.5, 'cool': 50, 'in': 1, 'out': 4},
         {'cost': 3., 'length': 7.5, 'cool': 50, 'in': 1, 'out': 'bottom'}]


def calc_length(design):

    # RECORD MAX POSSIBLE PATH
    max_path = 0

    # LOOP OVER PIECES ON BOTTOM
    for i in range(0, num_div_x*num_div_y*gene_per_section, gene_per_section):

        length = 0

        # IF THERE IS A PIECE PRESENT AT THIS LOCATION
        if design[i] > 0:

            # GET LOCATION ID OF PIECE
            piece_number = int(i / gene_per_section) + 1

            inlet, outlet, location = inlet_outlet(design, piece_number)

            if outlet is not None and outlet > 0:
                path_history = []
                length = traverse_length(design, piece_number, path_history)

        if length > max_path:
            max_path = length

    return max_path


def locate_piece(piece_number):

    floor = int(math.ceil(float(piece_number)/float(num_div_x*num_div_y))) % num_div_z
    if floor == 0:
        floor = num_div_z

    local_num = piece_number % (num_div_x * num_div_y)  # THIS IS THE PIECE NUMBER LOCAL TO IT'S OWN FLOOR
    row = int(math.ceil(float(local_num) / float(num_div_x))) % num_div_y
    if row == 0:
        row = num_div_y

    col = piece_number % num_div_x
    if col == 0:
        col = num_div_x

    return row, col, floor


def inlet_outlet(design, piece_number):

    # GET PIECE INFORMATION
    piece_gene_index = (piece_number-1)*gene_per_section
    piece_type = parts[design[piece_gene_index] - 1]

    # GET OUTLET FACE ID
    outlet = piece_type['out']
    if type(piece_type['out']) == int:
        outlet = (piece_type['out'] + design[(piece_number-1)*gene_per_section + 1]) % 4
        if outlet == 0:
            outlet = 4

    # GET INLET FACE ID
    inlet = piece_type['in']
    if type(piece_type['in']) == int:
        inlet = (piece_type['in'] + design[(piece_number - 1) * gene_per_section + 1]) % 4
        if inlet == 0:
            inlet = 4

    # GET ROW AND COLUMN ID OF PIECE
    row, col, floor = locate_piece(piece_number)
    location = (row, col, floor)

    out_neighbor = None
    in_neighbor = None

    if outlet == 'bottom' and floor > 1:
        out_neighbor = piece_number - num_div_x*num_div_y
    if inlet == 'top' and floor < num_div_z:
        in_neighbor = piece_number + num_div_x*num_div_y

    if row == 1:  # ON BOTTOM FACE
        if col == 1:  # ON LEFT FACE
            if outlet == 1:  # INTERIOR FACE
                out_neighbor = piece_number + num_div_x
            elif outlet == 2:
                out_neighbor = piece_number + 1  # INTERIOR FACE
            if inlet == 1:  # INTERIOR FACE
                in_neighbor = piece_number + num_div_x
            elif inlet == 2:
                in_neighbor = piece_number + 1  # INTERIOR FACE
        elif col == num_div_x:  # ON RIGHT FACE
            if outlet == 1:  # INTERIOR FACE
                out_neighbor = piece_number + num_div_x
            elif outlet == 4:  # INTERIOR FACE
                out_neighbor = piece_number - 1
            if inlet == 1:  # INTERIOR FACE
                in_neighbor = piece_number + num_div_x
            elif inlet == 4:  # INTERIOR FACE
                in_neighbor = piece_number - 1
        else:  # MIDDLE COLUMN
            if outlet == 1:  # INTERIOR FACE
                out_neighbor = piece_number + num_div_x
            elif outlet == 2:  # INTERIOR FACE
                out_neighbor = piece_number + 1
            elif outlet == 4:  # INTERIOR FACE
                out_neighbor = piece_number - 1
            if inlet == 1:  # INTERIOR FACE
                in_neighbor = piece_number + num_div_x
            elif inlet == 2:  # INTERIOR FACE
                in_neighbor = piece_number + 1
            elif inlet == 4:  # INTERIOR FACE
                in_neighbor = piece_number - 1
    elif row == num_div_y:  # ON TOP FACE
        if col == 1:  # ON LEFT FACE
            if outlet == 3:  # INTERIOR FACE
                out_neighbor = piece_number - num_div_x
            elif outlet == 2:  # INTERIOR FACE
                out_neighbor = piece_number + 1
            if inlet == 3:  # INTERIOR FACE
                in_neighbor = piece_number - num_div_x
            elif inlet == 2:  # INTERIOR FACE
                in_neighbor = piece_number + 1
        elif col == num_div_x:  # ON RIGHT FACE
            if outlet == 3:  # FACING INTERIOR
                out_neighbor = piece_number - num_div_x
            elif outlet == 4:  # INTERIOR FACE
                out_neighbor = piece_number - 1
            if inlet == 3:  # FACING INTERIOR
                in_neighbor = piece_number - num_div_x
            elif inlet == 4:  # INTERIOR FACE
                in_neighbor = piece_number - 1
        else:  # MIDDLE COLUMN
            if outlet == 3:  # FACING INTERIOR
                out_neighbor = piece_number - num_div_x
            elif outlet == 4:  # INTERIOR FACE
                out_neighbor = piece_number - 1
            elif outlet == 2:  # INTERIOR FACE
                out_neighbor = piece_number + 1
            if inlet == 3:  # FACING INTERIOR
                in_neighbor = piece_number - num_div_x
            elif inlet == 4:  # INTERIOR FACE
                in_neighbor = piece_number - 1
            elif inlet == 2:  # INTERIOR FACE
                in_neighbor = piece_number + 1
    else:  # IN MIDDLE ROW
        if col == 1:  # ON LEFT FACE
            if outlet == 1:  # FACING INTERIOR
                out_neighbor = piece_number + num_div_x
            elif outlet == 3:  # INTERIOR FACE
                out_neighbor = piece_number - num_div_x
            elif outlet == 2:
                out_neighbor = piece_number + 1
            if inlet == 1:  # FACING INTERIOR
                in_neighbor = piece_number + num_div_x
            elif inlet == 3:  # INTERIOR FACE
                in_neighbor = piece_number - num_div_x
            elif inlet == 2:
                in_neighbor = piece_number + 1
        elif col == num_div_x:  # ON RIGHT FACE
            if outlet == 1:  # FACING INTERIOR
                out_neighbor = piece_number + num_div_x  # FACING INTERIOR
            elif outlet == 3:
                out_neighbor = piece_number - num_div_x  # FACING INTERIOR
            elif outlet == 4:  # FACING INTERIOR
                out_neighbor = piece_number - 1
            if inlet == 1:  # FACING INTERIOR
                in_neighbor = piece_number + num_div_x  # FACING INTERIOR
            elif inlet == 3:
                in_neighbor = piece_number - num_div_x  # FACING INTERIOR
            elif inlet == 4:  # FACING INTERIOR
                in_neighbor = piece_number - 1
        else:  # INTERIOR PIECE
            if outlet == 1:  # FACING EXTERIOR
                out_neighbor = piece_number + num_div_x
            elif outlet == 3:  # FACING INTERIOR
                out_neighbor = piece_number - num_div_x
            elif outlet == 2:  # FACING INTERIOR
                out_neighbor = piece_number + 1
            elif outlet == 4:  # FACING INTERIOR
                out_neighbor = piece_number - 1
            if inlet == 1:  # FACING EXTERIOR
                in_neighbor = piece_number + num_div_x
            elif inlet == 3:  # FACING INTERIOR
                in_neighbor = piece_number - num_div_x
            elif inlet == 2:  # FACING INTERIOR
                in_neighbor = piece_number + 1
            elif inlet == 4:  # FACING INTERIOR
                in_neighbor = piece_number - 1

    # CHECK IF NEIGHBORS HAVE ALIGNING FACES
    if in_neighbor:

        in_gene_index = (in_neighbor - 1) * gene_per_section

        if design[in_gene_index] > 0:

            in_piece_type = parts[design[in_gene_index] - 1]

            in_n_outlet = in_piece_type['out']
            if type(in_piece_type['out']) == int:
                in_n_outlet = (in_piece_type['out'] + design[(in_neighbor - 1) * gene_per_section + 1]) % 4
                if in_n_outlet == 0:
                    in_n_outlet = 4

            if inlet == 'top':
                if in_n_outlet != 'bottom':
                    in_neighbor = -1
            elif in_n_outlet == 'bottom' or math.fabs(inlet - in_n_outlet) != 2:
                in_neighbor = -1

        else:

            in_neighbor = None

    if out_neighbor:

        out_gene_index = (out_neighbor - 1) * gene_per_section

        if design[out_gene_index] > 0:

            out_piece_type = parts[design[out_gene_index] - 1]

            out_n_inlet = out_piece_type['in']
            if type(out_piece_type['in']) == int:
                out_n_inlet = (out_piece_type['in'] + design[(out_neighbor - 1) * gene_per_section + 1]) % 4
                if out_n_inlet == 0:
                    out_n_inlet = 4

            if outlet == 'bottom':
                if out_n_inlet != 'top':
                    out_neighbor = -1
            elif out_n_inlet == 'top' or math.fabs(outlet - out_n_inlet) != 2:
                out_neighbor = -1

        else:

            out_neighbor = None

    return in_neighbor, out_neighbor, location


def traverse_length(design, piece_number, path_history):

    piece_gene_index = (piece_number - 1) * gene_per_section
    piece_type = parts[design[piece_gene_index] - 1]
    length = piece_type['length']

    in_neighbor, out_neighbor, location = inlet_outlet(design, piece_number)

    if in_neighbor is not None and in_neighbor > 0 and location not in path_history:
        path_history.append(location)
        length += traverse_length(design, in_neighbor, path_history)

    return length


def calc_cost(design):

    cost_sum = 0

    for i in range(0, len(design), gene_per_section):
        if design[i] > 0:
            part_num = design[i] - 1
            cost_sum += parts[part_num]['cost']

    return cost_sum


if __name__ == '__main__':


    gene_per_section = 2

    num_div_x = 3
    num_div_y = 3
    num_div_z = 3

    maximum_length = 0
    corresponding_cost = 0

    for i in range(1000000):
        if i % 10000 == 0:
            print(i)

        gen_design = [random.randrange(0, 5, 1) for r in range(num_div_x*num_div_y*num_div_z*gene_per_section)]

        # try:
        #     length_of_track = calc_length(gen_design)
        # except:
        #     length_of_track = 0

        length_of_track = calc_length(gen_design)

        if length_of_track >= maximum_length:
            maximum_length = length_of_track
            corresponding_cost = calc_cost(gen_design)
    # bad_design = [4, 4, 1, 4, 1, 1, 1, 1, 4, 1, 4, 4, 0, 3, 4, 2, 4, 3, 4, 0, 4, 2, 0, 4, 3, 1, 2, 2, 0, 2, 1, 4, 2,
    #               3, 0, 3, 0, 1, 2, 2, 4, 4, 1, 0, 3, 4, 3, 0, 0, 1, 1, 4, 4, 3]
    #
    # len = calc_length(bad_design)

    print(corresponding_cost)
    print(maximum_length)
