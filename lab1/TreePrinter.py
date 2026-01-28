from antlr4 import *
from LanguageLexer import LanguageLexer
from LanguageParser import LanguageParser

class TreePrinter:
    def __init__(self):
        self.indent = 0
        self.lines = []
    
    def print_tree(self, node, rule_names):
        if isinstance(node, TerminalNode):
            self.print_terminal(node)
        else:
            self.print_rule(node, rule_names)
        return self.lines
    
    def print_rule(self, node, rule_names):
        indent_str = "  " * self.indent
        rule_name = rule_names[node.getRuleIndex()] if node.getRuleIndex() >= 0 else "unknown"
        print(f"{indent_str}{rule_name}")
        
        self.indent += 1
        for child in node.getChildren():
            self.print_tree(child, rule_names)
        self.indent -= 1
    
    def print_terminal(self, node):
        indent_str = "  " * self.indent
        symbol = node.getSymbol()
        if symbol.type != -1:
            token_name = LanguageLexer.symbolicNames[symbol.type]
            token_text = node.getText().replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
            print(f"{indent_str}{token_name}: '{token_text}'")