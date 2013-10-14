
def enum(**enums):
    return type('Enum', (), enums)

ColumnType = enum(STRING=1,
                  NUMBER=2)

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

class Column:
    def __init__(self, name, ctype, constraint):
        self.name = name
        self.ctype = ctype
        self.constraint = constraint

class Table:
    def __init__(self, name, columns):
        self.name = name
        self.columns = columns

def get_tables(toks):
    tables = []
    for table_toks in toks.tables:
        tname = table_toks.name
        columns = []
        for col in table_toks.columns:
            if col.type == "STRING":
                ctype = ColumnType.STRING
            elif col.type == "NUMBER":
                ctype = ColumnType.NUMBER

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
            columns.append(Column(col.name, ctype, constraint))
        tables.append(Table(tname, columns))
    return tables


ParameterType = enum(STRING=1,
                     NUMBER=2)

class EqualsPredicate:
    def __init__(self, column, value):
        self.column = column
        self.value = value

class LessThanPredicate:
    def __init__(self, column, value):
        self.column = column
        self.value = value

class GreaterThanPredicate:
    def __init__(self, column, value):
        self.column = column
        self.value = value

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
    def __init__(self, table, column, predicate):
        self.table = table
        self.column = column
        self.predicate = predicate

class VariableDefinition:
    def __init__(self, name, assign_statement):
        self.name = name
        self.creation_statement = assign_statement

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

class ConstantExpression:
    def __init__(self, constant):
        self.constant = constant

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

def create_matching_predicate(pred_toks):
    cname = pred_toks.column
    cparam = pred_toks.parameter

    if pred_toks.comparator == "=":
        return EqualsPredicate(cname, cparam)
    elif pred_toks.comparator == "<":
        return LessThanPredicate(cname, cparam)
    elif pred_toks.comparator == ">":
        return GreaterThanPredicate(cname, cparam)

def create_statement(statement_toks):
    tname = statement_toks.table
    cname = statement_toks.column
    predicate = create_matching_predicate(statement_toks.predicate)
    if statement_toks[0] == "UPDATE":
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
        return SelectStatement(tname, 
                               cname,
                               predicate)
    elif statement_toks[0] == "var":
        return VariableDefinition(statement_toks.name,
                                  SelectStatement(tname,
                                                  cname,
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
                                                     
                
                
        
            
