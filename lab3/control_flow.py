from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple, Set
from enum import Enum
from port.builtin_functions import BuiltinFunctions
from port.type_system import TypeSystem

    

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
    var_type: Optional[str] = None  # Тип переменной/операции
    result_type: Optional[str] = None  # Тип результата операции
    attributes: Dict[str, Any] = field(default_factory=dict)  # Добавить эту строку

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
class VariableInfo:
    """Информация о переменной"""
    name: str
    type: str
    declared_at_line: int
    initialized: bool = False
    scope_level: int = 0
    offset: int = 0  # смещение в стековом фрейме
    is_param: bool = False
    
    

@dataclass
class SymbolTable:
    """Таблица символов (область видимости)"""
    variables: Dict[str, VariableInfo] = field(default_factory=dict)
    parent: Optional['SymbolTable'] = None
    scope_name: str = ""
    
    def add_variable(self, name: str, var_type: str, line: int, 
                    is_param: bool = False, offset: int = 0) -> VariableInfo:
        """Добавляет переменную в таблицу символов"""
        var_info = VariableInfo(
            name=name,
            type=var_type,
            declared_at_line=line,
            is_param=is_param,
            offset=offset,
            scope_level=self._get_scope_level()
        )
        self.variables[name] = var_info
        return var_info
    
    def get_variable(self, name: str) -> Optional[VariableInfo]:
        """Ищет переменную в текущей и родительских областях видимости"""
        if name in self.variables:
            return self.variables[name]
        elif self.parent:
            return self.parent.get_variable(name)
        return None
    
    def exists(self, name: str) -> bool:
        """Проверяет, существует ли переменная"""
        return self.get_variable(name) is not None
    
    def _get_scope_level(self) -> int:
        """Вычисляет уровень вложенности области видимости"""
        level = 0
        current = self
        while current.parent:
            level += 1
            current = current.parent
        return level

