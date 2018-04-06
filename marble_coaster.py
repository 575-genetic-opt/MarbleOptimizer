import random
import math
import sys
import matplotlib.pyplot as plt

sys.setrecursionlimit(200)
gene_per_section = 2

maximum_length = 0
corresponding_cost = 0

num_div_x = 10           # NUMBER OF COLUMNS
num_div_y = 10           # NUMBER OF ROWS
num_div_z = 10           # NUMBER OF FLOORS

dz = .1                  # HEIGHT OF PIECES (METERS)
dx = .1                  # X LENGTH OF PIECES (METERS)
dy = .1                  # Y LENGTH OF PIECES (METERS)

v_start = .1             # STARTING VELOCITY OF MARBLE (M/S)

mass = 0.00127           # MASS OF A MARBLE (KG)
lpl = .01                # percent of energy lost due to normal track use
g = 9.81                 # GRAVITY (M/S^2)

parts = [{'cost': 1., 'length': dz, 'loss': lpl*dz, 'cool': 90, 'e1': 'top', 'e2': 'bottom'},
         {'cost': 3., 'length': (dz/2 + dy/2)*.8, 'loss': lpl*(dz/2 + dy/2)*.8, 'cool': 50, 'e1': 'top', 'e2': 1},
         {'cost': 1., 'length': dy, 'loss': lpl*dy, 'cool': 70, 'e1': 1, 'e2': 3},
         {'cost': 3., 'length': (dy/2 + dx/2)*.8, 'loss': lpl*(dy/2 + dx/2)*.8, 'cool': 50, 'e1': 1, 'e2': 4},
         {'cost': 3., 'length': (dy/2 + dz/2)*.8, 'loss': lpl*(dy/2 + dx/2)*.8, 'cool': 50, 'e1': 1, 'e2': 'bottom'}]


def calc_length(design):

    # RECORD MAX POSSIBLE PATH
    max_path = 0

    # LIST OF GLOBAL PIECE NUMBERS IN BEST DESIGN
    max_loc_list = []
    max_part_list = []
    max_rot_list = []
    max_en_his = []

    # LOOP OVER PIECES ON TOP
    for i in range(0, num_div_x*num_div_y*gene_per_section, gene_per_section):

        for in_dir in ['e1', 'e2']:
            # SET STARTING ENERGIES
            up = num_div_y * dy * mass * g         # POTENTIAL ENERGY
            uk = .5 * mass * math.pow(v_start, 2)  # KINETIC ENERGY

            # SET STARTING DESIGN VALUES
            loc_his = []
            part_his = []
            rot_his = []
            en_his = []

            # GET LOCATION ID OF PIECE
            piece_number = int(i / gene_per_section) + 1 + int(num_div_x*num_div_y*(num_div_z-1))

            length = traverse_length(design, piece_number, loc_his, part_his, rot_his, en_his, in_dir, uk, up)

            if length > max_path:
                max_path = length
                max_loc_list = loc_his
                max_part_list = part_his
                max_rot_list = rot_his
                max_en_his = en_his

    return max_path, max_loc_list, max_part_list, max_rot_list, max_en_his


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


