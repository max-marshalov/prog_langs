from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple, Set
from enum import Enum

class OperationType(Enum):
    """Типы операций"""
    DECLARE = "declare"
    ASSIGN = "assign"
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    MOD = "mod"
    EQ = "eq"
    NE = "ne"
    LT = "lt"
    LE = "le"
    GT = "gt"
    GE = "ge"
    AND = "and"
    OR = "or"
    NOT = "not"
    CALL = "call"
    RETURN = "return"
    CONDITION = "condition"
    BREAK = "break"
    CONTINUE = "continue"
    NOOP = "noop"
    INCREMENT = "increment"
    DECREMENT = "decrement"
    NEGATE = "negate"
    CAST = "cast"
    ARRAY_ACCESS = "array_access"
    MEMBER_ACCESS = "member_access"

@dataclass
class Operation:
    type: OperationType
    value: Optional[str] = None
    left: Optional['Operation'] = None
    right: Optional['Operation'] = None
    args: List['Operation'] = field(default_factory=list)
    line: int = 0
    column: int = 0
    var_type: Optional[str] = None

@dataclass
class BasicBlock:
    id: int
    operations: List[Operation] = field(default_factory=list)
    true_branch: Optional['BasicBlock'] = None
    false_branch: Optional['BasicBlock'] = None
    next_block: Optional['BasicBlock'] = None
    is_loop_start: bool = False
    is_loop_end: bool = False

@dataclass
class ControlFlowGraph:
    entry_block: BasicBlock
    exit_block: BasicBlock
    blocks: List[BasicBlock] = field(default_factory=list)
    
    def add_block(self, block: BasicBlock):
        self.blocks.append(block)

@dataclass
class FunctionInfo:
    name: str
    signature: Dict[str, Any]
    cfg: ControlFlowGraph
    source_file: str
    operations_tree: Optional[Any] = None
    return_type: str = "void"
    parameters: List[Tuple[str, str]] = field(default_factory=list)  # (name, type)

@dataclass
class ParsingError:
    file_name: str
    line: int
    column: int
    message: str
    severity: str = "error"

@dataclass
class ASTNode:
    type: str
    value: Optional[str] = None
    children: List['ASTNode'] = field(default_factory=list)
    line: int = 0
    column: int = 0
    attributes: Dict[str, Any] = field(default_factory=dict)

