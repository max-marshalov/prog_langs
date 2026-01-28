
import sys
import os
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ast_parser import SimpleParser
from control_flow import ControlFlowBuilder
from visualizer import GraphVisualizer, HAS_GRAPHVIZ

def process_file(file_path: str, output_dir: str = ".") -> bool:
    if not os.path.exists(file_path):
        print(f"Ошибка: файл '{file_path}' не найден")
        return False
    
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        parser = SimpleParser()
        ast = parser.parse_file(file_path, source_code)
        
        cfg_builder = ControlFlowBuilder()
        functions = cfg_builder.build_from_ast(file_path, ast)
        if HAS_GRAPHVIZ:
            source_name = Path(file_path).stem
            output_file = Path(output_dir) / f"{source_name}.png"
            
            try:
                dot = GraphVisualizer.visualize_single_file(functions, os.path.basename(file_path))
                dot.format = 'png'
                dot.render(filename=output_file.with_suffix('').as_posix(), 
                          cleanup=True, 
                          view=False)
                for func in functions:
                    print(f"    Функция {func.name}: {len(func.cfg.blocks)} блоков")
                    for block in func.cfg.blocks:
                        conn_info = []
                        if block.next_block:
                            conn_info.append(f"next→{block.next_block.id}")
                        if block.true_branch:
                            conn_info.append(f"true→{block.true_branch.id}")
                        if block.false_branch:
                            conn_info.append(f"false→{block.false_branch.id}")
                        
                        if conn_info:
                            print(f"      Блок {block.id}: {', '.join(conn_info)}")
                        
                        for i, op in enumerate(block.operations):
                            op_info = f"#{i}: {op.type.name}"
                            
                            if op.type.name == 'ASSIGN' and op.left and op.right:
                                left_val = GraphVisualizer._operand_to_simple(op.left)
                                right_val = GraphVisualizer._operand_to_detail(op.right)
                                op_info += f" {left_val}={right_val}"
                            elif op.type.name == 'RETURN' and op.left:
                                ret_val = GraphVisualizer._operand_to_simple(op.left)
                                op_info += f" {ret_val}"
                            elif op.type.name == 'CALL' and op.value:
                                args = [GraphVisualizer._operand_to_simple(arg) for arg in op.args]
                                if args:
                                    op_info += f" {op.value}({','.join(args)})"
                                else:
                                    op_info += f" {op.value}()"
                            elif op.type.name in ['ADD', 'SUB', 'MUL', 'DIV', 'MOD', 
                                                 'EQ', 'NE', 'LT', 'LE', 'GT', 'GE',
                                                 'AND', 'OR'] and op.left and op.right:
                                left_val = GraphVisualizer._operand_to_simple(op.left)
                                right_val = GraphVisualizer._operand_to_simple(op.right)
                                op_symbol = GraphVisualizer._get_operator_symbol(op.type)
                                op_info += f" {left_val}{op_symbol}{right_val}"
                            
                            if op.line > 0:
                                op_info += f" [L{op.line}]"
                            print(f"        {op_info}")
            
            except Exception as graph_error:
                print(f"  Ошибка создания графа: {graph_error}")
                return False
        
       
        if cfg_builder.call_graph:
            print("  Граф вызовов:")
            for caller, callees in cfg_builder.call_graph.items():
                if callees:
                    print(f"    {caller} -> {', '.join(callees)}")
        

        if parser.errors:
            print("  Ошибки синтаксического анализа:")
            for error in parser.errors:
                print(f"    Строка {error.line}: {error.message}")
        
        if cfg_builder.errors:
            print("  Ошибки построения графа:")
            for error in cfg_builder.errors:
                print(f"    {error.message}")
        
        return True
        
    except Exception as e:
        print(f"  Ошибка обработки файла: {e}")
        import traceback
        print(f"  Детали: {traceback.format_exc()}")
        return False



def main():
    if len(sys.argv) < 2:
        print("Использование: python main.py <файл1> [файл2 ...]")
        sys.exit(1)
    input_files = []
    output_dir = "."
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--output' and i + 1 < len(sys.argv):
            output_dir = sys.argv[i + 1]
            i += 2
        elif arg.startswith('-'):
            print(f"Неизвестный параметр: {arg}")
            i += 1
        else:
            input_files.append(arg)
            i += 1
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\nВыходная директория: {output_path.absolute()}")
    print("=" * 60)
    
    success_count = 0
    for file_path in input_files:
        if process_file(file_path, output_dir):
            success_count += 1
        print()
    

    
    if success_count > 0:
        print(f"\nPNG файлы сохранены в: {output_path.absolute()}")

if __name__ == '__main__':
    main()
