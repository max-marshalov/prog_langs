# Generated from Language.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .LanguageParser import LanguageParser
else:
    from LanguageParser import LanguageParser

# This class defines a complete listener for a parse tree produced by LanguageParser.
class LanguageListener(ParseTreeListener):

    # Enter a parse tree produced by LanguageParser#source.
    def enterSource(self, ctx:LanguageParser.SourceContext):
        pass

    # Exit a parse tree produced by LanguageParser#source.
    def exitSource(self, ctx:LanguageParser.SourceContext):
        pass


    # Enter a parse tree produced by LanguageParser#CustomTypeRef.
    def enterCustomTypeRef(self, ctx:LanguageParser.CustomTypeRefContext):
        pass

    # Exit a parse tree produced by LanguageParser#CustomTypeRef.
    def exitCustomTypeRef(self, ctx:LanguageParser.CustomTypeRefContext):
        pass


    # Enter a parse tree produced by LanguageParser#ArrayTypeRef.
    def enterArrayTypeRef(self, ctx:LanguageParser.ArrayTypeRefContext):
        pass

    # Exit a parse tree produced by LanguageParser#ArrayTypeRef.
    def exitArrayTypeRef(self, ctx:LanguageParser.ArrayTypeRefContext):
        pass


    # Enter a parse tree produced by LanguageParser#BuiltinTypeRef.
    def enterBuiltinTypeRef(self, ctx:LanguageParser.BuiltinTypeRefContext):
        pass

    # Exit a parse tree produced by LanguageParser#BuiltinTypeRef.
    def exitBuiltinTypeRef(self, ctx:LanguageParser.BuiltinTypeRefContext):
        pass


    # Enter a parse tree produced by LanguageParser#builtinType.
    def enterBuiltinType(self, ctx:LanguageParser.BuiltinTypeContext):
        pass

    # Exit a parse tree produced by LanguageParser#builtinType.
    def exitBuiltinType(self, ctx:LanguageParser.BuiltinTypeContext):
        pass


    # Enter a parse tree produced by LanguageParser#funcSignature.
    def enterFuncSignature(self, ctx:LanguageParser.FuncSignatureContext):
        pass

    # Exit a parse tree produced by LanguageParser#funcSignature.
    def exitFuncSignature(self, ctx:LanguageParser.FuncSignatureContext):
        pass


    # Enter a parse tree produced by LanguageParser#argDefList.
    def enterArgDefList(self, ctx:LanguageParser.ArgDefListContext):
        pass

    # Exit a parse tree produced by LanguageParser#argDefList.
    def exitArgDefList(self, ctx:LanguageParser.ArgDefListContext):
        pass


    # Enter a parse tree produced by LanguageParser#argDef.
    def enterArgDef(self, ctx:LanguageParser.ArgDefContext):
        pass

    # Exit a parse tree produced by LanguageParser#argDef.
    def exitArgDef(self, ctx:LanguageParser.ArgDefContext):
        pass


    # Enter a parse tree produced by LanguageParser#sourceItem.
    def enterSourceItem(self, ctx:LanguageParser.SourceItemContext):
        pass

    # Exit a parse tree produced by LanguageParser#sourceItem.
    def exitSourceItem(self, ctx:LanguageParser.SourceItemContext):
        pass


    # Enter a parse tree produced by LanguageParser#funcDef.
    def enterFuncDef(self, ctx:LanguageParser.FuncDefContext):
        pass

    # Exit a parse tree produced by LanguageParser#funcDef.
    def exitFuncDef(self, ctx:LanguageParser.FuncDefContext):
        pass


    # Enter a parse tree produced by LanguageParser#statement.
    def enterStatement(self, ctx:LanguageParser.StatementContext):
        pass

    # Exit a parse tree produced by LanguageParser#statement.
    def exitStatement(self, ctx:LanguageParser.StatementContext):
        pass


    # Enter a parse tree produced by LanguageParser#varStatement.
    def enterVarStatement(self, ctx:LanguageParser.VarStatementContext):
        pass

    # Exit a parse tree produced by LanguageParser#varStatement.
    def exitVarStatement(self, ctx:LanguageParser.VarStatementContext):
        pass


    # Enter a parse tree produced by LanguageParser#identifierList.
    def enterIdentifierList(self, ctx:LanguageParser.IdentifierListContext):
        pass

    # Exit a parse tree produced by LanguageParser#identifierList.
    def exitIdentifierList(self, ctx:LanguageParser.IdentifierListContext):
        pass


    # Enter a parse tree produced by LanguageParser#ifStatement.
    def enterIfStatement(self, ctx:LanguageParser.IfStatementContext):
        pass

    # Exit a parse tree produced by LanguageParser#ifStatement.
    def exitIfStatement(self, ctx:LanguageParser.IfStatementContext):
        pass


    # Enter a parse tree produced by LanguageParser#block.
    def enterBlock(self, ctx:LanguageParser.BlockContext):
        pass

    # Exit a parse tree produced by LanguageParser#block.
    def exitBlock(self, ctx:LanguageParser.BlockContext):
        pass


    # Enter a parse tree produced by LanguageParser#whileStatement.
    def enterWhileStatement(self, ctx:LanguageParser.WhileStatementContext):
        pass

    # Exit a parse tree produced by LanguageParser#whileStatement.
    def exitWhileStatement(self, ctx:LanguageParser.WhileStatementContext):
        pass


    # Enter a parse tree produced by LanguageParser#doStatement.
    def enterDoStatement(self, ctx:LanguageParser.DoStatementContext):
        pass

    # Exit a parse tree produced by LanguageParser#doStatement.
    def exitDoStatement(self, ctx:LanguageParser.DoStatementContext):
        pass


    # Enter a parse tree produced by LanguageParser#breakStatement.
    def enterBreakStatement(self, ctx:LanguageParser.BreakStatementContext):
        pass

    # Exit a parse tree produced by LanguageParser#breakStatement.
    def exitBreakStatement(self, ctx:LanguageParser.BreakStatementContext):
        pass


    # Enter a parse tree produced by LanguageParser#returnStatement.
    def enterReturnStatement(self, ctx:LanguageParser.ReturnStatementContext):
        pass

    # Exit a parse tree produced by LanguageParser#returnStatement.
    def exitReturnStatement(self, ctx:LanguageParser.ReturnStatementContext):
        pass


    # Enter a parse tree produced by LanguageParser#expressionStatement.
    def enterExpressionStatement(self, ctx:LanguageParser.ExpressionStatementContext):
        pass

    # Exit a parse tree produced by LanguageParser#expressionStatement.
    def exitExpressionStatement(self, ctx:LanguageParser.ExpressionStatementContext):
        pass


    # Enter a parse tree produced by LanguageParser#emptyStatement.
    def enterEmptyStatement(self, ctx:LanguageParser.EmptyStatementContext):
        pass

    # Exit a parse tree produced by LanguageParser#emptyStatement.
    def exitEmptyStatement(self, ctx:LanguageParser.EmptyStatementContext):
        pass


    # Enter a parse tree produced by LanguageParser#placeExpr.
    def enterPlaceExpr(self, ctx:LanguageParser.PlaceExprContext):
        pass

    # Exit a parse tree produced by LanguageParser#placeExpr.
    def exitPlaceExpr(self, ctx:LanguageParser.PlaceExprContext):
        pass


    # Enter a parse tree produced by LanguageParser#unaryExpr.
    def enterUnaryExpr(self, ctx:LanguageParser.UnaryExprContext):
        pass

    # Exit a parse tree produced by LanguageParser#unaryExpr.
    def exitUnaryExpr(self, ctx:LanguageParser.UnaryExprContext):
        pass


    # Enter a parse tree produced by LanguageParser#bracesExpr.
    def enterBracesExpr(self, ctx:LanguageParser.BracesExprContext):
        pass

    # Exit a parse tree produced by LanguageParser#bracesExpr.
    def exitBracesExpr(self, ctx:LanguageParser.BracesExprContext):
        pass


    # Enter a parse tree produced by LanguageParser#literalExpr.
    def enterLiteralExpr(self, ctx:LanguageParser.LiteralExprContext):
        pass

    # Exit a parse tree produced by LanguageParser#literalExpr.
    def exitLiteralExpr(self, ctx:LanguageParser.LiteralExprContext):
        pass


    # Enter a parse tree produced by LanguageParser#binaryExpr.
    def enterBinaryExpr(self, ctx:LanguageParser.BinaryExprContext):
        pass

    # Exit a parse tree produced by LanguageParser#binaryExpr.
    def exitBinaryExpr(self, ctx:LanguageParser.BinaryExprContext):
        pass


    # Enter a parse tree produced by LanguageParser#callExpr.
    def enterCallExpr(self, ctx:LanguageParser.CallExprContext):
        pass

    # Exit a parse tree produced by LanguageParser#callExpr.
    def exitCallExpr(self, ctx:LanguageParser.CallExprContext):
        pass


    # Enter a parse tree produced by LanguageParser#indexerExpr.
    def enterIndexerExpr(self, ctx:LanguageParser.IndexerExprContext):
        pass

    # Exit a parse tree produced by LanguageParser#indexerExpr.
    def exitIndexerExpr(self, ctx:LanguageParser.IndexerExprContext):
        pass


    # Enter a parse tree produced by LanguageParser#exprList.
    def enterExprList(self, ctx:LanguageParser.ExprListContext):
        pass

    # Exit a parse tree produced by LanguageParser#exprList.
    def exitExprList(self, ctx:LanguageParser.ExprListContext):
        pass


    # Enter a parse tree produced by LanguageParser#literal.
    def enterLiteral(self, ctx:LanguageParser.LiteralContext):
        pass

    # Exit a parse tree produced by LanguageParser#literal.
    def exitLiteral(self, ctx:LanguageParser.LiteralContext):
        pass


    # Enter a parse tree produced by LanguageParser#binOp.
    def enterBinOp(self, ctx:LanguageParser.BinOpContext):
        pass

    # Exit a parse tree produced by LanguageParser#binOp.
    def exitBinOp(self, ctx:LanguageParser.BinOpContext):
        pass


    # Enter a parse tree produced by LanguageParser#unOp.
    def enterUnOp(self, ctx:LanguageParser.UnOpContext):
        pass

    # Exit a parse tree produced by LanguageParser#unOp.
    def exitUnOp(self, ctx:LanguageParser.UnOpContext):
        pass



del LanguageParser