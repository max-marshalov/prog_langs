
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
            func_label = f'ФУНКЦИЯ {func_name}\\nreturn: {func_info.return_type}'
            
            if func_info.parameters:
                func_label += f'\\nparams: {func_info.parameters}'
            
            dot.node(
                func_header_id,
                label=func_label,
                shape='box',
                style='bold',
                fontname='Arial',
                fontsize='16'
            )
            
            for block in func_info.cfg.blocks:
                block_id = GraphVisualizer._sanitize_id(f'{func_name}_block_{block.id}')
                
                label_parts = []
                
                if block == func_info.cfg.entry_block:
                    block_type = "ВХОД"
                elif block == func_info.cfg.exit_block:
                    block_type = "ВЫХОД"
                else:
                    block_type = "БЛОК"
                
                label_parts.append(f'{block_type} #{block.id}')
                connections = []
                if block.next_block:
                    connections.append(f'next→{block.next_block.id}')
                if block.true_branch:
                    connections.append(f'true→{block.true_branch.id}')
                if block.false_branch:
                    connections.append(f'false→{block.false_branch.id}')
                
                if connections:
                    label_parts.append(f'→ {", ".join(connections)}')
                if block.operations:
                    label_parts.append('---')
                
                for i, op in enumerate(block.operations):
                    op_str = GraphVisualizer._operation_to_compact_str(op, i)
                    label_parts.append(op_str)
                
                if not block.operations:
                    label_parts.append('(нет операций)')
                
                label = '\\n'.join(label_parts)
                
                if block == func_info.cfg.entry_block or block == func_info.cfg.exit_block:
                    shape = 'ellipse'
                else:
                    shape = 'box'
                
                dot.node(
                    block_id,
                    label=label,
                    shape=shape,
                    fontname='Courier New',
                    fontsize='16'
                )
            
            for block in func_info.cfg.blocks:
                block_id = GraphVisualizer._sanitize_id(f'{func_name}_block_{block.id}')
                
                if block.next_block:
                    next_id = GraphVisualizer._sanitize_id(f'{func_name}_block_{block.next_block.id}')
                    dot.edge(block_id, next_id)
                
                if block.true_branch:
                    true_id = GraphVisualizer._sanitize_id(f'{func_name}_block_{block.true_branch.id}')
                    dot.edge(block_id, true_id, label='T')
                
                if block.false_branch:
                    false_id = GraphVisualizer._sanitize_id(f'{func_name}_block_{block.false_branch.id}')
                    dot.edge(block_id, false_id, label='F')
        
        return dot
    
    @staticmethod
    def _operation_to_compact_str(op: Operation, index: int) -> str:
        result = f"#{index}: {op.type.name}"
        
        if op.type == OperationType.DECLARE:
            if op.value:
                result += f" {op.value}"
                if op.var_type:
                    result += f" -> {op.var_type}"
                if op.left:
                    init_val = GraphVisualizer._operand_to_simple(op.left)
                    result += f" = {init_val}"

        elif op.type == OperationType.ASSIGN:
            if op.left and op.right:
                left = GraphVisualizer._operand_to_simple(op.left)
                right = GraphVisualizer._operand_to_detail(op.right) 
                result += f" {left}={right}"
            elif op.value:
                result += f" {op.value}"
        
        elif op.type == OperationType.CALL:
            if op.value:
                args = []
                for arg in op.args:
                    args.append(GraphVisualizer._operand_to_simple(arg))
                if args:
                    result += f" {op.value}({','.join(args)})"
                else:
                    result += f" {op.value}()"
        
        elif op.type == OperationType.RETURN:
            if op.left:
                val = GraphVisualizer._operand_to_simple(op.left)
                result += f" {val}"
        
        elif op.type in [OperationType.ADD, OperationType.SUB, OperationType.MUL, 
                        OperationType.DIV, OperationType.MOD]:
            if op.left and op.right:
                left = GraphVisualizer._operand_to_simple(op.left)
                right = GraphVisualizer._operand_to_simple(op.right)
                op_symbol = GraphVisualizer._get_operator_symbol(op.type)
                result += f" {left}{op_symbol}{right}"
        
        elif op.type in [OperationType.EQ, OperationType.NE, OperationType.LT,
                        OperationType.LE, OperationType.GT, OperationType.GE]:
            if op.left and op.right:
                left = GraphVisualizer._operand_to_simple(op.left)
                right = GraphVisualizer._operand_to_simple(op.right)
                op_symbol = GraphVisualizer._get_operator_symbol(op.type)
                result += f" {left}{op_symbol}{right}"
        
        elif op.type in [OperationType.AND, OperationType.OR]:
            if op.left and op.right:
                left = GraphVisualizer._operand_to_simple(op.left)
                right = GraphVisualizer._operand_to_simple(op.right)
                op_symbol = GraphVisualizer._get_operator_symbol(op.type)
                result += f" {left}{op_symbol}{right}"
        
        elif op.type == OperationType.NOT:
            if op.left:
                val = GraphVisualizer._operand_to_simple(op.left)
                result += f" !{val}"
        
        elif op.type == OperationType.CONDITION:
            if op.left:
                cond = GraphVisualizer._operand_to_detail(op.left)  # Детализированное отображение условия
                result += f" {cond}"
        
        if hasattr(op, 'line') and op.line and op.line > 0:
            result += f" [L{op.line}]"
        
        return result
    
    @staticmethod
    def _operand_to_detail(operand) -> str:
        if operand is None:
            return "?"
        
        if isinstance(operand, Operation):
            if operand.type in [OperationType.ADD, OperationType.SUB, OperationType.MUL, 
                               OperationType.DIV, OperationType.MOD]:
                left = GraphVisualizer._operand_to_simple(operand.left)
                right = GraphVisualizer._operand_to_simple(operand.right)
                op_symbol = GraphVisualizer._get_operator_symbol(operand.type)
                return f"{operand.type.name}({left}{op_symbol}{right})"
            
            elif operand.type in [OperationType.EQ, OperationType.NE, OperationType.LT,
                                 OperationType.LE, OperationType.GT, OperationType.GE]:
                left = GraphVisualizer._operand_to_simple(operand.left)
                right = GraphVisualizer._operand_to_simple(operand.right)
                op_symbol = GraphVisualizer._get_operator_symbol(operand.type)
                return f"{operand.type.name}({left}{op_symbol}{right})"
            
            elif operand.type in [OperationType.AND, OperationType.OR]:
                left = GraphVisualizer._operand_to_simple(operand.left)
                right = GraphVisualizer._operand_to_simple(operand.right)
                op_symbol = GraphVisualizer._get_operator_symbol(operand.type)
                return f"{operand.type.name}({left}{op_symbol}{right})"
            
            elif operand.type == OperationType.CALL:
                args = []
                for arg in operand.args:
                    args.append(GraphVisualizer._operand_to_simple(arg))
                if args:
                    return f"{operand.value}({','.join(args)})"
                else:
                    return f"{operand.value}()"
            
            elif operand.type == OperationType.NOT:
                val = GraphVisualizer._operand_to_simple(operand.left)
                return f"NOT({val})"
            
            elif hasattr(operand, 'value') and operand.value:
                return str(operand.value)
            
            else:
                return operand.type.name
        
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
            if hasattr(operand, 'value') and operand.value:
                val = str(operand.value)
                if len(val) > 10:
                    val = val[:7] + "..."
                return val
            
            if operand.type in [OperationType.ADD, OperationType.SUB, OperationType.MUL,
                               OperationType.DIV, OperationType.MOD]:
                left = GraphVisualizer._operand_to_simple(operand.left)
                right = GraphVisualizer._operand_to_simple(operand.right)
                op_symbol = GraphVisualizer._get_operator_symbol(operand.type)
                return f"({left}{op_symbol}{right})"
            
            if operand.type in [OperationType.EQ, OperationType.NE, OperationType.LT,
                               OperationType.LE, OperationType.GT, OperationType.GE]:
                left = GraphVisualizer._operand_to_simple(operand.left)
                right = GraphVisualizer._operand_to_simple(operand.right)
                op_symbol = GraphVisualizer._get_operator_symbol(operand.type)
                return f"({left}{op_symbol}{right})"
            
            if operand.type in [OperationType.AND, OperationType.OR]:
                left = GraphVisualizer._operand_to_simple(operand.left)
                right = GraphVisualizer._operand_to_simple(operand.right)
                op_symbol = GraphVisualizer._get_operator_symbol(operand.type)
                return f"({left}{op_symbol}{right})"
            
            if operand.type == OperationType.CALL:
                args = []
                for arg in operand.args:
                    args.append(GraphVisualizer._operand_to_simple(arg))
                if args:
                    return f"{operand.value}({','.join(args)})"
                else:
                    return f"{operand.value}()"
            if operand.type == OperationType.NOT:
                val = GraphVisualizer._operand_to_simple(operand.left)
                return f"!{val}"
            return f"<{operand.type.name}>"
        
        elif hasattr(operand, 'value'):
            val = str(operand.value)
            if len(val) > 10:
                val = val[:7] + "..."
            return val
        
        return str(operand)[:10]
    
    @staticmethod
    def operand_to_detail(operand) -> str:
        return GraphVisualizer._operand_to_detail(operand)
    
    @staticmethod
    def operand_to_simple(operand) -> str:
        return GraphVisualizer._operand_to_simple(operand)
    
    @staticmethod
    def get_operator_symbol(op_type: OperationType) -> str:
        return GraphVisualizer._get_operator_symbol(op_type)
    