def inlet_outlet(design, g_piece_id, in_direction):

    # GET PIECE INFORMATION
    piece_gene_index = (g_piece_id - 1) * gene_per_section
    piece_rot = design[piece_gene_index + 1]
    piece_num = design[piece_gene_index] - 1
    piece_type = parts[piece_num]

    if in_direction == 'e1':
        # GET OUTLET FACE ID
        outlet = piece_type['e2']
        if type(piece_type['e2']) == int:
            outlet = (piece_type['e2'] + piece_rot) % 4
            if outlet == 0:
                outlet = 4

        # GET INLET FACE ID
        inlet = piece_type['e1']
        if type(piece_type['e1']) == int:
            inlet = (piece_type['e1'] + piece_rot) % 4
            if inlet == 0:
                inlet = 4
    else:
        # GET OUTLET FACE ID
        outlet = piece_type['e1']
        if type(piece_type['e1']) == int:
            outlet = (piece_type['e1'] + piece_rot) % 4
            if outlet == 0:
                outlet = 4

        # GET INLET FACE ID
        inlet = piece_type['e2']
        if type(piece_type['e2']) == int:
            inlet = (piece_type['e2'] + piece_rot) % 4
            if inlet == 0:
                inlet = 4

    # GET ROW AND COLUMN ID OF PIECE
    row, col, floor = locate_piece(g_piece_id)
    location = (row, col, floor)

    out_neighbor = 0
    in_neighbor = 0

    if outlet == 'bottom':
        if floor > 1:
            out_neighbor = g_piece_id - num_div_x * num_div_y
    elif outlet == 'top':
        if floor < num_div_z:
            out_neighbor = g_piece_id + num_div_x * num_div_y
    if inlet == 'top':
        if floor < num_div_z:
            in_neighbor = g_piece_id + num_div_x * num_div_y
    elif inlet == 'bottom':
        if floor > 1:
            in_neighbor = g_piece_id - num_div_x * num_div_y

    if row == 1:  # ON BOTTOM FACE
        if col == 1:  # ON LEFT FACE
            if outlet == 1:  # INTERIOR FACE
                out_neighbor = g_piece_id + num_div_x
            elif outlet == 2:
                out_neighbor = g_piece_id + 1  # INTERIOR FACE
            if inlet == 1:  # INTERIOR FACE
                in_neighbor = g_piece_id + num_div_x
            elif inlet == 2:
                in_neighbor = g_piece_id + 1  # INTERIOR FACE
        elif col == num_div_x:  # ON RIGHT FACE
            if outlet == 1:  # INTERIOR FACE
                out_neighbor = g_piece_id + num_div_x
            elif outlet == 4:  # INTERIOR FACE
                out_neighbor = g_piece_id - 1
            if inlet == 1:  # INTERIOR FACE
                in_neighbor = g_piece_id + num_div_x
            elif inlet == 4:  # INTERIOR FACE
                in_neighbor = g_piece_id - 1
        else:  # MIDDLE COLUMN
            if outlet == 1:  # INTERIOR FACE
                out_neighbor = g_piece_id + num_div_x
            elif outlet == 2:  # INTERIOR FACE
                out_neighbor = g_piece_id + 1
            elif outlet == 4:  # INTERIOR FACE
                out_neighbor = g_piece_id - 1
            if inlet == 1:  # INTERIOR FACE
                in_neighbor = g_piece_id + num_div_x
            elif inlet == 2:  # INTERIOR FACE
                in_neighbor = g_piece_id + 1
            elif inlet == 4:  # INTERIOR FACE
                in_neighbor = g_piece_id - 1
    elif row == num_div_y:  # ON TOP FACE
        if col == 1:  # ON LEFT FACE
            if outlet == 3:  # INTERIOR FACE
                out_neighbor = g_piece_id - num_div_x
            elif outlet == 2:  # INTERIOR FACE
                out_neighbor = g_piece_id + 1
            if inlet == 3:  # INTERIOR FACE
                in_neighbor = g_piece_id - num_div_x
            elif inlet == 2:  # INTERIOR FACE
                in_neighbor = g_piece_id + 1
        elif col == num_div_x:  # ON RIGHT FACE
            if outlet == 3:  # FACING INTERIOR
                out_neighbor = g_piece_id - num_div_x
            elif outlet == 4:  # INTERIOR FACE
                out_neighbor = g_piece_id - 1
            if inlet == 3:  # FACING INTERIOR
                in_neighbor = g_piece_id - num_div_x
            elif inlet == 4:  # INTERIOR FACE
                in_neighbor = g_piece_id - 1
        else:  # MIDDLE COLUMN
            if outlet == 3:  # FACING INTERIOR
                out_neighbor = g_piece_id - num_div_x
            elif outlet == 4:  # INTERIOR FACE
                out_neighbor = g_piece_id - 1
            elif outlet == 2:  # INTERIOR FACE
                out_neighbor = g_piece_id + 1
            if inlet == 3:  # FACING INTERIOR
                in_neighbor = g_piece_id - num_div_x
            elif inlet == 4:  # INTERIOR FACE
                in_neighbor = g_piece_id - 1
            elif inlet == 2:  # INTERIOR FACE
                in_neighbor = g_piece_id + 1
    else:  # IN MIDDLE ROW
        if col == 1:  # ON LEFT FACE
            if outlet == 1:  # FACING INTERIOR
                out_neighbor = g_piece_id + num_div_x
            elif outlet == 3:  # INTERIOR FACE
                out_neighbor = g_piece_id - num_div_x
            elif outlet == 2:
                out_neighbor = g_piece_id + 1
            if inlet == 1:  # FACING INTERIOR
                in_neighbor = g_piece_id + num_div_x
            elif inlet == 3:  # INTERIOR FACE
                in_neighbor = g_piece_id - num_div_x
            elif inlet == 2:
                in_neighbor = g_piece_id + 1
        elif col == num_div_x:  # ON RIGHT FACE
            if outlet == 1:  # FACING INTERIOR
                out_neighbor = g_piece_id + num_div_x  # FACING INTERIOR
            elif outlet == 3:
                out_neighbor = g_piece_id - num_div_x  # FACING INTERIOR
            elif outlet == 4:  # FACING INTERIOR
                out_neighbor = g_piece_id - 1
            if inlet == 1:  # FACING INTERIOR
                in_neighbor = g_piece_id + num_div_x  # FACING INTERIOR
            elif inlet == 3:
                in_neighbor = g_piece_id - num_div_x  # FACING INTERIOR
            elif inlet == 4:  # FACING INTERIOR
                in_neighbor = g_piece_id - 1
        else:  # INTERIOR PIECE
            if outlet == 1:  # FACING EXTERIOR
                out_neighbor = g_piece_id + num_div_x
            elif outlet == 3:  # FACING INTERIOR
                out_neighbor = g_piece_id - num_div_x
            elif outlet == 2:  # FACING INTERIOR
                out_neighbor = g_piece_id + 1
            elif outlet == 4:  # FACING INTERIOR
                out_neighbor = g_piece_id - 1
            if inlet == 1:  # FACING EXTERIOR
                in_neighbor = g_piece_id + num_div_x
            elif inlet == 3:  # FACING INTERIOR
                in_neighbor = g_piece_id - num_div_x
            elif inlet == 2:  # FACING INTERIOR
                in_neighbor = g_piece_id + 1
            elif inlet == 4:  # FACING INTERIOR
                in_neighbor = g_piece_id - 1

    # CHECK IF NEIGHBORS HAVE ALIGNING FACES
    if in_neighbor > 0:

        in_gene_index = (in_neighbor - 1) * gene_per_section
        in_piece_rot = design[in_gene_index + 1]
        in_piece_num = design[in_gene_index] - 1
        in_piece_type = parts[in_piece_num]

        in_n_e1 = in_piece_type['e1']
        if type(in_piece_type['e1']) == int:
            in_n_e1 = (in_piece_type['e1'] + in_piece_rot) % 4
            if in_n_e1 == 0:
                in_n_e1 = 4

        in_n_e2 = in_piece_type['e2']
        if type(in_piece_type['e2']) == int:
            in_n_e2 = (in_piece_type['e2'] + in_piece_rot) % 4
            if in_n_e2 == 0:
                in_n_e2 = 4

        in_neighbor_1 = in_neighbor
        in_neighbor_2 = in_neighbor

        if inlet == 'top':
            if in_n_e1 != 'bottom':
                in_neighbor_1 = 0
            if in_n_e2 != 'bottom':
                in_neighbor_2 = 0
        elif inlet == 'bottom':
            if in_n_e1 != 'top':
                in_neighbor_1 = 0
            if in_n_e2 != 'top':
                in_neighbor_2 = 0
        else:
            if type(in_n_e1) is int:
                if math.fabs(inlet - in_n_e1) != 2:
                    in_neighbor_1 = 0
            else:
                in_neighbor_1 = -1
            if type(in_n_e2) is int:
                if math.fabs(inlet - in_n_e2) != 2:
                    in_neighbor_2 = 0
            else:
                in_neighbor_2 = 0

        if in_neighbor_2 == 0:
            in_neighbor = in_neighbor_1

    in_direction = 'e1'

    if out_neighbor:

        out_gene_index = (out_neighbor - 1) * gene_per_section
        out_piece_rot = design[out_gene_index + 1]
        out_piece_num = design[out_gene_index] - 1
        out_piece_type = parts[out_piece_num]

        out_n_e1 = out_piece_type['e1']
        if type(out_piece_type['e1']) == int:
            out_n_e1 = (out_piece_type['e1'] + out_piece_rot) % 4
            if out_n_e1 == 0:
                out_n_e1 = 4

        out_n_e2 = out_piece_type['e2']
        if type(out_piece_type['e2']) == int:
            out_n_e2 = (out_piece_type['e2'] + out_piece_rot) % 4
            if out_n_e2 == 0:
                out_n_e2 = 4

        out_neighbor_1 = out_neighbor
        out_neighbor_2 = out_neighbor

        if outlet == 'bottom':
            if out_n_e1 != 'top':
                out_neighbor_1 = 0
            if out_n_e2 != 'top':
                out_neighbor_2 = 0
        elif outlet == 'top':
            if out_n_e1 != 'bottom':
                out_neighbor_1 = 0
            if out_n_e2 != 'bottom':
                out_neighbor_2 = 0
        else:
            if type(out_n_e1) is int:
                if math.fabs(outlet - out_n_e1) != 2:
                    out_neighbor_1 = 0
            else:
                out_neighbor_1 = 0
            if type(out_n_e2) is int:
                if math.fabs(outlet - out_n_e2) != 2:
                    out_neighbor_2 = 0
            else:
                out_neighbor_2 = 0

        if out_neighbor_2 > 0:
            in_direction = 'e2'
        else:
            out_neighbor = out_neighbor_1

    return in_neighbor, out_neighbor, location, in_direction


