#!/usr/bin/env python

from math import atan2, sqrt

file_in = "wall_endpoints.txt"
file_out = "walls_export.txt"

#Static strings roken into chunks since I didn't want to deal with mile-long
#strings or a huge amount of strings, and Python doesn't allow for
header = "      <static>1</static>\n      <link name='link'>\n"
#internal_pose ="        <pose>0 0 1.4 0 -0 0</pose>\n"
mid_0 ="     <collision name='collision'>\n          <geometry>\n            <box>\n"
#size              <size>7.5 0.2 2.8</size>
mid_1 ="            </box>\n          </geometry>\n          <max_contacts>10</max_contacts>\n          <surface>\n"
mid_2 ="            <bounce/>\n            <friction>\n              <ode/>\n            </friction>\n"
mid_3 ="            <contact>\n              <ode/>\n            </contact>\n          </surface>\n"
mid_4 ="        </collision>\n        <visual name='visual'>\n          <cast_shadows>0</cast_shadows>\n"
mid_5 ="          <geometry>\n            <box>\n"
#size              <size>7.5 0.2 2.8</size>
mid_6 ="            </box>\n          </geometry>\n          <material>\n            <script>\n"
mid_7 ="              <uri>model://grey_wall/materials/scripts</uri>\n              <uri>model://grey_wall/materials/textures</uri>\n              <name>vrc/grey_wall</name>\n"
mid_8 ="            </script>\n          </material>\n        </visual>\n        <velocity_decay>\n"
mid_9 ="          <linear>0</linear>\n          <angular>0</angular>\n        </velocity_decay>\n"
mid_10="        <self_collide>0</self_collide>\n        <kinematic>0</kinematic>\n        <gravity>1</gravity>\n      </link>\n"
#external_pose      <pose>-7 -1 0 0 -0 0</pose>
footer ="    </model>\n"

section_0 = mid_1 + mid_2 + mid_3 + mid_4 + mid_5
section_1 = mid_6 + mid_7 + mid_8 + mid_9 + mid_10


def export_wall(f, name, internal_pose, size, external_pose):
    full = name + header + internal_pose + mid_0 + size + section_0 + size + section_1 + external_pose + footer
    f.write(full)

def import_positions(filename):
    f = open(filename, "r")
    walls = []
    for line in f:
        parts = line.split()
        wall = [float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])]
        walls.append(wall)
    return walls

def process_walls(filename, walls):
    f = open(filename, "w")
    i = 0
    for wall in walls:
        name = "<model name='grey_wall" + str(i) + "'>\n"
        x0 = wall[0]
        y0 = wall[1]
        x1 = wall[2]
        y1 = wall[3]

        dx = x1 - x0
        dy = y1 - y0
        theta = atan2(dy,dx)
        length = sqrt(dx**2 + dy**2)


	internal_pose = "<pose>" + str(length/2) + " 0 1.4 0 -0 0</pose>\n"
        size = "              <size>" + str(length) + " 0.05 2.8</size>\n"
        external_pose = "      <pose>" + str(x0) + " " + str(y0) + " -1 0 0 " + str(theta) + "</pose>\n"
        i = i + 1
        export_wall(f, name, internal_pose, size, external_pose)

    f.close()

def main_func(f_in, f_out):
    walls = import_positions(f_in)
    process_walls(f_out, walls)


main_func(file_in, file_out)
