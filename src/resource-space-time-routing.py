# -*- coding: utf-8 -*-
"""
Created on Sat Apr 25 11:36:43 2020

DP for Vehicle routing in a resource-space-time network

@author: Gongyuan Lu
"""
from collections import namedtuple
import pandas as pd
import numpy as np
#from docplex.mp.model import Model
import csv
import networkx as nx
from mpl_toolkits import mplot3d
import matplotlib.pyplot as plt
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter,
                               AutoMinorLocator)



_MAX_NUMBER_OF_NODES=999
_MAX_NUMBER_OF_TIME_INTERVALS=20
_MAX_NUMBER_OF_RESOURCES=10
_MAX_LABEL_COST=9999
_MAX_NUMBER_OF_LINKS=9999

# read nodes
Len=[]
vertex_cost=[]

csvFile = open("node.csv", "r")
reader = csv.reader(csvFile)
g=nx.Graph()

for item in reader:
    if reader.line_num == 1:#drop the first line 
        continue
    Len.append(int(item[0])-1)
    vertex_cost.append(int(item[2]))
    
    g.add_node(int(item[0]),desc=int(item[0])-1)#for drawing network
csvFile.close()

print(vertex_cost)

_MAX_NUMBER_OF_NODES=len(Len)



# read links
links=[]
from_node_id=[]
to_node_id=[]
min_travel_time=[]#FFTT
max_travel_time=[]
arc_cost=[]
speed_limit=[]
resource_cost=[]
capacity=[]

csvFile = open("road_link.csv", "r")
reader = csv.reader(csvFile)

for item in reader:
    if reader.line_num == 1:#drop the first line 
        continue
    links.append(int(item[0]))
    from_node_id.append(int(int(item[1])-1))
    to_node_id.append(int(item[2])-1)
    min_travel_time.append(int(item[3]))
    max_travel_time.append(int(item[4]))
    arc_cost.append(int(item[5]))
    speed_limit.append(int(item[6]))
    resource_cost.append(int(item[7]))
    capacity.append(int(item[8]))
    
    g.add_edge(int(item[1]),int(item[2]))#for drawing network
csvFile.close()



_MAX_NUMBER_OF_LINKS=len(links)

print(_MAX_NUMBER_OF_LINKS)

#draw the network
pos=nx.spring_layout(g)
nx.draw(g,pos)
node_labels = nx.get_node_attributes(g, 'desc')
nx.draw_networkx_labels(g, pos, labels=node_labels)


# read vehicles
vehicles=[]
origin_node_id=[]
destination_node_id=[]
departure_time_start=[]
departure_time_end=[]
arrival_time_start=[]
arrival_time_end=[]
fuel=[]

csvFile = open("agent.csv", "r")
reader = csv.reader(csvFile)

for item in reader:
    if reader.line_num == 1:#drop the first line 
        continue
    vehicles.append(int(item[0])-1)
    origin_node_id.append(int(item[1])-1)
    destination_node_id.append(int(item[2])-1)
    departure_time_start.append(int(item[3]))
    departure_time_end.append(int(item[4]))
    arrival_time_start.append(int(item[5]))
    arrival_time_end.append(int(item[6]))
    fuel.append(int(item[7]))
    
csvFile.close()
print(arrival_time_end)


allowWaiting=True

### step 1: Initialization for all nodes
l_state_node_label_cost = np.zeros((_MAX_NUMBER_OF_NODES,_MAX_NUMBER_OF_TIME_INTERVALS,_MAX_NUMBER_OF_RESOURCES))
l_state_node_predecessor = np.zeros((_MAX_NUMBER_OF_NODES,_MAX_NUMBER_OF_TIME_INTERVALS,_MAX_NUMBER_OF_RESOURCES))
l_state_time_predecessor = np.zeros((_MAX_NUMBER_OF_NODES,_MAX_NUMBER_OF_TIME_INTERVALS,_MAX_NUMBER_OF_RESOURCES))
l_state_resource_predecessor = np.zeros((_MAX_NUMBER_OF_NODES,_MAX_NUMBER_OF_TIME_INTERVALS,_MAX_NUMBER_OF_RESOURCES))
#

for i in range(_MAX_NUMBER_OF_NODES):
    for t in range(_MAX_NUMBER_OF_TIME_INTERVALS):
        for r in range (_MAX_NUMBER_OF_RESOURCES):
            l_state_node_label_cost[i][t][r] = _MAX_LABEL_COST
            l_state_node_predecessor[i][t][r] =-1
            l_state_time_predecessor[i][t][r] =-1
            l_state_resource_predecessor[i][t][r] =-1
          
#print(l_state_resource_predecessor)  

