
import pickle
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
#import imageio

"""
Authors: Yuval Eppel, Raphael Shuhendler, Yotam Dery

December 2020, TAU

please make sure the folder 'input_files' is located next to this python file.
the folder 'output_files' will be created by the code and output files will be saved to it.

in this code, we will use a while loop, until len(removed_items_list)==25
at each point, each escort (out of the existing 5) will be either
'free', 'towards' an item, or 'with' an item.
if 'free' - the escort will look for the closest item and go towards it
(assuming no other escorts are approaching it), and approach it.
if 'towards' (distance >2), the escort will continue going to the item.
if 'with' - the escort will go towards the exit, in 3-steps and 5-steps, according to location.

if 2 escorts are too close - we will freeze one of them to let the other pass.
if an item is at the exit, we will remove it (at the next time unit) and record the time.

we will remember that each escort movement is happening in 3 time units (3 robot movements).
we will record each escort movement, and at the end retrieve the robots movements from it,
using the 'get_robot_moves_from_escort_moves(escort_move)' function below.

while working and debugging, we used plots and GIFs, to understand the situation (as descibed in the PDF,
but here we disabled this commands (changed them into #comments#) to make the code faster.
"""

#this function will be used at the end to convert all escort moves to robot moves.
def get_robot_moves_from_escort_moves(escort_move):
    if escort_move[2]==False:
        robot_moves = (escort_move,escort_move,escort_move)
    elif escort_move[2]==True:
        robot_moves = (escort_move[0],escort_move[1],False),(escort_move[1],escort_move[0],True),(escort_move[0],escort_move[1],False)
    return (robot_moves)

#function to plot df as a board

def plot_df(df,t=None):
    col_labels = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14]
    row_labels = [0,1,2,3,4,5,6,7,8]
    plt.matshow(df,cmap='Reds')
    plt.xticks(range(15), col_labels)
    plt.yticks(range(9), row_labels)
    for i in range(15):
        for j in range(9):
            c = df[i][j]
            plt.text(i, j, str(c), va='center', ha='center')
    plt.text(7, -1.5, 'EXIT', va='center', ha='center',c='r')
    plt.text(0,-1.5,'time is t=' + str(t))
    return plt
    #plt.show()

#function to get indexes of a value
#notice that returns (row,column) == (y,x) and not (x,y)
def getIndexes(dfObj, value):
    ''' Get index positions of value in dataframe i.e. dfObj.'''
    listOfPos = list()
    # Get bool dataframe with True at positions where the given value exists
    result = dfObj.isin([value])
    # Get list of columns that contains the value
    seriesObj = result.any()
    columnNames = list(seriesObj[seriesObj == True].index)
    # Iterate over list of columns and fetch the rows indexes where value exists
    for col in columnNames:
        rows = list(result[col][result[col] == True].index)
        for row in rows:
            listOfPos.append((row, col))
    # Return a list of tuples indicating the positions of value in the dataframe
    return listOfPos

#function to replace 2 values locations in a df
def simple_switch(df,val1,val2):
    val1_index = getIndexes(df,val1)[0]
    val2_index = getIndexes(df, val2)[0]
    df.loc[val1_index[0]][val1_index[1]] = val2
    df.loc[val2_index[0]][val2_index[1]] = val1
    return df
#get distance between escort and item
def get_distance(df,val1,val2):
    first_loc =  getIndexes(df,val1)[0]
    second_loc = getIndexes(df,val2)[0]
    return abs(first_loc[0]-second_loc[0])+abs(first_loc[1]-second_loc[1])

def find_closest_item(df,items_to_remove_list,escort):
    closest_item = None
    shortest_dist = 1000000
    for item in items_to_remove_list:
        distance = get_distance(df, escort, item)
        if distance < shortest_dist and item in items_to_remove_list:
            shortest_dist = distance
            closest_item = item
    return closest_item


def escort_move_towards_item(df,escort,item):

    escort_loc = getIndexes(df,escort)[0]
    item_loc = getIndexes(df,item)[0]
    #print(escort, item, escort_loc,item_loc)
    if escort_loc[1] < item_loc[1]:
        move_right(df,escort)
    elif escort_loc[1] > item_loc[1]:
        move_left(df,escort)
    elif escort_loc[1] == item_loc[1]:
        if escort_loc[0] > item_loc[0]:
            #print('UP')
            move_up(df,escort)
            #item_to_switch_with = df.loc[escort_loc[0]-1][escort_loc[1]]
        elif escort_loc[0] < item_loc[0]:
            #print ('DOWN')
            move_down(df,escort)
            #item_to_switch_with = df.loc[escort_loc[0]+1][escort_loc[1]]



