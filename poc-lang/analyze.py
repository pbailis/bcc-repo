
from sys import argv
from calder_parse import *
from calder_types import *
from calder_analysis import *

'''
CHECKS
--decrement
--conditional decrement
--delete
--uniqueness on insert
'''

toks = parse(argv[1])
tables = get_tables(toks)
procs = get_storedprocedures(toks)
if not analyze_for_conflicts(tables, procs):
    print "Some conflicts were found"
