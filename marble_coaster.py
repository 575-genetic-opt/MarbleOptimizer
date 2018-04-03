import random
import math
import sys

sys.setrecursionlimit(200)
gene_per_section = 2

maximum_length = 0
corresponding_cost = 0

num_div_x = 10
num_div_y = 10
num_div_z = 10

dz = .1  # HEIGHT OF PIECES (METERS)
dx = .1  # X LENGTH OF PIECES (METERS)
dy = .1  # Y LENGTH OF PIECES (METERS)

v_start = .1  # STARTING VELOCITY OF MARBLE (M/S)

mass = 0.00127  # MASS OF A MARBLE (KG)
loss_per_length = 0.01  # percent of energy lost due to normal track use
g = 9.81  # GRAVITY (M/S^2)

parts = [{'cost': 1., 'length': dz, 'loss': .1*dz, 'cool': 90, 'in': 'top', 'out': 'bottom'},
         {'cost': 3., 'length': (dz/2 + dy/2)*.8, 'loss': .1*(dz/2 + dy/2)*.8, 'cool': 50, 'in': 'top', 'out': 1},
         {'cost': 1., 'length': dy, 'loss': .1*dy, 'cool': 70, 'in': 1, 'out': 3},
         {'cost': 3., 'length': (dy/2 + dx/2)*.8, 'loss': .1*(dy/2 + dx/2)*.8, 'cool': 50, 'in': 1, 'out': 4},
         {'cost': 3., 'length': (dy/2 + dz/2)*.8, 'loss': .1*(dy/2 + dx/2)*.8, 'cool': 50, 'in': 1, 'out': 'bottom'}]


def calc_length(design):

    # RECORD MAX POSSIBLE PATH
    max_path = 0

    # LIST OF GLOBAL PIECE NUMBERS IN BEST DESIGN
    max_loc_list = []
    max_part_list = []
    max_rot_list = []

    # LOOP OVER PIECES ON TOP
    for i in range(0, num_div_x*num_div_y*gene_per_section, gene_per_section):

        # SET STARTING ENERGIES
        up = num_div_y * dy * mass * g         # POTENTIAL ENERGY
        uk = .5 * mass * math.pow(v_start, 2)  # KINETIC ENERGY

        # SET STARTING DESIGN VALUES
        loc_history = []
        part_history = []
        rot_history = []

        # GET LOCATION ID OF PIECE
        piece_number = int(i / gene_per_section) + 1 + int(num_div_x*num_div_y*(num_div_z-1))

        length = traverse_length(design, piece_number, loc_history, part_history, rot_history, uk, up)

        if length > max_path:
            max_path = length
            max_loc_list = loc_history
            max_part_list = part_history
            max_rot_list = rot_history

    return max_path, max_loc_list, max_part_list, max_rot_list


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

    if out_neighbor:

        out_gene_index = (out_neighbor - 1) * gene_per_section
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

    return in_neighbor, out_neighbor, location


def traverse_length(design, piece_number, path_history, part_history, rot_history, uk, up):

    piece_gene_index = (piece_number - 1) * gene_per_section
    piece_type = parts[design[piece_gene_index] - 1]

    length = piece_type['length']
    friction_loss = piece_type['loss']*uk

    in_neighbor, out_neighbor, location = inlet_outlet(design, piece_number)

    # Subtract friction loss from kinetic energy
    uk -= friction_loss

    # Subtract potential energy losses
    if len(path_history) > 0:
        uk -= (location[2] - path_history[-1][2])*dz*g*mass
        up += (location[2] - path_history[-1][2])*g*mass

    if out_neighbor > 0 and location not in path_history and uk > 0:
        path_history.append(location)
        part_history.append(design[piece_gene_index] - 1)
        rot_history.append(design[piece_gene_index])
        length += traverse_length(design, out_neighbor, path_history, part_history, rot_history, uk, up)
    else:
        path_history.append(location)
        part_history.append(design[piece_gene_index] - 1)
        rot_history.append(design[piece_gene_index])

    return length


def calc_cost(design):

    cost_sum = 0

    for part_num in design:
        cost_sum += parts[part_num]['cost']

    return cost_sum


def solve_track(design):

    max_path, max_loc_list, max_part_list, max_rot_list = calc_length(design)

    cost = calc_cost(max_part_list)

    return max_path, cost, max_part_list, max_loc_list, max_rot_list


if __name__ == '__main__':

    max_len = 0

    mt_length = None
    mt_cost = None
    mp_list = None
    mp_loc = None
    mr_list = None

    for _ in xrange(1000):
        gen_design = [random.randrange(1, 5, 1) for r in range(num_div_x*num_div_y*num_div_z*gene_per_section)]

        t_length, t_cost, p_list, p_loc, r_list = solve_track(gen_design)

        if t_length > maximum_length:
            maximum_length = t_length
            mt_length = t_length
            mt_cost = t_cost
            mp_list = p_list
            mp_loc = p_loc
            mr_list = r_list

    print mt_length
    print mt_cost
    print mp_list
    print mp_loc
    print mr_list
