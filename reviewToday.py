#!/usr/bin/python
#-*- coding: utf-8 -*-

import sys
import time
import sqlite3
# put input data into database
# calculate what need to be reviewd today
# interval: (*immediately on your own), today, +1 day, +3days, +7days, + 14 days, + 28 days, +90 days, + 180 days, + 365 days
INTERVALS = [0, 1, 3, 7, 14, 28, 90, 180, 365]

# database knowledgeDate
DB_NAME = "ReviewToday.db"
TABLE_NAME = "ReviewToday"

conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

# check table for debug
if len(sys.argv) == 2 and sys.argv[1] == "show":
    c.execute("select * from ReviewToday")
    print c.fetchall()
    exit(0)

# utils
def get_today_start_ts():
    t = time.localtime(time.time())
    time1 = time.mktime(time.strptime(time.strftime('%Y-%m-%d 00:00:00', t),'%Y-%m-%d %H:%M:%S'))
    return int(time1)

# public API, need table name
def has_table(table):
    c.execute("SELECT COUNT(*) FROM sqlite_master where type='table' and name=?", [table])
    return c.fetchone()[0] == 1


def item_exist(table, item):
    c.execute("SELECT COUNT(*) FROM {table} where name = ?".format(table = table), [item])
    ret = c.fetchone()[0]
    return ret == 1

def get_status(table, item):
    c.execute("SELECT * FROM {table} where name = ?".format(table = table), [item])
    return c.fetchone()[3]

# private API, get table name from a constant
def update_item(name, last_date):
    last_date = int(time.time()) + last_date * 86400
    ret = False
    if item_exist(TABLE_NAME, name):
        ret = True
        status = get_status(TABLE_NAME, name)
        status += 1
        next_date = -1
        if status == len(INTERVALS):
            status = -1
        else:
            next_date = last_date + INTERVALS[status] * 86400
        c.execute("UPDATE {table} SET next_date = ?, status = ? where name = ?".format(table = TABLE_NAME), [next_date, status, name])
    else:
        start_date = last_date
        next_date = last_date
        c.execute("INSERT INTO {table} VALUES(?, ?, ?, 0)".format(table = TABLE_NAME), [name, start_date, next_date])
    conn.commit()
    return ret

def remove_item(name):
    c.execute("DELETE FROM {table} where name = ?".format(table = TABLE_NAME), [name])
    conn.commit()
    return

def check_table():
    if not has_table(TABLE_NAME):
        print "no table, now create..."
        #create table
        # |name | start date | next date | status|
        c.execute("CREATE TABLE {table_name}(name text, start_date INTEGER, next_date INTEGER, status INTEGER)".format(table_name = TABLE_NAME))
        #c.execute("PRAGMA table_info ({tableName})".format(tableName = TABLE_NAME))
        conn.commit()
        print "Table created!"

def get_today_jobs():
    time_line = get_today_start_ts() + 86400
    c.execute("SELECT * FROM {table} where next_date < ?".format(table = TABLE_NAME), [time_line])
    return c.fetchall()

# main logic start here
check_table()


# def test_sets():
#     update_item('a',3)
#     update_item('a',4)
#     update_item('b',2)
# test_sets()
# c.execute("select * from knowledgeDate")
# print c.fetchall()

## UI part
from Tkinter import *
# list item to do today
#job_list = get_today_jobs()
#listb  = Listbox(root)
#for item in job_list:
#    listb.insert(0,item)
#listb.pack()
class Application(Frame):
    def renew_list(self):
        list_data = get_today_jobs()
        self.list.delete(0, 1000)
        for item in list_data:
            self.list.insert(0, item[0])

    def add(self):
        name = self.var_name.get()
        date = self.var_date.get()
        update_item(name, date)
        self.renew_list()

    def get_list_item_name(self):
        list_data_array = self.var_list.get()
        new_array = str(list_data_array)[1:-1]
        new_array = new_array.replace('u\'','\'').replace('\'','').split(', ')
        new_array[0] = new_array[0][0:-1]
        idxs = self.list.curselection()
        if len(idxs)==1:
            idx = int(idxs[0])
            return new_array[idx]
        else:
            return ""
    
    def done(self):
        name = self.get_list_item_name()
        if name != "":
            update_item(name, 0)
            self.renew_list()

    def remove(self):
        name = self.get_list_item_name()
        if name != "":
            remove_item(name)
            self.renew_list()

    def createWidgets(self):
        self.var_name = StringVar()
        self.var_date = IntVar()
        list_data = get_today_jobs()
        list_data_array = []
        for item in list_data:
            list_data_array.append(item[0])
        # must be tuple, or it will be like: [0] = [u'a', [1]=u'b']
        self.var_list = StringVar(value=tuple(list_data_array))

        self.var_name.set("example event")
        self.var_date.set(0)

        self.task_text = Entry(self, width=20)
        #self.task_text.insert("1.0", "example event")
        self.task_text.pack()
        self.task_text["textvariable"] = self.var_name
        
        self.task_date = Entry(self, width=20)
        #self.task_date.insert("1.0", "0:today, 1: yesterday")
        self.task_date.pack()
        self.task_date["textvariable"] = self.var_date
        

        self.add_button = Button(self)
        self.add_button["text"] = "Add"
        self.add_button["command"] = self.add
        self.add_button.pack()

        self.list = Listbox(self, listvariable=self.var_list, height = 10)
        # TODO: scroll bar
        # s = Scrollbar(orient=VERTICAL, command=self.list.yview)
        # self.list['yscrollcommand'] = s.set
        self.list.pack({"side": "left"})
        

        self.done_but = Button(self)
        self.done_but["text"] = "Update"
        self.done_but["command"] = self.done
        self.done_but.pack({"side": "left"})

        self.rm_but = Button(self)
        self.rm_but["text"] = "Remove"
        self.rm_but["command"] = self.remove
        self.rm_but.pack({"side": "left"})

    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.pack()
        self.createWidgets()

def run_loop():
    root = Tk()
    app = Application(master=root)
    app.master.title("Review Date Mgr")
    app.mainloop()

run_loop()


# close
conn.close()