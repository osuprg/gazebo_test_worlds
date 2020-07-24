#!/usr/bin/env python
import sys
import math
from numpy import arctan2

actor_speed = 1.8

#List of valid commands and their argument counts
commands = {
    "goto" : {
        "arg_count" : 3,
        "cmd_error" : "Usage is: 'goto [x_pos] [y_pos] [orientation]'. Units are meters and radians."
    },
    "speed" : {
        "arg_count" : 1,
        "cmd_error" : "Usage is: 'speed [new_speed]'. Units are m/s."
    },
    "wait" : {
        "arg_count" : 1,
        "cmd_error" : "Usage is: 'wait [seconds]'."
    },
    "end"  : {
        "arg_count" : 0,
        "cmd_error" : "Usage is 'end'."
    }
}

#String of all the characters that start a comment line
comment_chars = "#"

#Just pulls in the information from the file
def import_instructions(filename):
    f = open(filename, "r")
    lines = f.readlines()
    f.close()
    return lines

#Processes individual lines into commands and argument lists
def process_lines(lines):
    instructions = []
    i = 0
    j = 0
    actor_defined = False
    for line in lines:
        instructions.append(line.split())
        #Essentially skips the line if there aren't any
        if len(instructions) == 0 or len(instructions[i]) == 0:
            instructions.pop(i)
            j += 1
            continue
        if comment_chars.find(instructions[i][0][0]) != -1:
            instructions.pop()
            j += 1
        elif len(instructions[i]) == 0:
            instructions.pop()
            j += 1
        elif not actor_defined and len(instructions[i]) == 6:
            i += 1
            j += 1
            actor_defined = True
        #Throws an error if the given command isn't recognized
        elif not instructions[i][0] in commands:
            print "Error: Command " + instructions[i][0] + " not recognized (line " + str(j+1) + ")"
            exit()
        #Throws an error if a command is recognized, but
        #has the wrong number of arguments
        elif len(instructions[i]) - 1 != commands[instructions[i][0]]["arg_count"]:
            print "Error: Incorrect number of arguments for  " + instructions[i][0] + ":\n" + commands[instructions[j][0]]["cmd_error"] + "\n(line " + str(i+1) + ")"
            exit()
        else:
            i += 1
            j += 1
        if len(instructions) > 0 and instructions[i-1][0] == "end":
            actor_defined = False
    if actor_defined:
        print "Warning: No 'end' command found for last actor. Auto-appending."
        instructions.append(["end"])
    return instructions

#Uses "end" command to split overall list into list for individual actors
def split_instructions(instructions):
    separated_instructions = [[]]
    i = 0
    for instruction in instructions:
        if i > len(separated_instructions) - 1:
            separated_instructions.append([])
        separated_instructions[i].append(instruction)
        if instruction[0] == "end":
            i += 1
    return separated_instructions

#Processes our instructions into individual waypoints
#TODO: Fix whitespace lines not being ignored
def make_waypoints(instructions):
    waypoints = []
    speed = actor_speed
    time = 0
    file_out = ""
    for instruction in instructions:
        if instruction[0] == "speed":
            speed = float(instruction[1])
        elif instruction[0] == "wait":
            time += float(instruction[1])
            new_waypoint = [waypoints[-1][0], waypoints[-1][1], waypoints[-1][2]]
            new_waypoint.append(time)
            waypoints.append(new_waypoint)
        elif len(instruction) == 4:
            dx = round(float(instruction[1]) - float(waypoints[-1][0]), 2)
            dy = round(float(instruction[2]) - float(waypoints[-1][1]), 2)
            dt = round(math.sqrt(dx**2 + dy**2)/speed, 2)
            time += dt
            new_point = [instruction[1], instruction[2], instruction[3], str(time)]
            waypoints.append(new_point)
        elif len(instruction) == 6:
            file_out = instruction[1] + "_output.txt"
            waypoints.append([instruction[3], instruction[4], instruction[5], instruction[2]])
    #        time = instruction[2]
    return waypoints, file_out


#Code to fix arcing from orientation interpolation
def postprocess_waypoints(waypoint_list):
    i = len(waypoint_list) - 1
    while i > 0:
        x1 = float(waypoint_list[i-1][0])
        y1 = float(waypoint_list[i-1][1])
        t1 = float(waypoint_list[i-1][3])
        x2 = float(waypoint_list[i][0])
        y2 = float(waypoint_list[i][1])
        t2 = float(waypoint_list[i][3])
        dx = x2 - x1
        dy = y2 - y1
        dt = t2 - t1
        tot_len = math.sqrt(dx**2 + dy**2)
        if tot_len == 0:
            ux = 0
            uy = 0
        else:
            ux = dx/tot_len
            uy = dy/tot_len
        dir = arctan2(uy, ux)
        speed = tot_len / dt
        p1 = [str(x1 + ux * 0.05), str(y1 + uy * 0.05), str(dir), str(t1 + 0.05 * speed)]
        p2 = [str(x2 - ux * 0.05), str(y2 - uy * 0.05), str(dir), str(t2 - 0.05 * speed)]
        waypoint_list.insert(i, p2)
        waypoint_list.insert(i, p1)
        i -= 1
    return waypoint_list


#Puts waypoints into their final string form to be exported
def export_waypoints(waypoint_list):
    waypoint_strings = []
    for waypoint in waypoint_list:
        new_string = "<waypoint>\n"
        new_string += "\t<pose>%f %f 0 0 0 %f</pose>\n" % (float(waypoint[0]), float(waypoint[1]), float(waypoint[2]))
        new_string += "\t<time>%f</time>\n" % float(waypoint[3])
        new_string += "</waypoint>\n"
        waypoint_strings.append(new_string)
    return waypoint_strings

#Just exports to a given file
def save_to_file(waypoint_strings, filename="output.txt"):
    f = open(filename, "w+")
    for point in waypoint_strings:
        f.write(point)
    f.close()


if len(sys.argv) != 2:
    print "Error: Incorrect number of arguments"
    exit()


#TODO: Set up "If name == main" so stuff can be imported as library
file_lines = import_instructions(sys.argv[1])
processed_lines = process_lines(file_lines)
processed_instructions = split_instructions(processed_lines)
for actor in processed_instructions:
    output_file_name = ""
    waypoints_to_process, output_file_name = make_waypoints(actor)
    waypoints_to_stringify = postprocess_waypoints(waypoints_to_process)
    waypoint_string_list = export_waypoints(waypoints_to_stringify)
    save_to_file(waypoint_string_list, output_file_name)
