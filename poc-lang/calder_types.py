
def enum(**enums):
    return type('Enum', (), enums)

ColumnType = enum(STRING=1,
                  NUMBER=2,
                  REFERENCE=3)

class EqualsPredicate:
    def __init__(self, column, value):
        self.column = column
        self.value = value

    def __str__(self):
        return self.column+"="+self.value

class LessThanPredicate:
    def __init__(self, column, value):
        self.column = column
        self.value = value

    def __str__(self):
        return self.column+"<"+self.value

class GreaterThanPredicate:
    def __init__(self, column, value):
        self.column = column
        self.value = value

    def __str__(self):
        return self.column+">"+self.value

def create_matching_predicate(pred_toks):
    cname = pred_toks.predicate_column
    cparam = pred_toks.predicate_parameter

    if pred_toks.comparator == "=":
        return EqualsPredicate(cname, cparam)
    elif pred_toks.comparator == "<":
        return LessThanPredicate(cname, cparam)
    elif pred_toks.comparator == ">":
        return GreaterThanPredicate(cname, cparam)

class LessThanConstraint:
    def __init__(self, threshold):
        self.threshold = threshold

class GreaterThanConstraint:
    def __init__(self, threshold):
        self.threshold = threshold

class UniqueConstraint:
    pass

class SequenceConstraint:
    pass

class ForeignKeyConstraint:
    def __init__(self, table, column):
        self.table = table
        self.column = column

class AggregateConstraint:
    def __init__(self, table, column, predicate):
        self.table = table
        self.column = column
        self.predicate = predicate

class Column:
    def __init__(self, name, ctype, constraint):
        self.name = name
        self.ctype = ctype
        self.constraint = constraint

class Table:
    def __init__(self, name, columns, pkey):
        self.name = name
        self.columns = columns
        self.pkey = pkey

def get_tables(toks):
    tables = []
    for table_toks in toks.tables:
        tname = table_toks.table_name
        columns = []
        if table_toks.pkey:
            pkey = [col for col in table_toks.pkey.columns]
        else:
            pkey = None

        for col in table_toks.columns:
            if col.type == "STRING":
                ctype = ColumnType.STRING
            elif col.type == "NUMBER":
                ctype = ColumnType.NUMBER
            elif col.type == "REFERENCE":
                ctype = ColumnType.REFERENCE

            constraint = None
            if col.constraint:
                if col.constraint == "UNIQUE":
                    constraint = UniqueConstraint()
                elif col.constraint == "SEQUENCE":
                    constraint = SequenceConstraint()
                elif col.constraint == "<":
                    constraint = LessThanConstraint(col.thresh)
                elif col.constraint == ">":
                    constraint = GreaterThanConstraint(col.thresh)
                elif col.constraint == "FOREIGN KEY":
                    if ctype != ColumnType.REFERENCE:
                        print "FOREIGN KEY only allowed on REFERENCE columns!"
                        return
                    constraint = ForeignKeyConstraint(col.fk.table, col.fk.column)
                elif col.constraint == "AGGREGATES":
                    constraint = AggregateConstraint(col.agg.table, col.agg.column, create_matching_predicate(col.agg.predicate))
                    
            columns.append(Column(col.name, ctype, constraint))
        tables.append(Table(tname, columns, pkey))
    return tables


ParameterType = enum(STRING=1,
                     NUMBER=2)

class IncrementStatement:
    def __init__(self, table, column, value, predicate):
        self.table = table
        self.column = column
        self.value = value
        self.predicate = predicate

class DecrementStatement:
    def __init__(self, table, column, value, predicate):
        self.table = table
        self.column = column
        self.value = value
        self.predicate = predicate

class ConditionalIncrement:
    def __init__(self, predicate, if_statement, else_statement):
        self.predicate = predicate
        self.if_statement = if_statement
        self.else_statement = else_statement

class SelectStatement:
    def __init__(self, table, columns, predicate):
        self.table = table
        self.columns = columns
        self.predicate = predicate

class InsertStatement:
    def __init__(self, table, values):
        self.table = table
        self.values = values

class DeleteStatement:
    def __init__(self, table, predicate):
        self.table = table
        self.predicate = predicate

class VariableDefinition:
    def __init__(self, name, creation_statement):
        self.name = name
        self.creation_statement = creation_statement

class StoredProcedure:
    def __init__(self, name, parameters, statements):
        self.name = name
        self.parameters = parameters
        self.statements = statements

class SimpleArithmeticExpression:
    def __init__(self, operator, lhs, rhs):
        self.operator = operator
        self.lhs = lhs
        self.rhs = rhs

    def __str__(self):
        return self.lhs+self.operator+self.rhs

class ConstantExpression:
    def __init__(self, constant):
        self.constant = constant

    def __str__(self):
        return self.constant

class Parameter:
    def __init__(self, name, ptype):
        self.name = name
        self.ptype = ptype

def create_arithmetic_expression(expr_toks):
    if expr_toks.operator:
        return SimpleArithmeticExpression(expr_toks.operator,
                                          expr_toks.lhs,
                                          expr_toks.rhs)
    else:
        return ConstantExpression(expr_toks.constant)

def create_statement(statement_toks):
    tname = statement_toks.table
    cname = statement_toks.column
    if statement_toks.predicate:
        predicate = create_matching_predicate(statement_toks.predicate)
    if statement_toks[0] == "INSERT INTO":
        assigns = {}
        for assign in statement_toks.assignments:
            assigns[assign.column] = assign.value
        return InsertStatement(tname, assigns)
    elif statement_toks[0] == "DELETE FROM":
        return DeleteStatement(tname, predicate)                               
    elif statement_toks[0] == "UPDATE":
        if statement_toks.optype == "INCREMENT":
            return IncrementStatement(tname,
                                      cname,
                                      create_arithmetic_expression(statement_toks.expression),
                                      predicate)
        elif statement_toks.optype == "DECREMENT":
            return DecrementStatement(tname,
                                      cname,
                                      create_arithmetic_expression(statement_toks.expression),
                                      predicate)
    elif statement_toks[0] == "SELECT":
        print statement_toks
        return SelectStatement(tname, 
                               statement_toks.columns,
                               predicate)
    elif statement_toks[0] == "var":
        return VariableDefinition(statement_toks.name,
                                  SelectStatement(tname,
                                                  statement_toks.columns,
                                                  predicate))
    elif statement_toks[0] == "IF":
        predicate = create_matching_predicate(statement_toks.conditional_predicate)
        if_statement = create_statement(statement_toks.if_body)
        else_statement = create_statement(statement_toks.else_body)
        return ConditionalIncrement(predicate, if_statement, else_statement)    

def get_storedprocedures(toks):
    procs = []
    parameters = []
    for proc_toks in toks.storedprocedures:
        proc_name = proc_toks.name
        statements = []

        for param in proc_toks.parameters:
            parameters.append(Parameter(param.name, param.type))

        for statement_toks in proc_toks.statements:
            statements.append(create_statement(statement_toks))
                
        procs.append(StoredProcedure(proc_name, parameters, statements))

    return procs
