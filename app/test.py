import os
import logging
try:
    os.remove('/home/tolik/Documents/hwbot_v2/app/text.txt')
except FileNotFoundError:
    print('File not found')