@dataclass  
class FunctionInfo:
    name: str
    signature: Dict[str, Any]
    cfg: ControlFlowGraph
    source_file: str
    operations_tree: Optional[Any] = None
    return_type: str = "void"
    parameters: List[Tuple[str, str]] = field(default_factory=list)
    symbol_table: SymbolTable = field(default_factory=lambda: SymbolTable(scope_name="global"))
    local_vars_size: int = 0
    param_count: int = 0

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
    """Построитель графа потока управления с системой типов"""
    
    def __init__(self):
        self.functions: List[FunctionInfo] = []
        self.errors: List[ParsingError] = []
        self.current_block_id = 0
        self.call_graph: Dict[str, Set[str]] = {}
        
        # Текущий контекст анализа
        self.current_function_name: Optional[str] = None
        self.current_file_name: Optional[str] = None
        self.current_symbol_table: Optional[SymbolTable] = None
        self.scope_stack: List[SymbolTable] = []
    
    def _create_block(self) -> BasicBlock:
        """Создает новый базовый блок"""
        block = BasicBlock(id=self.current_block_id)
        self.current_block_id += 1
        return block
    
    def _enter_scope(self, scope_name: str = ""):
        """Вход в новую область видимости"""
        new_table = SymbolTable(
            parent=self.current_symbol_table,
            scope_name=scope_name
        )
        self.scope_stack.append(new_table)
        self.current_symbol_table = new_table
    
    def _exit_scope(self):
        """Выход из области видимости"""
        if self.scope_stack:
            self.scope_stack.pop()
            if self.scope_stack:
                self.current_symbol_table = self.scope_stack[-1]
            else:
                self.current_symbol_table = None
    
    def _add_variable_to_symbol_table(self, name: str, var_type: str, line: int, 
                                    is_param: bool = False, offset:int = 0) -> bool:
        """Добавляет переменную в текущую таблицу символов"""
        if not self.current_symbol_table:
            self.errors.append(ParsingError(
                file_name=self.current_file_name or "",
                line=line,
                column=0,
                message=f"Нет активной таблицы символов для переменной '{name}'"
            ))
            return False
        
        # Проверяем, существует ли уже переменная в текущей области
        if self.current_symbol_table.exists(name):
            existing = self.current_symbol_table.get_variable(name)
            self.errors.append(ParsingError(
                file_name=self.current_file_name or "",
                line=line,
                column=0,
                message=f"Переменная '{name}' уже объявлена в строке {existing.declared_at_line}"
            ))
            return False
        
        # Проверяем, допустим ли тип
        if not TypeSystem.is_valid_type(var_type) and var_type != "unknown":
            self.errors.append(ParsingError(
                file_name=self.current_file_name or "",
                line=line,
                column=0,
                message=f"Неизвестный тип '{var_type}' для переменной '{name}'"
            ))
            return False
        
        # Вычисляем смещение в стеке
        offset = 0
        if self.current_symbol_table.parent:  # Локальная переменная
            offset = -self._calculate_local_vars_size() - TypeSystem.get_size(var_type)
        
        # Добавляем переменную
        self.current_symbol_table.add_variable(name, var_type, line, is_param, offset)
        return True
    
    def _calculate_local_vars_size(self) -> int:
        """Вычисляет общий размер локальных переменных в текущей области"""
        if not self.current_symbol_table:
            return 0
        
        total_size = 0
        for var_info in self.current_symbol_table.variables.values():
            if not var_info.is_param:  # Только локальные переменные, не параметры
                total_size += TypeSystem.get_size(var_info.type)
        
        return total_size
    
    def _get_variable_type(self, name: str) -> Optional[str]:
        """Возвращает тип переменной из таблицы символов"""
        print(f"\nDEBUG _get_variable_type: Looking for '{name}'")
        
        if not self.current_symbol_table:
            print(f"  ERROR: No current symbol table!")
            return None
        
        print(f"  Current scope: '{self.current_symbol_table.scope_name}'")
        
        # Ищем в текущей и всех родительских областях
        current_table = self.current_symbol_table
        depth = 0
        
        while current_table:
            print(f"  Checking scope {depth} '{current_table.scope_name}':")
            
            # Проверим прямое наличие
            if name in current_table.variables:
                var_info = current_table.variables[name]
                print(f"    ✓ FOUND: {name} -> {var_info.type} (line {var_info.declared_at_line})")
                return var_info.type
            
            print(f"    Not found in this scope")
            
            # Проверим через метод get_variable (который может искать в родителях)
            var_info = current_table.get_variable(name)
            if var_info:
                print(f"    ✓ FOUND via get_variable(): {name} -> {var_info.type}")
                return var_info.type
            
            current_table = current_table.parent
            depth += 1
        
        print(f"  ✗ Variable '{name}' NOT FOUND in any scope")
        
        # Выведем все переменные во всех областях для отладки
        print(f"  All variables in scope hierarchy:")
        table = self.current_symbol_table
        depth = 0
        while table:
            print(f"    Scope {depth} '{table.scope_name}':")
            if table.variables:
                for var_name, info in table.variables.items():
                    print(f"      {var_name}: {info.type} (line {info.declared_at_line})")
            else:
                print(f"      (empty)")
            table = table.parent
            depth += 1
        
        return None
    
    def build_from_ast(self, file_name: str, ast: ASTNode) -> List[FunctionInfo]:
        try:
            self.current_file_name = file_name
            self._analyze_file(file_name, ast)
            return self.functions
        except Exception as e:
            self.errors.append(ParsingError(
                file_name=file_name,
                line=0,
                column=0,
                message=f"Ошибка при анализе файла: {str(e)}"
            ))
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return []
    
    def _analyze_file(self, file_name: str, ast: ASTNode):
        for node in ast.children:
            if node.type == 'function_declaration':
                self._process_function(file_name, node)
    
    def _process_function(self, file_name: str, func_node: ASTNode):
        func_name = "unknown"
        return_type = "void"
        parameters = []
        
        # Извлекаем информацию о функции
        for child in func_node.children:
            if child.type == 'function_name':
                func_name = child.value
            elif child.type == 'return_type':
                return_type = child.value
            elif child.type == 'parameter':
                param_name = child.value if child.value else "?"
                param_type = child.attributes.get('type', 'unknown') if hasattr(child, 'attributes') else 'unknown'
                parameters.append((param_name, param_type))
        
        # Сохраняем текущий контекст
        self.current_function_name = func_name
        
        # Создаем новую таблицу символов для функции
        self._enter_scope(f"function_{func_name}")
        
        # Добавляем параметры в таблицу символов
        param_offset = 16  # Параметры начинаются с положительного смещения от base pointer
        
        for param_name, param_type in parameters:
            if TypeSystem.is_valid_type(param_type) or param_type == "unknown":
                # Без offset или с offset=0
                self._add_variable_to_symbol_table(
                    name=param_name,
                    var_type=param_type,
                    line=func_node.line,
                    is_param=True
                    # offset=param_offset  <-- УБРАТЬ или добавить в метод
                )
                param_offset += TypeSystem.get_size(param_type)
            else:
                self.errors.append(ParsingError(
                    file_name=file_name,
                    line=func_node.line,
                    column=0,
                    message=f"Неизвестный тип параметра '{param_type}' для '{param_name}'"
                ))
        # Создаем CFG для функции
        entry_block = self._create_block()
        exit_block = self._create_block()
        body_node = None
        
        for child in func_node.children:
            if child.type == 'function_body':
                body_node = child
                break
        
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
                parameters=parameters,
                symbol_table=self.current_symbol_table
            )
            self.functions.append(func_info)
            self._exit_scope()  # Выходим из области видимости функции
            self.current_function_name = None
            return
        
        # Входим в область видимости тела функции
        self._enter_scope("function_body")
        
        current_block = entry_block
        final_block = self._process_statements(body_node.children, current_block, func_name, file_name, exit_block)

        if final_block:
            final_block.next_block = exit_block

        # Выходим из области видимости тела функции
        self._exit_scope()
        
        all_blocks = self._collect_all_blocks(entry_block)
        all_blocks.append(exit_block)
        
        cfg = ControlFlowGraph(entry_block, exit_block, all_blocks)
        
        # Вычисляем размер локальных переменных
        local_vars_size = self._calculate_local_vars_size()
        
        func_info = FunctionInfo(
            name=func_name,
            signature={'return_type': return_type, 'parameters': parameters},
            cfg=cfg,
            source_file=file_name,
            return_type=return_type,
            parameters=parameters,
            symbol_table=self.scope_stack[-1] if self.scope_stack else SymbolTable(),
            local_vars_size=local_vars_size,
            param_count=len(parameters)
        )
        
        self.functions.append(func_info)
        
        # Выходим из области видимости функции
        self._exit_scope()
        self.current_function_name = None
        self._calculate_stack_offsets(func_info)
    
    def _build_assignment_operation(self, node: ASTNode, func_name: str, file_name: str) -> Optional[Operation]:
        if len(node.children) < 2:
            return None
        
        left_child = node.children[0]
        right_child = node.children[1]
        
        # Парсим правую часть для определения типа
        right_op = self._parse_expression(
            right_child.value,
            right_child.line,
            right_child.column,
            func_name,
            file_name
        )
        
        # Если переменная не существует, создаем ее с типом из правой части
        var_name = left_child.value
        if var_name and not self._get_variable_type(var_name):
            # Выводим тип из правой части
            inferred_type = right_op.result_type or "int"  # по умолчанию int
            if inferred_type == "unknown":
                inferred_type = "int"
            
            # Добавляем переменную в таблицу символов
            self._add_variable_to_symbol_table(
                name=var_name,
                var_type=inferred_type,
                line=left_child.line
            )
        
        left_op = Operation(
            type=OperationType.NOOP,
            value=var_name,
            line=left_child.line,
            column=left_child.column,
            var_type=self._get_variable_type(var_name) if var_name else None
        )
        
        # Проверка типов при присваивании
        if left_op.var_type and right_op.result_type:
            if not TypeSystem.can_implicit_cast(right_op.result_type, left_op.var_type):
                self.errors.append(ParsingError(
                    file_name=file_name,
                    line=node.line,
                    column=node.column,
                    message=f"Несовместимые типы при присваивании: '{right_op.result_type}' -> '{left_op.var_type}'"
                ))
        
        assign_op = Operation(
            type=OperationType.ASSIGN,
            left=left_op,
            right=right_op,
            line=node.line,
            column=node.column,
            result_type=left_op.var_type
        )
        
        return assign_op
    
    def _build_return_operation(self, node: ASTNode, func_name: str, file_name: str) -> Optional[Operation]:
        # Получаем ожидаемый тип возвращаемого значения
        expected_type = "void"
        for func_info in self.functions:
            if func_info.name == func_name:
                expected_type = func_info.return_type
                break
        
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
                
                # Проверка типа возвращаемого значения
                if value_op.result_type and expected_type != "void":
                    if not TypeSystem.can_implicit_cast(value_op.result_type, expected_type):
                        self.errors.append(ParsingError(
                            file_name=file_name,
                            line=node.line,
                            column=node.column,
                            message=f"Несовместимый тип возвращаемого значения: '{value_op.result_type}' -> '{expected_type}'"
                        ))
                
                return Operation(
                    type=OperationType.RETURN,
                    left=value_op,
                    line=node.line,
                    column=node.column,
                    result_type=expected_type
                )
        else:
            # Проверяем, что функция void возвращает пустое значение
            if expected_type != "void":
                self.errors.append(ParsingError(
                    file_name=file_name,
                    line=node.line,
                    column=node.column,
                    message=f"Функция должна возвращать значение типа '{expected_type}'"
                ))
        
        return Operation(
            type=OperationType.RETURN,
            line=node.line,
            column=node.column,
            result_type="void"
        )
    
    def _process_escape_sequences(self, string_literal: str) -> str:
        """Обрабатывает escape-последовательности в строковых литералах"""
        # Убираем кавычки
        if len(string_literal) >= 2:
            # Определяем тип кавычки (одинарная или двойная)
            quote_char = string_literal[0]
            if quote_char not in ['"', "'"]:
                return string_literal
                
            content = string_literal[1:-1]
            
            # Заменяем escape-последовательности
            replacements = {
                '\\n': '\n',
                '\\t': '\t',
                '\\r': '\r',
                '\\"': '"',
                "\\'": "'",
                '\\\\': '\\'
            }
            
            for esc_char, real_char in replacements.items():
                content = content.replace(esc_char, real_char)
            
            # Возвращаем с оригинальными кавычками
            return f'{quote_char}{content}{quote_char}'
        
        return string_literal

    
    def _parse_expression(self, expr: str, line: int, column: int, 
                         func_name: str, file_name: str) -> Operation:
        expr = expr.strip()
        # Обработка escape-последовательностей
        if (expr.startswith('"') and expr.endswith('"')) or (expr.startswith("'") and expr.endswith("'")):
            expr = self._process_escape_sequences(expr)
        
        # Определяем тип литерала
        literal_type = self._get_literal_type(expr)
        
        if literal_type != "unknown":
            # Для char литералов убедимся, что тип определился правильно
            if literal_type == 'char' and expr.startswith("'") and expr.endswith("'"):
                return Operation(
                    type=OperationType.NOOP,
                    value=expr,
                    line=line,
                    column=column,
                    result_type='char'  # Явно указываем char
                )
            elif literal_type == 'string':
                return Operation(
                    type=OperationType.NOOP,
                    value=expr,
                    line=line,
                    column=column,
                    result_type='string'
                )
            elif literal_type == 'int':
                return Operation(
                    type=OperationType.NOOP,
                    value=expr,
                    line=line,
                    column=column,
                    result_type='int'
                )
            elif literal_type == 'bool':
                return Operation(
                    type=OperationType.NOOP,
                    value=expr,
                    line=line,
                    column=column,
                    result_type='bool'
                )
        # Объявление с инициализацией в for: i -> int = 0
        if '->' in expr and '=' in expr:
            arrow_pos = expr.find('->')
            eq_pos = expr.find('=')
            
            if arrow_pos < eq_pos:
                var_part = expr[:eq_pos].strip()
                value_part = expr[eq_pos+1:].strip()
                
                if '->' in var_part:
                    name_type = var_part.split('->', 1)
                    var_name = name_type[0].strip()
                    var_type = name_type[1].strip()
                    
                    print(f"DEBUG: Found declaration with init: {var_name} -> {var_type} = {value_part}")
                    
                    # ВАЖНОЕ ИСПРАВЛЕНИЕ: Сначала добавляем переменную в таблицу символов!
                    if not self._add_variable_to_symbol_table(var_name, var_type, line):
                        print(f"WARNING: Failed to add variable '{var_name}' to symbol table")
                    else:
                        print(f"SUCCESS: Added variable '{var_name}' of type '{var_type}' to symbol table")
                    
                    # Теперь парсим значение (после добавления переменной)
                    value_op = self._parse_expression(value_part, line, column, func_name, file_name)
                    
                    return Operation(
                        type=OperationType.DECLARE,
                        value=var_name,
                        var_type=var_type,
                        left=value_op,
                        line=line,
                        column=column,
                        result_type=var_type
                    )
        
        # Постфиксные операции
        if expr.endswith('++'):
            var_name = expr[:-2].strip()
            var_type = self._get_variable_type(var_name)
            return Operation(
                type=OperationType.INCREMENT,
                value=var_name,
                line=line,
                column=column,
                var_type=var_type,
                result_type=var_type
            )
        
        elif expr.endswith('--'):
            var_name = expr[:-2].strip()
            print(f"DEBUG: Parsing decrement for '{var_name}'")
            
            # Попробуем все возможные способы получить тип
            var_type = None
            
            # Способ 1: Из таблицы символов
            var_type = self._get_variable_type(var_name)
            
            # Способ 2: Если не нашли, попробуем по имени
            if not var_type:
                print(f"  Variable '{var_name}' not found, trying to infer from name")
                if var_name == 'i':
                    var_type = 'int'
                elif var_name == 'f':
                    var_type = 'double'
                elif var_name == 'b':
                    var_type = 'int'
                elif var_name == 'a':
                    var_type = 'string'
            
            # Способ 3: По умолчанию
            if not var_type:
                var_type = 'int'
                print(f"  Using default type 'int'")
            
            print(f"  Final type for '{var_name}': {var_type}")
            
            return Operation(
                type=OperationType.DECREMENT,
                value=var_name,
                line=line,
                column=column,
                var_type=var_type,
                result_type=var_type
            )
        
        # Префиксные операции
        elif expr.startswith('++'):
            var_name = expr[2:].strip()
            var_type = self._get_variable_type(var_name)
            return Operation(
                type=OperationType.INCREMENT,
                value=var_name,
                line=line,
                column=column,
                var_type=var_type,
                result_type=var_type,
                attributes={'prefix': True}
            )
        
        elif expr.startswith('--'):
            var_name = expr[:2].strip()
            var_type = self._get_variable_type(var_name)
            return Operation(
                type=OperationType.DECREMENT,
                value=var_name,
                line=line,
                column=column,
                var_type=var_type,  # Сохраняем тип переменной
                result_type=var_type  # Результат декремента того же типа
            )
        
        # Простые идентификаторы
        if self._is_simple_identifier(expr):
            var_type = self._get_variable_type(expr)
            return Operation(
                type=OperationType.NOOP,
                value=expr,
                line=line,
                column=column,
                var_type=var_type,
                result_type=var_type
            )
        
        # Операции сравнения
        comparison_ops = [
            ('==', OperationType.EQ),
            ('!=', OperationType.NE),
            ('<', OperationType.LT),
            ('<=', OperationType.LE),
            ('>', OperationType.GT),
            ('>=', OperationType.GE),
        ]
        
        for op_str, op_type in comparison_ops:
            if op_str in expr:
                parts = expr.split(op_str, 1)
                if len(parts) == 2:
                    left = parts[0].strip()
                    right = parts[1].strip()
                    
                    left_op = self._parse_expression(left, line, column, func_name, file_name)
                    right_op = self._parse_expression(right, line, column, func_name, file_name)
                    
                    # Проверка типов для сравнения
                    if left_op.result_type and right_op.result_type:
                        if not TypeSystem.can_implicit_cast(left_op.result_type, right_op.result_type) and \
                           not TypeSystem.can_implicit_cast(right_op.result_type, left_op.result_type):
                            self.errors.append(ParsingError(
                                file_name=file_name,
                                line=line,
                                column=column,
                                message=f"Несовместимые типы для сравнения: '{left_op.result_type}' и '{right_op.result_type}'"
                            ))
                    
                    return Operation(
                        type=op_type,
                        left=left_op,
                        right=right_op,
                        line=line,
                        column=column,
                        result_type='bool'
                    )
        
        # Арифметические операции
        arithmetic_ops = [
            ('+', OperationType.ADD),
            ('-', OperationType.SUB),
            ('*', OperationType.MUL),
            ('/', OperationType.DIV),
            ('%', OperationType.MOD),
        ]

    # Сначала * / %
        for op_str, op_type in [('*', OperationType.MUL), ('/', OperationType.DIV), ('%', OperationType.MOD)]:
            if op_str in expr:
                parts = expr.split(op_str, 1)
                if len(parts) == 2:
                    left = parts[0].strip()
                    right = parts[1].strip()
                    
                    left_op = self._parse_expression(left, line, column, func_name, file_name)
                    right_op = self._parse_expression(right, line, column, func_name, file_name)
                    
                    # Определяем результирующий тип
                    result_type = self._check_binary_operation_types(
                        op_type, left_op.result_type, right_op.result_type,
                        line, column, file_name
                    )
                    
                    return Operation(
                        type=op_type,
                        left=left_op,
                        right=right_op,
                        line=line,
                        column=column,
                        result_type=result_type
                    )

        # Затем + -
        for op_str, op_type in [('+', OperationType.ADD), ('-', OperationType.SUB)]:
            if op_str in expr:
                pos = expr.find(op_str)
                if pos > 0:
                    before = expr[pos-1]
                    if before not in ['+', '-', '*', '/', '%', '=', '!', '<', '>', '&', '|']:
                        parts = expr.split(op_str, 1)
                        if len(parts) == 2:
                            left = parts[0].strip()
                            right = parts[1].strip()
                            
                            left_op = self._parse_expression(left, line, column, func_name, file_name)
                            right_op = self._parse_expression(right, line, column, func_name, file_name)
                            
                            # Определяем результирующий тип
                            result_type = self._check_binary_operation_types(
                                op_type, left_op.result_type, right_op.result_type,
                                line, column, file_name
                            )
                            
                            return Operation(
                                type=op_type,
                                left=left_op,
                                right=right_op,
                                line=line,
                                column=column,
                                result_type=result_type
                            )
        
        # Логические операции
        logical_ops = [
            ('&&', OperationType.AND),
            ('||', OperationType.OR),
        ]
        
        for op_str, op_type in logical_ops:
            if op_str in expr:
                parts = expr.split(op_str, 1)
                if len(parts) == 2:
                    left = parts[0].strip()
                    right = parts[1].strip()
                    
                    left_op = self._parse_expression(left, line, column, func_name, file_name)
                    right_op = self._parse_expression(right, line, column, func_name, file_name)
                    
                    # Проверяем, что оба операнда булевы
                    if left_op.result_type != 'bool' or right_op.result_type != 'bool':
                        self.errors.append(ParsingError(
                            file_name=file_name,
                            line=line,
                            column=column,
                            message=f"Логическая операция требует булевых операндов, получено: '{left_op.result_type}' и '{right_op.result_type}'"
                        ))
                    
                    return Operation(
                        type=op_type,
                        left=left_op,
                        right=right_op,
                        line=line,
                        column=column,
                        result_type='bool'
                    )
        
        # Вызов функции
        if '(' in expr and ')' in expr:
            paren_pos = expr.find('(')
            func_name_call = expr[:paren_pos].strip()
            # Извлекаем аргументы
            paren_count = 1
            end_pos = paren_pos + 1
            while end_pos < len(expr) and paren_count > 0:
                if expr[end_pos] == '(':
                    paren_count += 1
                elif expr[end_pos] == ')':
                    paren_count -= 1
                end_pos += 1
            
            args_str = expr[paren_pos+1:end_pos-1].strip()
            
            # Парсим аргументы
            args = []
            if args_str:
                arg_parts = self._split_arguments(args_str)
                for arg in arg_parts:
                    if arg:
                        arg_op = self._parse_expression(arg, line, column, func_name, file_name)
                        args.append(arg_op)
            
            # Добавляем в граф вызовов
            if func_name != func_name_call:
                if func_name not in self.call_graph:
                    self.call_graph[func_name] = set()
                self.call_graph[func_name].add(func_name_call)
            
            
            # Определяем тип возвращаемого значения
            if BuiltinFunctions.is_standard_function(func_name_call):
                func_info = BuiltinFunctions.get_function_info(func_name_call)
                return_type = func_info['return_type']
            else:
                # Для пользовательских функций ищем в уже обработанных
                return_type = 'int'  # по умолчанию
                for func in self.functions:
                    if func.name == func_name_call:
                        return_type = func.return_type
                        break
            
            return Operation(
                type=OperationType.CALL,
                value=func_name_call,
                args=args,
                line=line,
                column=column,
                result_type=return_type
            )
        
        # Если ничего не подошло
        return Operation(
            type=OperationType.NOOP,
            value=expr,
            line=line,
            column=column,
            result_type='unknown'
        )
    
    def _check_binary_operation_types(self, op_type: OperationType, 
                                left_type: Optional[str], right_type: Optional[str],
                                line: int, column: int, file_name: str) -> str:
        print(f"DEBUG _check_binary_operation_types: {op_type.name}, left={left_type}, right={right_type}")
        
        if not left_type or not right_type:
            return "unknown"
        
        # Операции сравнения (==, !=, <, <=, >, >=)
        comparison_ops = [OperationType.EQ, OperationType.NE, OperationType.LT, 
                        OperationType.LE, OperationType.GT, OperationType.GE]
        
        if op_type in comparison_ops:
            print(f"  Comparison operation detected")
            
            # Разрешаем сравнение char с char
            if left_type == 'char' and right_type == 'char':
                return 'bool'
            
            # Разрешаем сравнение int с int и т.д.
            if left_type == right_type:
                return 'bool'
            
            # Проверяем возможность неявного приведения типов
            if not TypeSystem.can_implicit_cast(left_type, right_type) and \
            not TypeSystem.can_implicit_cast(right_type, left_type):
                self.errors.append(ParsingError(
                    file_name=file_name,
                    line=line,
                    column=column,
                    message=f"Несовместимые типы для сравнения: '{left_type}' и '{right_type}'"
                ))
            
            return 'bool'
        
        # Арифметические операции
        arithmetic_ops = [OperationType.ADD, OperationType.SUB, OperationType.MUL, 
                        OperationType.DIV, OperationType.MOD]
        
        if op_type in arithmetic_ops:
            print(f"  Arithmetic operation detected")
            
            # Определяем допустимые числовые типы (добавляем char как числовой)
            numeric_types = ['char', 'int', 'float', 'double']
            
            # Проверяем, что оба операнда числовые
            if left_type not in numeric_types:
                self.errors.append(ParsingError(
                    file_name=file_name,
                    line=line,
                    column=column,
                    message=f"Нечисловой тип '{left_type}' в арифметической операции {op_type.name}"
                ))
                return "unknown"
            
            if right_type not in numeric_types:
                self.errors.append(ParsingError(
                    file_name=file_name,
                    line=line,
                    column=column,
                    message=f"Нечисловой тип '{right_type}' в арифметической операции {op_type.name}"
                ))
                return "unknown"
            
            # Определяем более широкий тип
            type_precedence = {'char': 0, 'int': 1, 'float': 2, 'double': 3}
            left_precedence = type_precedence.get(left_type, -1)
            right_precedence = type_precedence.get(right_type, -1)
            
            result_type = left_type if left_precedence >= right_precedence else right_type
            print(f"  Result type: {result_type}")
            
            return result_type
        
        return "unknown"
    
    
    def _split_arguments(self, args_str: str) -> List[str]:
        """Разделяет строку аргументов с учетом вложенных скобок"""
        args = []
        current = []
        paren_count = 0
        
        for char in args_str:
            if char == '(':
                paren_count += 1
                current.append(char)
            elif char == ')':
                paren_count -= 1
                current.append(char)
            elif char == ',' and paren_count == 0:
                args.append(''.join(current).strip())
                current = []
            else:
                current.append(char)
        
        if current:
            args.append(''.join(current).strip())
        
        return args
    
    def _is_simple_identifier(self, expr: str) -> bool:
        if not expr:
            return False
        
        if not (expr[0].isalpha() or expr[0] == '_'):
            return False
        
        for char in expr:
            if not (char.isalnum() or char == '_'):
                return False
        
        return True
    
    def _is_number(self, s: str) -> bool:
        try:
            float(s)
            return True
        except ValueError:
            return False
    
    def _process_statements(self, statements: List[ASTNode], start_block: BasicBlock,
                           func_name: str, file_name: str, exit_block: BasicBlock) -> Optional[BasicBlock]:
        """Обработка списка операторов"""
        current_block = start_block
        
        for stmt in statements:
            if stmt.type == 'assignment':
                op = self._build_assignment_operation(stmt, func_name, file_name)
                if op:
                    current_block.operations.append(op)

            elif stmt.type == 'var_declaration':
                op = self._build_var_declaration_operation(stmt, func_name, file_name)
                if op:
                    current_block.operations.append(op)

            elif stmt.type == 'var_declaration_with_init':
                op = self._build_var_declaration_with_init_operation(stmt, func_name, file_name)
                if op:
                    current_block.operations.append(op)

            elif stmt.type == 'function_call' or stmt.type == 'call':
                op = self._build_function_call_operation(stmt, func_name, file_name)
                if op:
                    current_block.operations.append(op)

            elif stmt.type == 'if_statement':
                after_if_block = self._process_if_statement(stmt, current_block, 
                                                          func_name, file_name, exit_block)
                if not after_if_block:
                    return None
                current_block = after_if_block

            elif stmt.type == 'while_statement':
                after_while_block = self._process_while_statement(stmt, current_block, 
                                                                func_name, file_name, exit_block)
                current_block = after_while_block

            elif stmt.type == 'do_while_statement':
                after_do_while_block = self._process_do_while_statement(stmt, current_block, 
                                                                    func_name, file_name, exit_block)
                current_block = after_do_while_block

            elif stmt.type == 'for_statement':
                after_for_block = self._process_for_statement(stmt, current_block,
                                                            func_name, file_name, exit_block)
                if after_for_block:
                    current_block = after_for_block
                else:
                    return None

            elif stmt.type == 'return':
                op = self._build_return_operation(stmt, func_name, file_name)
                if op:
                    current_block.operations.append(op)
                current_block.next_block = exit_block
                return None
            
            elif stmt.type == 'break':
                op = Operation(
                    type=OperationType.BREAK,
                    line=stmt.line,
                    column=stmt.column
                )
                current_block.operations.append(op)
                
            elif stmt.type == 'continue':
                op = Operation(
                    type=OperationType.CONTINUE,
                    line=stmt.line,
                    column=stmt.column
                )
                current_block.operations.append(op)
                
            elif stmt.type == 'expression_statement':
                op = self._build_expression_statement_operation(stmt, func_name, file_name)
                if op:
                    current_block.operations.append(op)
            
            elif stmt.type == 'block':
                if stmt.children:
                    block_start = self._create_block()
                    
                    # Входим в новую область видимости для блока
                    self._enter_scope("block")
                    
                    block_end = self._process_statements(stmt.children, block_start, 
                                                       func_name, file_name, exit_block)
                    
                    # Выходим из области видимости блока
                    self._exit_scope()
                    
                    if block_end:
                        current_block.next_block = block_start
                        current_block = block_end
                    else:
                        current_block.next_block = block_start
                        return None
            
            elif stmt.type == 'empty_statement':
                pass
                
            else:
                op = Operation(
                    type=OperationType.NOOP,
                    value=f"Unknown: {stmt.type}",
                    line=stmt.line,
                    column=stmt.column
                )
                current_block.operations.append(op)
        
        return current_block
    
    def _build_var_declaration_operation(self, node: ASTNode, func_name: str, file_name: str) -> Optional[Operation]:
        if len(node.children) < 2:
            return None
        
        var_name = node.children[0].value if node.children[0].value else "?"
        var_type = node.children[1].value if node.children[1].value else "?"
        
        # Добавляем переменную в таблицу символов
        if not self._add_variable_to_symbol_table(var_name, var_type, node.line):
            return None
        
        return Operation(
            type=OperationType.DECLARE,
            value=var_name,
            var_type=var_type,
            line=node.line,
            column=node.column,
            result_type=var_type
        )

    def _build_var_declaration_with_init_operation(self, node: ASTNode, func_name: str, file_name: str) -> Optional[Operation]:
        if len(node.children) < 3:
            return None
        
        var_name = node.children[0].value if node.children[0].value else "?"
        var_type = node.children[1].value if node.children[1].value else "?"
        
        # Добавляем переменную в таблицу символов
        if not self._add_variable_to_symbol_table(var_name, var_type, node.line):
            return None
        
        # Помечаем как инициализированную
        var_info = self.current_symbol_table.get_variable(var_name)
        
        # Парсим значение инициализации
        init_expr = node.children[2].value if node.children[2].value else ""
        init_op = self._parse_expression(init_expr, node.line, node.column, func_name, file_name)
        
        # Проверяем типы
        if init_op.result_type:
            if not TypeSystem.can_implicit_cast(init_op.result_type, var_type):
                self.errors.append(ParsingError(
                    file_name=file_name,
                    line=node.line,
                    column=node.column,
                    message=f"Несовместимые типы при инициализации: '{init_op.result_type}' -> '{var_type}'"
                ))
        
        return Operation(
            type=OperationType.DECLARE,
            value=var_name,
            var_type=var_type,
            left=init_op,
            line=node.line,
            column=node.column,
            result_type=var_type
        )
    
    def _build_function_call_operation(self, node: ASTNode, func_name: str, file_name: str) -> Optional[Operation]:
        
        print(f"\nDEBUG _build_function_call_operation for node: {node}")
        
        # Извлекаем имя функции из дочернего узла
        call_func_name = None
        args_nodes = []

        for child in node.children:
            if child.type == 'function_name':
                call_func_name = child.value
                print(f"  Found function_name: '{call_func_name}'")
            elif child.type == 'expression':
                args_nodes.append(child)
        
        if not call_func_name:
            print(f"  ERROR: No function name found")
            return None
        
        print(f"  Building call to '{call_func_name}' with {len(args_nodes)} args")
        
        args_ops = []
        for i, arg_node in enumerate(args_nodes):
            if arg_node.value:
                print(f"    Parsing arg {i}: '{arg_node.value}'")
                
                # Для scanf все аргументы кроме первого должны быть указателями
                if call_func_name == 'scanf' and i > 0:
                    # Извлекаем имя переменной (убираем & если есть)
                    var_name = arg_node.value.strip()
                    if var_name.startswith('&'):
                        var_name = var_name[1:].strip()
                    print(f"      scanf argument: {var_name}, treating as pointer")
                    
                    # Создаем специальную операцию
                    arg_op = Operation(
                        type=OperationType.NOOP,
                        value=var_name,
                        line=arg_node.line,
                        column=arg_node.column,
                        attributes={'is_pointer': True}
                    )
                    
                    # Получаем тип переменной
                    var_type = self._get_variable_type(var_name)
                    if var_type:
                        arg_op.result_type = var_type  # Базовый тип (int)
                        arg_op.var_type = var_type     # Также сохраняем базовый тип
                    else:
                        arg_op.result_type = 'int'
                        arg_op.var_type = 'int'
                else:
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
        
        # Определяем тип возвращаемого значения
        return_type = 'void'
        
        if BuiltinFunctions.is_standard_function(call_func_name):
            func_info = BuiltinFunctions.get_function_info(call_func_name)
            return_type = func_info['return_type']
            print(f"  ✓ '{call_func_name}' is standard, return_type: {return_type}")
        else:
            print(f"  ✗ '{call_func_name}' is NOT standard, searching in user functions...")
            for func in self.functions:
                if func.name == call_func_name:
                    return_type = func.return_type
                    print(f"  Found user function '{call_func_name}' with return type: {return_type}")
                    break
            else:
                print(f"  No user function found, using default return type: {return_type}")
        
        op = Operation(
            type=OperationType.CALL,
            value=call_func_name,
            args=args_ops,
            line=node.line,
            column=node.column,
            result_type=return_type
        )
        
        return op
    
    def _build_expression_statement_operation(self, node: ASTNode, func_name: str, file_name: str) -> Optional[Operation]:
        if not node.children or node.children[0].type != 'expression':
            return None
        
        expr = node.children[0].value if node.children[0].value else ""
        if not expr:
            return None
        
        return self._parse_expression(expr, node.line, node.column, func_name, file_name)
    
    # Остальные методы, которые были в оригинальном коде
    def _process_if_statement(self, if_node: ASTNode, current_block: BasicBlock,
                             func_name: str, file_name: str, exit_block: BasicBlock) -> Optional[BasicBlock]:
        """Обработка оператора if"""
        # Создаем блок для условия
        condition_block = self._create_block()
        
        condition_expr = None
        true_body_node = None
        false_body_node = None
        
        # Находим условие, true_body и false_body
        for child in if_node.children:
            if child.type == 'condition' and child.children:
                condition_expr = child.children[0].value if child.children[0].value else ""
            elif child.type == 'true_body':
                true_body_node = child
            elif child.type == 'false_body':
                false_body_node = child
        
        if not condition_expr:
            self.errors.append(ParsingError(
                file_name=file_name,
                line=if_node.line,
                column=if_node.column,
                message="Отсутствует условие в if"
            ))
            return current_block
        
        # Парсим условие
        cond_op = self._parse_expression(condition_expr, if_node.line, if_node.column, func_name, file_name)
        if cond_op:
            condition_block.operations.append(cond_op)
        
        # Создаем блок после if (точка слияния ветвей)
        after_if = self._create_block()
        after_if.next_block = exit_block
        
        # Обрабатываем true ветку
        if true_body_node and true_body_node.children:
            true_start = self._create_block()
            
            # Входим в область видимости true ветки
            self._enter_scope("if_true")
            
            true_end = self._process_statements(true_body_node.children, true_start, 
                                               func_name, file_name, after_if)
            
            # Выходим из области видимости true ветки
            self._exit_scope()
            
            if true_end:
                if true_end.next_block is None:
                    true_end.next_block = after_if
            else:
                true_start.next_block = after_if
            
            condition_block.true_branch = true_start
        else:
            condition_block.true_branch = after_if
        
        # Обрабатываем false ветку
        if false_body_node and false_body_node.children:
            false_start = self._create_block()
            
            # Входим в область видимости false ветки
            self._enter_scope("if_false")
            
            false_end = self._process_statements(false_body_node.children, false_start, 
                                                func_name, file_name, after_if)
            
            # Выходим из области видимости false ветки
            self._exit_scope()
            
            if false_end:
                if false_end.next_block is None:
                    false_end.next_block = after_if
            else:
                false_start.next_block = after_if
            
            condition_block.false_branch = false_start
        else:
            condition_block.false_branch = after_if
        
        # Соединяем текущий блок с блоком условия
        current_block.next_block = condition_block
        
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
            
            # Входим в область видимости тела цикла
            self._enter_scope("while_body")
            
            body_end = self._process_statements(loop_body.children, body_start, func_name, file_name, exit_block)
            
            # Выходим из области видимости тела цикла
            self._exit_scope()
            
            if body_end:
                body_end.next_block = condition_block
            condition_block.true_branch = body_start
        else:
            condition_block.true_branch = condition_block
        
        condition_block.false_branch = after_loop
        current_block.next_block = condition_block
        
        return after_loop
    
    def _process_do_while_statement(self, do_while_node: ASTNode, current_block: BasicBlock,
                                   func_name: str, file_name: str, exit_block: BasicBlock) -> BasicBlock:
        """Обработка оператора do-while"""
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
            # Входим в область видимости тела цикла
            self._enter_scope("do_while_body")
            
            body_end = self._process_statements(loop_body.children, body_start, func_name, file_name, exit_block)
            
            # Выходим из области видимости тела цикла
            self._exit_scope()
            
            if body_end:
                body_end.next_block = condition_block
        else:
            body_start.next_block = condition_block
        
        condition_block.true_branch = body_start
        condition_block.false_branch = after_loop 
        
        current_block.next_block = body_start
        
        return after_loop
    
    def _process_for_statement(self, for_node: ASTNode, current_block: BasicBlock,
                            func_name: str, file_name: str, exit_block: BasicBlock) -> Optional[BasicBlock]:
        """Обработка оператора for"""
        # Извлекаем части for: init, condition, increment, body
        init_expr = None
        condition_expr = None
        increment_expr = None
        loop_body = None
        
        for child in for_node.children:
            if child.type == 'init':
                if child.children and child.children[0].type == 'expression':
                    init_expr = child.children[0].value if child.children[0].value else ""
            elif child.type == 'condition':
                if child.children and child.children[0].type == 'expression':
                    condition_expr = child.children[0].value if child.children[0].value else ""
            elif child.type == 'increment':
                if child.children and child.children[0].type == 'expression':
                    increment_expr = child.children[0].value if child.children[0].value else ""
            elif child.type == 'body':
                loop_body = child
        
        # Создаем блок для инициализации
        init_block = self._create_block()
        
        # Блок для условия
        condition_block = self._create_block()
        condition_block.is_loop_start = True
        
        # Блок для тела цикла
        body_start = self._create_block()
        
        # Блок для инкремента
        increment_block = self._create_block()
        
        # Блок после цикла
        after_loop = self._create_block()
        
        # 1. Обрабатываем инициализацию
        if init_expr:
            init_op = self._parse_expression(init_expr, for_node.line, for_node.column, func_name, file_name)
            if init_op:
                init_block.operations.append(init_op)
        
        # 2. Обрабатываем условие
        if condition_expr:
            cond_op = self._parse_expression(condition_expr, for_node.line, for_node.column, func_name, file_name)
            if cond_op:
                condition_block.operations.append(cond_op)
        else:
            # Если условие не указано, считаем его всегда истинным
            cond_op = Operation(
                type=OperationType.NOOP,
                value='true',
                line=for_node.line,
                column=for_node.column,
                result_type='bool'
            )
            condition_block.operations.append(cond_op)
        
        # 3. Обрабатываем инкремент
        if increment_expr:
            inc_op = self._parse_expression(increment_expr, for_node.line, for_node.column, func_name, file_name)
            if inc_op:
                increment_block.operations.append(inc_op)
        
        # 4. Обрабатываем тело цикла
        if loop_body and loop_body.children:
            # Входим в область видимости тела цикла
            self._enter_scope("for_body")
            
            body_end = self._process_statements(loop_body.children, body_start, 
                                            func_name, file_name, exit_block)
            
            # Выходим из области видимости тела цикла
            self._exit_scope()
            
            if body_end:
                # После тела идем в блок инкремента
                body_end.next_block = increment_block
            else:
                # Если тело содержит return, не соединяем с increment_block
                body_start.next_block = increment_block
        else:
            # Пустое тело
            body_start.next_block = increment_block
        
        # 5. Соединяем блоки
        
        # Текущий блок ведет в блок инициализации
        current_block.next_block = init_block
        
        # Инициализация ведет в проверку условия
        init_block.next_block = condition_block
        
        # Условие ветвится: true -> тело, false -> после цикла
        condition_block.true_branch = body_start
        condition_block.false_branch = after_loop
        
        # Инкремент ведет обратно к проверке условия
        increment_block.next_block = condition_block
        
        # Помечаем condition_block как конец цикла (для break/continue)
        condition_block.is_loop_end = True
        
        # Возвращаем блок после цикла
        return after_loop
    
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
    
    def _calculate_stack_offsets(self, func_info: FunctionInfo):
        """Вычисляет смещения переменных в стековом фрейме"""
        # Параметры: положительные смещения от RBP
        param_offset = 16  # RBP+16 - первый параметр
        
        for param_name, param_type in func_info.parameters:
            if param_name in func_info.symbol_table.variables:
                var_info = func_info.symbol_table.variables[param_name]
                var_info.offset = param_offset
                param_offset += TypeSystem.get_size(param_type)
        
        # Локальные переменные: отрицательные смещения от RBP
        local_offset = -8  # Начинаем с -8
        
        # Собираем все локальные переменные из всех областей видимости
        all_vars = self._collect_all_local_vars(func_info.symbol_table)
        
        for var_info in all_vars:
            if not var_info.is_param:
                var_info.offset = local_offset
                local_offset -= TypeSystem.get_size(var_info.type)
        
        func_info.local_vars_size = abs(local_offset + 8)  # Общий размер локальных переменных
    
    def _collect_all_local_vars(self, symbol_table):
        """Собирает все локальные переменные из всех вложенных областей видимости"""
        all_vars = []
        
        def collect_from_table(table):
            for var_info in table.variables.values():
                if not var_info.is_param:
                    all_vars.append(var_info)
            # Рекурсивно проверяем дочерние таблицы символов
            # (если они хранятся в структуре)
        
        collect_from_table(symbol_table)
        return all_vars
    
    def _get_literal_type(self, literal: str) -> str:
        """Определяет тип литерала"""
        literal = literal.strip()
        
        if not literal:
            return "unknown"
        
        # Числовые литералы
        if self._is_number(literal):
            if '.' in literal:
                return 'float' if 'f' in literal.lower() else 'double'
            else:
                return 'int'
        
        # Символьные литералы (одинарные кавычки)
        if literal.startswith("'") and literal.endswith("'"):
            # Для char литералов содержимое должно быть длиной 1 или escape-последовательность
            if len(literal) == 3:  # Например, 'a'
                return 'char'
            elif len(literal) == 4 and literal[1] == '\\':  # Например, '\n'
                return 'char'
            else:
                # Неправильный char литерал
                return 'string'  # или выбросить ошибку
        
        # Строковые литералы (двойные кавычки)
        elif literal.startswith('"') and literal.endswith('"'):
            return 'string'
        
        # Булевы литералы
        elif literal.lower() in ['true', 'false']:
            return 'bool'
        
        return "unknown"