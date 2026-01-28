grammar Language;


source: sourceItem* EOF;

typeRef
    : builtinType # BuiltinTypeRef
    | IDENTIFIER  # CustomTypeRef  
    | typeRef LBRACK (COMMA)* RBRACK # ArrayTypeRef
    ;

builtinType: BOOL | BYTE | INT | UINT | LONG | ULONG | CHAR | STRING_TYPE;

funcSignature: typeRef? IDENTIFIER LPAREN argDefList RPAREN;
argDefList: (argDef (COMMA argDef)*)?;
argDef: typeRef? IDENTIFIER;

sourceItem: funcDef;
funcDef: funcSignature (block | SEMI);

statement
    : varStatement
    | ifStatement
    | block
    | whileStatement
    | doStatement
    | breakStatement
    | returnStatement
    | expressionStatement
    | emptyStatement
    ;

varStatement: typeRef identifierList SEMI;
identifierList: IDENTIFIER (ASSIGN expr)? (COMMA IDENTIFIER (ASSIGN expr)?)*;

ifStatement: IF LPAREN expr RPAREN statement (ELSE statement)?;
block: LBRACE statement* RBRACE;
whileStatement: WHILE LPAREN expr RPAREN statement;
doStatement: DO block WHILE LPAREN expr RPAREN SEMI;
breakStatement: BREAK SEMI;
returnStatement: RETURN expr? SEMI;  // Добавлено правило для return
expressionStatement: expr SEMI;
emptyStatement: SEMI;

expr
    : expr binOp expr                  # binaryExpr
    | unOp expr                        # unaryExpr
    | LPAREN expr RPAREN               # bracesExpr
    | expr LPAREN exprList RPAREN      # callExpr
    | expr LBRACK exprList RBRACK      # indexerExpr
    | IDENTIFIER                       # placeExpr
    | literal                          # literalExpr
    ;

exprList: (expr (COMMA expr)*)?;

literal
    : BOOL_LITERAL
    | STRING
    | CHAR_LITERAL
    | HEX
    | BITS
    | DEC
    ;

binOp: MUL | MINUS | PLUS | DIV | ASSIGN | EQ | NEQ | LT | GT | LTE | GTE | AND | OR;
unOp: MINUS | NOT | TILDE;

// Lexer rules

// Keywords
BOOL: 'bool';
BYTE: 'byte';
INT: 'int';
UINT: 'uint';
LONG: 'long';
ULONG: 'ulong';
CHAR: 'char';
STRING_TYPE: 'string';
IF: 'if';
ELSE: 'else';
WHILE: 'while';
DO: 'do';
BREAK: 'break';
RETURN: 'return';  // Добавлен return

// Literals
BOOL_LITERAL: 'true' | 'false';
IDENTIFIER: [a-zA-Z_][a-zA-Z_0-9]*;
STRING: '"' (~["\\] | '\\' .)* '"';
CHAR_LITERAL: '\'' .? '\'';
HEX: '0' [xX] [0-9A-Fa-f]+;
BITS: '0' [bB] [01]+;
DEC: [0-9]+;

// Operators
PLUS: '+';
MINUS: '-';
MUL: '*';
DIV: '/';
ASSIGN: '=';
EQ: '==';
NEQ: '!=';
LT: '<';
GT: '>';
LTE: '<=';
GTE: '>=';
AND: '&&';
OR: '||';
NOT: '!';
TILDE: '~';

// Punctuation
LPAREN: '(';
RPAREN: ')';
LBRACE: '{';
RBRACE: '}';
LBRACK: '[';
RBRACK: ']';
SEMI: ';';
COMMA: ',';

// Whitespace and comments
WS: [ \t\r\n]+ -> skip;
COMMENT: '//' ~[\r\n]* -> skip;
MULTILINE_COMMENT: '/*' .*? '*/' -> skip;