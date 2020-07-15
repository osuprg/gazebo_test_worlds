#!/usr/bin/env python

waypoint_string = "<time>{timestamp}</time>\n<pose>{x} {y} {z} {r} {p} {yaw}</pose>\n"
script_header = "<script>\n<loop>{does_loop}</loop>\n<delay_start>{start_time}</delay_start>\n<auto_start>{does_auto_start}</auto_start>\n<trajectory id=\"{id}\" type=\"{type}\">\n"
script_footer = ""
