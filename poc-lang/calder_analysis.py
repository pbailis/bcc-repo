
from calder_types import *
from termcolor import colored

def analyze_for_conflicts(tables, procedures):
    passed = True
    passed &= sequence_check(tables, procedures)

    return passed
    
def warn(errstring):
    print colored("CONFLICT FOUND: %s" % (errstring), "red")

def passed_info(passed, testname):
    if passed:
        print colored("Passed '%s' test!" % (testname), "green")
    else:
        print colored("Failed '%s' test... Please see warnings." % (testname), "red")

def sequence_check(tables, procedures):
    passed = True
    for table in tables:
        for column in table.columns:
            if isinstance(column.constraint, SequenceConstraint):
                warn("%s.%s uses SEQUENCE" % (table.name, column.name))
                
                # TODO: print out all tables that do inserts
                
                passed = False

    passed_info(passed, "Sequence number check")
    return passed

