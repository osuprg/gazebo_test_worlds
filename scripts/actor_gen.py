#!/usr/bin/env python
import sys
import math

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
    actor_defined = False
    for line in lines:
        instructions.append(line.split())
        #Essentially skips the line if there aren't any
        if comment_chars.find(instructions[i][0][0]) != -1:
            i += 1
        elif not actor_defined and len(instructions[i]) == 6:
            i += 1
            actor_defined = True
        #Throws an error if the given command isn't recognized
        elif not instructions[i][0] in commands:
            print "Error: Command " + instructions[i][0] + " not recognized (line " + str(i+1) + ")"
            exit()
        #Throws an error if a command is recognized, but
        #has the wrong number of arguments
        elif not len(instructions[i]) - 1 != commands[instructions[i][0]]["arg_count"]:
            print "Error: Incorrect number of arguments for  " + instructions[i][0] + ":\n" + commands[instructions[i][0]]["cmd_error"] + "\n(line " + str(i+1) + ")"
            exit()
        else:
            i += 1
        if instructions[i][0] == "end":
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
        separated_instructions[i].append(instruction)
        if instruction[0] == "end":
            i += 1
    return separated_instructions

#Processes our instructions into individual waypoints
def make_waypoints(instructions):
    waypoints = []
    speed = actor_speed
    time = 0
    for instruction in instructions:
        if instruction[0] == "speed":
            speed = float(instruction[1])
        elif instruction[0] == "wait":
            time += float(instruction[1])
            waypoints.append([waypoints[-1][0:2]])
            waypoints[-1].append(time)
        elif len(instruction) == 3:
            dx = round(instruction[0] - waypoints[-1][0], 2)
            dy = round(instruction[1] - waypoints[-1][0], 2)
            dt = round(math.sqrt(dx**2 + dy**2)/speed, 2)
            time += dt
            new_point = instruction
            new_point.append(time)
            waypoints.append(new_point)
        elif len(instructions) == 6:
            waypoints.append(instruction[3], instruction[4], instruction[5], instruction[2])
    #        time = instruction[2]
    return waypoints

def export_waypoints(waypoint_list):
    waypoint_strings = []
    for waypoint in waypoint_list:
        new_string = "<waypoint>\n"
        new_string += "\t<pose>%f %f 0 0 0 %f</pose>\n" % (waypoint[0], waypoint[1], waypoint[2])
        new_string += "\t<time>%f</time>\n" % waypoint[3]
        new_string += "</waypoint>\n"
        waypoint_strings.append(new_string)
    return waypoint_strings

def save_to_file(waypoint_strings, filename="output.txt"):
    f = open(filename)
    for point in waypoint_strings:
        f.write(point)
    f.close()


if len(sys.argv) != 2:
    print "Error: Incorrect number of arguments"
    exit()

file_lines = import_instructions(sys.argv[1])
processed_lines = process_lines(file_lines)
processed_instructions = split_instructions(processed_lines)
waypoints_to_stringify = make_waypoints(processed_instructions)
waypoint_string_list = export_waypoints(waypoints_to_stringify)
save_to_file(waypoint_string_list)
