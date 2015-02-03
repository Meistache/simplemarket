#!/usr/bin/python
"""
    Copyright 2011, Dipesh Amin <yaypunkrock@gmail.com>
    Copyright 2011, Stefan Beller <stefanbeller@googlemail.com>

    This file is part of tradey, a trading bot in the mana world
    see www.themanaworld.org
"""
import time
import os
import xml.dom.minidom
from subprocess import call
from xml.etree.ElementTree import *

def clean_xml(parse):
    data = ''
    pos_start = 0
    while parse.find('<', pos_start) != -1:
        pos_start = parse.find('<', pos_start)
        pos_end = parse.find('>', pos_start+1)
        data += parse[pos_start:pos_end+1]
        pos_start = pos_end
    return data

class UserTree:
    def __init__(self):
        self.tree = ElementTree(file="data/user.xml")
        self.root = self.tree.getroot()

    def add_user(self, name, stalls, delisted, al):
        if self.get_user(name) == -10:
            user = SubElement(self.root, "user")
            user.set("name", name)
            user.set("stalls", str(stalls))
            user.set("used_stalls", str(0))
            user.set("delisted", str(delisted))
            user.set("money", str(0))
            user.set("id", str(0))
            user.set("accesslevel", str(al))
            self.save()

    def get_user(self, name):
        for elem in self.root:
            if elem.get("name") == name:
                return elem
        return -10

    def remove_user(self, name):
        for elem in self.root:
            if elem.get("name") == name:
                self.root.remove(elem)
                self.save()
                return 1
        return -10

    def save(self):
        # Be sure to call save() after any changes to the tree.
        f = open('data/user.xml', 'w')
        dom = xml.dom.minidom.parseString(clean_xml(tostring(self.root)))
        f.write(dom.toprettyxml('    '))
        f.close()

class ItemTree:
    def __init__(self):
        self.tree = ElementTree(file="data/sale.xml")
        self.root = self.tree.getroot()
        self.u_id = set()

        for elem in self.root:
            self.u_id.add(int(elem.get("uid")))

    def getId(self, index):
        id_itter = 1
        while id_itter in self.u_id:
                id_itter += 1
	id_itter += index
        self.u_id.add(id_itter)
        return id_itter

    def remove_id(self, uid):
        # Free up used id's.
        self.u_id.remove(uid)

    def add_item(self, name, item_id, amount, price):
        user = SubElement(self.root, "item")
        user.set("name", name)
        user.set("itemId", str(item_id))
        user.set("price", str(price))
        user.set("add_time", str(time.time()))
        user.set("amount", str(amount))
        user.set("uid", str(self.getId(0)))
        self.save()

    def get_uid(self, uid):
        for elem in self.root:
            if elem.get("uid") == str(uid):
                return elem
        return -10

    def remove_item_uid(self, uid):
        for elem in self.root:
            if elem.get("uid") == str(uid):
                self.root.remove(elem)
                self.remove_id(uid)
                self.save()
                return 1
        return -10

    def save(self):
        # Be sure to call save() after any changes to the tree.
        f = open('data/sale.xml', 'w')
        dom = xml.dom.minidom.parseString(clean_xml(tostring(self.root)))
        f.write(dom.toprettyxml('    '))
        f.close()

class StackTree:
    def __init__(self):
	self.MIN = 101
	self.MAX = 300
        self.tree = ElementTree(file="data/stack.xml")
        self.root = self.tree.getroot()
        self.u_id = set()
	self.nextid = self.MIN 

        for elem in self.root:
            self.u_id.add(int(elem.get("uid")))

    def getId(self, index):
        id_itter = 1
        while id_itter in self.u_id:
                id_itter += 1
	id_itter += index
        self.u_id.add(id_itter)
        return id_itter

    def remove_id(self, uid):
        # Free up used id's.
        self.u_id.remove(uid)

    def add_item(self, name, item_id, amount, price):
        user = SubElement(self.root, "item")
        user.set("name", name)
        user.set("itemId", str(item_id))
        user.set("price", str(price))
        user.set("amount", str(amount))
        user.set("index", str(0))
        user.set("uid", str(self.getId(100)))
        self.save()

    def get_uid(self, uid):
        for elem in self.root:
            if elem.get("uid") == str(uid):
                return elem
        return -10

    def set_index(self, itemid, index):
        for elem in self.root:
            if elem.get("itemId") == str(itemid):
                elem.set("index", str(index))
                return 1
        return -10

    def remove_item_uid(self, uid):
        for elem in self.root:
            if elem.get("uid") == str(uid):
                self.root.remove(elem)
                self.remove_id(uid)
		if self.nextid == self.MAX:
			self.nextid = self.MIN
		else:
			self.nextid = uid+1
                self.save()
                return 1
        return -10
 
    def save(self):
        # Be sure to call save() after any changes to the tree.
        f = open('data/stack.xml', 'w')
        dom = xml.dom.minidom.parseString(clean_xml(tostring(self.root)))
        f.write(dom.toprettyxml('    '))
        f.close()


class DelistedTree:
    def __init__(self):
        self.tree = ElementTree(file="data/delisted.xml")
        self.root = self.tree.getroot()
        self.u_id = set()

        for elem in self.root:
            self.u_id.add(int(elem.get("uid")))

    def getId(self, index):
        id_itter = 1
        while id_itter in self.u_id:
                id_itter += 1
	id_itter += index
        self.u_id.add(id_itter)
        return id_itter

    def remove_id(self, uid):
        # Free up used id's.
        self.u_id.remove(uid)

    def add_item(self, name, item_id, amount, index):
        user = SubElement(self.root, "item")
        user.set("name", name)
        user.set("itemId", str(item_id))
        user.set("amount", str(amount))
        user.set("index", str(index))
        user.set("uid", str(self.getId(300)))
        self.save()

    def get_uid(self, uid):
        for elem in self.root:
            if elem.get("uid") == str(uid):
                return elem
        return -10

    def remove_item_uid(self, uid):
        for elem in self.root:
            if elem.get("uid") == str(uid):
                self.root.remove(elem)
                self.remove_id(uid)
                self.save()
                return 1
        return -10

    def save(self):
        # Be sure to call save() after any changes to the tree.
        f = open('data/delisted.xml', 'w')
        dom = xml.dom.minidom.parseString(clean_xml(tostring(self.root)))
        f.write(dom.toprettyxml('    '))
        f.close()

def saveData(commitmessage = "commit"):
    # This assumes the current working directory is the tradey directory.
    os.chdir("data")
    call(["git", "commit","-a", '-m "' + commitmessage + '"'])
    os.chdir("..")

if __name__ == '__main__':
    print "Do not run this file directly. Run main.py"