def initialize(wh,items_to_remove_lst):
    #set up initial DF
    wh_df = pd.DataFrame(wh)
    new_items_to_remove_list = []
    # setting the indexes from down to up like in the classroom
    #wh_df.index = [8,7,6,5,4,3,2,1,0]

    #adding 500 to all desired items so we can find them on the graph
    for item in items_to_remove_list:
        wh_df = wh_df.replace(item,item+500)
        #items_to_remove_list[items_to_remove_list.index(item)]=item+500
        new_items_to_remove_list.append(item+500)


    # changing the initial zeros to something unique, and that has different color (1001-1005)
    escorts_initial_locations =  getIndexes(wh_df,0)
    wh_df.loc[escorts_initial_locations[0][0]][escorts_initial_locations[0][1]] = 1001
    wh_df.loc[escorts_initial_locations[1][0]][escorts_initial_locations[1][1]] = 1002
    wh_df.loc[escorts_initial_locations[2][0]][escorts_initial_locations[2][1]] = 1003
    wh_df.loc[escorts_initial_locations[3][0]][escorts_initial_locations[3][1]] = 1004
    wh_df.loc[escorts_initial_locations[4][0]][escorts_initial_locations[4][1]] = 1005

    return wh_df,new_items_to_remove_list

def go_towards_exit(df,cur_escort,cur_item):
    exit_loc = (0,7)
    escort_loc = getIndexes(df,cur_escort)[0]
    item_loc = getIndexes(df,cur_item)[0]
    if item_loc[0]==exit_loc[0]:
        do_5_step(df,cur_escort,cur_item)
    elif item_loc[1]==exit_loc[1]:
        do_5_step(df, cur_escort, cur_item)
    else:
        do_3_step(df, cur_escort, cur_item)

def do_5_step(df,escort,item):
    exit_loc = (0,7)
    escort_loc = getIndexes(df,escort)[0]
    item_loc = getIndexes(df,item)[0]
    if item_loc[0]==0:

        #move left
        if item_loc[1] >7:
            if item_loc[0]==escort_loc[0]:
                if item_loc[1]-1==escort_loc[1]:
                    move_right(df,escort)
                    return
                if item_loc[1]-2==escort_loc[1]:
                    move_right(df,escort)
                    return
                if item_loc[1]+1==escort_loc[1]:
                    move_down(df,escort)
                    return
                if item_loc[1]+2==escort_loc[1]:
                    move_left(df,escort)
                    return
            elif item_loc[0]==escort_loc[0]-1:
                if item_loc[1]+1==escort_loc[1]:
                    move_left(df,escort)
                    return
                if item_loc[1]==escort_loc[1]:
                    move_left(df,escort)
                    return
                if item_loc[1]-1==escort_loc[1]:
                    move_up(df,escort)
                    return
        #move right
        elif item_loc[1]<7:
            if item_loc[0]==escort_loc[0]:
                if item_loc[1]-1==escort_loc[1]:
                    move_down(df,escort)
                    return
                if item_loc[1]-2==escort_loc[1]:
                    move_right(df,escort)
                    return
                if item_loc[1]+1==escort_loc[1]:
                    move_left(df,escort)
                    return
                if item_loc[1]+2==escort_loc[1]:
                    move_left(df,escort)
                    return
            elif item_loc[0]==escort_loc[0]-1:
                if item_loc[1]+1==escort_loc[1]:
                    move_up(df,escort)
                    return
                if item_loc[1]==escort_loc[1]:
                    move_right(df,escort)
                    return
                if item_loc[1]-1==escort_loc[1]:
                    move_right(df,escort)
                    return
    # move up
    elif item_loc[1]==7:
        if escort_loc[1]==7:
            if escort_loc[0]-1 == item_loc[0]:
                move_right(df,escort)
                return
            if escort_loc[0]-2 == item_loc[0]:
                move_up(df,escort)
                return
            if escort_loc[0]+1 == item_loc[0]:
                move_down(df,escort)
                return
            if escort_loc[0]+2 == item_loc[0]:
                move_down(df,escort)
                return
        if escort_loc[1]<7 and escort_loc[0]!=item_loc[0]:
            move_right(df,escort)
            return
        if escort_loc[1]<7 and escort_loc[0]==item_loc[0]:
            move_down(df,escort)
            return
        if escort_loc[1]>8:
            move_left(df,escort)
            return
        if escort_loc[1]==8:
            if escort_loc[0] == item_loc[0]:
                move_up(df,escort)
                return
            if escort_loc[0]-1 == item_loc[0]:
                move_up(df,escort)
                return
            if escort_loc[0]-2 == item_loc[0]:
                move_up(df,escort)
                return
            if escort_loc[0]+1 == item_loc[0]:
                move_left(df,escort)
                return



            if escort_loc[0]+1 == item_loc[0]:
                move_right(df,escort)
        if item_loc[0] == escort_loc[0]:
            if item_loc[1] - 1 == escort_loc[1]:
                move_down(df, escort)
                return
            if item_loc[1] + 1 == escort_loc[1]:
                move_left(df, escort)
                return
        elif item_loc[0] == escort_loc[0] - 1:
            if item_loc[1] + 1 == escort_loc[1]:
                move_up(df, escort)
                return
            if item_loc[1] == escort_loc[1]:
                move_right(df, escort)
                return
            if item_loc[1] - 1 == escort_loc[1]:
                move_right(df, escort)
                return


    else:
        do_3_step(df,escort,item)