r0=_MAX_NUMBER_OF_RESOURCES-1#start with full fuel tank

fig, host = plt.subplots(figsize=(15,8))
fig.subplots_adjust(right=0.75)

host.grid(True)
    
    
host.set_ylabel("Node index")
host.set_xlabel("Time")
host.set_ylim(-2, 10)
host.set_xlim(-2, 30)

for v in vehicles:
    #get vehicle infomation for writing and reading convenience   
    origin_node = origin_node_id[v]
    destination_node = destination_node_id[v]
    departure_time_begin = departure_time_start[v]

#    departure_time_end=departure_time_end[v]
#    arrival_time_begining=arrival_time_start[v]
    arrival_time_ending = arrival_time_end[v]
    l_state_node_label_cost[origin_node][departure_time_begin][r0] = 0
   
    for t in range(_MAX_NUMBER_OF_TIME_INTERVALS):#for each time interval
        if t%20 == 0:
            print("vehicle ",v, "is scanning time ",t,"...")
        for link in range(_MAX_NUMBER_OF_LINKS):#scan links
            from_node=int(from_node_id[link])
            to_node=to_node_id[link]

            for r in range(_MAX_NUMBER_OF_RESOURCES):#scan all resource level
                new_to_node_arrival_time = -1
                temporary_label_cost = 9999
                if l_state_node_label_cost[from_node][t][r] < _MAX_LABEL_COST-1:
                    #scan all possible travel time from min time to max time, using delta_t
#                    for delta_t in range(min_travel_time[link],max_travel_time[link]+1):
                    delta_t=min_travel_time[link]
                    resource_consumption=resource_cost[link]#int(time_dependent_resource_consumption(max_travel_time[link],resource_cost[link],delta_t))

                    r2=int(min(_MAX_NUMBER_OF_RESOURCES - 1, r - resource_consumption))
                    if r2<0: #if fuel tank become less than empty after travel through this link, this is not a feasible route
                        continue
                    #part 1: link based update
                    new_to_node_arrival_time=min(t + delta_t, _MAX_NUMBER_OF_TIME_INTERVALS - 1)
                    temporary_label_cost = l_state_node_label_cost[from_node][t][r] + arc_cost[link]
                    if temporary_label_cost<l_state_node_label_cost[to_node][new_to_node_arrival_time][r2]:
                        #update cost label and node/time predecessor
                        l_state_node_label_cost[to_node][new_to_node_arrival_time][r2] = temporary_label_cost
                        l_state_node_predecessor[to_node][new_to_node_arrival_time][r2] = from_node
                        l_state_time_predecessor[to_node][new_to_node_arrival_time][r2] = t
                        l_state_resource_predecessor[to_node][new_to_node_arrival_time][r2] = r
                    #part 2: same node based update for waiting arcs	
						#if the upstream node is a waiting node
                    if allowWaiting:
                        new_to_node_arrival_time = min(t + 1, _MAX_NUMBER_OF_TIME_INTERVALS - 1)
                        temporary_label_cost = l_state_node_label_cost[from_node][t][r] + vertex_cost[from_node]
                        if temporary_label_cost < l_state_node_label_cost[from_node][new_to_node_arrival_time][r]:
                            #update cost label and node/time predecessor
                            l_state_node_label_cost[from_node][new_to_node_arrival_time][r] = temporary_label_cost
                            l_state_node_predecessor[from_node][new_to_node_arrival_time][r] = from_node
                            l_state_time_predecessor[from_node][new_to_node_arrival_time][r] = t
                            l_state_resource_predecessor[from_node][new_to_node_arrival_time][r] = r
