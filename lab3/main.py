import sys
import os
import subprocess
from pathlib import Path

from generators.win_x86_gen import WinX86AsmGenerator
from generators.linux_x86_gen import LinuxX86AsmGenerator
from generators.riscv_gen import RiscV64AsmGenerator

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ast_parser import SimpleParser
from control_flow import ControlFlowBuilder
from visualizer import GraphVisualizer, HAS_GRAPHVIZ

def process_file(file_path: str, output_dir: str = ".", generate_asm = True, 
                 asm_generator: str = "linux", auto_build: bool = False) -> bool:
    
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

        if parser.errors or cfg_builder.errors:
            print(f"  Обнаружены ошибки {parser.errors}, {cfg_builder.errors}, граф не будет построен")
            return False
        
        # Генерация ассемблерного кода
        if generate_asm and functions:
            if asm_generator == "linux":
                generator = LinuxX86AsmGenerator()
            elif asm_generator == 'win':
                generator = WinX86AsmGenerator()
            elif asm_generator == 'riscv':
                generator = RiscV64AsmGenerator()
                
            asm_code = generator.generate_program(functions)
            
            source_name = Path(file_path).stem
            if asm_generator == 'riscv':
                asm_file = Path(output_dir) / f"{source_name}_{asm_generator}.s"
            else:
                asm_file = Path(output_dir) / f"{source_name}_{asm_generator}.asm"
            
            with open(asm_file, 'w', encoding='utf-8') as f:
                f.write(asm_code)
            
            print(f"  Ассемблерный код сохранен в: {asm_file}")
                
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
                            op_info = GraphVisualizer._operation_to_compact_str(op, i)
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
        print("Использование: python main.py <файл1> [файл2 ...] [опции]")
        print("Опции:")
        print("  --output <директория>    Выходная директория")
        print("  --generator <linux/win>  Генератор ассемблера (по умолчанию: linux)")
        print("  --build                  Автоматическая сборка (только для Linux)")
        print("  --no-asm                 Не генерировать ассемблерный код")
        sys.exit(1)
    
    input_files = []
    output_dir = "."
    generate_asm = True
    asm_generator = "linux"
    auto_build = False
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--output' and i + 1 < len(sys.argv):
            output_dir = sys.argv[i + 1]
            i += 2
        elif arg == '--generator' and i + 1 < len(sys.argv):
            asm_generator = sys.argv[i + 1]
            if asm_generator not in ['riscv', 'linux', 'win', 'windows']:
                print(f"Ошибка: неизвестный генератор '{asm_generator}'")
                sys.exit(1)
            if asm_generator in ['win', 'windows']:
                asm_generator = 'win'
            i += 2
        elif arg == '--build':
            auto_build = True
            i += 1
        elif arg == '--no-asm':
            generate_asm = False
            i += 1
        elif arg.startswith('-'):
            print(f"Неизвестный параметр: {arg}")
            i += 1
        else:
            input_files.append(arg)
            i += 1
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\nВыходная директория: {output_path.absolute()}")
    print(f"Генератор: {asm_generator}")
    if auto_build and asm_generator == 'linux':
        print("Автосборка: ВКЛЮЧЕНА")
    print("=" * 60)
    
    success_count = 0
    for file_path in input_files:
        if process_file(file_path, output_dir, generate_asm, asm_generator, auto_build):
            success_count += 1
        print()
    
    if success_count > 0:
        print(f"\nPNG файлы сохранены в: {output_path.absolute()}")

if __name__ == '__main__':
    main()