def do_3_step(df,escort,item):
    exit_loc = (0,7)
    escort_loc = getIndexes(df,escort)[0]
    item_loc = getIndexes(df,item)[0]
    if item_loc[0]==0 or item_loc[1]==7:
        do_5_step(df,escort,item)
        return
    else:
        # move left and up
        if item_loc[1]>7:
            if escort_loc[0]==item_loc[0]:
                if escort_loc[1]-1==item_loc[1]:
                    move_up(df,escort)
                    return
                elif escort_loc[1]-2==item_loc[1]:
                    move_left(df,escort)
                    return
                elif escort_loc[1]+1==item_loc[1]:
                    move_right(df,escort)
                    return
                elif escort_loc[1]+2==item_loc[1]:
                    move_right(df,escort)
                    return
            elif escort_loc[0]+1==item_loc[0]:
                if escort_loc[1]==item_loc[1]:
                    move_down(df,escort)
                    return
                elif escort_loc[1]-1==item_loc[1]:
                    move_left(df,escort)
                    return
            elif escort_loc[0] - 1 == item_loc[0]:
                if escort_loc[1]==item_loc[1]:
                    move_left(df,escort)
                    return
                elif escort_loc[1]+1==item_loc[1]:
                    move_up(df,escort)
                    return
                elif escort_loc[1]-1==item_loc[1]:
                    move_up(df,escort)
                    return
        # move right and up
        if item_loc[1]<7:
            if escort_loc[0]==item_loc[0]:
                if escort_loc[1]-1==item_loc[1]:
                    move_left(df,escort)
                    return
                elif escort_loc[1]-2==item_loc[1]:
                    move_left(df,escort)
                    return
                elif escort_loc[1]+1==item_loc[1]:
                    move_up(df,escort)
                    return
                elif escort_loc[1]+2==item_loc[1]:
                    move_right(df,escort)
                    return
            elif escort_loc[0]+1==item_loc[0]:
                if escort_loc[1]==item_loc[1]:
                    move_down(df,escort)
                    return
                elif escort_loc[1]+1==item_loc[1]:
                    move_right(df,escort)
                    return
                elif escort_loc[1]-1==item_loc[1]:
                    move_left(df,escort)
                    return
            elif escort_loc[0] - 1 == item_loc[0]:
                if escort_loc[1]==item_loc[1]:
                    move_right(df,escort)
                    return
                elif escort_loc[1]+1==item_loc[1]:
                    move_up(df,escort)
                    return
                elif escort_loc[1] - 1 == item_loc[1]:
                    move_up(df, escort)
                    return


def move_up(df,escort):
    escort_loc = getIndexes(df,escort)[0]
    item_loc = (escort_loc[0]-1,escort_loc[1])
    if escort_loc[0]==0:
        return
    simple_switch(df,escort,df.loc[item_loc[0],item_loc[1]])

