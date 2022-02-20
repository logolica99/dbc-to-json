from transmutator import *
sf = open('example.dbc','r')
dbcString = sf.read()
# print(dbcString)

parceDbc(dbcString,{})