def traverse_length(design, g_piece_id, path_his, part_his, rot_his, en_his, in_dir, uk, up):

    piece_gene_index = (g_piece_id - 1) * gene_per_section
    piece_rot = design[piece_gene_index + 1]
    piece_num = design[piece_gene_index] - 1
    piece_type = parts[piece_num]

    length = piece_type['length']
    friction_loss = piece_type['loss']*uk

    in_neighbor, out_neighbor, location, in_dir = inlet_outlet(design, g_piece_id, in_dir)

    # Subtract friction loss from kinetic energy
    uk -= friction_loss

    # Subtract potential energy losses
    if len(path_his) > 0:
        uk -= (location[2] - path_his[-1][2]) * dz * g * mass
        up += (location[2] - path_his[-1][2]) * dz * g * mass

    if out_neighbor > 0 and location not in path_his and uk > 0:
        path_his.append(location)
        part_his.append(piece_num)
        rot_his.append(piece_rot)
        en_his.append(uk)
        length += traverse_length(design, out_neighbor, path_his, part_his, rot_his, en_his, in_dir, uk, up)
    else:
        path_his.append(location)
        part_his.append(piece_num)
        rot_his.append(piece_rot)
        en_his.append(uk)

    return length


def calc_cost(design):

    cost_sum = 0

    for part_num in design:
        cost_sum += parts[part_num]['cost']

    return cost_sum


