from pyparsing import *
 
def parse(input_file):
    # table declaration parsing
    begin_declare_table = Suppress( CaselessLiteral( "DECLARE TABLE" ) ) + Word ( alphas ).setResultsName("name")
    end_declare_table = Suppress( CaselessLiteral( "END TABLE" ) )
    unique = Literal("UNIQUE")
    sequential = Literal("SEQUENCE")
    gt = ">" + Word( nums ).setResultsName("thresh")
    lt = "<" + Word( nums ).setResultsName("thresh")
    constraint = ( unique | sequential | gt | lt )
    column_type = oneOf("STRING NUMBER").setResultsName("type")
    column = column_type + Word( alphas ).setResultsName("name") + Optional(constraint).setResultsName("constraint")
    tabledeclaration = begin_declare_table + OneOrMore( Group ( column ) ).setResultsName("columns") + end_declare_table
    tabledeclarations = OneOrMore( Group ( tabledeclaration ) )

    # stored procedure parsing
    endstmt = Suppress( ";" )
    begin_stored_procedure = Suppress( CaselessLiteral( "BEGIN PROCEDURE" ) )
    end_stored_procedure = Suppress( CaselessLiteral( "END PROCEDURE" ) )

    arithmetic_operator = oneOf("+ -")
    arithmetic_expr = ( Group ( Word( alphanums ).setResultsName("lhs") +
                          arithmetic_operator.setResultsName("operator") +
                          Word( alphanums ).setResultsName("rhs") ) | 
                        Group( Word( alphanums ).setResultsName("constant") ) )

    sp_parameter_type = oneOf(" STRING NUMERIC ").setResultsName("type")
    sp_parameter_name = Word( alphanums ).setResultsName("name") 
    sp_parameter = CaselessLiteral( "PARAMETER" ) + sp_parameter_name + sp_parameter_type
    
    table = Word( alphas ).setResultsName("table")
    column = Word( alphas ).setResultsName("column")
    columns = Group( delimitedList( column ) ).setResultsName("columns")

    predicate_parameter = Word( alphanums ).setResultsName("parameter")
    predicate_comparator = oneOf("= < >").setResultsName("comparator")
    predicate = ( Word( alphas ).setResultsName("column") +
                  predicate_comparator +
                  predicate_parameter ).setResultsName("predicate")

    numeric_modify_stmt = ( CaselessLiteral( "UPDATE" ) +
                            table +
                            ( CaselessLiteral( "INCREMENT" ) | CaselessLiteral( "DECREMENT" ) ).setResultsName("optype") +
                            column +
                            CaselessLiteral( "BY" ) +
                            arithmetic_expr.setResultsName("expression") + 
                            CaselessLiteral( "WHERE" ) +
                            predicate )

    select_stmt = ( CaselessLiteral( "SELECT" ) + 
                    columns + 
                    CaselessLiteral( "FROM" ) +
                    table +
                    CaselessLiteral( "WHERE" ) +
                    predicate )

    update_stmt = ( numeric_modify_stmt )
    varassign_stmt = ( CaselessLiteral( "var" ) +
                       Word( alphas ).setResultsName("name") + 
                       "=" +
                       select_stmt.setResultsName("assign_statement")
                       )

    conditional_update_stmt = ( CaselessLiteral( "IF" ) +
                                predicate.setResultsName("conditional_predicate") +
                                ":" +
                                update_stmt.setResultsName("if_body") + endstmt +
                                Optional( CaselessLiteral( "ELSE:" ) +
                                update_stmt.setResultsName("else_body") )
                                )

    

    statement = ( update_stmt |
                  conditional_update_stmt |
                  select_stmt |
                  varassign_stmt ) + endstmt

    storedproc = ( begin_stored_procedure +
                   Word( alphas ).setResultsName("name") +
                   ZeroOrMore ( Group( sp_parameter ) ).setResultsName("parameters") +
                   OneOrMore ( Group( statement ) ).setResultsName("statements") +
                   end_stored_procedure )
    storedprocedures = OneOrMore( Group ( storedproc ) )

    calderprogram = tabledeclarations.setResultsName("tables") + storedprocedures.setResultsName("storedprocedures")

    return calderprogram.parseFile(input_file)