class ControlFlowBuilder:
    """Построитель графа потока управления"""
    
    def __init__(self):
        self.functions: List[FunctionInfo] = []
        self.errors: List[ParsingError] = []
        self.current_block_id = 0
        self.call_graph: Dict[str, Set[str]] = {}
    
    def build_from_ast(self, file_name: str, ast: ASTNode) -> List[FunctionInfo]:
        try:
            self._analyze_file(file_name, ast)
            return self.functions
        except Exception as e:
            self.errors.append(ParsingError(
                file_name=file_name,
                line=0,
                column=0,
                message=f"Ошибка при анализе файла: {str(e)}"
            ))
            return []
    
    def _analyze_file(self, file_name: str, ast: ASTNode):
        for node in ast.children:
            if node.type == 'function_declaration':
                self._process_function(file_name, node)
    
    def _process_function(self, file_name: str, func_node: ASTNode):
        func_name = "unknown"
        return_type = "void"
        parameters = []  # Список параметров
        
        for child in func_node.children:
            if child.type == 'function_name':
                func_name = child.value
            elif child.type == 'return_type':
                return_type = child.value
            elif child.type == 'parameter':
                param_name = child.value if child.value else "?"
                param_type = child.attributes.get('type', 'unknown') if hasattr(child, 'attributes') else 'unknown'
                parameters.append((param_name, param_type))
        
        entry_block = self._create_block()
        exit_block = self._create_block()
        body_node = None
        for child in func_node.children:
            if child.type == 'function_body':
                body_node = child
                break
        
        # Добавляем объявления параметров в entry block
        for param_name, param_type in parameters:
            param_decl_op = Operation(
                type=OperationType.DECLARE,
                value=param_name,
                var_type=param_type,
                line=func_node.line,
                column=func_node.column
            )
            entry_block.operations.append(param_decl_op)
        
        if not body_node:
            cfg = ControlFlowGraph(entry_block, exit_block)
            entry_block.next_block = exit_block
            cfg.add_block(entry_block)
            cfg.add_block(exit_block)
            
            func_info = FunctionInfo(
                name=func_name,
                signature={'return_type': return_type, 'parameters': parameters},
                cfg=cfg,
                source_file=file_name,
                return_type=return_type,
                parameters=[p[0] for p in parameters]  # Только имена параметров
            )
            self.functions.append(func_info)
            return
        
        current_block = entry_block
        final_block = self._process_statements(body_node.children, current_block, func_name, file_name, exit_block)

        if final_block:
            final_block.next_block = exit_block

        all_blocks = self._collect_all_blocks(entry_block)
        all_blocks.append(exit_block)
        
        cfg = ControlFlowGraph(entry_block, exit_block, all_blocks)
        
        func_info = FunctionInfo(
            name=func_name,
            signature={'return_type': return_type, 'parameters': parameters},
            cfg=cfg,
            source_file=file_name,
            return_type=return_type,
            parameters=[p[0] for p in parameters]
        )
        
        self.functions.append(func_info)
    
    def _build_var_declaration_operation(self, node: ASTNode, func_name: str, file_name: str) -> Optional[Operation]:
        if len(node.children) < 2:
            return None
        
        var_name = node.children[0].value if node.children[0].value else "?"
        var_type = node.children[1].value if node.children[1].value else "?"
        
        return Operation(
            type=OperationType.DECLARE,
            value=var_name,
            var_type=var_type,
            line=node.line,
            column=node.column
        )
    
    
    def _build_assignment_operation(self, node: ASTNode, func_name: str, file_name: str) -> Optional[Operation]:
        if len(node.children) < 2:
            return None
        
        left_child = node.children[0]
        right_child = node.children[1]
        
        left_op = Operation(
            type=OperationType.NOOP,
            value=left_child.value,
            line=left_child.line,
            column=left_child.column
        )
        
        right_op = self._parse_expression(
            right_child.value,
            right_child.line,
            right_child.column,
            func_name,
            file_name
        )
        
        assign_op = Operation(
            type=OperationType.ASSIGN,
            left=left_op,
            right=right_op,
            line=node.line,
            column=node.column
        )
        
        return assign_op
    
    def _build_return_operation(self, node: ASTNode, func_name: str, file_name: str) -> Optional[Operation]:
        if node.children:
            expr_child = node.children[0]
            if expr_child.type == 'expression':
                value_op = self._parse_expression(
                    expr_child.value,
                    expr_child.line,
                    expr_child.column,
                    func_name,
                    file_name
                )
                return Operation(
                    type=OperationType.RETURN,
                    left=value_op,
                    line=node.line,
                    column=node.column
                )
        
        return Operation(
            type=OperationType.RETURN,
            line=node.line,
            column=node.column
        )
    

    def _process_do_while_statement(self, do_while_node: ASTNode, current_block: BasicBlock,
                                   func_name: str, file_name: str, exit_block: BasicBlock) -> BasicBlock:
        body_start = self._create_block()
        body_start.is_loop_start = True
        
        condition_expr = None
        loop_body = None
        
        for child in do_while_node.children:
            if child.type == 'condition' and child.children:
                condition_expr = child.children[0].value if child.children[0].value else ""
            elif child.type == 'body':
                loop_body = child
        
        if not condition_expr:
            self.errors.append(ParsingError(
                file_name=file_name,
                line=do_while_node.line,
                column=do_while_node.column,
                message="Отсутствует условие в do-while"
            ))
            return current_block
        
        condition_block = self._create_block()
        condition_block.is_loop_end = True

        cond_op = self._parse_expression(condition_expr, do_while_node.line, do_while_node.column, func_name, file_name)
        if cond_op:
            condition_block.operations.append(cond_op)

        after_loop = self._create_block()
        if loop_body:
            body_end = self._process_statements(loop_body.children, body_start, func_name, file_name, exit_block)
            if body_end:
                body_end.next_block = condition_block
        else:
            body_start.next_block = condition_block
        
        condition_block.true_branch = body_start
        condition_block.false_branch = after_loop 
        
        current_block.next_block = body_start
        
        return after_loop
    
    def _parse_expression(self, expr: str, line: int, column: int, 
                     func_name: str, file_name: str) -> Operation:
        expr = expr.strip()
        
        print(f"DEBUG _parse_expression: parsing '{expr}'")

        if '->' in expr and '=' in expr:
        # Находим позиции
            arrow_pos = expr.find('->')
            eq_pos = expr.find('=')
            
            if arrow_pos < eq_pos:
                # Это объявление с инициализацией
                var_part = expr[:eq_pos].strip()
                value_part = expr[eq_pos+1:].strip()
                
                if '->' in var_part:
                    name_type = var_part.split('->', 1)
                    var_name = name_type[0].strip()
                    var_type = name_type[1].strip()
                    
                    print(f"DEBUG: Found declaration with init in for: {var_name} -> {var_type} = {value_part}")
                    
                    # Парсим значение
                    value_op = self._parse_expression(value_part, line, column, func_name, file_name)
                    
                    # Создаем операцию DECLARE
                    return Operation(
                        type=OperationType.DECLARE,
                        value=var_name,
                        var_type=var_type,
                        left=value_op,
                        line=line,
                        column=column
                    )
        
        # Обработка инкремента i++
        if expr.endswith('++'):
            var_name = expr[:-2].strip()
            print(f"DEBUG: Found increment: {var_name}++")
            return Operation(
                type=OperationType.INCREMENT,
                left=Operation(type=OperationType.NOOP, value=var_name, line=line, column=column),
                right=Operation(type=OperationType.NOOP, value='1', line=line, column=column),
                line=line,
                column=column
            )
        elif expr.endswith('--'):
            var_name = expr[:-2].strip()
            print(f"DEBUG: Found postfix decrement: {var_name}--")
            # Используем DECREMENT вместо SUB
            return Operation(
                type=OperationType.DECREMENT,
                value=var_name,
                line=line,
                column=column,
                left=Operation(type=OperationType.NOOP, value=var_name, line=line, column=column)  # переменная
            )
        elif expr.startswith('++'):
            var_name = expr[2:].strip()
            print(f"DEBUG: Found prefix increment: ++{var_name}")
            return Operation(
                type=OperationType.INCREMENT,
                value=var_name,
                line=line,
                column=column,
                left=Operation(type=OperationType.NOOP, value=var_name, line=line, column=column),
                attributes={'prefix': True}  # отмечаем как префиксный
            )
        
        # Обработка ПРЕФИКСНОГО декремента --i
        elif expr.startswith('--'):
            var_name = expr[2:].strip()
            print(f"DEBUG: Found prefix decrement: --{var_name}")
            return Operation(
                type=OperationType.DECREMENT,
                value=var_name,
                line=line,
                column=column,
                left=Operation(type=OperationType.NOOP, value=var_name, line=line, column=column),
                attributes={'prefix': True}  # отмечаем как префиксный
            )
        # Словарь для хранения информации о вызовах функций
        func_calls_info = {}
        
        # 1. Находим и обрабатываем все вызовы функций
        # Используем стек для нахождения парных скобок
        stack = []
        func_calls = []
        i = 0
        
        while i < len(expr):
            if expr[i] == '(':
                stack.append(i)
            elif expr[i] == ')' and stack:
                start = stack.pop()
                # Проверяем, есть ли перед '(' имя функции
                if start > 0:
                    # Ищем начало имени функции
                    j = start - 1
                    while j >= 0 and (expr[j].isalnum() or expr[j] == '_'):
                        j -= 1
                    func_start = j + 1
                    if func_start < start:
                        func_name_call = expr[func_start:start].strip()
                        args_str = expr[start+1:i].strip()
                        
                        # Парсим аргументы сразу
                        args = []
                        if args_str:
                            # Разделяем аргументы с учетом вложенных вызовов
                            arg_parts = []
                            current_arg = []
                            paren_count = 0
                            
                            for char in args_str:
                                if char == '(':
                                    paren_count += 1
                                    current_arg.append(char)
                                elif char == ')':
                                    paren_count -= 1
                                    current_arg.append(char)
                                elif char == ',' and paren_count == 0:
                                    arg_part = ''.join(current_arg).strip()
                                    if arg_part:
                                        arg_parts.append(arg_part)
                                    current_arg = []
                                else:
                                    current_arg.append(char)
                            
                            if current_arg:
                                arg_part = ''.join(current_arg).strip()
                                if arg_part:
                                    arg_parts.append(arg_part)
                            
                            for arg in arg_parts:
                                if arg:
                                    arg_op = self._parse_expression(arg, line, column, func_name, file_name)
                                    args.append(arg_op)
                        
                        # Сохраняем информацию о вызове функции
                        call_id = len(func_calls_info)
                        func_calls_info[call_id] = {
                            'func_name': func_name_call,
                            'args': args,
                            'start': func_start,
                            'end': i+1
                        }
                        
                        # Добавляем в граф вызовов
                        if func_name != func_name_call:
                            if func_name not in self.call_graph:
                                self.call_graph[func_name] = set()
                            self.call_graph[func_name].add(func_name_call)
                        
                        func_calls.append((func_start, i+1, call_id))
            i += 1
        
        # 2. Заменяем вызовы функций на placeholders с сохранением информации
        expr_with_placeholders = expr
        for start, end, call_id in sorted(func_calls, key=lambda x: x[0], reverse=True):
            placeholder = f"__CALL_{call_id}__"
            expr_with_placeholders = expr_with_placeholders[:start] + placeholder + expr_with_placeholders[end:]
        
        print(f"DEBUG: Expression with placeholders: '{expr_with_placeholders}'")
        
        # 3. Парсим бинарные операции в выражении с placeholders
        ops = [
            ('+', OperationType.ADD),
            ('-', OperationType.SUB),
            ('*', OperationType.MUL),
            ('/', OperationType.DIV),
            ('%', OperationType.MOD),
            ('==', OperationType.EQ),
            ('!=', OperationType.NE),
            ('<', OperationType.LT),
            ('<=', OperationType.LE),
            ('>', OperationType.GT),
            ('>=', OperationType.GE),
            ('&&', OperationType.AND),
            ('||', OperationType.OR),
        ]
        
        # Проверяем каждую операцию
        for op_str, op_type in ops:
            if op_str in expr_with_placeholders:
                # Ищем оператор вне скобок и вне placeholders
                pos = expr_with_placeholders.find(op_str)
                if pos != -1:
                    # Проверяем, что это не внутри placeholder
                    is_in_placeholder = False
                    for placeholder in ['__CALL_', '__']:
                        placeholder_pos = expr_with_placeholders.find(placeholder)
                        if placeholder_pos != -1 and placeholder_pos <= pos < placeholder_pos + len(placeholder):
                            is_in_placeholder = True
                            break
                    
                    if not is_in_placeholder:
                        left_expr = expr_with_placeholders[:pos].strip()
                        right_expr = expr_with_placeholders[pos+len(op_str):].strip()
                        
                        print(f"DEBUG: Found operator '{op_str}': left='{left_expr}', right='{right_expr}'")
                        
                        if left_expr and right_expr:
                            left_op = self._parse_simple_operand(left_expr, func_calls_info, line, column, func_name, file_name)
                            right_op = self._parse_simple_operand(right_expr, func_calls_info, line, column, func_name, file_name)
                            
                            return Operation(
                                type=op_type,
                                left=left_op,
                                right=right_op,
                                line=line,
                                column=column
                            )
        
        # 4. Если нет операций, это простой операнд
        return self._parse_simple_operand(expr_with_placeholders, func_calls_info, line, column, func_name, file_name)

    def _parse_simple_operand(self, expr: str, func_calls_info: dict, line: int, column: int,
                            func_name: str, file_name: str) -> Operation:
        """Парсит простой операнд (переменную, число, или вызов функции)"""
        expr = expr.strip()
        
        # Проверяем, является ли это placeholder для вызова функции
        if expr.startswith('__CALL_') and expr.endswith('__'):
            call_id_str = expr[7:-2]  # Убираем __CALL_ и __
            if call_id_str.isdigit():
                call_id = int(call_id_str)
                if call_id in func_calls_info:
                    info = func_calls_info[call_id]
                    # Создаем операцию CALL с сохраненными аргументами
                    return Operation(
                        type=OperationType.CALL,
                        value=info['func_name'],
                        args=info['args'],
                        line=line,
                        column=column
                    )
        
        # Проверяем, является ли числом
        if self._is_number(expr):
            return Operation(
                type=OperationType.NOOP,
                value=expr,
                line=line,
                column=column
            )
        
        # Проверяем, является ли строкой
        if (expr.startswith('"') and expr.endswith('"')) or (expr.startswith("'") and expr.endswith("'")):
            return Operation(
                type=OperationType.NOOP,
                value=expr,
                line=line,
                column=column
            )
        
        # Проверяем, является ли булевым значением
        if expr.lower() in ['true', 'false']:
            return Operation(
                type=OperationType.NOOP,
                value=expr.lower(),
                line=line,
                column=column
            )
        
        # По умолчанию считаем переменной
        return Operation(
            type=OperationType.NOOP,
            value=expr,
            line=line,
            column=column
        )
    
    def _is_number(self, s: str) -> bool:
        try:
            float(s)
            return True
        except ValueError:
            return False
        
    def _process_statements(self, statements: List[ASTNode], start_block: BasicBlock,
                       func_name: str, file_name: str, exit_block: BasicBlock) -> Optional[BasicBlock]:
        """Обработка списка операторов"""
        print(f"\n{'='*60}")
        print(f"DEBUG _process_statements: START")
        print(f"  Processing {len(statements)} statements")
        print(f"  Start block: {start_block.id}")
        print(f"  Exit block: {exit_block.id}")
        print(f"{'='*60}")
        
        current_block = start_block
        
        for i, stmt in enumerate(statements):
            print(f"\n  Statement {i}: type={stmt.type}, line={stmt.line}, value={stmt.value}")
            
            if stmt.type == 'assignment':
                print(f"    Processing ASSIGNMENT")
                op = self._build_assignment_operation(stmt, func_name, file_name)
                if op:
                    current_block.operations.append(op)
                    print(f"    Added assignment to block {current_block.id}: {op.type}")

            elif stmt.type == 'var_declaration':
                print(f"    Processing VAR_DECLARATION")
                op = self._build_var_declaration_operation(stmt, func_name, file_name)
                if op:
                    current_block.operations.append(op)
                    print(f"    Added var declaration to block {current_block.id}: {op.value} -> {op.var_type}")

            elif stmt.type == 'var_declaration_with_init':
                print(f"    Processing VAR_DECLARATION_WITH_INIT")
                op = self._build_var_declaration_with_init_operation(stmt, func_name, file_name)
                if op:
                    current_block.operations.append(op)
                    print(f"    Added var declaration with init to block {current_block.id}: {op.value} -> {op.var_type} = ...")

            elif stmt.type == 'function_call' or stmt.type == 'call':
                print(f"    Processing FUNCTION_CALL (type={stmt.type})")
                op = self._build_function_call_operation(stmt, func_name, file_name)
                if op:
                    current_block.operations.append(op)
                    print(f"    Added function call to block {current_block.id}: CALL {op.value}()")

            elif stmt.type == 'if_statement':
                print(f"    Processing IF_STATEMENT")
                print(f"    Calling _process_if_statement with exit_block={exit_block.id}")
                after_if_block = self._process_if_statement(stmt, current_block, 
                                                        func_name, file_name, exit_block)
                if not after_if_block:
                    print(f"    WARNING: _process_if_statement returned None!")
                    print(f"    Likely contains return statement")
                    return None
                print(f"    if_statement processed, new current_block: {after_if_block.id}")
                current_block = after_if_block

            elif stmt.type == 'while_statement':
                print(f"    Processing WHILE_STATEMENT")
                after_while_block = self._process_while_statement(stmt, current_block, 
                                                                func_name, file_name, exit_block)
                print(f"    while_statement processed, new current_block: {after_while_block.id}")
                current_block = after_while_block

            elif stmt.type == 'do_while_statement':
                print(f"    Processing DO_WHILE_STATEMENT")
                after_do_while_block = self._process_do_while_statement(stmt, current_block, 
                                                                    func_name, file_name, exit_block)
                print(f"    do_while_statement processed, new current_block: {after_do_while_block.id}")
                current_block = after_do_while_block

            elif stmt.type == 'for_statement':
                print(f"    Processing FOR_STATEMENT")
                after_for_block = self._process_for_statement(stmt, current_block,
                                                            func_name, file_name, exit_block)
                if after_for_block:
                    print(f"    for_statement processed, new current_block: {after_for_block.id}")
                    current_block = after_for_block
                else:
                    print(f"    for_statement returned None, likely contains return")
                    return None

            elif stmt.type == 'return':
                print(f"    Processing RETURN")
                op = self._build_return_operation(stmt, func_name, file_name)
                if op:
                    current_block.operations.append(op)
                    print(f"    Added return operation to block {current_block.id}")
                print(f"    Setting current_block({current_block.id}).next_block = exit_block({exit_block.id})")
                current_block.next_block = exit_block
                print(f"    Returning None (end of execution path)")
                print(f"{'='*60}")
                print(f"DEBUG _process_statements: END (return found)")
                print(f"{'='*60}\n")
                return None
            
            elif stmt.type == 'break':
                print(f"    Processing BREAK")
                op = Operation(
                    type=OperationType.BREAK,
                    line=stmt.line,
                    column=stmt.column
                )
                current_block.operations.append(op)
                print(f"    Added break operation to block {current_block.id}")
                # Для break нужно специальное соединение блоков, обрабатывается в циклах
                
            elif stmt.type == 'continue':
                print(f"    Processing CONTINUE")
                op = Operation(
                    type=OperationType.CONTINUE,
                    line=stmt.line,
                    column=stmt.column
                )
                current_block.operations.append(op)
                print(f"    Added continue operation to block {current_block.id}")
                # Для continue нужно специальное соединение блоков, обрабатывается в циклах
                
            elif stmt.type == 'expression_statement':
                print(f"    Processing EXPRESSION_STATEMENT")
                op = self._build_expression_statement_operation(stmt, func_name, file_name)
                if op:
                    current_block.operations.append(op)
                    print(f"    Added expression statement to block {current_block.id}: {op.type}")
            
            elif stmt.type == 'block':
                print(f"    Processing BLOCK")
                # Вложенный блок { ... }
                if stmt.children:
                    block_start = self._create_block()
                    print(f"    Created block_start: {block_start.id}")
                    
                    block_end = self._process_statements(stmt.children, block_start, 
                                                    func_name, file_name, exit_block)
                    
                    if block_end:
                        print(f"    block_end: {block_end.id}")
                        # Соединяем текущий блок с началом вложенного блока
                        current_block.next_block = block_start
                        # После вложенного блока продолжаем с текущего
                        current_block = block_end
                    else:
                        print(f"    block_end is None (contains return)")
                        current_block.next_block = block_start
                        return None
            
            elif stmt.type == 'empty_statement':
                print(f"    Processing EMPTY_STATEMENT (;)")
                # Пустой оператор, ничего не делаем
                pass
                
            else:
                print(f"    WARNING: Unknown statement type: {stmt.type}")
                # Создаем NOOP для неизвестных операторов
                op = Operation(
                    type=OperationType.NOOP,
                    value=f"Unknown: {stmt.type}",
                    line=stmt.line,
                    column=stmt.column
                )
                current_block.operations.append(op)
        
        print(f"\n  Finished processing all statements")
        print(f"  Final block: {current_block.id}")
        print(f"  Block {current_block.id} operations: {len(current_block.operations)}")
        if current_block.operations:
            for j, op in enumerate(current_block.operations):
                print(f"    Op {j}: {op.type.name} value={op.value}")
        print(f"  Block {current_block.id}.next_block: {current_block.next_block.id if current_block.next_block else 'None'}")
        
        print(f"{'='*60}")
        print(f"DEBUG _process_statements: END")
        print(f"{'='*60}\n")
        
        return current_block
    def _process_if_statement(self, if_node: ASTNode, current_block: BasicBlock,
                             func_name: str, file_name: str, exit_block: BasicBlock) -> Optional[BasicBlock]:
        """Обработка оператора if"""
        print(f"\n{'='*60}")
        print(f"DEBUG _process_if_statement: START")
        print(f"  Called from line {if_node.line}")
        print(f"  Current block: {current_block.id}")
        print(f"  Exit block: {exit_block.id}")
        print(f"{'='*60}")
        
        # Создаем блок для условия
        condition_block = self._create_block()
        print(f"  Created condition_block: {condition_block.id}")
        
        condition_expr = None
        true_body_node = None
        false_body_node = None
        
        # Находим условие, true_body и false_body
        print(f"  Scanning if_node children ({len(if_node.children)} total):")
        for i, child in enumerate(if_node.children):
            print(f"    Child {i}: type={child.type}, value={child.value}")
            if child.type == 'condition' and child.children:
                condition_expr = child.children[0].value if child.children[0].value else ""
                print(f"      Found condition: {condition_expr}")
            elif child.type == 'true_body':
                true_body_node = child
                print(f"      Found true_body with {len(child.children)} children")
            elif child.type == 'false_body':
                false_body_node = child
                print(f"      Found false_body with {len(child.children)} children")
        
        if not condition_expr:
            print(f"  ERROR: No condition found!")
            self.errors.append(ParsingError(
                file_name=file_name,
                line=if_node.line,
                column=if_node.column,
                message="Отсутствует условие в if"
            ))
            return current_block
        
        # Парсим условие
        print(f"  Parsing condition expression: '{condition_expr}'")
        cond_op = self._parse_expression(condition_expr, if_node.line, if_node.column, func_name, file_name)
        if cond_op:
            condition_block.operations.append(cond_op)
            print(f"  Added condition operation to block {condition_block.id}")
        
        # Создаем блок после if (точка слияния ветвей)
        after_if = self._create_block()
        print(f"  Created after_if block: {after_if.id}")
        print(f"  Setting after_if({after_if.id}).next_block = exit_block({exit_block.id})")
        after_if.next_block = exit_block
        
        # Обрабатываем true ветку
        print(f"\n  Processing TRUE branch:")
        if true_body_node and true_body_node.children:
            true_start = self._create_block()
            print(f"    Created true_start block: {true_start.id}")
            print(f"    Calling _process_statements with exit_block=after_if({after_if.id})")
            
            true_end = self._process_statements(true_body_node.children, true_start, 
                                               func_name, file_name, after_if)
            
            if true_end:
                print(f"    true_end block: {true_end.id}")
                print(f"    true_end.next_block: {true_end.next_block.id if true_end.next_block else 'None'}")
                if true_end.next_block is None:
                    print(f"    Setting true_end({true_end.id}).next_block = after_if({after_if.id})")
                    true_end.next_block = after_if
                else:
                    print(f"    true_end already has next_block: {true_end.next_block.id}")
            else:
                print(f"    true_end is None!")
                true_start.next_block = after_if
            
            print(f"    Setting condition_block({condition_block.id}).true_branch = true_start({true_start.id})")
            condition_block.true_branch = true_start
        else:
            print(f"    No true body or empty")
            print(f"    Setting condition_block({condition_block.id}).true_branch = after_if({after_if.id})")
            condition_block.true_branch = after_if
        
        # Обрабатываем false ветку
        print(f"\n  Processing FALSE branch:")
        if false_body_node and false_body_node.children:
            false_start = self._create_block()
            print(f"    Created false_start block: {false_start.id}")
            print(f"    Calling _process_statements with exit_block=after_if({after_if.id})")
            
            false_end = self._process_statements(false_body_node.children, false_start, 
                                                func_name, file_name, after_if)
            
            if false_end:
                print(f"    false_end block: {false_end.id}")
                print(f"    false_end.next_block: {false_end.next_block.id if false_end.next_block else 'None'}")
                if false_end.next_block is None:
                    print(f"    Setting false_end({false_end.id}).next_block = after_if({after_if.id})")
                    false_end.next_block = after_if
                else:
                    print(f"    false_end already has next_block: {false_end.next_block.id}")
            else:
                print(f"    false_end is None!")
                false_start.next_block = after_if
            
            print(f"    Setting condition_block({condition_block.id}).false_branch = false_start({false_start.id})")
            condition_block.false_branch = false_start
        else:
            print(f"    No false body or empty")
            print(f"    Setting condition_block({condition_block.id}).false_branch = after_if({after_if.id})")
            condition_block.false_branch = after_if
        
        # Соединяем текущий блок с блоком условия
        print(f"\n  Connecting blocks:")
        print(f"    Setting current_block({current_block.id}).next_block = condition_block({condition_block.id})")
        current_block.next_block = condition_block
        
        print(f"\n  Summary:")
        print(f"    condition_block({condition_block.id}):")
        print(f"      true_branch: {condition_block.true_branch.id if condition_block.true_branch else 'None'}")
        print(f"      false_branch: {condition_block.false_branch.id if condition_block.false_branch else 'None'}")
        print(f"    after_if({after_if.id}).next_block: {after_if.next_block.id if after_if.next_block else 'None'}")
        
        print(f"\n  Returning after_if block: {after_if.id}")
        print(f"{'='*60}")
        print(f"DEBUG _process_if_statement: END")
        print(f"{'='*60}\n")
        
        return after_if
    def _process_while_statement(self, while_node: ASTNode, current_block: BasicBlock,
                                func_name: str, file_name: str, exit_block: BasicBlock) -> BasicBlock:
        """Обработка оператора while"""
        condition_block = self._create_block()
        condition_block.is_loop_start = True
        
        condition_expr = None
        loop_body = None
        
        for child in while_node.children:
            if child.type == 'condition' and child.children:
                condition_expr = child.children[0].value if child.children[0].value else ""
            elif child.type == 'body':
                loop_body = child
        
        if not condition_expr:
            self.errors.append(ParsingError(
                file_name=file_name,
                line=while_node.line,
                column=while_node.column,
                message="Отсутствует условие в while"
            ))
            return current_block
        
        cond_op = self._parse_expression(condition_expr, while_node.line, while_node.column, func_name, file_name)
        if cond_op:
            condition_block.operations.append(cond_op)
        
        after_loop = self._create_block()
        condition_block.is_loop_end = True
        
        if loop_body:
            body_start = self._create_block()
            body_end = self._process_statements(loop_body.children, body_start, func_name, file_name, exit_block)
            if body_end:
                body_end.next_block = condition_block
            condition_block.true_branch = body_start
        else:
            condition_block.true_branch = condition_block
        
        condition_block.false_branch = after_loop
        current_block.next_block = condition_block
        
        return after_loop
    
    def _create_block(self) -> BasicBlock:
        block = BasicBlock(id=self.current_block_id)
        self.current_block_id += 1
        return block
    
    def _build_function_call_operation(self, node: ASTNode, func_name: str, file_name: str) -> Optional[Operation]:
        if not node.children:
            return None
        
        func_name_node = None
        args_nodes = []

        for child in node.children:
            if child.type == 'function_name':
                func_name_node = child
            elif child.type == 'expression':
                args_nodes.append(child)
        
        if not func_name_node or not func_name_node.value:
            return None
        
        call_func_name = func_name_node.value
        args_ops = []
        for arg_node in args_nodes:
            if arg_node.value:
                arg_op = self._parse_expression(
                    arg_node.value,
                    arg_node.line,
                    arg_node.column,
                    func_name,
                    file_name
                )
                args_ops.append(arg_op)
        if func_name != call_func_name:
            if func_name not in self.call_graph:
                self.call_graph[func_name] = set()
            self.call_graph[func_name].add(call_func_name)
        
        return Operation(
            type=OperationType.CALL,
            value=call_func_name,
            args=args_ops,
            line=node.line,
            column=node.column
        )
    
    def _collect_all_blocks(self, start_block: BasicBlock) -> List[BasicBlock]:
        visited = set()
        blocks = []
        stack = [start_block]
        
        while stack:
            block = stack.pop()
            if block.id in visited:
                continue
            
            visited.add(block.id)
            blocks.append(block)
            
            if block.next_block:
                stack.append(block.next_block)
            if block.true_branch:
                stack.append(block.true_branch)
            if block.false_branch:
                stack.append(block.false_branch)
        
        return blocks
    
    def _build_var_declaration_with_init_operation(self, node: ASTNode, func_name: str, file_name: str) -> Optional[Operation]:
        """Создание операции для объявления переменной с инициализацией"""
        if len(node.children) < 3:
            return None
        
        var_name = node.children[0].value if node.children[0].value else "?"
        var_type = node.children[1].value if node.children[1].value else "?"
        
        # Парсим значение инициализации
        init_expr = node.children[2].value if node.children[2].value else ""
        init_op = self._parse_expression(init_expr, node.line, node.column, func_name, file_name)
        
        # Создаем операцию DECLARE с инициализацией
        return Operation(
            type=OperationType.DECLARE,
            value=var_name,
            var_type=var_type,
            left=init_op,  # Инициализирующее значение
            line=node.line,
            column=node.column
        )
    
    def _build_expression_statement_operation(self, node: ASTNode, func_name: str, file_name: str) -> Optional[Operation]:
        """Создание операции для выражения-оператора"""
        if not node.children or node.children[0].type != 'expression':
            return None
        
        expr = node.children[0].value if node.children[0].value else ""
        if not expr:
            return None
        
        print(f"DEBUG _build_expression_statement_operation: parsing '{expr}'")
        
        # Парсим выражение
        return self._parse_expression(expr, node.line, node.column, func_name, file_name)
    
    def _process_for_statement(self, for_node: ASTNode, current_block: BasicBlock,
                            func_name: str, file_name: str, exit_block: BasicBlock) -> Optional[BasicBlock]:
        """Обработка оператора for"""
        print(f"\n{'='*60}")
        print(f"DEBUG _process_for_statement: START")
        print(f"  Processing for statement at line {for_node.line}")
        print(f"  Current block: {current_block.id}")
        print(f"  Exit block: {exit_block.id}")
        print(f"{'='*60}")
        
        # Извлекаем части for: init, condition, increment, body
        init_expr = None
        condition_expr = None
        increment_expr = None
        loop_body = None
        
        print(f"  Scanning for_node children ({len(for_node.children)} total):")
        for i, child in enumerate(for_node.children):
            print(f"    Child {i}: type={child.type}, value={child.value}")
            if child.type == 'init':
                # ВАЖНО: извлекаем значение из дочернего узла expression
                if child.children and child.children[0].type == 'expression':
                    init_expr = child.children[0].value if child.children[0].value else ""
                    print(f"      Found init expression: '{init_expr}'")
            elif child.type == 'condition':
                if child.children and child.children[0].type == 'expression':
                    condition_expr = child.children[0].value if child.children[0].value else ""
                    print(f"      Found condition expression: '{condition_expr}'")
            elif child.type == 'increment':
                if child.children and child.children[0].type == 'expression':
                    increment_expr = child.children[0].value if child.children[0].value else ""
                    print(f"      Found increment expression: '{increment_expr}'")
            elif child.type == 'body':
                loop_body = child
                print(f"      Found body with {len(child.children)} children")
        
        # Создаем блок для инициализации
        init_block = self._create_block()
        print(f"  Created init_block: {init_block.id}")
        
        # Блок для условия
        condition_block = self._create_block()
        condition_block.is_loop_start = True
        print(f"  Created condition_block: {condition_block.id}")
        
        # Блок для тела цикла
        body_start = self._create_block()
        print(f"  Created body_start: {body_start.id}")
        
        # Блок для инкремента
        increment_block = self._create_block()
        print(f"  Created increment_block: {increment_block.id}")
        
        # Блок после цикла
        after_loop = self._create_block()
        print(f"  Created after_loop: {after_loop.id}")
        
        # 1. Обрабатываем инициализацию
        if init_expr:
            print(f"  Processing init expression: '{init_expr}'")
            init_op = self._parse_expression(init_expr, for_node.line, for_node.column, func_name, file_name)
            if init_op:
                init_block.operations.append(init_op)
                print(f"  Added init operation to block {init_block.id}: {init_op.type}")
        else:
            print(f"  No init expression")
        
        # 2. Обрабатываем условие
        if condition_expr:
            print(f"  Processing condition expression: '{condition_expr}'")
            cond_op = self._parse_expression(condition_expr, for_node.line, for_node.column, func_name, file_name)
            if cond_op:
                condition_block.operations.append(cond_op)
                print(f"  Added condition operation to block {condition_block.id}: {cond_op.type}")
        else:
            # Если условие не указано, считаем его всегда истинным
            print(f"  No condition specified, using always true")
            cond_op = Operation(
                type=OperationType.NOOP,
                value='true',
                line=for_node.line,
                column=for_node.column
            )
            condition_block.operations.append(cond_op)
        
        # 3. Обрабатываем инкремент
        if increment_expr:
            print(f"  Processing increment expression: '{increment_expr}'")
            inc_op = self._parse_expression(increment_expr, for_node.line, for_node.column, func_name, file_name)
            if inc_op:
                increment_block.operations.append(inc_op)
                print(f"  Added increment operation to block {increment_block.id}: {inc_op.type}")
        else:
            print(f"  No increment expression")
        
        # 4. Обрабатываем тело цикла
        print(f"  Processing loop body:")
        if loop_body and loop_body.children:
            print(f"    Body has {len(loop_body.children)} statements")
            
            # Обрабатываем тело цикла
            body_end = self._process_statements(loop_body.children, body_start, 
                                            func_name, file_name, exit_block)
            
            if body_end:
                print(f"    Body end block: {body_end.id}")
                # После тела идем в блок инкремента
                print(f"    Setting body_end({body_end.id}).next_block = increment_block({increment_block.id})")
                body_end.next_block = increment_block
            else:
                print(f"    Body end is None (contains return/break)")
                # Если тело содержит return, не соединяем с increment_block
                body_start.next_block = increment_block
        else:
            print(f"    Empty loop body")
            # Пустое тело
            body_start.next_block = increment_block
        
        # 5. Соединяем блоки
        
        # Текущий блок ведет в блок инициализации
        print(f"\n  Connecting blocks:")
        print(f"    Setting current_block({current_block.id}).next_block = init_block({init_block.id})")
        current_block.next_block = init_block
        
        # Инициализация ведет в проверку условия
        print(f"    Setting init_block({init_block.id}).next_block = condition_block({condition_block.id})")
        init_block.next_block = condition_block
        
        # Условие ветвится: true -> тело, false -> после цикла
        print(f"    Setting condition_block({condition_block.id}).true_branch = body_start({body_start.id})")
        condition_block.true_branch = body_start
        print(f"    Setting condition_block({condition_block.id}).false_branch = after_loop({after_loop.id})")
        condition_block.false_branch = after_loop
        
        # Инкремент ведет обратно к проверке условия
        print(f"    Setting increment_block({increment_block.id}).next_block = condition_block({condition_block.id})")
        increment_block.next_block = condition_block
        
        # Помечаем condition_block как конец цикла (для break/continue)
        condition_block.is_loop_end = True
        
        print(f"\n  Summary:")
        print(f"    init_block({init_block.id}): {len(init_block.operations)} operations")
        print(f"    condition_block({condition_block.id}): true→{condition_block.true_branch.id}, false→{condition_block.false_branch.id}")
        print(f"    body_start({body_start.id}): {len(body_start.operations)} operations")
        print(f"    increment_block({increment_block.id}): {len(increment_block.operations)} operations")
        print(f"    after_loop({after_loop.id}).next_block: {after_loop.next_block.id if after_loop.next_block else 'None'}")
        
        print(f"\n{'='*60}")
        print(f"DEBUG _process_for_statement: END")
        print(f"{'='*60}\n")
        
        # Возвращаем блок после цикла
        return after_loop