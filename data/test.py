import timetable
import importlib
print(timetable.monday)

file = open('data/timetable.py', 'a')
file.write('monday.append(2)\n')
file.close()

print(timetable.monday)

importlib.reload(timetable)
print(timetable.monday)
