import os
import sys

lib_directory = os.path.dirname(os.path.abspath(__file__))
if lib_directory not in sys.path:
   sys.path.insert(0, lib_directory)