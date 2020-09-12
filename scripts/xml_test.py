#!/usr/bin/env python

from lxml import etree

root = etree.Element("root")


def mod_element(root_elem):
    new_elem = etree.Element("Testing")
    root_elem.append(new_elem)
    return root_elem

new_root = mod_element(root)

print("Old tree:")
print(etree.tostring(root, pretty_print=True))

print("New tree:")
print(etree.tostring(new_root, pretty_print=True))