def move_right(df,escort):
    escort_loc = getIndexes(df,escort)[0]
    item_loc = (escort_loc[0],escort_loc[1]+1)
    if escort_loc[1]==14:
        return
    simple_switch(df,escort,df.loc[item_loc[0],item_loc[1]])

def move_left(df,escort):
    escort_loc = getIndexes(df,escort)[0]
    item_loc = (escort_loc[0],escort_loc[1]-1)
    if escort_loc[1]==0:
        return
    simple_switch(df,escort,df.loc[item_loc[0],item_loc[1]])

def move_down(df,escort):
    escort_loc = getIndexes(df,escort)[0]
    item_loc = (escort_loc[0]+1,escort_loc[1])
    if escort_loc[0]==8:
        return
    simple_switch(df,escort,df.loc[item_loc[0],item_loc[1]])

def calc_escorts_distance(df,e1,e2,e3,e4,e5):
    d12 = get_distance(df,e1,e2)
    d13 = get_distance(df, e1, e3)
    d14 = get_distance(df, e1, e4)
    d15 = get_distance(df, e1, e5)
    d23 = get_distance(df, e2, e3)
    d24 = get_distance(df, e2, e4)
    d25 = get_distance(df, e2, e5)
    d34 = get_distance(df, e3, e4)
    d35 = get_distance(df, e3, e5)
    d45 = get_distance(df, e4, e5)
    return (d12,d13,d14,d15,d23,d24,d25,d34,d35,d45)

#starting the main function

