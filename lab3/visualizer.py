
import re
from typing import List, Dict, Set
from control_flow import ControlFlowGraph, BasicBlock, FunctionInfo, Operation, OperationType

try:
    import graphviz
    HAS_GRAPHVIZ = True
except ImportError:
    HAS_GRAPHVIZ = False

class GraphVisualizer:
    
    @staticmethod
    def _sanitize_id(name: str) -> str:
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        if sanitized and sanitized[0].isdigit():
            sanitized = 'n' + sanitized
        return sanitized
    
    @staticmethod
    def visualize_single_file(functions: List[FunctionInfo], source_filename: str) -> graphviz.Digraph:
        if not HAS_GRAPHVIZ:
            raise ImportError("Graphviz не установлен")
        
        filename_base = source_filename.replace('.', '_').replace(' ', '_')
        dot = graphviz.Digraph(name=f'CFG_{filename_base}', format='png')
        
        dot.attr(
            rankdir='TB',
            labelloc='t',
            fontname='Arial'
        )
        
        func_names = ', '.join([f.name for f in functions])
        dot.attr(label=f'Файл: {source_filename}\\nФункции: {func_names}')
        
        for func_idx, func_info in enumerate(functions):
            func_name = func_info.name

            func_header_id = GraphVisualizer._sanitize_id(f'header_{func_name}')
            
            # Формируем строку параметров с типами
            params_str = ""
            if hasattr(func_info, 'signature') and 'parameters' in func_info.signature:
                params = func_info.signature['parameters']
                if params:
                    param_list = []
                    for param in params:
                        if isinstance(param, tuple) and len(param) == 2:
                            param_list.append(f"{param[0]} -> {param[1]}")
                        elif isinstance(param, str):
                            param_list.append(param)
                        else:
                            param_list.append(str(param))
                    params_str = ', '.join(param_list)
            
            func_label = f'ФУНКЦИЯ {func_name}({params_str}) -> {func_info.return_type}'
            
            dot.node(
                func_header_id,
                label=func_label,
                shape='box',
                style='bold',
                fontname='Arial',
                fontsize='16'
            )
            
            # ВАЖНО: Теперь будем использовать тот же формат, что и в консоли
            for block in func_info.cfg.blocks:
                block_id = GraphVisualizer._sanitize_id(f'{func_name}_block_{block.id}')
                
                # Формируем label как в консольном выводе
                label_parts = []
                
                # Тип блока
                if block == func_info.cfg.entry_block:
                    block_type = "ВХОД"
                elif block == func_info.cfg.exit_block:
                    block_type = "ВЫХОД"
                else:
                    block_type = "БЛОК"
                
                label_parts.append(f'{block_type} {block.id}')
                
                # Соединения (только для отладки, можно закомментировать если мешает)
                connections = []
                if block.next_block:
                    connections.append(f'next→{block.next_block.id}')
                if block.true_branch:
                    connections.append(f'true→{block.true_branch.id}')
                if block.false_branch:
                    connections.append(f'false→{block.false_branch.id}')
                
                if connections:
                    label_parts.append(f'→ {", ".join(connections)}')
                
                # Операции (самое важное)
                if block.operations:
                    label_parts.append('---')
                    for i, op in enumerate(block.operations):
                        # Используем тот же метод, что и для консоли
                        op_str = GraphVisualizer._operation_to_compact_str(op, i)
                        label_parts.append(op_str)
                
                if not block.operations and block != func_info.cfg.entry_block and block != func_info.cfg.exit_block:
                    label_parts.append('(нет операций)')
                
                label = '\\n'.join(label_parts)
                
                # Определяем форму и стиль блока
                if block == func_info.cfg.entry_block:
                    shape = 'ellipse'
                    style = 'filled'
                    fillcolor = 'lightblue'
                elif block == func_info.cfg.exit_block:
                    shape = 'ellipse'
                    style = 'filled'
                    fillcolor = 'lightcoral'
                else:
                    shape = 'box'
                    style = 'filled'
                    fillcolor = 'lightyellow'
                
                # Создаем узел блока
                dot.node(
                    block_id,
                    label=label,
                    shape=shape,
                    style=style,
                    fillcolor=fillcolor,
                    fontname='Courier New',
                    fontsize='14'
                )
            
            # Создаем ребра между блоками
            for block in func_info.cfg.blocks:
                block_id = GraphVisualizer._sanitize_id(f'{func_name}_block_{block.id}')
                
                # Обычный переход (next)
                if block.next_block:
                    next_id = GraphVisualizer._sanitize_id(f'{func_name}_block_{block.next_block.id}')
                    dot.edge(block_id, next_id, color='black')
                
                # Ветвление по true
                if block.true_branch:
                    true_id = GraphVisualizer._sanitize_id(f'{func_name}_block_{block.true_branch.id}')
                    dot.edge(block_id, true_id, label='T', color='green')
                
                # Ветвление по false
                if block.false_branch:
                    false_id = GraphVisualizer._sanitize_id(f'{func_name}_block_{block.false_branch.id}')
                    dot.edge(block_id, false_id, label='F', color='red')
        
        return dot
    

    @staticmethod
    def _operation_to_compact_str(op: Operation, index: int) -> str:
        result = f"#{index}: {op.type.name}"
        
        # Добавляем информацию о типах в квадратных скобках
        type_parts = []
        if op.var_type and op.var_type != "unknown":
            type_parts.append(f"var:{op.var_type}")
        if op.result_type and op.result_type != "unknown":
            type_parts.append(f"res:{op.result_type}")
        
        if type_parts:
            result += f" [{', '.join(type_parts)}]"
        
        if op.type == OperationType.DECLARE:
            if op.value:
                result += f" {op.value}"
                if op.var_type:
                    result += f":{op.var_type}"
                if op.left:
                    init_val = GraphVisualizer._operand_to_str_with_type(op.left)
                    result += f" = {init_val}"
        
        elif op.type == OperationType.ASSIGN:
            if op.left and op.right:
                left_str = GraphVisualizer._operand_to_structural(op.left)
                right_str = GraphVisualizer._operand_to_str_with_type(op.right)
                left_type = op.left.var_type or op.left.result_type or "?"
                if f":{left_type}" not in left_str:
                    left_str = f"{left_str}:{left_type}"
                result += f" {left_str} = {right_str}"
        
        elif op.type == OperationType.CALL:
            if op.value:
                args = []
                for arg in op.args:
                    args.append(GraphVisualizer._operand_to_str_with_type(arg))
                
                if args:
                    result += f" {op.value}({', '.join(args)})"
                else:
                    result += f" {op.value}()"
        
        elif op.type == OperationType.RETURN:
            if op.left:
                val = GraphVisualizer._operand_to_str_with_type(op.left)
                result += f" {val}"
        
        elif op.type == OperationType.INCREMENT:
            if op.value:
                var_type = op.var_type or op.result_type or "?"
                if var_type and var_type != "unknown":
                    type_info = f":{var_type}"
                else:
                    type_info = ""
                
                if hasattr(op, 'attributes') and op.attributes.get('prefix'):
                    result += f" ++{op.value}{type_info}"
                else:
                    result += f" {op.value}++{type_info}"
            else:
                result += f" <increment>"
        
        elif op.type == OperationType.DECREMENT:
            if op.value:
                var_type = op.var_type or op.result_type or "?"
                if var_type and var_type != "unknown":
                    type_info = f":{var_type}"
                else:
                    type_info = ""
                
                if hasattr(op, 'attributes') and op.attributes.get('prefix'):
                    result += f" --{op.value}{type_info}"
                else:
                    result += f" {op.value}--{type_info}"
            else:
                result += f" <decrement>"
        
        elif op.type in [OperationType.ADD, OperationType.SUB, OperationType.MUL,
                        OperationType.DIV, OperationType.MOD]:
            if op.left and op.right:
                left_str = GraphVisualizer._operand_to_str_with_type(op.left)
                right_str = GraphVisualizer._operand_to_str_with_type(op.right)
                op_symbol = GraphVisualizer._get_operator_symbol(op.type)
                result += f" {left_str}{op_symbol}{right_str}"
        
        elif op.type in [OperationType.EQ, OperationType.NE, OperationType.LT,
                        OperationType.LE, OperationType.GT, OperationType.GE]:
            if op.left and op.right:
                left_str = GraphVisualizer._operand_to_str_with_type(op.left)
                right_str = GraphVisualizer._operand_to_str_with_type(op.right)
                op_symbol = GraphVisualizer._get_operator_symbol(op.type)
                result += f" {left_str}{op_symbol}{right_str}"
        
        elif op.type in [OperationType.AND, OperationType.OR]:
            if op.left and op.right:
                left_str = GraphVisualizer._operand_to_str_with_type(op.left)
                right_str = GraphVisualizer._operand_to_str_with_type(op.right)
                op_symbol = GraphVisualizer._get_operator_symbol(op.type)
                result += f" {left_str}{op_symbol}{right_str}"
        
        elif op.type == OperationType.NOT:
            if op.left:
                val = GraphVisualizer._operand_to_str_with_type(op.left)
                result += f" !{val}"
        
        elif op.type == OperationType.CONDITION:
            if op.left:
                cond = GraphVisualizer._operand_to_str_with_type(op.left)
                result += f" {cond}"
        
        elif op.type in [OperationType.BREAK, OperationType.CONTINUE, OperationType.NOOP,
                        OperationType.NEGATE, OperationType.CAST, 
                        OperationType.ARRAY_ACCESS, OperationType.MEMBER_ACCESS]:
            if op.value:
                result += f" {op.value}"
        
        if hasattr(op, 'line') and op.line and op.line > 0:
            result += f" [L{op.line}]"
        
        return result
    
    @staticmethod
    def _operand_to_detail(operand) -> str:
        if operand is None:
            return "?"
        
        if isinstance(operand, Operation):
            if operand.type == OperationType.ADD:
                left = GraphVisualizer._operand_to_simple(operand.left)
                right = GraphVisualizer._operand_to_detail(operand.right)
                return f"{left}+{right}"
            
            elif operand.type == OperationType.SUB:
                left = GraphVisualizer._operand_to_simple(operand.left)
                right = GraphVisualizer._operand_to_simple(operand.right)
                return f"{left}-{right}"
            
            elif operand.type == OperationType.CALL:
                args = []
                for arg in operand.args:
                    # Для аргументов используем детальное представление
                    args.append(GraphVisualizer._operand_to_detail(arg))
                if args:
                    return f"{operand.value}({','.join(args)})"
                else:
                    return f"{operand.value}()"
            
            elif operand.type == OperationType.EQ:
                left = GraphVisualizer._operand_to_simple(operand.left)
                right = GraphVisualizer._operand_to_simple(operand.right)
                return f"{left}=={right}"
            
            elif hasattr(operand, 'value') and operand.value:
                return str(operand.value)
            
            else:
                return f"<{operand.type.name}>"
        
        elif hasattr(operand, 'value'):
            return str(operand.value)
        
        return str(operand)
    
    @staticmethod
    def _get_operator_symbol(op_type: OperationType) -> str:
        symbol_map = {
            OperationType.ADD: '+',
            OperationType.SUB: '-',
            OperationType.MUL: '*',
            OperationType.DIV: '/',
            OperationType.MOD: '%',
            OperationType.EQ: '==',
            OperationType.NE: '!=',
            OperationType.LT: '<',
            OperationType.LE: '<=',
            OperationType.GT: '>',
            OperationType.GE: '>=',
            OperationType.AND: '&&',
            OperationType.OR: '||',
        }
        return symbol_map.get(op_type, '?')
    

    @staticmethod
    def _operand_to_simple(operand) -> str:
        if operand is None:
            return "?"
        
        if isinstance(operand, Operation):
            if operand.type == OperationType.CALL:
                args = []
                for arg in operand.args:
                    args.append(GraphVisualizer._operand_to_simple(arg))
                if args:
                    return f"{operand.value}({','.join(args)})"
                else:
                    return f"{operand.value}()"
            
            elif operand.type == OperationType.ADD:
                left = GraphVisualizer._operand_to_simple(operand.left)
                right = GraphVisualizer._operand_to_simple(operand.right)
                return f"({left}+{right})"
            
            elif operand.type == OperationType.SUB:
                left = GraphVisualizer._operand_to_simple(operand.left)
                right = GraphVisualizer._operand_to_simple(operand.right)
                return f"({left}-{right})"
            
            elif operand.type == OperationType.EQ:
                left = GraphVisualizer._operand_to_simple(operand.left)
                right = GraphVisualizer._operand_to_simple(operand.right)
                return f"({left}=={right})"
            
            elif hasattr(operand, 'value') and operand.value:
                return str(operand.value)
            
            return f"<{operand.type.name}>"
        
        elif hasattr(operand, 'value'):
            return str(operand.value)
    
        return str(operand)
    
    @staticmethod
    def _operand_to_structural(operand) -> str:
        """Структурное представление операнда с указанием типов операций"""
        if operand is None:
            return "?"
        
        if isinstance(operand, Operation):
            if hasattr(operand, 'var_type') and operand.var_type:
                if operand.type == OperationType.NOOP:
                    return f"{operand.value}:{operand.var_type}"
                
            elif operand.type == OperationType.INCREMENT:
                if operand.value:
                    if hasattr(operand, 'attributes') and operand.attributes.get('prefix'):
                        return f"++{operand.value}"
                    else:
                        return f"{operand.value}++"
            
            elif operand.type == OperationType.DECREMENT:
                if operand.value:
                    if hasattr(operand, 'attributes') and operand.attributes.get('prefix'):
                        return f"--{operand.value}"
                    else:
                        return f"{operand.value}--"
            
            elif operand.type in [OperationType.ADD, OperationType.SUB, 
                                OperationType.MUL, OperationType.DIV, OperationType.MOD]:
                left = GraphVisualizer._operand_to_structural(operand.left)
                right = GraphVisualizer._operand_to_structural(operand.right)
                op_name = operand.type.name
                return f"{op_name}({left}, {right})"
            
            elif operand.type in [OperationType.EQ, OperationType.NE, OperationType.LT,
                                OperationType.LE, OperationType.GT, OperationType.GE]:
                left = GraphVisualizer._operand_to_structural(operand.left)
                right = GraphVisualizer._operand_to_structural(operand.right)
                op_name = operand.type.name
                return f"{op_name}({left}, {right})"
            
            elif operand.type in [OperationType.AND, OperationType.OR]:
                left = GraphVisualizer._operand_to_structural(operand.left)
                right = GraphVisualizer._operand_to_structural(operand.right)
                op_name = operand.type.name
                return f"{op_name}({left}, {right})"
            
            elif operand.type == OperationType.NOT:
                val = GraphVisualizer._operand_to_structural(operand.left)
                return f"NOT({val})"
            
            elif operand.type == OperationType.CALL:
                args = []
                for arg in operand.args:
                    args.append(GraphVisualizer._operand_to_structural(arg))
                if args:
                    return f"CALL {operand.value}({', '.join(args)})"
                else:
                    return f"CALL {operand.value}()"
            
            elif operand.type == OperationType.NOOP:
                if hasattr(operand, 'value') and operand.value:
                    return str(operand.value)
            
            # Для других типов операций
            return f"{operand.type.name}"
        
        elif hasattr(operand, 'value'):
            return str(operand.value)
        
        return str(operand)
    
    @staticmethod
    def operand_to_detail(operand) -> str:
        return GraphVisualizer._operand_to_detail(operand)
    
    @staticmethod
    def operand_to_simple(operand) -> str:
        return GraphVisualizer._operand_to_simple(operand)
    
    @staticmethod
    def get_operator_symbol(op_type: OperationType) -> str:
        return GraphVisualizer._get_operator_symbol(op_type)
    

    @staticmethod
    def _is_increment_operation(op: Operation) -> bool:
        """Проверяет, является ли операция инкрементом (i++)"""
        if op.type != OperationType.ADD:
            return False
        
        if not op.left or not op.right:
            return False
        
        # Проверяем i + 1
        if (op.left.type == OperationType.NOOP and 
            op.right.type == OperationType.NOOP and 
            op.right.value == '1'):
            return True
        
        # Проверяем 1 + i
        if (op.right.type == OperationType.NOOP and 
            op.left.type == OperationType.NOOP and 
            op.left.value == '1'):
            return True
        
        return False

    @staticmethod
    def _is_decrement_operation(op: Operation) -> bool:
        """Проверяет, является ли операция декрементом (i--)"""
        if op.type != OperationType.SUB:
            return False
        
        if not op.left or not op.right:
            return False
        
        # Проверяем i - 1
        if (op.left.type == OperationType.NOOP and 
            op.right.type == OperationType.NOOP and 
            op.right.value == '1'):
            return True
        
        return False

    @staticmethod
    def _get_increment_decrement_variable(op: Operation):
        """Возвращает имя переменной для инкремента/декремента, или None если это не такая операция"""
        if GraphVisualizer._is_increment_operation(op) or GraphVisualizer._is_decrement_operation(op):
            # Для i + 1
            if op.left.type == OperationType.NOOP and op.left.value and op.left.value != '1':
                return op.left.value
            # Для 1 + i
            elif op.right.type == OperationType.NOOP and op.right.value and op.right.value != '1':
                return op.right.value
        return None
    
    @staticmethod
    def _operand_to_str_with_type(operand) -> str:
        """Возвращает строковое представление операнда с типом если нужно"""
        if operand is None:
            return "?"
        
        base_str = GraphVisualizer._operand_to_structural(operand)
        
        # Получаем тип операнда
        op_type = None
        if hasattr(operand, 'result_type') and operand.result_type and operand.result_type != "unknown":
            op_type = operand.result_type
        elif hasattr(operand, 'var_type') and operand.var_type and operand.var_type != "unknown":
            op_type = operand.var_type
        
        # Добавляем тип только если он еще не присутствует в строке
        if op_type and f":{op_type}" not in base_str:
            return f"{base_str}:{op_type}"
        
        return base_str