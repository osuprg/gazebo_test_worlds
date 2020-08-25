#!/usr/bin/env python
import sys
import math
from numpy import arctan2
from math import atan2, sqrt
from lxml import etree

#NOTE TO SELF: etree works as a DOM, meaning that
#passing it to a function modifies the original
#root element

class WorldGenerator:
    def __init__(self, file_in="input.txt", file_out="output.world", base_file=None):
        self.line_number = 0
        self.file_in = file_in
        self.file_out = file_out
        self.actor_speed = None
        self.root_elem = None
        self.material = None
        #List of valid commands and their argument counts
        self.commands = {
            "goto" : {
                "arg_count" : 3,
                "cmd_error" : "Usage is: 'goto [x_pos] [y_pos] [orientation]'. Units are meters and radians.",
                "cmd_func"  : self.goto_func
            },
            "speed" : {
                "arg_count" : 1,
                "cmd_error" : "Usage is: 'speed [new_speed]'. Units are m/s.",
                "cmd_func"  : self.speed_func,
                "default"   : 1.8
            },
            "wait" : {
                "arg_count" : 1,
                "cmd_error" : "Usage is: 'wait [seconds]'.",
                "cmd_func"  : self.wait_func
            },
            "material" : {
                "arg_count" : 1,
                "cmd_error" : "Usage is 'material [material_uri]'.",
                "cmd_func"  : self.material_func,
                "default"   : "model://grey_wall/materials/scripts"
            },
            "wall" : {
                "arg_count" : 4,
                "cmd_error" : "Usage is 'wall [x1] [y1] [x2] [y2]'.",
                "cmd_func"  : self.wall_func
            },
            "door" : {
                "arg_count" : 4,
                "cmd_error" : "Usage is 'door [x1] [y1] [x2] [y2]'.",
                "cmd_func"  : self.door_func
            },
            "zone" : {
                "arg_count" : 5,
                "cmd_error" : "Usage is 'zone [zone_name] [x1] [y1] [x2] [y2]'",
                "cmd_func"  : self.zone_func
            },
            "model" : {
                "arg_count" : 5,
                "cmd_error" : "Usage is 'model [model_file] [model_name] [x] [y] [orientation]'",
                "cmd_func"  : self.model_func
            },
            "actor" : {
                "arg_count" : 5,
                "cmd_error" : "Usage is 'actor [actor_name] [x] [y] [orientation] [start_time]'",
                "cmd_func"  : self.actor_func
            },
            "include" : {
                "arg_count" : 1,
                "cmd_error" : "To be implemented: Usage is 'include [path_to_file]'",
                "cmd_func"  : self.include_func
            },
            "duplicate" : {
                "arg_count" : 5,
                "cmd_error" : "To be implemented: Usage is 'duplicate [old_element_name] [new_element_name] [x] [y] [orientation]'",
                "cmd_func"  : self.duplicate_func
            }
        }

        #String of all the characters that start a comment line
        self.comment_chars = "#"

    #TODO: Check if changes needed
    #Just pulls in the information from the file
    def import_instructions(self, filename):
        f = open(filename, "r")
        lines = f.readlines()
        f.close()
        return lines

    #TODO: Modify to new recursive format
    #Processes individual lines into commands and argument lists
    def process_lines(self, lines, root_elem, level):
        #Checks to see if we already have a root element to work off of
        #If not, we create a new root element for the entire tree
        if root_elem == None:
            self.root_elem = etree.Element("sdf", version="1.5")
            root_elem = etree.SubElement(self.root_elem, "world")
            root_elem.attrib["name"] = "default"
        #Loops through all of the lines
        while len(lines) > 0:
            count = self.tab_count(lines[0])
            self.line_number += 1
            #Checks to make sure we're at the right indentation level
            while count != level:
                if count > level + 1:
                    print(f"Error: Indentation level at line {self.line_number} exceeds expected values ({level} or {level + 1}). Currently {count}")
                    exit()
                if count > level:
                    self.line_number -= 1
                    lines = self.process_lines(lines, root_elem, level + 1)
                if count < level:
                    return lines
                if len(lines) == 0:
                    return lines
                count = self.tab_count(lines[0])
            #Ensures that there are still lines to process
            #Shouldn't be needed. Primarily here as a safeguard
            #against coder mistakes
            if len(lines) == 0:
                break
            #Splits off the first line in the lines list
            line = lines.pop(0).split()
            #Checks for blank lines
            if len(line) == 0 or len(line[0]) == 0:
                continue
            #Checks for comment characters at the beginning
            if self.comment_chars.find(line[0][0]) != -1:
                continue

            #Splits off the command from the overall line
            #The remaining part of the line is the argument list
            command = line.pop(0)

            #Checks to makes sure that the command exists
            if not command in self.commands:
                print f"Error: Command {command} not recognized (line {self.line_number})"
                exit()

            #Checks to make sure the number of arguments is correct
            if len(line) != self.commands[command]["arg_count"]:
                print f"Error: Incorrect number of arguments for {command} :\n{self.commands[command]["cmd_error"]}\n(line {self.line_number})"
                exit()

            try:
                #Run command function associated with command
                self.commands[command]["cmd_func"](line, root_elem)
            except:
                print(f"Unknown error when running command {command} on line {self.line_number}.\nTry checking the command's arguments are the correct type")
        #Should return an empty array.
        return lines




    #Simple utility function to count how many tabs are at the start
    #of a line
    def tab_count(self, line):
        i = 0
        while line[i] == '\t':
            i += 1
        return i

    #TODO: Check to see if even needed anymore
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

    #TODO: Check if needed once new XML format is used
    #Processes our instructions into individual waypoints
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


    #TODO: Move interpolation fix to other command functions
    #Code to fix arcing from orientation interpolation
    #Essentially makes the actor face the next point very quickly
    #instead of the change in orientation being split over the entire duration of
    #walking between the waypoints. Actor always walks in the direction it's facing
    #(as far as I can tell) which means the actor would end up walking in arcs
    #instead of lines
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


    #TODO: See if even needed once XML format is included
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

    #TODO: Adjust to use new format
    #Just exports to a given file
    def save_to_file(waypoint_strings, filename="output.txt"):
        f = open(filename, "w+")
        for point in waypoint_strings:
            f.write(point)
        f.close()

    #Functions for individual commands
    def goto_func(self, args, root_elem):
        last_waypoint = root_elem[len(root_elem) - 1]

        #Need to split out all of the elements of the last waypoint's
        #pose.
        last_pos_full = last_waypoint[0].text.split()

        #Position 1 is the position of the last waypoint pose.
        #Position 2 is the position of the new waypoint pose.
        #Time 1 is the timestamp of the last waypoint.
        pos_1 = [float(last_pos_full[0]), float(last_pos_full[1])]
        pos_2 = [float(args[0]), float(args[1]), float(args[2])]
        time_1 = float(last_waypoint[1].text)
        dx = pos_2[0] - pos_1[0]
        dy = pos_2[1] - pos_1[1]
        tot_len = math.sqrt(dx**2 + dy**2)
        dt = round(tot_len/self.actor_speed, 2)

        #The following unit vectors, direction, and interp 1 and 2
        #are used to get around interpolation issues with SDF.
        #Essentially, somewhere in the process it attempts to
        #interpolate the change in orientation, which ends up creating
        #large arcs between points which is.... Problematic. At least
        #when you're trying to make an actor turn and walk through a
        #hallway and they end up clipping through a few walls.

        #Unit vectors for change in x and y, and direction
        #of movement from point to point.
        ux = dx/tot_len
        uy = dy/tot_len
        dir = arctan2(uy, ux)

        #Set the poses of the interpolation-issue-dodging points to be
        #5 centimeters from the first and second points.The change in orientation
        #is completed in those 5 centimeters, which means any arcs are done almost
        #immediately
        interp_1 = [pos_1[0] + ux * 0.05, pos_1[1] + uy * 0.05, dir]
        interp_2 = [pos_2[0] - ux * 0.05, pos_2[1] - uy * 0.05, dir]

        #Figures out the timestamps for the interpolation-issue-dodging points
        t1 = 0.05 * self.actor_speed + time_1
        t2 = -0.05 * self.actor_speed + time_1 + dt

        #Makes all three waypoints (the two interpolation issue ones, and the
        #original one that we wanted to add on), then adds them to the XML DOM
        way_1 = etree.Element("waypoint")
        way_1.append(etree.Element("time"))
        way_1.append(etree.Element("pose"))
        way_1[0].text = str(t1)
        way_1[1].text = f"{interp_1[0]} {interp_1[1]} 0 0 0 {interp_1[2]}"


        way_2 = etree.Element("waypoint")
        way_2.append(etree.Element("time"))
        way_2.append(etree.Element("pose"))
        way_2[0].text = str(t2)
        way_2[1].text = f"{interp_2[0]} {interp_2[1]} 0 0 0 {interp_2[2]}"


        way_3 = etree.Element("waypoint")
        way_3.append(etree.Element("time"))
        way_3.append(etree.Element("pose"))
        way_3[0].text = str(time_1 + dt)
        way_3[1].text = f"{pos_2[0]} {pos_2[1]} 0 0 0 {pos_2[2]}"

        root_elem.append(way_1)
        root_elem.append(way_2)
        root_elem.append(way_3)


    #Sets class-level speed
    def speed_func(self, args, root_elem):
        self.actor_speed = args[0]

    #Makes current actor wait for a set number of seconds
    def wait_func(self, args, root_elem):
        #Pulls out last waypoint
        last_waypoint = root_elem[len(root_elem) - 1]

        #Makes a new XML element
        new_point = etree.Element("waypoint")

        #Figures out all of our time differences
        dt = float(args[0])
        t1 = float(last_waypoint[1].text)
        t2 = t1 + dt

        #Appends our new time and then the same pose
        new_point.append(etree.Element("time"))
        new_point[0].text = str(t2)

        new_point.append(etree.Element("pose"))
        new_point[1].text = last_waypoint[0].text

        #Adds our new point to the XML DOM
        root_elemt.append(new_point)

    #Sets current default material
    def material_func(self, args, root_elem):
        if args[0] == "default":
            self.material = self.commands["material"]["default"]
        else:
            self.material = args[0]

    #TODO
    def wall_func(self, args, root_elem):
        return 0

    #TODO
    def door_func(self, args, root_elem):
        return 0

    #TODO
    def zone_func(self, args, root_elem):
        return 0

    #TODO
    def model_func(self, args, root_elem):
        return 0

    #TODO
    def actor_func(self, args, root_elem):
        return 0

    #TODO
    def include_func(self, args, root_elem):
        return 0

    #TODO
    def duplicate_func(self, args, root_elem):
        return 0
