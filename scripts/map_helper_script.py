#!/usr/bin/env python
from PIL import Image, ImageDraw

file_in = "wall_endpoints.txt"
file_out = "map.pgm"

def import_positions(filename):
    f = open(filename, "r")
    walls = []
    for line in f:
        parts = line.split()
        wall = [float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])]
        walls.append(wall)
    return walls

def process_walls(filename, walls):
    xmax = 0
    ymax = 0
    for coords in walls:
        x = max([float(coords[0]), float(coords[2])])
        y = max([float(coords[1]), float(coords[3])])
        xmax = max([x, xmax])
        ymax = max([y, ymax])

    im = Image.new(mode = "RGB", size = (int(xmax * 20 * 1.25), int(ymax * 20 * 1.25)), color = (255, 255, 255))
    draw = ImageDraw.Draw(im)
    for wall in walls:
        p1 = (int(xmax * 0.1 + 20*float(wall[0])), int(ymax * 0.1 +20*(ymax - float(wall[1]))))
        p2 = (int(xmax*0.1 + 20*float(wall[2])), int(ymax*0.1 + 20*(ymax - float(wall[3]))))
        draw.line([p1, p2], fill = "black", width = 1)
    im.save(filename)

def main_func(f_in, f_out):
    walls = import_positions(f_in)
    process_walls(f_out, walls)

main_func(file_in, file_out)
