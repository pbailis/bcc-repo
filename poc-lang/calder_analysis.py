
from calder_types import *
from termcolor import colored

def analyze_for_conflicts(tables, procedures):
    passed = True
    passed &= sequence_check(tables, procedures)
    passed &= uniqueness_check(tables, procedures)
    passed &= inequality_check(tables, procedures)
    passed &= fk_check(tables, procedures)
    passed &= agg_check(tables, procedures)

    return passed
    
def warn(procedure, errstring):
    print colored("CONFLICT FOUND IN PROCEDURE %s: %s" % (procedure.name, errstring), "white", "on_red")

def passed_info(passed, testname):
    if passed:
        print colored("Passed '%s' test!" % (testname), "green")
    else:
        print colored("Failed '%s' test... Please see warnings." % (testname), "red")

def qualified_name(table, column):
    return table+"."+column

def sequence_check(tables, procedures):
    passed = True

    # Checks:
    # 1.) Insertion into a sequenced table.
    # 2.) Deletion from a sequenced table.

    sequence_tables = []

    for table in tables:
        for column in table.columns:
            if isinstance(column.constraint, SequenceConstraint):
                sequence_tables.append(table.name)


    for procedure in procedures:
        for statement in procedure.statements:
            if isinstance(statement, InsertStatement) and statement.table in sequence_tables:
                warn(procedure,
                     "INSERT INTO %s, which has a SEQUENCE" % (table.name))
                passed = False
            elif isinstance(statement, DeleteStatement) and statement.table in sequence_tables:
                warn(procedure,
                     "DELETE FROM %s, which has a SEQUENCE" % (table.name))
                passed = False

    passed_info(passed, "Sequence number check")
    return passed


def uniqueness_check(tables, procedures):
    passed = True

    # Checks:
    # 1.) Inserting a specific value into a UNIQUE column.

    unique_columns = []

    for table in tables:
        for column in table.columns:
            if isinstance(column.constraint, UniqueConstraint):
                unique_columns.append(qualified_name(table.name, column.name))

    for procedure in procedures:
        for statement in procedure.statements:
            if isinstance(statement, InsertStatement):
                for cname in statement.values:
                    if qualified_name(statement.table, cname) in unique_columns:
                        warn(procedure,
                             "INSERT INTO %s, which is UNIQUE -- for arbitrary values, this is unsafe" % 
                             (qualified_name(statement.table, cname)))
                        passed = False

    passed_info(passed, "Uniqueness check")
    return passed

def inequality_check(tables, procedures):
    # Checks:
    # 1.) > -- DECREMENT
    # 2.) < -- INCREMENT

    less_than_cols = []
    greater_than_cols = []

    passed = True
    for table in tables:
        for column in table.columns:
            if isinstance(column.constraint, LessThanConstraint):
                less_than_cols.append(qualified_name(table.name, column.name))
            elif isinstance(column.constraint, GreaterThanConstraint):
                greater_than_cols.append(qualified_name(table.name, column.name))
            passed = False

    for procedure in procedures:
        for statement in procedure.statements:
            if isinstance(statement, DecrementStatement) and qualified_name(statement.table, statement.column) in greater_than_cols:
                warn(procedure,
                     "DECREMENT %s BY %s [condition: %s]" % (qualified_name(statement.table, statement.column),
                                                                statement.value,
                                                                statement.predicate))
                passed = False

            elif isinstance(statement, IncrementStatement) and qualified_name(statement.table, statement.column) in less_than_cols:
                warn(procedure,
                     "INCREMENT %s BY %s [condition: %s]" % (qualified_name(statement.table, statement.column),
                                                                statement.value,
                                                                statement.predicate))
                passed = False


            elif isinstance(statement, ConditionalIncrement):
                s = statement.if_statement
                if isinstance(s, DecrementStatement) and qualified_name(s.table, s.column) in greater_than_cols:
                    warn(procedure,
                         "CONDITIONAL (TRUE) DECREMENT %s BY %s [condition: %s]" % (qualified_name(s.table, s.column),
                                                                                    s.value,
                                                                                    s.predicate))
                    passed = False
                elif isinstance(s, IncrementStatement) and qualified_name(s.table, s.column) in less_than_cols:
                    warn(procedure,
                         "CONDITIONAL (TRUE) INCREMENT %s BY %s [condition: %s]" % (qualified_name(s.table, s.column),
                                                                                    s.value,
                                                                                    s.predicate))
                    passed = False

                s = statement.else_statement
                if isinstance(s, DecrementStatement) and qualified_name(s.table, s.column) in greater_than_cols:
                    warn(procedure,
                         "CONDITIONAL (FALSE) DECREMENT %s BY %s [condition: %s]" % (qualified_name(s.table, s.column),
                                                                                    s.value,
                                                                                    s.predicate))
                    passed = False
                elif isinstance(s, IncrementStatement) and qualified_name(s.table, s.column) in less_than_cols:
                    warn(procedure,
                         "CONDITIONAL (FALSE) INCREMENT %s BY %s [condition: %s]" % (qualified_name(s.table, s.column),
                                                                                    s.value,
                                                                                    s.predicate))
                    passed = False
                
    passed_info(passed, "Inequality check")
    return passed

def fk_check(tables, procedures):
    passed = True
    for table in tables:
        for column in table.columns:
            passed = False
            
    passed_info(passed, "Foreign key constraint check")
    return passed

def agg_check(tables, procedures):
    passed = True
    for table in tables:
        for column in table.columns:
            passed = False
            
    passed_info(passed, "Aggregation constraint check")
    return passed
