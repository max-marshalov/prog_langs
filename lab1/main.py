from antlr4 import *
from LanguageLexer import LanguageLexer
from LanguageParser import LanguageParser
from TreePrinter import *
import sys
import os
def main():
    if len(sys.argv) < 2:
        print("Usage: python parser_file.py <path_to_source_file> <path_to_outfile>")
        print("Example: python parser_file.py test_code.txt out.txt")
        sys.exit(1)
    
    file_path = sys.argv[1]

    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found")
        sys.exit(1)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            test_code = file.read()
    except Exception as e:
        print(f"Error reading file '{file_path}': {e}")
        sys.exit(1)
    
    print(f"=== Parsing file: {file_path} ===")
    print("=== Source code ===")
    print(test_code)
    print("=" * 50)

    input_stream = InputStream(test_code)
    lexer = LanguageLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = LanguageParser(stream)
    
    tree = parser.source()
    printer = TreePrinter()
    
    print("=== Parse Tree ===")
    printer.print_rule(tree, parser.ruleNames)

if __name__ == '__main__':
    main()