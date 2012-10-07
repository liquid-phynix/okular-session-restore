#!/usr/bin/python2

import os
if os.getuid() == 0:
    print 'you are root, lets quit'
    exit(-1)
    
import dbus, dbus.service, dbus.proxies, gobject, json, subprocess, sys
from dbus.mainloop.glib import DBusGMainLoop

session_file = os.getenv('HOME') + '/.okularsession'

store = {}
bus = None

def loadSession():
    try:
        f = open(session_file, 'r')
        for fn in json.load(f):
            subprocess.Popen(['okular', fn])
        f.close()
    except IOError: pass

def saveSession():
    with open(session_file, 'w') as f:
        json.dump(store.values(), f, indent = 1)

def getDoc(name):
    proxy = dbus.proxies.ProxyObject(conn = bus.get_connection(), bus_name = name, object_path = '/okular')
    return proxy.currentDocument(dbus_interface = 'org.kde.okular')
        
def nameOwnerChanged(name, old_owner, new_owner):
    if not name.startswith('org.kde.okular'): return
    if new_owner == "":
        del store[name]
    else:
        doc = getDoc(name)
        if doc != "":
            store[name] = doc
    saveSession()

if __name__ == '__main__':
    DBusGMainLoop(set_as_default = True)
    try:
        bus = dbus.SessionBus()
        if len(sys.argv) == 2 and sys.argv[1] == 'update':
            proxy = dbus.proxies.ProxyObject(conn = bus.get_connection(), bus_name = 'org.freedesktop.DBus', object_path = '/org/freedesktop/DBus')
            for name in proxy.ListNames(dbus_interface = 'org.freedesktop.DBus'):
                if name.startswith('org.kde.okular'):
                    doc = getDoc(name)
                    if doc != "":
                        store[name] = doc
            saveSession()
            exit(0)
            
    except dbus.DBusException:
        print 'cannot connect to sessionbus'
    try:
        myBus = dbus.service.BusName('org.mcstar.okularsession', bus = bus, do_not_queue = True)

        loop = gobject.MainLoop()
        bus.add_signal_receiver(nameOwnerChanged, dbus_interface = "org.freedesktop.DBus", signal_name = "NameOwnerChanged")
        try:
            loadSession()
            loop.run()
        except KeyboardInterrupt:
            exit(-1)
        finally:
            saveSession()
    except dbus.DBusException:
        print 'already connected to dbus'
