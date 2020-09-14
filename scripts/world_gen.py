#!/usr/bin/env python3
import sys
import math
from copy import deepcopy
from math import atan2, sqrt
from lxml import etree
from shapely.geometry import MultiLineString, LineString

#NOTE TO SELF: etree works as a DOM, meaning that
#passing it to a function modifies the original
#root element

class WorldGenerator:
    def __init__(self, file_in="input.txt", file_out="output.world", base_file=None):
        self.line_number = 0
        self.door_count = 0
        self.file_in = file_in
        self.file_out = file_out
        self.actor_speed = None
        self.root_elem = None
        self.material = None

        #Idea behind wall and material array is that it's easier to (and likely
        #more efficient) to store every wall as a shapely Line in an array until
        #the end of the command list, in case the wall needs to be split to make
        #room for a door. Every wall in the array wall_array[i] will use the
        #material listed at material_array[i].
        self.wall_array = [[]]
        self.material_array = []
        #List of valid commands and their argument counts
        self.commands = {
            "goto" : {
                "arg_count" : 3,
                "arg_func"  : self.arg_count,
                "cmd_error" : "Usage is: 'goto [x_pos] [y_pos] [orientation]'. Units are meters and radians.",
                "cmd_func"  : self.goto_func
            },
            "speed" : {
                "arg_count" : 1,
                "arg_func"  : self.arg_count,
                "cmd_error" : "Usage is: 'speed [new_speed]'. Units are m/s.",
                "cmd_func"  : self.speed_func,
                "default"   : 1.8
            },
            "wait" : {
                "arg_count" : 1,
                "arg_func"  : self.arg_count,
                "cmd_error" : "Usage is: 'wait [seconds]'.",
                "cmd_func"  : self.wait_func
            },
            "material" : {
                "arg_count" : 1,
                "arg_func"  : self.arg_count,
                "cmd_error" : "To be implemented: Usage is 'material [material_name]'.",
                "cmd_func"  : self.material_func,
                "default"   : "vrc/grey_wall"
            },
            "wall" : {
                "arg_count" : 4,
                "arg_func"  : self.arg_count,
                "cmd_error" : "Usage is 'wall [x1] [y1] [x2] [y2]'.",
                "cmd_func"  : self.wall_func
            },
            "door" : {
                "arg_count" : 4,
                "arg_func"  : self.arg_count,
                "cmd_error" : "Usage is 'door [x1] [y1] [x2] [y2]'.",
                "cmd_func"  : self.door_func
            },
            "zone" : {
                "arg_count" : 5,
                "arg_func"  : self.arg_count,
                "cmd_error" : "Usage is 'zone [zone_name] [x1] [y1] [x2] [y2]'",
                "cmd_func"  : self.zone_func
            },
            "model" : {
                "arg_count" : 4,
                "arg_func"  : self.arg_count,
                "cmd_error" : "Usage is 'model [model_name] [x] [y] [orientation]'",
                "cmd_func"  : self.model_func
            },
            "actor" : {
                "arg_count" : 5,
                "arg_func"  : self.arg_count,
                "cmd_error" : "Usage is 'actor [actor_name] [x] [y] [orientation] [start_time]'",
                "cmd_func"  : self.actor_func
            },
            "include" : {
                "arg_count" : 2,
                "arg_func"  : self.arg_count,
                "cmd_error" : "To be implemented: Usage is 'include [path_to_file] [xml_element_to_find]'.\nUse 'none' as your XML element argument if you wish to import a file in its entirety",
                "cmd_func"  : self.include_func
            },
            "duplicate" : {
                "arg_count" : 5,
                "arg_func"  : self.arg_count,
                "cmd_error" : "To be implemented: Usage is 'duplicate [old_element_name] [new_element_name] [x] [y] [orientation]'",
                "cmd_func"  : self.duplicate_func
            },
            "explicit" : {
                "arg_count" : 1,
                "arg_func"  : self.arg_count,
                "cmd_error" : "Usage is 'explicit [element_tag]'",
                "cmd_func"  : self.explicit_func
            },
            "attribute" : {
                "arg_count" : 2,
                "arg_func"  : self.arg_count,
                "cmd_error" : "Usage is 'attribute [attribute_name] [attribute_value]'",
                "cmd_func"  : self.attribute_func
            },
            "text" : {
                "arg_func"  : self.text_arg_count,
                "cmd_error" : "Usage is 'text [set/add] [element_text]'",
                "cmd_func"  : self.text_func
            }
        }

        #String of all the characters that start a comment line
        self.comment_chars = "#"

    #Just pulls in the information from the file
    def import_instructions(self):
        f = open(self.file_in, "r")
        lines = f.readlines()
        f.close()
        return lines

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
                    lines = self.process_lines(lines, root_elem[-1], level + 1)
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
                print(f"Error: Command {command} not recognized (line {self.line_number})")
                exit()

            #Checks to make sure the number of arguments is correct
            if not self.commands[command]["arg_func"](command, line):
                print(f"Error: Incorrect number of arguments for {command} :\n{self.commands[command]['cmd_error']}\n(line {self.line_number})")
                exit()

            try:
                #Run command function associated with command
                self.commands[command]['cmd_func'](line, root_elem)
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

    #Saves the tree to the file specified by self.file_out
    def save_to_file(self):
        f = open(self.file_out, "w+")
        f.write('<?xml version="1.0" ?>\n')
        f.write(etree.tostring(self.root_elem, pretty_print=True).decode())
        f.close()

    #Functions for individual commands
    def goto_func(self, args, root_elem):
        if self.actor_speed == None:
            self.speed_func(["default"], root_elem)

        traj_elem = root_elem.find("script").find("trajectory")

        last_waypoint = traj_elem[len(root_elem) - 1]

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
        dir = atan2(uy, ux)

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

        traj_elem.append(way_1)
        traj_elem.append(way_2)
        traj_elem.append(way_3)

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

    #Sets current material to be used. If the current material
    #hasn't been used before, it's given a new place in the materials array
    def material_func(self, args, root_elem):
        material = args[0]
        if args[0] == 'default':
            self.material = self.commands["material"]["default"]
            material = self.material
        else:
            self.material = material
        if not material in self.material_array:
            self.material_array.append(material)
            self.wall_array.append([])

    #Function to append a LineString representing a wall to the appropriate
    #wall_array index, corresponding to the associated material index
    def wall_func(self, args, root_elem):
        x1, y1, x2, y2 = [float(arg) for arg in args]
        if self.material == None:
            self.material_func(["default"], self.root_elem)
        index = self.material_array.index(self.material)
        self.wall_array[index].append(LineString([(x1, y1), (x2, y2)]))

    #TODO: Make use materials instead of just the grey wall
    #TODO: Redo the handling of doors and walls to be more consistent
    #Function to create a doorway in a wall. This is the specific reason
    #for handling the walls in a postprocessing function (defined lower down).
    #This would be a complete pain to code and really inefficient if we were to
    #modify the XML DOM to handle the walls.
    def door_func(self, args, root_elem):
        x1, y1, x2, y2 = [float(arg) for arg in args]
        door_line = LineString([(x1, y1), (x2, y2)])
        index = [-1, -1]
        #Searches for the wall the door should be part of.
        #Searches from the back based off the assumption that
        #the most recent wall is likely the one this door should be in.
        for i in reversed(range(len(self.wall_array))):
            for j in reversed(range(len(self.wall_array[i]))):
                if self.wall_array[i][j].contains(door_line):
                    index = [i, j]
                    break
            if index[0] != -1:
                break

        i, j = index

        for wall in self.wall_array[i][j].difference(door_line):
            self.wall_array[i].append(wall)


        del self.wall_array[i][j]


        #Making this an actual doorway instead of just a gap

        #Splits out the individual door line points for ease of access
        p1 = door_line.coords[0]
        p2 = door_line.coords[1]

        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        theta = atan2(dy, dx)

        #Makes the initial door_top element
        door_top = etree.Element("model", name=f"doorway_{self.door_count}")
        door_top.append(etree.Element("static"))
        door_top[0].text = "1"

        door_top.append(etree.Element("pose"))
        door_top[1].text = f"{p1[0]} {p1[1]} 0 0 0 {theta}"

        link = etree.Element("link", name="link")
        link.append(etree.Element("pose"))
        link[0].text = f"{door_line.length/2} 0 2.4 0 0 0"

        #Making box to be appended to both the visual and collision elements.
        #Should be able to append to first then deepcopy to second
        box = etree.Element("box")
        box.append(etree.Element("size"))
        box[0].text = f"{round(door_line.length, 2)} 0.1 0.8"

        geometry = etree.Element("geometry")
        geometry.append(box)

        #Appending things to the collision element of the model
        link.append(etree.Element("collision", attrib={"name" : "collision"}))
        link[1].append(deepcopy(geometry))
        link[1].append(etree.Element("max_contacts"))
        link[1][1].text = "10"

        #Appending things to the visual element of the model
        link.append(etree.Element("visual", attrib={"name" : "visual"}))
        link[2].append(etree.Element("cast_shadows"))
        link[2][0].text = "1"
        link[2].append(deepcopy(geometry))
        link[2].append(etree.Element("material"))
        link[2][2].append(etree.Element("script"))
        link[2][2][0].append(etree.Element("uri"))
        link[2][2][0][0].text = "model://grey_wall/materials/scripts"
        link[2][2][0].append(etree.Element("uri"))
        link[2][2][0][1].text = "model://grey_wall/materials/textures"
        link[2][2][0].append(etree.Element("name"))
        link[2][2][0][2].text = self.material

        door_top.append(link)

        root_elem.append(door_top)

        #I don't believe there's anything else that needs to be added
        #but if any errors are encountered, this may be where additional
        #things need to be inserted


    #TODO
    def zone_func(self, args, root_elem):
        print("To be implemented")

    #Adds a model element to the current root element
    def model_func(self, args, root_elem):
        model = etree.SubElement(root_elem, "model", attrib={"name":f"{args[0]}"})
        pose = etree.Element("pose")
        pose.text = f"{args[1]} {args[2]} 0 0 0 {args[3]}"
        model.append(pose)

    #Creates a new actor with initial information set
    def actor_func(self, args, root_elem):
        actor = etree.Element("actor", attrib={"name":f"{args[0]}"})

        script = etree.SubElement(actor, "script")
        loop = etree.SubElement(script, "loop")
        loop.text = "true"

        delay_start = etree.SubElement(script, "delay_start")
        delay_start.text = args[4]



        trajectory = etree.Element("trajectory", id="0", type="walking")
        trajectory.append(etree.Element("waypoint"))
        trajectory[0].append(etree.Element("time"))
        trajectory[0][0].text = "0"
        trajectory[0].append(etree.Element("pose"))
        trajectory[0][1].text = f"{args[1]} {args[2]} 0 0 0 {args[3]}"


        root_elem.append(actor)


    #Includes either XML or text from another file
    def include_func(self, args, root_elem):
        if args[1] == 'none':
            f = open(args[0])
            if root_elem.text == None:
                root_elem.text = ""
            root_elem.text += f.read()
            f.close()
        else:
            f = open(args[0])
            tree = etree.parse(f)
            f.close()
            tree_root = tree.getroot()
            elem_to_use = self.find_elem(args[1], tree_root)
            if elem_to_use == None:
                elem_to_use = self.find_tag(args[1], tree_root)
            root_elem.append(elem_to_use)

    #Duplicates an element, giving it a new pose and name
    #Note: Doesn't work with actors since they use waypoints
    #      while this only changes the overall pose.
    #      Actor duplication may come in a future update.
    def duplicate_func(self, args, root_elem):
        new_elem = deepcopy(self.find_elem(args[0], root_elem))
        if(new_elem == None):
            new_elem = deepcopy(self.find_elem(args[0], self.root_elem))
        if(new_elem == None):
            print(f"Error: Element {args[0]} does not exist (line {self.line_number})")
            exit()
        new_elem.attrib['name'] = args[1]
        pose_elem = self.find_tag("pose", new_elem)
        old_pose = pose_elem.text.split()
        pose_elem.text = f"{args[2]} {args[3]} {old_pose[2]} {old_pose[3]} {old_pose[4]} {args[4]}"
        root_elem.append(new_elem)

    #Function to create a new element with a specific tag that isn't
    #currently covered by existing commands
    def explicit_func(self, args, root_elem):
        etree.SubElement(root_elem, args[0])

    #Function to set a given attribute of an element
    def attribute_func(self, args, root_elem):
        root_elem.set(args[0], args[1])

    #Function to manually set the text associated with an element
    def text_func(self, args, root_elem):
        type = args.pop(0)
        end_string = ""
        #We need all of the bits of the string to be combined either way
        for word in args:
            end_string = end_string + word + " "
        #Removes trailing space
        #end_string.pop(len(end_string) - 1)
        if type == "set":
            root_elem.text = end_string
        elif type == "add":
            root_elem.text = root_elem.text + " " + end_string
        else:
            print(f"Error: Text command type '{type}' not recognized. Valid types are 'set' and 'add'")
            print(f"Line {self.line_number}")
            exit()

    #Processes the wall array
    def walls_postprocess(self):
        if len(self.wall_array) > 0:
            i = 0
            name_num = 0
            for wall_subarray in self.wall_array:
                for wall in wall_subarray:
                    points = wall.coords
                    x1 = points[0][0]
                    y1 = points[0][1]
                    x2 = points[1][0]
                    y2 = points[1][1]

                    #Find our theta and our length
                    dx = x2 - x1
                    dy = y2 - y1
                    theta = atan2(dy,dx)
                    length = sqrt(dx**2 + dy**2)

                    #Sets up the geometry that's going to be needed
                    #for both collision and visual elements
                    geom_elem = etree.Element("geometry")
                    geom_elem.append(etree.Element("box"))
                    geom_elem[0].append(etree.Element("size"))
                    geom_elem[0][0].text = f"{str(length)} 0.1 2.8"

                    #This is, without a doubt, some of the ugliest non-prototype code I've written,
                    #and for that I apologize.
                    #There's just a bunch of little elements that need to be included
                    #in the wall model, and this is the best way I can think of handling that.
                    wall_elem = etree.Element("model", attrib={"name" : f"wall_{str(name_num)}"})
                    wall_elem.append(etree.Element("static"))
                    wall_elem[0].text = "1"
                    wall_elem.append(etree.Element("link", attrib={"name" : "link"}))
                    wall_elem[1].append(etree.Element("collision", attrib={"name" : "collision"}))
                    wall_elem[1][0].append(deepcopy(geom_elem))
                    wall_elem[1][0].append(etree.Element("max_contacts"))
                    wall_elem[1][0][0].text = "10"
                    wall_elem[1].append(etree.Element("visual", attrib={"name" : "visual"}))
                    wall_elem[1][1].append(etree.Element("cast_shadows"))
                    wall_elem[1][1][0].text = "0"
                    wall_elem[1][1].append(deepcopy(geom_elem))


                    #TODO: Figure out what's up with Gazebo crashing when
                    #different things are entered for script and texture URIs.
                    #Takes the material stored at the class level and
                    #makes the uris for script and texture from it.
                    #I can't think of a better way to do this at this point in time.
                    #I may revisit this when I have a better understanding of how
                    #textures and materials are done in SDF.
                    material_base = self.material_array[i].split('/')[-1]
                    wall_elem[1][1].append(etree.Element("material"))
                    wall_elem[1][1][2].append(etree.Element("script"))
                    wall_elem[1][1][2][0].append(etree.Element("uri"))
                    wall_elem[1][1][2][0][0].text = f"model://grey_wall/materials/scripts"
                    wall_elem[1][1][2][0].append(etree.Element("uri"))
                    wall_elem[1][1][2][0][1].text = f"model://grey_wall/materials/textures"
                    wall_elem[1][1][2][0].append(etree.Element("name"))
                    wall_elem[1][1][2][0][2].text = self.material_array[i]

                    #The first pose adjusts the link pose. By default, the link's
                    #origin is at its very center, meaning that placing it at
                    #"0 0 0" in a model or world will put the overall center of the
                    #link at "0 0 0". By shifting it up by half its height and
                    #off by half its width, we make the "0 0 0" of the wall one end
                    #of it, so running a wall from "0 0" to "1 0" will give us that
                    #instead of a wall from "-0.5 0" to "0.5 0".
                    wall_elem[1].append(etree.Element("pose"))
                    wall_elem[1][2].text = f"{str(length/2)} 0 1.4 0 0 0"
                    wall_elem.append(etree.Element("pose"))
                    wall_elem[2].text = f"{str(x1)} {str(y1)} 0 0 0 {str(theta)}"

                    #Tacks it onto our root element. In the future, I hope to adjust
                    #this to be appendable to individual models. The reason I didn't
                    #just make the wall function create the model and append it to the
                    #above element is that I wasn't sure how to integrate that with
                    #making the doorways with the door command.
                    self.root_elem[0].append(wall_elem)
                    name_num += 1
                i += 1

    #Helper function to search for a specified element in
    #a tree.
    def find_elem(self, elem_name, root_elem):
        if 'name' in root_elem.attrib and root_elem.get('name').lower() == elem_name.lower():
            return root_elem
        for elem in root_elem:
            if self.find_elem(elem_name, elem) != None:
                return elem
        return None

    #Helper function to search for the first of a given tag in
    #a tree.
    def find_tag(self, elem_name, root_elem):
        if root_elem.tag.lower() == elem_name.lower():
            return root_elem
        for elem in root_elem:
            if self.find_tag(elem_name, elem) != None:
                return elem
        return None

    #Argument count function. Used for commands with static number of arguments
    def arg_count(self, command, args):
        return len(args) == self.commands[command]["arg_count"]

    #Special argument count function for text. Only invalid numbers of arguments
    #are one (since that would mean either "set" or "add" ) or none.
    def text_arg_count(self, command, args):
        if len(args) < 2:
            return False
        else:
            return True


    def run(self):
        self.process_lines(self.import_instructions(), self.root_elem, 0)
        self.walls_postprocess()
        self.save_to_file()


if __name__ == "__main__":
    worldGen = WorldGenerator()
    worldGen.run()