def main_function_for_single_warehouse(items_to_remove_list,wh,wh_index=0):
    removal_times =[]
    escort_moves=[[],[],[],[],[]]
    wh_df = initialize(wh,items_to_remove_list)[0]
    items_to_remove_list = initialize(wh,items_to_remove_list)[1]
    removed_items_lst =[]
    escort_allocations = {1001:'free',1002:'free',1003:'free',1004:'free',1005:'free'}
    t=0
    #we used the plots for debugging and for GIFs creation as described n the PDF.
    #it slows the code down so we disabled it
    #plt = plot_df(wh_df,t)
    #plt.savefig('plots/' + str(t) + '.png')
    while len(removed_items_lst)<25:
    #while t<12:


        #remaining are items which are allocated to escorts but are not removed yet.
        #we use this list to allocate them to escorts 1004,1005 which do not 'wait' for others, to avoid being stuck.
        remaining=[]
        for e in escort_allocations.keys():
            if escort_allocations[e] != 'free':
                a=escort_allocations[e][0]
                if a !=None:
                    if a >500:
                        remaining.append(a)
        #in the last items, make sure 1004,1005 are allocated to them so the system doesn't get stuck
        #(because escorts are too close).
        #check if escort 1004 is not free
        if escort_allocations[1005] !='free' and escort_allocations[1005][0] != None:
            # its item is not relevant
            if escort_allocations[1005][0]<500 :
                if len(remaining)>0:
                    escort_allocations[1005]=[remaining[0],'towards']
        if escort_allocations[1004] !='free' and escort_allocations[1004][0] != None:
            if escort_allocations[1004][0]<500:
                if len(remaining) > 0:
                    escort_allocations[1004]=[remaining[0],'towards']
        t+=1
        print (t)
        #removing items which are at the exit point
        if wh_df.loc[0,7] >600 and wh_df.loc[0,7]<1000:
            removed_items_lst.append(wh_df.loc[0,7]-500)
            removal_times.append([wh_df.loc[0,7]-500,t])
            if wh_df.loc[0, 7] in items_to_remove_list:
                items_to_remove_list.remove(wh_df.loc[0, 7])
            for escort in escort_allocations:
                if escort_allocations[escort][0]==wh_df.loc[0,7]:
                    escort_allocations[escort] = 'free'

            wh_df.loc[0, 7] = -t
        t += 2
        print(t)
        #iterating through escorts
        for escort in [1001,1002,1003,1004,1005]:
            escort_loc_before_moving = getIndexes(wh_df,escort)[0]
            #if the escort has None, it means it has no more items to pick - we are close to finish.
            # in that case, move towards the corner so the escort will not block the exit.
            if escort_allocations[escort][0]==None:
                escort_allocations[escort]=[wh_df.loc[8,0],'towards']
            if escort_allocations[escort][0] in [1001,1002,1003,1004,1005]:
                if escort_allocations[escort][0]>1000:
                    escort_allocations[escort]=[wh_df.loc[8,0],'towards']

            #make sure only 1 escort moves if 2 are too close:
            distances = calc_escorts_distance(wh_df, 1001, 1002, 1003, 1004, 1005)
            min_dist = 1000
            if escort == 1001:
                for dist in distances[:4]:
                    if dist < 3:
                        min_dist = dist
            if escort == 1002:
                for dist in distances[4:7]:
                    if dist < 3:
                        min_dist = dist
            if escort == 1003:
                for dist in distances[7:9]:
                    if dist < 3:
                        min_dist = dist
            if escort == 1004:
                for dist in distances[9:]:
                    if dist < 3:
                        min_dist = dist
            if min_dist < 3:
                escort_move = (escort_loc_before_moving, escort_loc_before_moving, not escort_loc_before_moving == escort_loc_before_moving)
                escort_moves[list(escort_allocations.keys()).index(escort)].append(escort_move)
                continue

            if escort_allocations[escort] is not 'free':
                if get_distance(wh_df,escort,escort_allocations[escort][0])<=1:
                    escort_allocations[escort][1]='with'
                if escort_allocations[escort][1]=='with':
                    #if the escort is too far from the item it is allocated to(after being with it) - the escort will release it
                    if get_distance(wh_df,escort,escort_allocations[escort][0])>2:
                        items_to_remove_list.append(escort_allocations[escort][0])
                        escort_allocations[escort]='free'
                    else:
                        item=escort_allocations[escort][0]
                        go_towards_exit(wh_df,escort,item)
            if escort_allocations[escort][1]=='towards':
                escort_move_towards_item(wh_df, escort, escort_allocations[escort][0])
            elif escort_allocations[escort]=='free':

                escort_allocations[escort] = [find_closest_item(wh_df,items_to_remove_list,escort),'towards']
                if escort_allocations[escort][0] in items_to_remove_list:

                    items_to_remove_list.remove(escort_allocations[escort][0])
                    escort_move_towards_item(wh_df,escort,escort_allocations[escort][0])

            escort_loc_after_moving = getIndexes(wh_df, escort)[0]
            escort_move = (escort_loc_before_moving,escort_loc_after_moving,not escort_loc_before_moving==escort_loc_after_moving)
            escort_moves[list(escort_allocations.keys()).index(escort)].append(escort_move)
    removal_times_df = pd.DataFrame(removal_times)
    removal_times_df.to_pickle('output_files/extractions_wh'+str(wh_index)+'.p')
    #converting the escort moves to understand robot moves
    #print (escort_moves)
    robot_moves =[[],[],[],[],[]]
    for escort in escort_moves:
        for move in escort:
            #print (move)
            moves = get_robot_moves_from_escort_moves(move)
            robot_moves[escort_moves.index(escort)].append(moves[0])
            robot_moves[escort_moves.index(escort)].append(moves[1])
            robot_moves[escort_moves.index(escort)].append(moves[2])
    robot_moves_df = pd.DataFrame(robot_moves)
    robot_moves_df.to_pickle('output_files/robot_moves_wh' + str(wh_index) + '.p')

        #plt = plot_df(wh_df,t)
        #plt.savefig('plots\\'+str(t)+'.png')
    #following code is used to create a gif of the warehouse, it slows down the code so we disabled it
    ##################################
    #images=[]
    #lst = os.listdir('plots')
    #sorted_lst = sorted(lst, key=lambda fname: int(fname.split('.')[0]))
    #for filename in sorted_lst:
    #    images.append(imageio.imread('plots/'+filename))


    #imageio.mimsave('gif_name.gif',images,'GIF',duration=0.1)
    #########################


#read files
wh_lst=[]
input_files_names = os.listdir('input_files')
for input_file in input_files_names:
    if input_file[:10] == 'items_list':
        full_items_to_remove_list = pd.read_pickle('input_files/'+input_file)
    elif input_file[:2]=='wh':
        wh = pd.read_pickle('input_files/'+input_file)
        wh_lst.append(wh)

# creating directory for the output_files
##############################
path = "output_files"
try:
    os.mkdir(path)
    print ('"Creation of the directory %s succeeded')
except OSError:
    print ("Creation of the directory %s failed, maybe it already exists" % path)
##############################
#running the function for all inputs
for wh in wh_lst:
    items_to_remove_list = full_items_to_remove_list
    main_function_for_single_warehouse(items_to_remove_list,wh , wh_lst.index(wh)+1)


