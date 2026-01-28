# Generated from Language.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .LanguageParser import LanguageParser
else:
    from LanguageParser import LanguageParser

# This class defines a complete generic visitor for a parse tree produced by LanguageParser.

class LanguageVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by LanguageParser#source.
    def visitSource(self, ctx:LanguageParser.SourceContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LanguageParser#CustomTypeRef.
    def visitCustomTypeRef(self, ctx:LanguageParser.CustomTypeRefContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LanguageParser#ArrayTypeRef.
    def visitArrayTypeRef(self, ctx:LanguageParser.ArrayTypeRefContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LanguageParser#BuiltinTypeRef.
    def visitBuiltinTypeRef(self, ctx:LanguageParser.BuiltinTypeRefContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LanguageParser#builtinType.
    def visitBuiltinType(self, ctx:LanguageParser.BuiltinTypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LanguageParser#funcSignature.
    def visitFuncSignature(self, ctx:LanguageParser.FuncSignatureContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LanguageParser#argDefList.
    def visitArgDefList(self, ctx:LanguageParser.ArgDefListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LanguageParser#argDef.
    def visitArgDef(self, ctx:LanguageParser.ArgDefContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LanguageParser#sourceItem.
    def visitSourceItem(self, ctx:LanguageParser.SourceItemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LanguageParser#funcDef.
    def visitFuncDef(self, ctx:LanguageParser.FuncDefContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LanguageParser#statement.
    def visitStatement(self, ctx:LanguageParser.StatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LanguageParser#varStatement.
    def visitVarStatement(self, ctx:LanguageParser.VarStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LanguageParser#identifierList.
    def visitIdentifierList(self, ctx:LanguageParser.IdentifierListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LanguageParser#ifStatement.
    def visitIfStatement(self, ctx:LanguageParser.IfStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LanguageParser#block.
    def visitBlock(self, ctx:LanguageParser.BlockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LanguageParser#whileStatement.
    def visitWhileStatement(self, ctx:LanguageParser.WhileStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LanguageParser#doStatement.
    def visitDoStatement(self, ctx:LanguageParser.DoStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LanguageParser#breakStatement.
    def visitBreakStatement(self, ctx:LanguageParser.BreakStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LanguageParser#returnStatement.
    def visitReturnStatement(self, ctx:LanguageParser.ReturnStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LanguageParser#expressionStatement.
    def visitExpressionStatement(self, ctx:LanguageParser.ExpressionStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LanguageParser#emptyStatement.
    def visitEmptyStatement(self, ctx:LanguageParser.EmptyStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LanguageParser#placeExpr.
    def visitPlaceExpr(self, ctx:LanguageParser.PlaceExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LanguageParser#unaryExpr.
    def visitUnaryExpr(self, ctx:LanguageParser.UnaryExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LanguageParser#bracesExpr.
    def visitBracesExpr(self, ctx:LanguageParser.BracesExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LanguageParser#literalExpr.
    def visitLiteralExpr(self, ctx:LanguageParser.LiteralExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LanguageParser#binaryExpr.
    def visitBinaryExpr(self, ctx:LanguageParser.BinaryExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LanguageParser#callExpr.
    def visitCallExpr(self, ctx:LanguageParser.CallExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LanguageParser#indexerExpr.
    def visitIndexerExpr(self, ctx:LanguageParser.IndexerExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LanguageParser#exprList.
    def visitExprList(self, ctx:LanguageParser.ExprListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LanguageParser#literal.
    def visitLiteral(self, ctx:LanguageParser.LiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LanguageParser#binOp.
    def visitBinOp(self, ctx:LanguageParser.BinOpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by LanguageParser#unOp.
    def visitUnOp(self, ctx:LanguageParser.UnOpContext):
        return self.visitChildren(ctx)



del LanguageParser