def solve_track(design):

    max_path, max_loc_list, max_part_list, max_rot_list, en_his = calc_length(design)

    cost = calc_cost(max_part_list)

    return max_path, cost, max_part_list, max_loc_list, max_rot_list, en_his


def good_design():

    design = [1]*(num_div_x*num_div_y*num_div_z*gene_per_section)

    p_gene = num_div_x*num_div_y*(num_div_z-1)*gene_per_section
    design[p_gene] = 1
    design[p_gene + 1] = 1

    p_gene -= num_div_x*num_div_y*gene_per_section

    design[p_gene] = 2
    design[p_gene + 1] = 1

    p_gene += 1*gene_per_section

    design[p_gene] = 3
    design[p_gene + 1] = 1

    p_gene += 1*gene_per_section

    design[p_gene] = 3
    design[p_gene + 1] = 3

    p_gene += 1*gene_per_section

    design[p_gene] = 3
    design[p_gene + 1] = 1

    p_gene += 1*gene_per_section

    design[p_gene] = 4
    design[p_gene + 1] = 4

    p_gene += num_div_x*gene_per_section

    design[p_gene] = 3
    design[p_gene + 1] = 4

    p_gene += num_div_x*gene_per_section

    design[p_gene] = 3
    design[p_gene + 1] = 2

    p_gene += num_div_x*gene_per_section

    design[p_gene] = 5
    design[p_gene + 1] = 2

    p_gene -= num_div_x*num_div_y*gene_per_section

    design[p_gene] = 1
    design[p_gene + 1] = 2

    p_gene -= num_div_x * num_div_y*gene_per_section

    design[p_gene] = 1
    design[p_gene + 1] = 3

    p_gene -= num_div_x * num_div_y*gene_per_section

    design[p_gene] = 1
    design[p_gene + 1] = 4

    p_gene -= num_div_x * num_div_y*gene_per_section

    design[p_gene] = 2
    design[p_gene + 1] = 3

    p_gene -= 1*gene_per_section

    design[p_gene] = 2
    design[p_gene + 1] = 1

    p_gene += num_div_x*num_div_y*gene_per_section

    design[p_gene] = 5
    design[p_gene + 1] = 3

    p_gene -= 1*gene_per_section

    design[p_gene] = 5
    design[p_gene + 1] = 1

    p_gene -= num_div_x * num_div_y*gene_per_section

    design[p_gene] = 1
    design[p_gene + 1] = 1

    return design


if __name__ == '__main__':

    gen_design = good_design()

    t_length, t_cost, p_list, p_loc, r_list, e_list = solve_track(gen_design)

    speeds = []
    for e in e_list:
        speeds.append(math.sqrt(e/(.5*mass)))

    print(t_length)
    print(t_cost)
    print(p_list)
    print(p_loc)
    print(r_list)
    print(len(p_list))
    print(e_list)
    print(speeds)

