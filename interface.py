# Interface class to feed into main.py
import sys
sys.path.append("..")

from variables import MetaVariables
import variables as variables
from analyzer_helper import *
from database_connector import database_connector
from report_maker import report_maker

# Utility Classes

# Variables

# Analyzer Classes
# from acpi_analyzer import *
# from pnp_analyzer import *

if __name__ == "__main__":
    pa = pnp_analyzer()
