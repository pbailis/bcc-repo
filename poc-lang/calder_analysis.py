
from calder_types import *
from termcolor import colored

def analyze_for_conflicts(tables, procedures):
    passed = True
    passed &= sequence_check(tables, procedures)
    passed &= pkey_check(tables, procedures)
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

def table_name(qualified_name):
    return qualified_name.split('.')[0]

def column_name(qualified_name):
    return qualified_name.split('.')[1]

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

def pkey_check(tables, procedures):
    passed = True

    # Checks:
    # 1.) Inserting a specific value into all PRIMARY KEY columns.

    for table in tables:
        if table.pkey:
            for procedure in procedures:
                for statement in procedure.statements:
                    if isinstance(statement, InsertStatement) and statement.table == table.name:
                        pkeys_to_match = list(table.pkey)
                        for cname in statement.values:
                            if cname in pkeys_to_match:
                                pkeys_to_match.remove(cname)
                        if len(pkeys_to_match) == 0:
                            warn(procedure,
                             "INSERTING %s, which form(s) a PRIMARY KEY for %s" % 
                                 (statement.values.keys(), table.name))
                            passed = False

    passed_info(passed, "Primary key insert check")
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

    # if a table column is a foreign key reference, record the table it references
    tablecol_to_fkey = {}
    # if a table is referenced, record a list of table-columns that reference it
    fkey_to_tablecols = {}

    for table in tables:
        for column in table.columns:
            if isinstance(column.constraint, ForeignKeyConstraint):
                qual_table_name = qualified_name(table.name, column.name)
                qual_fkey_name = qualified_name(column.constraint.table, column.constraint.column)
                tablecol_to_fkey[qual_table_name] = qual_fkey_name

                if table.name not in fkey_to_tablecols:
                    fkey_to_tablecols[table.name] = []
                fkey_to_tablecols[table.name].append(qual_table_name)
    
    for procedure in procedures:
        for statement in procedure.statements:
            if isinstance(statement, InsertStatement):
                for column in statement.values:
                    analyze_column = qualified_name(statement.table, column)
                    # if this is a foreign key column...
                    if analyze_column in tablecol_to_fkey:
                        target_table_and_column = tablecol_to_fkey[analyze_column]
                        target_table = table_name(target_table_and_column)
                        target_column = column_name(target_table_and_column)
                        target_value = statement.values[column]

                        # try to find a matching insert or select
                        found_match = False
                        for match_statement in procedure.statements:
                            if isinstance(match_statement, InsertStatement) and match_statement.table == target_table:
                                if target_column in statement.values and match_statement.values[target_column] == target_value:
                                    found_match = True
                                    break

                            elif isinstance(match_statement, VariableDefinition):
                                if (match_statement.creation_statement.table == target_table and
                                    target_column in match_statement.creation_statement.columns[0] and
                                    match_statement.name == target_value):
                                    found_match = True
                                    break

                        if not found_match:
                            passed = False
                            warn(procedure,
                                 "INSERT TO %s (FKEY TO %s; value: %s) BUT NO MATCHING INSERT/SELECT FOUND" % (analyze_column,
                                                                                                               target_table_and_column,
                                                                                                               target_value))
            if isinstance(statement, DeleteStatement):
                # for all constraint columns, make sure we clean up our references...
                if statement.table not in fkey_to_tablecols:
                    continue

                for referencing_column in fkey_to_tablecols[statement.table]:
                    # try to find a matching delete
                    found_match = False
                    for match_statement in procedure.statements:
                        # punt on the hard cases for now....
                        if (isinstance(match_statement, DeleteStatement) 
                            and match_statement.table == table_name(referencing_column)
                            # cake; delete all of the references....
                            and (match_statement.predicate.value == "*" or
                            # slightly more complex; delete if select predicates match
                                 (qualified_name(statement.table, statement.predicate.column) ==
                                  tablecol_to_fkey[qualified_name(match_statement.table, match_statement.predicate.column)]
                                  and match_statement.predicate.value == statement.predicate.value))):
                            # otherwise, give up (conservative)
                            found_match = True
                            break

                    if not found_match:
                        passed = False
                        warn(procedure,
                             "DELETE FROM %s BUT NO MATCHING DELETE FROM REFERENCING COLUMN %s" % (statement.table,
                                                                                                       referencing_column))
            
    passed_info(passed, "Foreign key constraint check")
    return passed

def agg_check(tables, procedures):
    passed = True
    for table in tables:
        for column in table.columns:
            passed = False
            
    passed_info(passed, "Aggregation constraint check (NOT IMPLEMENTED)")
    return passed
