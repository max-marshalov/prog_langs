import re
from typing import List, Dict, Optional, Any, Set, Tuple
from control_flow import FunctionInfo, Operation, OperationType, VariableInfo, TypeSystem, BasicBlock

class WinX86AsmGenerator:
    """Генератор ассемблерного кода x86-64"""
    
    def __init__(self):
        self.string_constants: Dict[str, int] = {}
        self.next_const_id = 0
        self.var_offsets: Dict[str, int] = {}
        self.label_counter = 0
        self.functions: List[FunctionInfo] = []  # Список всех функций

    def _escape_string_for_nasm(self, string: str) -> str:
        """Экранирует строку для NASM, сохраняя строки как единые литералы"""
        if not string:
            return '0'
        
        
        
        
        def is_printable_ascii(char):
            code = ord(char)
            return 32 <= code <= 126  # Печатные ASCII
        
        def needs_escape_in_string(char):
            return char in ('"', '\\', '\n', '\r', '\t')
        
        
        can_be_single_literal = True
        for char in string:
            if not is_printable_ascii(char) or needs_escape_in_string(char):
                can_be_single_literal = False
                break
        
        if can_be_single_literal:
            
            escaped = string.replace('\\', '\\\\').replace('"', '\\"')
            return f'"{escaped}"'
        
        
        result_parts = []
        current_part = []
        
        i = 0
        while i < len(string):
            char = string[i]
            
            
            if is_printable_ascii(char) and not needs_escape_in_string(char):
                # Начинаем собирать группу печатных символов
                group_start = i
                while i < len(string) and is_printable_ascii(string[i]) and not needs_escape_in_string(string[i]):
                    current_part.append(string[i])
                    i += 1
                
                # Добавляем группу как единый литерал
                if current_part:
                    group_str = ''.join(current_part)
                    escaped = group_str.replace('\\', '\\\\').replace('"', '\\"')
                    result_parts.append(f'"{escaped}"')
                    current_part = []
                continue
            
            # Обработка специальных символов
            if char == '\n':
                # Для Windows: CR+LF
                result_parts.append('13')
                result_parts.append('10')
                i += 1
            elif char == '\r':
                # Проверяем следующий символ
                if i + 1 < len(string) and string[i + 1] == '\n':
                    # CR+LF
                    result_parts.append('13')
                    result_parts.append('10')
                    i += 2
                else:
                    # Одиночный CR
                    result_parts.append('13')
                    i += 1
            elif char == '\t':
                result_parts.append('9')
                i += 1
            elif char == '"':
                result_parts.append('"\\""')
                i += 1
            elif char == '\\':
                result_parts.append('"\\\\"')
                i += 1
            else:
                # Любой другой символ - выводим код
                result_parts.append(str(ord(char)))
                i += 1
        
        return ', '.join(result_parts)
    
    def generate_program(self, functions: List[FunctionInfo]) -> str:
        """Генерирует программу на основе реальных функций"""
        self.functions = functions  # Сохраняем список функций
        
        # Собираем все строковые константы
        for func in functions:
            self._collect_strings_from_function(func)
        
        asm_lines = [
            'default rel',
            'global main',
            'extern printf, scanf, exit, _getch',
            '',
            'section .data',
        ]
        
        # Добавляем строковые константы
        for string, const_id in sorted(self.string_constants.items(), key=lambda x: x[1]):
            nasm_string = self._escape_string_for_nasm(string)
            asm_lines.append(f'    str_{const_id} db {nasm_string}, 0')
        
        asm_lines.extend([
            '',
            'section .bss',
            '    ; Global variables',
            '',
            'section .text',
            ''
        ])
        
        # Генерируем все функции
        for func in functions:
            asm_lines.extend(self._generate_function_asm(func))
        
        return '\n'.join(asm_lines)
    
    def _collect_strings_from_function(self, func: FunctionInfo):
        """Собирает строковые константы из функции"""
        visited = set()
        stack = [func.cfg.entry_block]
        
        while stack:
            block = stack.pop()
            if block.id in visited:
                continue
            visited.add(block.id)
            
            for op in block.operations:
                if op.value and (op.value.startswith('"') or op.value.startswith("'")):
                    string_val = op.value.strip('"\'')
                    # Уже обработано escape-последовательности в парсере
                    if string_val not in self.string_constants:
                        self.string_constants[string_val] = self.next_const_id
                        self.next_const_id += 1
                
                if op.type == OperationType.CALL:
                    for arg_op in op.args:
                        if arg_op.value and (arg_op.value.startswith('"') or arg_op.value.startswith("'")):
                            string_val = arg_op.value.strip('"\'')
                            if string_val not in self.string_constants:
                                self.string_constants[string_val] = self.next_const_id
                                self.next_const_id += 1
            
            if block.next_block:
                stack.append(block.next_block)
            if block.true_branch:
                stack.append(block.true_branch)
            if block.false_branch:
                stack.append(block.false_branch)
    
    def _generate_function_asm(self, func: FunctionInfo) -> List[str]:
        """Генерирует ассемблерный код для функции на основе CFG"""

        
        # Собираем все переменные из таблицы символов
        local_vars = self._collect_local_variables(func)

        
        # Создаем смещения для переменных
        self.var_offsets = self._calculate_var_offsets(func, local_vars)
        
        asm_lines = [
            f'; {"="*50}',
            f'; Function: {func.name}',
            f'; Return type: {func.return_type}',
            f'; Local variables: {list(local_vars.keys())}',
            f'; {"="*50}',
            f'{func.name}:',
        ]
        
        # Пролог
        asm_lines.extend(self._generate_function_prologue(func, local_vars))
        
        # Генерируем код из CFG
        processed_blocks = set()
        asm_lines.extend(self._generate_cfg_code(func.cfg.entry_block, processed_blocks, func, local_vars))
        
        # Если не было выхода из функции, добавляем эпилог
        if not any(line.startswith(f'.{func.name}_exit') for line in asm_lines):
            asm_lines.extend(self._generate_function_epilogue(func))
        
        asm_lines.append('')
        
        return asm_lines
    
    def _collect_local_variables(self, func: FunctionInfo) -> Dict[str, str]:
        """Собирает все локальные переменные функции"""
        local_vars = {}
        
        # Сначала из таблицы символов функции
        if hasattr(func, 'symbol_table') and func.symbol_table:
            for var_name, var_info in func.symbol_table.variables.items():
                local_vars[var_name] = var_info.type  # Добавляем все переменные
        

        
        # Также из операций DECLARE в CFG
        if hasattr(func, 'cfg') and hasattr(func.cfg, 'entry_block'):
            visited = set()
            stack = [func.cfg.entry_block]
            
            while stack:
                block = stack.pop()
                if block.id in visited:
                    continue
                visited.add(block.id)
                
                for op in block.operations:
                    if op.type == OperationType.DECLARE and op.value:
                        var_name = op.value
                        # Очищаем имя переменной от -> type
                        var_name = self._clean_var_name(var_name)
                        var_type = op.var_type if op.var_type else 'int'
                        if var_name not in local_vars:
                            local_vars[var_name] = var_type
                
                if block.next_block:
                    stack.append(block.next_block)
                if block.true_branch:
                    stack.append(block.true_branch)
                if block.false_branch:
                    stack.append(block.false_branch)
        
        return local_vars
    
    def _clean_var_name(self, var_name: str) -> str:
        """Очищает имя переменной от -> type"""
        if not var_name:
            return var_name
        # Извлекаем только имя переменной до ->
        if '->' in var_name:
            return var_name.split('->')[0].strip()
        return var_name
    
    def _get_var_offset(self, var_name: str) -> Optional[int]:
        """Получает смещение переменной, очищая имя при необходимости"""
        clean_name = self._clean_var_name(var_name)
        return self.var_offsets.get(clean_name)
    
    def _calculate_var_offsets(self, func: FunctionInfo, local_vars: Dict[str, str]) -> Dict[str, int]:
        """Вычисляет смещения переменных в стеке с учетом параметров"""
        offsets = {}
        
        # Параметры: положительные смещения от RBP
        param_offset = 16  # RBP+16 - первый параметр в shadow space
        
        # Сначала параметры
        for param_name, param_type in func.parameters:
            clean_param = self._clean_var_name(param_name)
            if clean_param in local_vars:
                offsets[clean_param] = param_offset
                param_offset += 8  # Все параметры по 8 байт для выравнивания
        
        # Локальные переменные: отрицательные смещения от RBP
        local_offset = -8
        
        for var_name, var_type in local_vars.items():
            clean_name = self._clean_var_name(var_name)
            if clean_name not in offsets:  # Если не параметр
                offsets[clean_name] = local_offset
                # Увеличиваем смещение в зависимости от размера типа
                if var_type == 'char':
                    local_offset -= 1
                elif var_type == 'int':
                    local_offset -= 4
                elif var_type == 'float':
                    local_offset -= 4
                elif var_type == 'double':
                    local_offset -= 8
                elif var_type == 'string':
                    local_offset -= 8  # указатель
                else:
                    local_offset -= 4  # по умолчанию
        
        return offsets
    
    def _generate_function_prologue(self, func: FunctionInfo, local_vars: Dict[str, str]) -> List[str]:
        lines = [
            '    push rbp',
            '    mov rbp, rsp',
        ]
        
        # Выделяем место для локальных переменных
        # Минимальный размер стека для shadow space + локальные переменные
        stack_size = 32  # shadow space
        local_size = len(local_vars) * 8
        stack_size += local_size
        stack_size = ((stack_size + 15) // 16) * 16  # Выравнивание
        lines.append(f'    sub rsp, {stack_size}')
        
        # Сохраняем параметры из регистров в локальные переменные
        # Windows x64: rcx, rdx, r8, r9 - первые 4 параметра
        param_registers = ['rcx', 'rdx', 'r8', 'r9']
        
        for i, (param_name, param_type) in enumerate(func.parameters):
            clean_param = self._clean_var_name(param_name)
            if i < 4 and clean_param in local_vars:  # Первые 4 параметра в регистрах
                offset = self._get_var_offset(clean_param)
                if offset is not None:
                    if param_type == 'char':
                        lines.append(f'    mov [rbp{offset:+d}], cl ; save {clean_param}')
                    else:
                        lines.append(f'    mov [rbp{offset:+d}], {param_registers[i]} ; save {clean_param}')
        
        # Инициализируем локальные переменные (не параметры)
        for var_name, offset in self.var_offsets.items():
            # Проверяем, является ли переменная параметром
            is_param = any(self._clean_var_name(p[0]) == var_name for p in func.parameters)
            if not is_param:  # Не параметры
                var_type = local_vars.get(var_name, 'int')
                if var_type == 'char':
                    lines.append(f'    mov byte [rbp{offset:+d}], 0 ; {var_name} = 0')
                else:
                    lines.append(f'    mov dword [rbp{offset:+d}], 0 ; {var_name} = 0')
        
        return lines
    
    def _generate_function_epilogue(self, func: FunctionInfo) -> List[str]:
        """Генерирует эпилог функции"""
        exit_label = f'.{func.name}_exit'
        
        return [
            f'{exit_label}:',
            '    mov rsp, rbp',
            '    pop rbp',
            '    ret'
        ]
    
    def _generate_cfg_code(self, block: BasicBlock, processed: set, 
                          func: FunctionInfo, local_vars: Dict[str, str]) -> List[str]:
        """Генерирует код из CFG"""
        if not block or block.id in processed:
            return []
        
        processed.add(block.id)
        lines = []
        
        # Добавляем метку блока
        lines.append(f'.L{func.name}_block_{block.id}:')
        
        # Генерируем ВСЕ операции блока
        for op in block.operations:
            op_lines = self._generate_operation(op, func, local_vars)
            if op_lines:
                lines.extend(op_lines)
            else:
                lines.append(f'    ; No code generated for operation {op.type.name}')
        
        # Обрабатываем переходы
        jump_lines = self._generate_block_jumps(block, func)
        if jump_lines:
            lines.extend(jump_lines)
        
        # Рекурсивно обрабатываем связанные блоки
        if block.next_block and block.next_block.id not in processed:
            lines.extend(self._generate_cfg_code(block.next_block, processed, func, local_vars))
        if block.true_branch and block.true_branch.id not in processed:
            lines.extend(self._generate_cfg_code(block.true_branch, processed, func, local_vars))
        if block.false_branch and block.false_branch.id not in processed:
            lines.extend(self._generate_cfg_code(block.false_branch, processed, func, local_vars))
        
        return lines
    
    def _generate_block_jumps(self, block: BasicBlock, func: FunctionInfo) -> List[str]:
        """Генерирует переходы в конце блока"""
        lines = []
        
        if block.next_block:
            lines.append(f'    jmp .L{func.name}_block_{block.next_block.id}')
        elif block.true_branch and block.false_branch:
            # Нужно определить, какой тип перехода нужен
            # Проверяем последнюю операцию в блоке
            if block.operations:
                last_op = block.operations[-1]
                
                # Если последняя операция - сравнение (EQ, NE, LT и т.д.)
                if last_op.type in [OperationType.EQ, OperationType.NE, OperationType.LT, 
                                OperationType.LE, OperationType.GT, OperationType.GE]:
                    # Используем условные переходы после cmp
                    true_label = f'.L{func.name}_block_{block.true_branch.id}'
                    false_label = f'.L{func.name}_block_{block.false_branch.id}'
                    
                    # Выбираем правильную инструкцию перехода в зависимости от типа операции
                    if last_op.type == OperationType.EQ:
                        lines.append(f'    je {true_label}  ; jump if equal')
                    elif last_op.type == OperationType.NE:
                        lines.append(f'    jne {true_label} ; jump if not equal')
                    elif last_op.type == OperationType.LT:
                        lines.append(f'    jl {true_label}  ; jump if less')
                    elif last_op.type == OperationType.LE:
                        lines.append(f'    jle {true_label} ; jump if less or equal')
                    elif last_op.type == OperationType.GT:
                        lines.append(f'    jg {true_label}  ; jump if greater')
                    elif last_op.type == OperationType.GE:
                        lines.append(f'    jge {true_label} ; jump if greater or equal')
                    
                    lines.append(f'    jmp {false_label}')
                else:
                    # Для других условий (например, while(1)) используем test
                    true_label = f'.L{func.name}_block_{block.true_branch.id}'
                    false_label = f'.L{func.name}_block_{block.false_branch.id}'
                    lines.append('    test eax, eax  ; test condition')
                    lines.append(f'    jnz {true_label}  ; jump if true')
                    lines.append(f'    jmp {false_label} ; jump if false')
            else:
                # Если нет операций, используем test по умолчанию
                true_label = f'.L{func.name}_block_{block.true_branch.id}'
                false_label = f'.L{func.name}_block_{block.false_branch.id}'
                lines.append('    test eax, eax  ; test condition')
                lines.append(f'    jnz {true_label}  ; jump if true')
                lines.append(f'    jmp {false_label} ; jump if false')
        
        elif block.true_branch:
            lines.append(f'    jmp .L{func.name}_block_{block.true_branch.id}')
        elif block.false_branch:
            lines.append(f'    jmp .L{func.name}_block_{block.false_branch.id}')
        
        return lines
    
    def _generate_operation(self, op: Operation, func: FunctionInfo, 
                       local_vars: Dict[str, str]) -> List[str]:
        """Генерирует код для одной операции"""
        lines = []
        
        if op.type == OperationType.DECLARE:
            var_name = op.value or "?"
            clean_name = self._clean_var_name(var_name)
            offset = self._get_var_offset(clean_name)
            lines.append(f'    ; Variable {clean_name} declared at [rbp{offset:+d}]')
        
        elif op.type == OperationType.CALL:
            func_name = op.value or "?"
            lines.append(f'    ; Call {func_name}')
            
            # Проверяем, стандартная ли это функция
            is_standard = func_name in ['printf', 'scanf', 'exit', '_getch']
            
            if is_standard:
                # Стандартные функции
                arg_code = self._prepare_standard_function_args(op, func_name, local_vars)
                if arg_code:
                    lines.extend(arg_code)
                    lines.append('    sub rsp, 32  ; shadow space')
                    lines.append(f'    call {func_name}')
                    lines.append('    add rsp, 32')
            else:
                # Пользовательские функции
                arg_code = self._prepare_user_function_args(op, func_name, local_vars)
                if arg_code:
                    lines.extend(arg_code)
                lines.append('    sub rsp, 32 ; shadow space')
                lines.append(f'    call {func_name}')
                lines.append('    add rsp, 32')
        
        elif op.type == OperationType.NOOP:
            if op.value == '1':
                lines.append('    mov eax, 1  ; while(1) condition')
            elif op.value:
                clean_value = self._clean_var_name(op.value)
                if clean_value in local_vars:
                    # Загрузка значения переменной в eax
                    offset = self._get_var_offset(clean_value)
                    if offset is not None:
                        lines.append(f'    mov eax, [rbp{offset:+d}] ; load {clean_value}')
        
        elif op.type == OperationType.EQ:
            # Генерация кода для сравнения
            compare_code = self._generate_compare_code(op, func, local_vars)
            if compare_code:
                lines.extend(compare_code)
        
        elif op.type == OperationType.ASSIGN:
            # Генерация кода для присваивания
            assign_code = self._generate_assign_code(op, func, local_vars)
            if assign_code:
                lines.extend(assign_code)
        
        elif op.type == OperationType.SUB:
            # Генерация кода для операции вычитания (может быть отдельной операцией)
            
            # Если это отдельная операция (не часть присваивания), генерируем код
            sub_code = self._generate_arithmetic_code(op, func, local_vars)
            if sub_code:
                lines.extend(sub_code)
        
        elif op.type in [OperationType.ADD, OperationType.MUL, OperationType.DIV]:
            # Генерация кода для арифметических операций
            arith_code = self._generate_arithmetic_code(op, func, local_vars)
            if arith_code:
                lines.extend(arith_code)

        elif op.type == OperationType.RETURN:
            # Генерация кода для возврата
            return_code = self._generate_return_code(op, func, local_vars)
            if return_code:
                lines.extend(return_code)
        
        else:
            lines.append(f'    ; Unsupported operation type: {op.type.name}')
        
        return lines
        
    def _generate_return_code(self, op: Operation, func: FunctionInfo,
                         local_vars: Dict[str, str]) -> List[str]:
        """Генерирует код для операции возврата"""
        lines = []
        

        
        if op and op.left:
            # Есть возвращаемое значение
            if op.left.type == OperationType.ADD:
                # Это выражение типа fib(t1) + fib(t2)
                
                # Левый операнд - fib(t1)
                left_operand = op.left.left
                # Правый операнд - fib(t2)
                right_operand = op.left.right
                
                if left_operand and right_operand:
                    
                    # Генерируем код для левого вызова (fib(t1))
                    if left_operand.type == OperationType.CALL:
                        func_name = left_operand.value
                        
                        # Подготавливаем аргументы
                        if left_operand.args:
                            arg_op = left_operand.args[0]
                            arg_value = arg_op.value if hasattr(arg_op, 'value') else None
                            clean_arg = self._clean_var_name(arg_value)
                            
                            # Загружаем аргумент
                            arg_offset = self._get_var_offset(clean_arg)
                            if arg_offset is not None:
                                lines.append(f'    mov ecx, [rbp{arg_offset:+d}] ; load {clean_arg} for {func_name}')
                        
                        # Вызываем функцию
                        lines.append('    sub rsp, 32 ; shadow space')
                        lines.append(f'    call {func_name}')
                        lines.append('    add rsp, 32')
                        
                        # Сохраняем результат
                        lines.append('    push rax ; save result of left call')
                    
                    # Генерируем код для правого вызова (fib(t2))
                    if right_operand.type == OperationType.CALL:
                        func_name = right_operand.value
                        
                        # Подготавливаем аргументы
                        if right_operand.args:
                            arg_op = right_operand.args[0]
                            arg_value = arg_op.value if hasattr(arg_op, 'value') else None
                            clean_arg = self._clean_var_name(arg_value)
                            
                            # Загружаем аргумент
                            arg_offset = self._get_var_offset(clean_arg)
                            if arg_offset is not None:
                                lines.append(f'    mov ecx, [rbp{arg_offset:+d}] ; load {clean_arg} for {func_name}')
                        
                        # Вызываем функцию
                        lines.append('    sub rsp, 32 ; shadow space')
                        lines.append(f'    call {func_name}')
                        lines.append('    add rsp, 32')
                        
                        # Результат в ebx
                        lines.append('    mov ebx, eax ; save result of right call')
                    
                    # Восстанавливаем левый результат и складываем
                    if left_operand and left_operand.type == OperationType.CALL:
                        lines.append('    pop rax ; restore left result')
                        lines.append('    add eax, ebx ; add both results')
            
            elif op.left.type == OperationType.NOOP and op.left.value:
                # Простой возврат n
                value = op.left.value
                clean_value = self._clean_var_name(value)
                offset = self._get_var_offset(clean_value)
                if offset is not None:
                    lines.append(f'    mov eax, [rbp{offset:+d}] ; load {clean_value}')
                elif value.isdigit():
                    lines.append(f'    mov eax, {value}')
        
        lines.append(f'    jmp .{func.name}_exit')
        return lines
    
    def _contains_function_call(self, op: Operation) -> bool:
        """Проверяет, содержит ли выражение вызов функции"""
        if op.type == OperationType.CALL:
            return True
        
        if op.left and self._contains_function_call(op.left):
            return True
        
        if op.right and self._contains_function_call(op.right):
            return True
        
        return False
    
    def _prepare_standard_function_args(self, op: Operation, func_name: str, 
                                     local_vars: Dict[str, str]) -> List[str]:
        """Подготавливает аргументы для стандартных функций (printf, scanf)"""
        lines = []
        arg_registers = ['rcx', 'rdx', 'r8', 'r9']
        
        for i, arg_op in enumerate(op.args[:4]):
            if i >= len(arg_registers):
                break
                
            if arg_op.type == OperationType.NOOP and arg_op.value:
                value = arg_op.value
                clean_value = self._clean_var_name(value)
                
                # Строковый литерал
                if value.startswith('"') or value.startswith("'"):
                    string_val = value.strip('"\'')
                    const_id = self.string_constants.get(string_val)
                    if const_id is not None:
                        lines.append(f'    lea {arg_registers[i]}, [str_{const_id}]')
                
                # Переменная
                elif clean_value in local_vars:
                    offset = self._get_var_offset(clean_value)
                    if offset is not None:
                        # Для scanf передаем адреса
                        if func_name == 'scanf' and i >= 1:
                            lines.append(f'    lea {arg_registers[i]}, [rbp{offset:+d}] ; &{clean_value}')
                        else:
                            # Для других функций передаем значения
                            lines.append(f'    mov {arg_registers[i]}, [rbp{offset:+d}] ; {clean_value}')
                
                # Числовой литерал
                elif value.isdigit():
                    lines.append(f'    mov {arg_registers[i]}, {value}')
        
        return lines
    
    def _prepare_user_function_args(self, op: Operation, func_name: str,
                                 local_vars: Dict[str, str]) -> List[str]:
        """Подготавливает аргументы для пользовательских функций"""
        lines = []
        arg_registers = ['rcx', 'rdx', 'r8', 'r9']
        
        for i, arg_op in enumerate(op.args[:4]):
            if i >= len(arg_registers):
                break
                
            if arg_op.type == OperationType.NOOP and arg_op.value:
                value = arg_op.value
                clean_value = self._clean_var_name(value)
                
                # Переменная
                if clean_value in local_vars:
                    offset = self._get_var_offset(clean_value)
                    if offset is not None:
                        lines.append(f'    mov {arg_registers[i]}, [rbp{offset:+d}] ; {clean_value}')
                
                # Числовой литерал
                elif value.isdigit():
                    lines.append(f'    mov {arg_registers[i]}, {value}')
        
        return lines
    
    def _generate_compare_code(self, op: Operation, func: FunctionInfo, 
                          local_vars: Dict[str, str]) -> List[str]:
        """Генерирует код для операции сравнения"""
        lines = []
        
        if op.left and op.right:
            left_var = op.left.value if hasattr(op.left, 'value') else None
            right_val = op.right.value if hasattr(op.right, 'value') else None
            
            if left_var and right_val:
                clean_left = self._clean_var_name(left_var)
                offset = self._get_var_offset(clean_left)
                if offset is not None:
                    # Загружаем переменную
                    lines.append(f'    mov eax, [rbp{offset:+d}] ; load {clean_left}')
                    
                    # Сравниваем с значением
                    if right_val.isdigit():
                        lines.append(f'    cmp eax, {right_val} ; compare with {right_val}')
                    elif right_val.startswith("'") and right_val.endswith("'"):
                        char_val = right_val.strip("'")
                        if char_val:
                            ascii_code = ord(char_val)
                            lines.append(f'    cmp eax, {ascii_code} ; compare with {right_val}')
        
        return lines

    def _generate_assign_code(self, op: Operation, func: FunctionInfo,
                            local_vars: Dict[str, str]) -> List[str]:
        """Генерирует код для операции присваивания"""
        lines = []
        

        
        if op.left and op.right:
            # Целевая переменная
            dest_var_full = op.left.value if hasattr(op.left, 'value') else None
            dest_var = self._clean_var_name(dest_var_full)
            
            
            # Если правая часть - вызов функции
            if op.right.type == OperationType.CALL:
                func_name = op.right.value
                
                # Подготавливаем аргументы
                if func_name in ['printf', 'scanf', 'exit', '_getch']:
                    arg_code = self._prepare_standard_function_args(op.right, func_name, local_vars)
                else:
                    arg_code = self._prepare_user_function_args(op.right, func_name, local_vars)
                
                if arg_code:
                    lines.extend(arg_code)
                
                # Вызов функции
                if func_name in ['printf', 'scanf', 'exit', '_getch']:
                    lines.append('    sub rsp, 32  ; shadow space')
                    lines.append(f'    call {func_name}')
                    lines.append('    add rsp, 32')
                else:
                    lines.append('    sub rsp, 32 ; shadow space')
                    lines.append(f'    call {func_name}')
                    lines.append('    add rsp, 32')
                
                # Сохраняем результат
                if dest_var:
                    dest_offset = self._get_var_offset(dest_var)
                    if dest_offset is not None:
                        lines.append(f'    mov [rbp{dest_offset:+d}], eax ; {dest_var} = результат')
            
            # Если правая часть - операция вычитания (n - 1)
            elif op.right.type == OperationType.SUB:
                
                # Генерируем код для вычитания
                sub_lines = self._generate_arithmetic_code(op.right, func, local_vars)
                if sub_lines:
                    lines.extend(sub_lines)
                    # Сохраняем результат в целевую переменную
                    if dest_var:
                        dest_offset = self._get_var_offset(dest_var)
                        if dest_offset is not None:
                            lines.append(f'    mov [rbp{dest_offset:+d}], eax ; store {dest_var}')
                else:
                    # Альтернативная реализация
                    if op.right.left and op.right.right:
                        left_val = op.right.left.value if hasattr(op.right.left, 'value') else None
                        right_val = op.right.right.value if hasattr(op.right.right, 'value') else None
                        
                        
                        # Загружаем левый операнд
                        if left_val:
                            clean_left = self._clean_var_name(left_val)
                            if clean_left in local_vars:
                                left_offset = self._get_var_offset(clean_left)
                                if left_offset is not None:
                                    lines.append(f'    mov eax, [rbp{left_offset:+d}] ; load {clean_left}')
                            elif left_val.isdigit():
                                lines.append(f'    mov eax, {left_val}')
                        
                        # Вычитаем правый операнд
                        if right_val:
                            if right_val.isdigit():
                                lines.append(f'    sub eax, {right_val} ; subtract {right_val}')
                            else:
                                clean_right = self._clean_var_name(right_val)
                                if clean_right in local_vars:
                                    right_offset = self._get_var_offset(clean_right)
                                    if right_offset is not None:
                                        lines.append(f'    sub eax, [rbp{right_offset:+d}] ; subtract {clean_right}')
                        
                        # Сохраняем результат
                        if dest_var:
                            dest_offset = self._get_var_offset(dest_var)
                            if dest_offset is not None:
                                lines.append(f'    mov [rbp{dest_offset:+d}], eax ; store in {dest_var}')
            
            # Если правая часть - другая арифметическая операция
            elif op.right.type in [OperationType.ADD, OperationType.MUL, OperationType.DIV]:
                # Проверяем, содержит ли выражение вызовы функций
                if self._contains_function_call(op.right):
                    # Сложное выражение с вызовами
                    expr_lines = self._generate_expression_with_calls(op.right, func, local_vars)
                    lines.extend(expr_lines)
                else:
                    # Простое арифметическое выражение
                    arith_code = self._generate_arithmetic_code(op.right, func, local_vars)
                    if arith_code:
                        lines.extend(arith_code)
                
                # Сохраняем результат
                if dest_var:
                    dest_offset = self._get_var_offset(dest_var)
                    if dest_offset is not None:
                        lines.append(f'    mov [rbp{dest_offset:+d}], eax ; store in {dest_var}')
        
        return lines

    def _generate_arithmetic_code(self, op: Operation, func: FunctionInfo,
                                local_vars: Dict[str, str]) -> List[str]:
        """Генерирует код для арифметической операции"""
        lines = []
        
        if not op.left or not op.right:
            return lines
        
        left_var = op.left.value if hasattr(op.left, 'value') else None
        right_var = op.right.value if hasattr(op.right, 'value') else None
        

        
        # Загружаем левый операнд
        if left_var:
            clean_left = self._clean_var_name(left_var)
            if clean_left in local_vars:
                offset = self._get_var_offset(clean_left)
                if offset is not None:
                    lines.append(f'    mov eax, [rbp{offset:+d}] ; load {clean_left}')
        elif left_var and left_var.isdigit():
            lines.append(f'    mov eax, {left_var}')
        
        # Загружаем правый операнд
        if right_var:
            clean_right = self._clean_var_name(right_var)
            if clean_right in local_vars:
                offset = self._get_var_offset(clean_right)
                if offset is not None:
                    if op.type == OperationType.ADD:
                        lines.append(f'    add eax, [rbp{offset:+d}] ; add {clean_right}')
                    elif op.type == OperationType.SUB:
                        lines.append(f'    sub eax, [rbp{offset:+d}] ; subtract {clean_right}')
                    elif op.type == OperationType.MUL:
                        lines.append(f'    imul eax, [rbp{offset:+d}] ; multiply by {clean_right}')
                    elif op.type == OperationType.DIV:
                        lines.append(f'    cdq')  # Расширяем eax в edx:eax
                        lines.append(f'    idiv dword [rbp{offset:+d}] ; divide by {clean_right}')
            elif right_var and right_var.isdigit():
                if op.type == OperationType.ADD:
                    lines.append(f'    add eax, {right_var}')
                elif op.type == OperationType.SUB:
                    lines.append(f'    sub eax, {right_var}')
                elif op.type == OperationType.MUL:
                    lines.append(f'    imul eax, {right_var}')
                elif op.type == OperationType.DIV:
                    lines.append(f'    mov ebx, {right_var}')
                    lines.append('    cdq')
                    lines.append('    idiv ebx')
        
        return lines
    
    def _generate_expression_with_calls(self, op: Operation, func: FunctionInfo,
                                      local_vars: Dict[str, str]) -> List[str]:
        """Генерирует код для выражения, которое может содержать вызовы функций"""
        lines = []
        

        
        if op.type in [OperationType.ADD, OperationType.SUB, OperationType.MUL, OperationType.DIV]:
            # Сначала вычисляем левую часть
            if op.left:
                if self._contains_function_call(op.left):
                    left_lines = self._generate_expression_with_calls(op.left, func, local_vars)
                    lines.extend(left_lines)
                elif op.left.type == OperationType.NOOP and op.left.value:
                    # Переменная или константа
                    value = op.left.value
                    clean_value = self._clean_var_name(value)
                    if clean_value in local_vars:
                        offset = self._get_var_offset(clean_value)
                        if offset is not None:
                            lines.append(f'    mov eax, [rbp{offset:+d}] ; load {clean_value}')
                    elif value.isdigit():
                        lines.append(f'    mov eax, {value}')
                
                # Сохраняем результат левой части
                lines.append('    push rax ; save left result')
            
            # Затем вычисляем правую часть
            if op.right:
                if op.right.type == OperationType.CALL:
                    # Вызов функции в правой части
                    func_name = op.right.value
                    lines.append(f'    ; Calling {func_name} in expression')
                    
                    # Подготавливаем аргументы
                    if func_name in ['printf', 'scanf', 'exit', '_getch']:
                        arg_code = self._prepare_standard_function_args(op.right, func_name, local_vars)
                    else:
                        arg_code = self._prepare_user_function_args(op.right, func_name, local_vars)
                    
                    if arg_code:
                        lines.extend(arg_code)
                    
                    # Вызываем функцию
                    if func_name in ['printf', 'scanf', 'exit', '_getch']:
                        lines.append('    sub rsp, 32 ; shadow space')
                        lines.append(f'    call {func_name}')
                        lines.append('    add rsp, 32')
                    else:
                        lines.append(f'    call {func_name}')
                    
                    # Результат функции в eax
                    lines.append('    mov ebx, eax ; save function result')
                elif self._contains_function_call(op.right):
                    right_lines = self._generate_expression_with_calls(op.right, func, local_vars)
                    lines.extend(right_lines)
                    lines.append('    mov ebx, eax ; save function result')
                elif op.right.type == OperationType.NOOP and op.right.value:
                    # Переменная или константа
                    value = op.right.value
                    clean_value = self._clean_var_name(value)
                    if clean_value in local_vars:
                        offset = self._get_var_offset(clean_value)
                        if offset is not None:
                            lines.append(f'    mov ebx, [rbp{offset:+d}] ; load {clean_value}')
                    elif value.isdigit():
                        lines.append(f'    mov ebx, {value}')
            
            # Восстанавливаем левую часть и выполняем операцию
            if op.left:
                lines.append('    pop rax ; restore left result')
            
            # Выполняем арифметическую операцию
            if op.type == OperationType.ADD:
                lines.append('    add eax, ebx')
            elif op.type == OperationType.SUB:
                lines.append('    sub eax, ebx')
            elif op.type == OperationType.MUL:
                lines.append('    imul eax, ebx')
            elif op.type == OperationType.DIV:
                lines.append('    cdq')
                lines.append('    idiv ebx')
        
        elif op.type == OperationType.CALL:
            # Генерируем вызов функции
            func_name = op.value or "?"
            lines.append(f'    ; Call {func_name} from expression')
            
            # Подготавливаем аргументы
            if func_name in ['printf', 'scanf', 'exit', '_getch']:
                arg_code = self._prepare_standard_function_args(op, func_name, local_vars)
            else:
                arg_code = self._prepare_user_function_args(op, func_name, local_vars)
            
            if arg_code:
                lines.extend(arg_code)
            
            # Вызываем функцию
            if func_name in ['printf', 'scanf', 'exit', '_getch']:
                lines.append('    sub rsp, 32  ; shadow space')
                lines.append(f'    call {func_name}')
                lines.append('    add rsp, 32')
            else:
                lines.append(f'    call {func_name}')
        
        return lines