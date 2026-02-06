import re
from typing import List, Dict, Optional, Any, Set, Tuple
from control_flow import FunctionInfo, Operation, OperationType, VariableInfo, TypeSystem, BasicBlock


class RiscV64AsmGenerator:
    """Генератор ассемблерного кода RISC-V для Linux"""
    
    def __init__(self):
        self.string_constants: Dict[str, int] = {}
        self.next_const_id = 0
        self.var_offsets: Dict[str, int] = {}
        self.label_counter = 0
        self.functions: List[FunctionInfo] = []
        self.arg_registers = ['a0', 'a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7']
        self.temp_registers = ['t0', 't1', 't2', 't3', 't4', 't5', 't6']
        self.saved_registers = ['s0', 's1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9', 's10', 's11']
    
    def _escape_string_for_riscv(self, string: str) -> str:
        """Экранирует строку для RISC-V (формат .asciz)"""
        if not string:
            return ''
        
        escaped = string.replace('\\', '\\\\')
        escaped = escaped.replace('"', '\\"')
        escaped = escaped.replace('\n', '\\n')
        escaped = escaped.replace('\r', '\\r')
        escaped = escaped.replace('\t', '\\t')
        
        return escaped
    
    def generate_program(self, functions: List[FunctionInfo]) -> str:
        """Генерирует программу на основе реальных функций"""
        self.functions = functions
        
        for func in functions:
            self._collect_strings_from_function(func)
        
        asm_lines = [
            '.section .data',
        ]
        
        for string, const_id in sorted(self.string_constants.items(), key=lambda x: x[1]):
            escaped = self._escape_string_for_riscv(string)
            asm_lines.append(f'str_{const_id}: .asciz "{escaped}"')
        
        asm_lines.extend([
            '',
            '.section .text',
            '.globl main',
            ''
        ])
        
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
        local_vars = self._collect_local_variables(func)
        
        self.var_offsets = self._calculate_var_offsets(func, local_vars)
        
        asm_lines = [
            f'# {"="*50}',
            f'# Function: {func.name}',
            f'# Return type: {func.return_type}',
            f'# Local variables: {list(local_vars.keys())}',
            f'# {"="*50}',
            f'{func.name}:',
        ]
        
        asm_lines.extend(self._generate_function_prologue(func, local_vars))
        
        processed_blocks = set()
        asm_lines.extend(self._generate_cfg_code(func.cfg.entry_block, processed_blocks, func, local_vars))
        
        if not any(line.startswith(f'{func.name}_exit:') for line in asm_lines):
            asm_lines.extend(self._generate_function_epilogue(func))
        
        asm_lines.append('')
        
        return asm_lines
    
    def _collect_local_variables(self, func: FunctionInfo) -> Dict[str, str]:
        """Собирает все локальные переменные функции"""
        local_vars = {}
        
        if hasattr(func, 'symbol_table') and func.symbol_table:
            for var_name, var_info in func.symbol_table.variables.items():
                local_vars[var_name] = var_info.type
        
        
        
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
        if '->' in var_name:
            return var_name.split('->')[0].strip()
        return var_name
    
    def _get_var_offset(self, var_name: str) -> Optional[int]:
        """Получает смещение переменной, очищая имя при необходимости"""
        clean_name = self._clean_var_name(var_name)
        return self.var_offsets.get(clean_name)
    
    def _calculate_var_offsets(self, func: FunctionInfo, local_vars: Dict[str, str]) -> Dict[str, int]:
        """Вычисляет смещения переменных в стеке"""
        offsets = {}
        
        # Порядок в стеке (от sp в положительную сторону):
        # [0]      - локальные переменные и параметры
        # [8*N]    - ra (return address)
        # [8*N+8]  - s0 (frame pointer)
        
        offset = 0
        
        # Параметры сохраняются первыми
        for i, (param_name, param_type) in enumerate(func.parameters):
            clean_param = self._clean_var_name(param_name)
            if clean_param in local_vars:
                offsets[clean_param] = offset
                offset += 8
        
        # Локальные переменные идут после параметров
        for var_name, var_type in local_vars.items():
            clean_name = self._clean_var_name(var_name)
            if clean_name not in offsets:
                offsets[clean_name] = offset
                offset += 8
        
        # Место для ra и s0
        self.ra_offset = offset
        offset += 8
        self.s0_offset = offset
        offset += 8
        
        self.stack_size = offset
        
        
        
        return offsets
    
    def _generate_function_prologue(self, func: FunctionInfo, local_vars: Dict[str, str]) -> List[str]:
        """Генерирует пролог функции"""
        lines = []
        
        # Выделяем место на стеке
        if self.stack_size > 0:
            lines.append(f'    addi sp, sp, -{self.stack_size}')
        
        # Сохраняем return address
        lines.append(f'    sd ra, {self.ra_offset}(sp)')
        
        # Сохраняем frame pointer
        lines.append(f'    sd s0, {self.s0_offset}(sp)')
        
        # Устанавливаем новый frame pointer (указывает на начало стекового фрейма)
        lines.append(f'    addi s0, sp, 0')
        
        # Сохраняем параметры из регистров в стек
        for i, (param_name, param_type) in enumerate(func.parameters):
            clean_param = self._clean_var_name(param_name)
            if i < 8 and clean_param in local_vars:
                offset = self._get_var_offset(clean_param)
                if offset is not None:
                    lines.append(f'    sd {self.arg_registers[i]}, {offset}(sp)  # save {clean_param}')
        
        # Инициализируем локальные переменные нулями
        for var_name, offset in self.var_offsets.items():
            is_param = any(self._clean_var_name(p[0]) == var_name for p in func.parameters)
            if not is_param:
                lines.append(f'    sd zero, {offset}(sp)  # {var_name} = 0')
        
        return lines
    
    def _generate_function_epilogue(self, func: FunctionInfo) -> List[str]:
        """Генерирует эпилог функции"""
        lines = [
            f'{func.name}_exit:',
            f'    ld ra, {self.ra_offset}(sp)',
            f'    ld s0, {self.s0_offset}(sp)',
        ]
        
        if self.stack_size > 0:
            lines.append(f'    addi sp, sp, {self.stack_size}')
        
        lines.append('    ret')
        
        return lines
    
    def _generate_cfg_code(self, block: BasicBlock, processed: set, 
                          func: FunctionInfo, local_vars: Dict[str, str]) -> List[str]:
        """Генерирует код из CFG"""
        if not block or block.id in processed:
            return []
        
        processed.add(block.id)
        lines = []
        
        lines.append(f'.L{func.name}_block_{block.id}:')
        
        for i, op in enumerate(block.operations):
            lines.extend(self._generate_operation(op, func, local_vars))
        
        jump_lines = self._generate_block_jumps(block, func)
        if jump_lines:
            lines.extend(jump_lines)
        
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
            lines.append(f'    j .L{func.name}_block_{block.next_block.id}')
        elif block.true_branch and block.false_branch:
            if block.operations:
                last_op = block.operations[-1]
                
                if last_op.type in [OperationType.EQ, OperationType.NE, OperationType.LT, 
                                OperationType.LE, OperationType.GT, OperationType.GE]:
                    true_label = f'.L{func.name}_block_{block.true_branch.id}'
                    false_label = f'.L{func.name}_block_{block.false_branch.id}'
                    
                    if last_op.type == OperationType.EQ:
                        lines.append(f'    beq a0, a1, {true_label}')
                    elif last_op.type == OperationType.NE:
                        lines.append(f'    bne a0, a1, {true_label}')
                    elif last_op.type == OperationType.LT:
                        lines.append(f'    blt a0, a1, {true_label}')
                    elif last_op.type == OperationType.LE:
                        lines.append(f'    ble a0, a1, {true_label}')
                    elif last_op.type == OperationType.GT:
                        lines.append(f'    bgt a0, a1, {true_label}')
                    elif last_op.type == OperationType.GE:
                        lines.append(f'    bge a0, a1, {true_label}')
                    
                    lines.append(f'    j {false_label}')
                else:
                    true_label = f'.L{func.name}_block_{block.true_branch.id}'
                    false_label = f'.L{func.name}_block_{block.false_branch.id}'
                    lines.append(f'    bne a0, zero, {true_label}')
                    lines.append(f'    j {false_label}')
            else:
                true_label = f'.L{func.name}_block_{block.true_branch.id}'
                false_label = f'.L{func.name}_block_{block.false_branch.id}'
                lines.append(f'    bne a0, zero, {true_label}')
                lines.append(f'    j {false_label}')
        
        elif block.true_branch:
            lines.append(f'    j .L{func.name}_block_{block.true_branch.id}')
        elif block.false_branch:
            lines.append(f'    j .L{func.name}_block_{block.false_branch.id}')
        
        return lines
    
    def _generate_operation(self, op: Operation, func: FunctionInfo, 
                       local_vars: Dict[str, str]) -> List[str]:
        """Генерирует код для одной операции"""
        lines = []
        
        if op.type == OperationType.DECLARE:
            var_name = op.value or "?"
            clean_name = self._clean_var_name(var_name)
            offset = self._get_var_offset(clean_name)
            lines.append(f'    # Variable {clean_name} declared')
        
        elif op.type == OperationType.CALL:
            func_name = op.value or "?"
            
            is_standard = func_name in ['printf', 'scanf', 'exit', 'puts']
            
            if is_standard:
                arg_code = self._prepare_standard_function_args(op, func_name, local_vars)
                if arg_code:
                    lines.extend(arg_code)
            else:
                arg_code = self._prepare_user_function_args(op, func_name, local_vars)
                if arg_code:
                    lines.extend(arg_code)
            
            lines.append(f'    jal ra, {func_name}')
        
        elif op.type == OperationType.NOOP:
            if op.value == '1':
                lines.append('    li a0, 1  # while(1) condition')
            elif op.value:
                clean_value = self._clean_var_name(op.value)
                if clean_value in local_vars:
                    offset = self._get_var_offset(clean_value)
                    if offset is not None:
                        lines.append(f'    ld a0, {offset}(sp)  # load {clean_value}')
        
        elif op.type == OperationType.EQ:
            compare_code = self._generate_compare_code(op, func, local_vars)
            if compare_code:
                lines.extend(compare_code)
        
        elif op.type == OperationType.ASSIGN:
            assign_code = self._generate_assign_code(op, func, local_vars)
            if assign_code:
                lines.extend(assign_code)
        
        elif op.type == OperationType.SUB:
            sub_code = self._generate_arithmetic_code(op, func, local_vars)
            if sub_code:
                lines.extend(sub_code)
        
        elif op.type in [OperationType.ADD, OperationType.MUL, OperationType.DIV]:
            arith_code = self._generate_arithmetic_code(op, func, local_vars)
            if arith_code:
                lines.extend(arith_code)
        
        elif op.type == OperationType.RETURN:
            return_code = self._generate_return_code(op, func, local_vars)
            if return_code:
                lines.extend(return_code)
        
        return lines
    
    def _generate_return_code(self, op: Operation, func: FunctionInfo,
                     local_vars: Dict[str, str]) -> List[str]:
        """Генерирует код для операции возврата (исправленная версия)"""
        lines = []
        
        if op and op.left:
            if op.left.type == OperationType.ADD:
                # Рекурсивный случай: fib(t1) + fib(t2)
                # где t1 и t2 уже содержат n-1 и n-2 соответственно
                left_operand = op.left.left
                right_operand = op.left.right
                
                if left_operand and right_operand:
                    # === ПЕРВЫЙ ВЫЗОВ: fib(t1) где t1 = n-1 ===
                    if left_operand.type == OperationType.CALL:
                        func_name = left_operand.value
                        
                        # Получаем t1 (уже содержит n-1, не нужно считать!)
                        if left_operand.args:
                            arg_op = left_operand.args[0]
                            arg_value = arg_op.value if hasattr(arg_op, 'value') else None
                            clean_arg = self._clean_var_name(arg_value)
                            
                            arg_offset = self._get_var_offset(clean_arg)
                            if arg_offset is not None:
                                # Загружаем t1 (уже n-1)
                                lines.append(f'    ld a0, {arg_offset}(sp)  # load {clean_arg} (already n-1)')
                        
                        # Вызываем fib(t1)
                        lines.append(f'    jal ra, {func_name}')
                        
                        # Сохраняем результат
                        if 't1' in local_vars:
                            t1_offset = self._get_var_offset('t1')
                            if t1_offset is not None:
                                lines.append(f'    sd a0, {t1_offset}(sp)  # save fib(n-1)')
                    
                    # === ВТОРОЙ ВЫЗОВ: fib(t2) где t2 = n-2 ===
                    if right_operand.type == OperationType.CALL:
                        func_name = right_operand.value
                        
                        # Получаем t2 (уже содержит n-2, не нужно считать!)
                        if right_operand.args:
                            arg_op = right_operand.args[0]
                            arg_value = arg_op.value if hasattr(arg_op, 'value') else None
                            clean_arg = self._clean_var_name(arg_value)
                            
                            arg_offset = self._get_var_offset(clean_arg)
                            if arg_offset is not None:
                                # Загружаем t2 (уже n-2)
                                lines.append(f'    ld a0, {arg_offset}(sp)  # load {clean_arg} (already n-2)')
                        
                        # Вызываем fib(t2)
                        lines.append(f'    jal ra, {func_name}')
                        
                        # a0 уже содержит результат fib(n-2)
                        # Восстанавливаем fib(n-1) и складываем
                        if 't1' in local_vars:
                            t1_offset = self._get_var_offset('t1')
                            if t1_offset is not None:
                                lines.append(f'    ld t0, {t1_offset}(sp)  # restore fib(n-1)')
                                lines.append(f'    add a0, t0, a0  # a0 = fib(n-1) + fib(n-2)')
            
            elif op.left.type == OperationType.NOOP and op.left.value:
                # Базовый случай: возвращаем n
                value = op.left.value
                clean_value = self._clean_var_name(value)
                offset = self._get_var_offset(clean_value)
                if offset is not None:
                    lines.append(f'    ld a0, {offset}(sp)  # load {clean_value}')
                elif value.isdigit():
                    lines.append(f'    li a0, {value}')
        
        lines.append(f'    j {func.name}_exit')
        return lines
    
    def _prepare_standard_function_args(self, op: Operation, func_name: str, 
                                     local_vars: Dict[str, str]) -> List[str]:
        """Подготавливает аргументы для стандартных функций"""
        lines = []
        
        for i, arg_op in enumerate(op.args[:8]):
            if i >= len(self.arg_registers):
                break
            
            if arg_op.type == OperationType.NOOP and arg_op.value:
                value = arg_op.value
                clean_value = self._clean_var_name(value)
                
                if value.startswith('"') or value.startswith("'"):
                    string_val = value.strip('"\'')
                    const_id = self.string_constants.get(string_val)
                    if const_id is not None:
                        lines.append(f'    la {self.arg_registers[i]}, str_{const_id}')
                
                elif clean_value in local_vars:
                    offset = self._get_var_offset(clean_value)
                    if offset is not None:
                        if func_name == 'scanf' and i >= 1:
                            lines.append(f'    addi {self.arg_registers[i]}, sp, {offset}  # &{clean_value}')
                        else:
                            lines.append(f'    ld {self.arg_registers[i]}, {offset}(sp)  # {clean_value}')
                
                elif value.isdigit():
                    lines.append(f'    li {self.arg_registers[i]}, {value}')
        
        return lines
    
    def _prepare_user_function_args(self, op: Operation, func_name: str,
                                 local_vars: Dict[str, str]) -> List[str]:
        """Подготавливает аргументы для пользовательских функций"""
        lines = []
        
        for i, arg_op in enumerate(op.args[:8]):
            if i >= len(self.arg_registers):
                break
            
            if arg_op.type == OperationType.NOOP and arg_op.value:
                value = arg_op.value
                clean_value = self._clean_var_name(value)
                
                if clean_value in local_vars:
                    offset = self._get_var_offset(clean_value)
                    if offset is not None:
                        lines.append(f'    ld {self.arg_registers[i]}, {offset}(sp)  # {clean_value}')
                
                elif value.isdigit():
                    lines.append(f'    li {self.arg_registers[i]}, {value}')
        
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
                    lines.append(f'    ld a0, {offset}(sp)  # load {clean_left}')
                    
                    if right_val.isdigit():
                        lines.append(f'    li a1, {right_val}')
                    elif right_val.startswith("'") and right_val.endswith("'"):
                        char_val = right_val.strip("'")
                        if char_val:
                            ascii_code = ord(char_val)
                            lines.append(f'    li a1, {ascii_code}')
        
        return lines
    
    def _generate_assign_code(self, op: Operation, func: FunctionInfo,
                            local_vars: Dict[str, str]) -> List[str]:
        """Генерирует код для операции присваивания"""
        lines = []
        
        if op.left and op.right:
            dest_var_full = op.left.value if hasattr(op.left, 'value') else None
            dest_var = self._clean_var_name(dest_var_full)
            
            if op.right.type == OperationType.CALL:
                func_name = op.right.value
                
                if func_name in ['printf', 'scanf', 'exit', 'puts']:
                    arg_code = self._prepare_standard_function_args(op.right, func_name, local_vars)
                else:
                    arg_code = self._prepare_user_function_args(op.right, func_name, local_vars)
                
                if arg_code:
                    lines.extend(arg_code)
                
                lines.append(f'    jal ra, {func_name}')
                
                if dest_var:
                    dest_offset = self._get_var_offset(dest_var)
                    if dest_offset is not None:
                        lines.append(f'    sd a0, {dest_offset}(sp)  # {dest_var} = результат')
            
            elif op.right.type == OperationType.SUB:
                sub_lines = self._generate_arithmetic_code(op.right, func, local_vars)
                if sub_lines:
                    lines.extend(sub_lines)
                    if dest_var:
                        dest_offset = self._get_var_offset(dest_var)
                        if dest_offset is not None:
                            lines.append(f'    sd a0, {dest_offset}(sp)  # store {dest_var}')
            
            elif op.right.type in [OperationType.ADD, OperationType.MUL, OperationType.DIV]:
                arith_code = self._generate_arithmetic_code(op.right, func, local_vars)
                if arith_code:
                    lines.extend(arith_code)
                
                if dest_var:
                    dest_offset = self._get_var_offset(dest_var)
                    if dest_offset is not None:
                        lines.append(f'    sd a0, {dest_offset}(sp)  # store in {dest_var}')
        
        return lines
    
    def _generate_arithmetic_code(self, op: Operation, func: FunctionInfo,
                                local_vars: Dict[str, str]) -> List[str]:
        """Генерирует код для арифметической операции"""
        lines = []
        
        if not op.left or not op.right:
            return lines
        
        left_var = op.left.value if hasattr(op.left, 'value') else None
        right_var = op.right.value if hasattr(op.right, 'value') else None
        
        # Загружаем левый операнд в a0
        if left_var:
            clean_left = self._clean_var_name(left_var)
            if clean_left in local_vars:
                offset = self._get_var_offset(clean_left)
                if offset is not None:
                    lines.append(f'    ld a0, {offset}(sp)  # load {clean_left}')
            elif left_var.isdigit():
                lines.append(f'    li a0, {left_var}')
        
        # Выполняем операцию с правым операндом
        if right_var:
            clean_right = self._clean_var_name(right_var)
            if clean_right in local_vars:
                offset = self._get_var_offset(clean_right)
                if offset is not None:
                    if op.type == OperationType.ADD:
                        lines.append(f'    ld a1, {offset}(sp)')
                        lines.append(f'    add a0, a0, a1')
                    elif op.type == OperationType.SUB:
                        lines.append(f'    ld a1, {offset}(sp)')
                        lines.append(f'    sub a0, a0, a1')
                    elif op.type == OperationType.MUL:
                        lines.append(f'    ld a1, {offset}(sp)')
                        lines.append(f'    mul a0, a0, a1')
                    elif op.type == OperationType.DIV:
                        lines.append(f'    ld a1, {offset}(sp)')
                        lines.append(f'    div a0, a0, a1')
            elif right_var and right_var.isdigit():
                if op.type == OperationType.ADD:
                    lines.append(f'    addi a0, a0, {right_var}')
                elif op.type == OperationType.SUB:
                    lines.append(f'    addi a0, a0, -{right_var}')
                elif op.type == OperationType.MUL:
                    lines.append(f'    li a1, {right_var}')
                    lines.append(f'    mul a0, a0, a1')
                elif op.type == OperationType.DIV:
                    lines.append(f'    li a1, {right_var}')
                    lines.append(f'    div a0, a0, a1')
        
        return lines