#                if l_state_node_label_cost[from_node][t][r] < _MAX_LABEL_COST - 1:
    
    total_cost = _MAX_LABEL_COST
    
    ##back tracking shortest path
    #prepare path information storage
    min_cost_time_index = arrival_time_ending
    reversed_path_node_sequence=np.zeros((_MAX_NUMBER_OF_TIME_INTERVALS))
    reversed_path_time_sequence=np.zeros((_MAX_NUMBER_OF_TIME_INTERVALS))
    reversed_path_resource_sequence=np.zeros((_MAX_NUMBER_OF_TIME_INTERVALS))
    reversed_path_cost_sequence=np.zeros((_MAX_NUMBER_OF_TIME_INTERVALS))
    
    #step 1 find the destination at ending time with  minimum cost
    #different total cost may appear at different resource index, we must find the min total cost at each resource node
    final_resource_node = -1
    for r in range(_MAX_NUMBER_OF_RESOURCES):
        if l_state_node_label_cost[destination_node][min_cost_time_index][r]<total_cost:
            total_cost = l_state_node_label_cost[destination_node][min_cost_time_index][r]
            final_resource_node = r
            

    #step 2: backtrack from destination to the origin (based on node and time predecessors)
    node_size = 0
    reversed_path_node_sequence[node_size] = destination_node
    reversed_path_time_sequence[node_size] = min_cost_time_index
    reversed_path_resource_sequence[node_size]=final_resource_node
    reversed_path_cost_sequence[node_size] = l_state_node_label_cost[destination_node][min_cost_time_index][final_resource_node]
    
    node_size=node_size+1
    
    pred_node = int(l_state_node_predecessor[destination_node][min_cost_time_index][final_resource_node])
    pred_time = int(l_state_time_predecessor[destination_node][min_cost_time_index][final_resource_node])
    pred_resource = int(l_state_resource_predecessor[destination_node][min_cost_time_index][final_resource_node])
    
    while pred_node != -1 & node_size < _MAX_NUMBER_OF_TIME_INTERVALS: 
        reversed_path_node_sequence[node_size] = pred_node
        reversed_path_time_sequence[node_size] = pred_time
        reversed_path_resource_sequence[node_size] = pred_resource
        reversed_path_cost_sequence[node_size]=l_state_node_label_cost[pred_node][pred_time][pred_resource]

        node_size=node_size+1
        
        pred_node_record = pred_node
        pred_time_record = pred_time
        pred_resource_record = pred_resource
        
        pred_node = int(l_state_node_predecessor[pred_node_record][pred_time_record][pred_resource_record])
        pred_time = int(l_state_time_predecessor[pred_node_record][pred_time_record][pred_resource_record])
        pred_resource = int(l_state_resource_predecessor[pred_node_record][pred_time_record][pred_resource_record])

    #correct the route format by reversing the path node sequence
    path_node_sequence=np.zeros((node_size))
    path_time_sequence=np.zeros((node_size))
    path_resource_sequence=np.zeros((node_size))
    path_cost_sequence=np.zeros((node_size))
    
    
    for n in range(node_size):
        path_node_sequence[n] = reversed_path_node_sequence[node_size - n - 1]
        path_time_sequence[n] = reversed_path_time_sequence[node_size - n - 1]
        path_resource_sequence[n] = reversed_path_resource_sequence[node_size - n - 1]
        path_cost_sequence[n] = reversed_path_cost_sequence[node_size - n - 1]
    
    
    
host.plot(path_time_sequence,path_node_sequence,marker='o',linewidth='1')
host.set_xlabel('Time (hour)')
host.set_ylabel('Node')
#
##        
fig = plt.figure(figsize=(15,8))
ax = plt.axes(projection='3d')
print(path_time_sequence)
drawXline=[]
drawYline=[]
drawZline=[]
for i in range(len(path_node_sequence)):
    if(path_node_sequence[i]>=0 ):
        drawXline.append(path_time_sequence[i])
        drawYline.append(path_node_sequence[i])
        drawZline.append(path_resource_sequence[i])

zeros=[]
for i in range(len(drawXline)):  
    zeros.append(0)
     
    
# Tweaking display region and labels
ymax=max(path_node_sequence)+1
ax.set_xlim(0, 20)
ax.set_ylim(0, ymax)
ax.set_zlim(0, 10)
ax.set_xlabel('Time (hour)')
ax.set_ylabel('Node')
ax.set_zlabel('Resource (gallon)')

# Data for a three-dimensional line
xline = drawXline
yline = drawYline
zline = drawZline

ax.plot3D(xline, yline, zeros, 'gray',linewidth=3,marker='o')
for i in range(len(drawXline)):
    ax.plot3D([xline[i],0], [yline[i],yline[i]],[zline[i],zline[i]], 'blue',linestyle='dashed',linewidth=0.5)
    ax.plot3D([xline[i],xline[i]], [yline[i],yline[i]],[0,zline[i]], 'blue',linestyle='dashed',linewidth=0.5)
    ax.plot3D([xline[i],xline[i]], [yline[i],ymax],[zline[i],zline[i]], 'blue',linestyle='dashed',linewidth=0.5)
ax.plot3D(xline, yline, zline, 'black',linewidth=3,marker='o')

#ax.plot3D(zeros, yline, zline, 'black',linewidth=3,marker='o')

ax.xaxis.set_major_locator(MultipleLocator(2))
ax.xaxis.set_major_formatter(FormatStrFormatter('%d'))


#
#ax.plot3D(zeros, yline, zline, 'gray')
#ax.plot3D(xline, zeros, zline, 'gray')
#ax.plot3D(xline, yline, zeros, 'gray')

#ax.scatter3D(xline, yline, zline)
#
#
#    
    
    
    
    
    
    
    
