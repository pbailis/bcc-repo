from pyparsing import *

calder_name = Word( alphanums + '*$/%_' )
 
predicate_parameter = ( calder_name | "*" ).setResultsName("predicate_parameter")
predicate_comparator = oneOf("= < >").setResultsName("comparator")
predicate = ( calder_name.setResultsName("predicate_column") +
              predicate_comparator +
              predicate_parameter ).setResultsName("predicate")

def parse(input_file):
    # table declaration parsing
    comment = ("#" + restOfLine).suppress()

    begin_declare_table = Suppress( CaselessLiteral( "DECLARE TABLE" ) ) + calder_name.setResultsName("name")
    end_declare_table = Suppress( CaselessLiteral( "END TABLE" ) )
    unique = Literal("UNIQUE")
    sequential = Literal("SEQUENCE")
    gt = ">" + Word( nums ).setResultsName("thresh")
    lt = "<" + Word( nums ).setResultsName("thresh")
    fk = ( CaselessLiteral( "FOREIGN KEY" ) +
           calder_name.setResultsName("table") +
           "." +
           calder_name.setResultsName("column") ).setResultsName("fk")
    agg = ( CaselessLiteral( "AGGREGATES" ) +
            calder_name.setResultsName("table") + 
            "." + 
            calder_name.setResultsName("column") +
            Optional( CaselessLiteral("WHERE") + predicate ).setResultsName("predicate") ).setResultsName("agg")
    constraint = ( unique | sequential | gt | lt | fk | agg )
    column_type = oneOf("STRING NUMBER REFERENCE").setResultsName("type")
    column = column_type + calder_name.setResultsName("name") + Optional(constraint).setResultsName("constraint")
    primary_key = ( CaselessLiteral("PRIMARY KEY") + delimitedList( Group( calder_name.setResultsName("name") ) ).setResultsName("columns") )
    tabledeclaration = ( begin_declare_table + 
                         Optional( primary_key ).setResultsName("pkey") +
                         OneOrMore( Group ( column ) ).setResultsName("columns")
                         + end_declare_table )
    tabledeclarations = OneOrMore( Group ( tabledeclaration ) )

    # stored procedure parsing
    endstmt = Suppress( ";" )
    begin_stored_procedure = Suppress( CaselessLiteral( "BEGIN PROCEDURE" ) )
    end_stored_procedure = Suppress( CaselessLiteral( "END PROCEDURE" ) )

    arithmetic_operator = oneOf("+ -")
    arithmetic_expr = ( Group ( calder_name.setResultsName("lhs") +
                                arithmetic_operator.setResultsName("operator") +
                                calder_name.setResultsName("rhs") ) | 
                        Group( calder_name.setResultsName("constant") ) )

    sp_parameter_type = oneOf(" STRING NUMERIC ").setResultsName("type")
    sp_parameter_name = calder_name.setResultsName("name") 
    sp_parameter = CaselessLiteral( "PARAMETER" ) + sp_parameter_name + sp_parameter_type
    
    table = calder_name.setResultsName("table")
    column = calder_name.setResultsName("column")
    columns = Group( delimitedList( column ) ).setResultsName("columns")

    numeric_modify_stmt = ( CaselessLiteral( "UPDATE" ) +
                            table +
                            ( CaselessLiteral( "INCREMENT" ) | CaselessLiteral( "DECREMENT" ) ).setResultsName("optype") +
                            column +
                            CaselessLiteral( "BY" ) +
                            arithmetic_expr.setResultsName("expression") + 
                            CaselessLiteral( "WHERE" ) +
                            predicate )

    insert_assignment = column + "=" + calder_name.setResultsName("value")
    insert_stmt = ( CaselessLiteral( "INSERT INTO" ) +
                    table +
                    CaselessLiteral( "VALUES" ) +
                    delimitedList( Group( insert_assignment ) ).setResultsName("assignments") )

    delete_stmt = ( CaselessLiteral( "DELETE FROM" ) +
                    table +
                    CaselessLiteral( "WHERE" ) 
                    + predicate )

    select_stmt = ( CaselessLiteral( "SELECT" ) + 
                    columns + 
                    CaselessLiteral( "FROM" ) +
                    table +
                    CaselessLiteral( "WHERE" ) +
                    predicate )

    update_stmt = ( numeric_modify_stmt )
    varassign_stmt = ( CaselessLiteral( "var" ) +
                       calder_name.setResultsName("name") + 
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

    statement = ( insert_stmt |
                  delete_stmt |
                  update_stmt |
                  conditional_update_stmt |
                  select_stmt |
                  varassign_stmt ) + endstmt

    storedproc = ( begin_stored_procedure +
                   calder_name.setResultsName("name") +
                   ZeroOrMore ( Group( sp_parameter ) ).setResultsName("parameters") +
                   OneOrMore ( Group( statement ) ).setResultsName("statements") +
                   end_stored_procedure )
    storedprocedures = OneOrMore( Group ( storedproc ) )

    calderprogram = tabledeclarations.setResultsName("tables") + storedprocedures.setResultsName("storedprocedures")
    calderprogram.ignore(comment)

    return calderprogram.parseFile(input_file)
