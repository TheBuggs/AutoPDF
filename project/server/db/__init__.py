#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlite3

connection = sqlite3.connect('../../db/db.db')

with open('../../db/schema.sql') as f:
    connection.executescript(f.read())

cur = connection.cursor()

connection.commit()
connection.close()