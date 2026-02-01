
import re
from typing import List, Optional, Tuple
from control_flow import ASTNode, ParsingError

class SimpleParser:
    
    def __init__(self):
        self.errors: List[ParsingError] = []
        self.current_line = 0
        self.current_column = 0
        self.debug = True
    
    def parse_file(self, file_name: str, source_code: str) -> ASTNode:
        """Парсинг исходного кода файла"""
        self.errors.clear()
        
        lines = self._remove_comments(source_code)
        root = ASTNode(type='program', children=[], line=1, column=1)
        
        self.current_line = 1
        i = 0
        
        while i < len(lines):
            line = lines[i].rstrip()
            self.current_column = 1
            
            if not line:
                i += 1
                self.current_line += 1
                continue
            
            if self._is_function_declaration(line):
                func_node, lines_consumed = self._parse_function_declaration(
                    lines[i:], self.current_line, file_name
                )
                if func_node:
                    root.children.append(func_node)
                i += lines_consumed
                self.current_line += lines_consumed
            else:
                i += 1
                self.current_line += 1
        
        return root
    
    def _remove_comments(self, source: str) -> List[str]:
        lines = []
        for line in source.split('\n'):
            if '//' in line:
                line = line[:line.index('//')]
            lines.append(line.rstrip())
        return lines
    
    def _is_function_declaration(self, line: str) -> bool:
        """Проверка, является ли строка объявлением функции"""
        return line.strip().startswith('function ')
    
    def _parse_function_declaration(self, lines: List[str], start_line: int, 
                               file_name: str) -> Tuple[Optional[ASTNode], int]:
        """Разбор объявления функции с типами параметров"""
        full_declaration = []
        brace_count = 0
        lines_consumed = 0
        
        for i, line in enumerate(lines):
            full_declaration.append(line)
            lines_consumed += 1
            
            brace_count += line.count('{')
            brace_count -= line.count('}')
            
            if brace_count == 0 and i > 0:
                break
        
        full_text = '\n'.join(full_declaration)
        
        # Паттерн для функции с типами параметров: function name(param -> type) -> return_type
        pattern = r'function\s+(\w+)\s*\(([^)]*)\)\s*->\s*(\w+)\s*\{'
        match = re.search(pattern, full_text)
        
        if not match:
            pattern2 = r'function\s+(\w+)\s*\(([^)]*)\)\s*\{'
            match = re.search(pattern2, full_text)
            if not match:
                self.errors.append(ParsingError(
                    file_name=file_name,
                    line=start_line,
                    column=1,
                    message="Некорректное объявление функции"
                ))
                return None, lines_consumed
            else:
                func_name = match.group(1)
                params_str = match.group(2)
                return_type = "void"
        else:
            func_name = match.group(1)
            params_str = match.group(2)
            return_type = match.group(3)
        
        # Парсим параметры с типами
        parameters = []
        if params_str.strip():
            param_parts = params_str.split(',')
            for param in param_parts:
                param = param.strip()
                if '->' in param:
                    name_type = param.split('->', 1)
                    param_name = name_type[0].strip()
                    param_type = name_type[1].strip()
                    parameters.append((param_name, param_type))
                elif param:
                    parameters.append((param, "unknown"))
        
        body_start = full_text.find('{') + 1
        body_end = full_text.rfind('}')
        body_text = full_text[body_start:body_end].strip()
        
        func_node = ASTNode(
            type='function_declaration',
            line=start_line,
            column=1,
            attributes={
                'name': func_name, 
                'return_type': return_type,
                'parameters': parameters
            }
        )
        
        func_node.children.append(ASTNode(
            type='function_name',
            value=func_name,
            line=start_line,
            column=full_text.find(func_name) + 1
        ))
        
        # Добавляем параметры
        for param_name, param_type in parameters:
            param_node = ASTNode(
                type='parameter',
                value=param_name,
                line=start_line,
                column=full_text.find(param_name) + 1 if param_name in full_text else 1,
                attributes={'type': param_type}
            )
            func_node.children.append(param_node)
        
        func_node.children.append(ASTNode(
            type='return_type',
            value=return_type,
            line=start_line,
            column=full_text.find('->') + 3 if '->' in full_text else 1
        ))
        
        body_node = self._parse_function_body(body_text, start_line + full_text[:body_start].count('\n'), file_name)
        if body_node:
            func_node.children.append(body_node)
        
        return func_node, lines_consumed
    
    def _parse_function_body(self, body_text: str, start_line: int, 
                        file_name: str) -> ASTNode:
        """Разбор тела функции"""
        print(f"\nDEBUG _parse_function_body:")
        print(f"  body_text: '{body_text}'")
        print(f"  start_line: {start_line}")
        
        body_node = ASTNode(type='function_body', line=start_line, column=1)
        
        if not body_text.strip():
            print(f"  Empty body text")
            return body_node
        
        lines = body_text.split('\n')
        print(f"  Split into {len(lines)} lines")
        
        line_num = start_line
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            print(f"  Line {i} (absolute {line_num}): '{line}'")
            
            if not line:
                i += 1
                line_num += 1
                continue
            
            stmt_node, lines_consumed = self._parse_statement(lines[i:], line_num, file_name)
            
            if stmt_node:
                print(f"    Parsed statement: type={stmt_node.type}, value={stmt_node.value}")
                body_node.children.append(stmt_node)
            
            print(f"    Consumed {lines_consumed} lines")
            i += lines_consumed
            line_num += lines_consumed
        
        print(f"  Total statements in body: {len(body_node.children)}")
        return body_node
    
    def _parse_statement(self, lines: List[str], line_num: int, 
                    file_name: str) -> Tuple[Optional[ASTNode], int]:
        """Разбор оператора с поддержкой объявления с инициализацией"""
        line = lines[0].strip()
        
        if not line:
            return None, 1
        
        line = line.rstrip(';')
        
        # Проверяем вызовы функций ПЕРВЫМ делом
        # Используем регулярное выражение для поиска вызова функции
        if '(' in line and ')' in line:
            # Ищем паттерн: имя_функции(аргументы)
            # Это регулярное выражение ищет имя функции, затем скобки с содержимым
            # Оно должно обрабатывать вложенные скобки внутри аргументов
            pattern = r'^(\w+)\s*\((.*)\)\s*$'
            match = re.match(pattern, line)
            
            if match:
                func_name = match.group(1)
                args_str = match.group(2)
                
                # Проверяем, что это действительно вызов функции, а не что-то еще
                # Исключаем ключевые слова
                if func_name not in ['if', 'while', 'for', 'do', 'return', 'break', 'continue']:
                    print(f"    DEBUG: Found function call: {func_name}({args_str})")
                    
                    node = ASTNode(type='call', line=line_num, column=1)
                    node.children.append(ASTNode(
                        type='function_name',
                        value=func_name,
                        line=line_num,
                        column=1
                    ))
                    
                    # Парсим аргументы
                    if args_str.strip():
                        args = self._parse_expression_list(args_str, line_num)
                        for arg in args:
                            node.children.append(arg)
                    
                    return node, 1
        
        # Остальные проверки остаются как были
        if line.startswith('for '):
            return self._parse_for_statement(lines, line_num, file_name)
        
        elif line.startswith('if '):
            return self._parse_if_statement(lines, line_num, file_name)
        
        elif line.startswith('do'):
            return self._parse_do_while_statement(lines, line_num, file_name)
        
        elif line.startswith('while '):
            return self._parse_while_statement(lines, line_num, file_name)
        
        elif line.startswith('return '):
            node = ASTNode(type='return', line=line_num, column=1)
            ret_val = line[7:].strip()
            if ret_val:
                node.children.append(ASTNode(
                    type='expression',
                    value=ret_val,
                    line=line_num,
                    column=line.find('return') + 7
                ))
            return node, 1
        
        # ASSIGNMENT
        elif '=' in line and not any(op in line for op in ['==', '!=', '<=', '>=']):
            parts = line.split('=', 1)
            if len(parts) == 2:
                node = ASTNode(type='assignment', line=line_num, column=1)
                node.children.append(ASTNode(
                    type='identifier',
                    value=parts[0].strip(),
                    line=line_num,
                    column=1
                ))
                node.children.append(ASTNode(
                    type='expression',
                    value=parts[1].strip(),
                    line=line_num,
                    column=line.find('=') + 2
                ))
                return node, 1
        
        # ОБЪЯВЛЕНИЕ ПЕРЕМЕННОЙ С ИНИЦИАЛИЗАЦИЕЙ: a -> int = 10
        if '->' in line and '=' in line and not line.startswith('function '):
            # Проверяем порядок: должно быть сначала ->, потом =
            arrow_pos = line.find('->')
            eq_pos = line.find('=')
            
            if arrow_pos < eq_pos:
                # Разбираем: var_name -> type = value
                var_part = line[:eq_pos].strip()
                value_part = line[eq_pos+1:].strip()
                
                # Разбираем var_name -> type
                if '->' in var_part:
                    name_type = var_part.split('->', 1)
                    var_name = name_type[0].strip()
                    var_type = name_type[1].strip()
                    
                    node = ASTNode(type='var_declaration_with_init', line=line_num, column=1)
                    node.children.append(ASTNode(
                        type='identifier',
                        value=var_name,
                        line=line_num,
                        column=1
                    ))
                    node.children.append(ASTNode(
                        type='type',
                        value=var_type,
                        line=line_num,
                        column=line.find('->') + 3
                    ))
                    node.children.append(ASTNode(
                        type='expression',
                        value=value_part,
                        line=line_num,
                        column=line.find('=') + 2
                    ))
                    return node, 1
        
        # ОБЪЯВЛЕНИЕ ПЕРЕМЕННОЙ БЕЗ ИНИЦИАЛИЗАЦИИ: a -> int
        elif '->' in line and not line.startswith('function '):
            parts = line.split('->', 1)
            if len(parts) == 2:
                var_name = parts[0].strip()
                var_type = parts[1].strip()
                
                node = ASTNode(type='var_declaration', line=line_num, column=1)
                node.children.append(ASTNode(
                    type='identifier',
                    value=var_name,
                    line=line_num,
                    column=1
                ))
                node.children.append(ASTNode(
                    type='type',
                    value=var_type,
                    line=line_num,
                    column=line.find('->') + 3
                ))
                return node, 1
        
        
        
        # ФУНКЦИЯ ВЫЗЫВАЕТСЯ САМА ПО СЕБЕ (не в выражении)
        elif '(' in line and ')' in line and not line.startswith('if') and not line.startswith('while'):
            # Проверяем, нет ли операторов в выражении
            has_operator = any(op in line for op in ['+', '-', '*', '/', '%', '==', '!=', '<', '>', '<=', '>=', '&&', '||'])
            
            if not has_operator:
                # Это простой вызов функции
                match = re.match(r'(\w+)\s*\((.*)\)', line)
                if match:
                    node = ASTNode(type='call', line=line_num, column=1)
                    node.children.append(ASTNode(
                        type='function_name',
                        value=match.group(1),
                        line=line_num,
                        column=1
                    ))
                    
                    args_str = match.group(2)
                    if args_str.strip():
                        args = self._parse_expression_list(args_str, line_num)
                        for arg in args:
                            node.children.append(arg)
                    
                    return node, 1
        elif '(' in line and ')' in line:
            # Это может быть вызов функции как оператор
            match = re.match(r'(\w+)\s*\((.*)\)', line)
            if match:
                node = ASTNode(type='call', line=line_num, column=1)
                node.children.append(ASTNode(
                    type='function_name',
                    value=match.group(1),
                    line=line_num,
                    column=1
                ))
                
                args_str = match.group(2)
                if args_str.strip():
                    args = self._parse_expression_list(args_str, line_num)
                    for arg in args:
                        node.children.append(arg)
                
                return node, 1
        else:
            # Проверяем, является ли это выражением (содержит операторы)
            if any(op in line for op in ['+', '-', '*', '/', '%', '==', '!=', '<', '>', '<=', '>=', '&&', '||']):
                node = ASTNode(type='expression_statement', line=line_num, column=1)
                node.children.append(ASTNode(
                    type='expression',
                    value=line,
                    line=line_num,
                    column=1
                ))
                return node, 1
        
        return None, 1

    def _parse_if_statement(self, lines: List[str], line_num: int, 
                           file_name: str) -> Tuple[Optional[ASTNode], int]:
        """Разбор оператора if (может быть с else/else if)"""
        if self.debug:
            print(f"\n    [DEBUG] Parsing IF statement at line {line_num}")
            print(f"      First line: '{lines[0]}'")
        
        first_line = lines[0].strip()
        
        # Извлекаем условие с учетом вложенных скобок
        condition = self._extract_condition(first_line)
        if not condition:
            self.errors.append(ParsingError(
                file_name=file_name,
                line=line_num,
                column=1,
                message="Некорректный оператор if"
            ))
            return None, 1
        
        if self.debug:
            print(f"      Condition: '{condition}'")
        
        first_line = lines[0].strip()
        
        # Извлекаем условие
        pattern = r'if\s*\((.*?)\)'
        match = re.search(pattern, first_line)
        if not match:
            self.errors.append(ParsingError(
                file_name=file_name,
                line=line_num,
                column=1,
                message="Некорректный оператор if"
            ))
            return None, 1
        
        condition = match.group(1).strip()
        
        if self.debug:
            print(f"      Condition: '{condition}'")
        
        # Создаем узел if
        if_node = ASTNode(type='if_statement', line=line_num, column=1)
        
        # Добавляем условие
        cond_node = ASTNode(type='condition', line=line_num, column=first_line.find('(') + 2)
        cond_node.children.append(ASTNode(
            type='expression',
            value=condition,
            line=line_num,
            column=first_line.find('(') + 2
        ))
        if_node.children.append(cond_node)
        
        # Извлекаем тело if
        after_if = first_line[match.end():].strip()
        
        if after_if and after_if.startswith('{'):
            if self.debug:
                print(f"      IF body has braces")
            
            # Тело в фигурных скобках
            body_text, body_lines = self._extract_block_body(lines, line_num, file_name)
            if body_text:
                true_body = ASTNode(type='true_body', line=line_num, column=first_line.find(')') + 2)
                true_body_children = self._parse_statement_list(body_text, line_num + 1, file_name)
                for child in true_body_children:
                    true_body.children.append(child)
                if_node.children.append(true_body)
            
            lines_consumed = body_lines
            
            if self.debug:
                print(f"      IF body processed, consumed {lines_consumed} lines")
            
        else:
            if self.debug:
                print(f"      IF body without braces")
            
            # Тело без скобок - одна строка
            if after_if:
                # Однострочное тело
                true_body = ASTNode(type='true_body', line=line_num, column=first_line.find(')') + 2)
                stmt_node, _ = self._parse_statement([after_if], line_num, file_name)
                if stmt_node:
                    true_body.children.append(stmt_node)
                if_node.children.append(true_body)
                lines_consumed = 1
            else:
                # Тело на следующей строке
                if len(lines) > 1:
                    body_line = lines[1].strip()
                    true_body = ASTNode(type='true_body', line=line_num + 1, column=1)
                    stmt_node, _ = self._parse_statement([body_line], line_num + 1, file_name)
                    if stmt_node:
                        true_body.children.append(stmt_node)
                    if_node.children.append(true_body)
                    lines_consumed = 2
                else:
                    lines_consumed = 1
        
        # ВАЖНОЕ ИСПРАВЛЕНИЕ: После обработки if блока, нужно проверить следующие строки на наличие else
        # даже если они не являются непосредственным продолжением
        
        if self.debug:
            print(f"      Checking for ELSE after if block...")
            print(f"      Total lines available: {len(lines)}, already consumed: {lines_consumed}")
        
        # Проверяем следующие строки на наличие else
        i = lines_consumed
        found_else = False
        
        while i < len(lines) and not found_else:
            current_line = lines[i].strip()
            
            if self.debug:
                print(f"      Checking line {line_num + i}: '{current_line}'")
            
            if not current_line:
                # Пустая строка - пропускаем
                i += 1
                continue
            
            if current_line.startswith('else'):
                found_else = True
                else_line = current_line
                else_line_num = line_num + i
                
                if self.debug:
                    print(f"      Found ELSE at line {else_line_num}: '{else_line}'")
                
                after_else = else_line[4:].strip() if len(else_line) > 4 else ""
                
                if after_else and after_else.startswith('{'):
                    # Тело else в фигурных скобках
                    if self.debug:
                        print(f"      ELSE body has braces")
                    
                    # Используем оставшиеся строки начиная с текущей
                    remaining_lines = lines[i:]
                    else_body_text, else_lines = self._extract_block_body(
                        remaining_lines, else_line_num, file_name
                    )
                    
                    if else_body_text:
                        false_body = ASTNode(type='false_body', line=else_line_num, column=1)
                        false_body_children = self._parse_statement_list(else_body_text, else_line_num + 1, file_name)
                        for child in false_body_children:
                            false_body.children.append(child)
                        if_node.children.append(false_body)
                    
                    lines_consumed = i + else_lines
                    
                elif after_else and after_else.startswith('if'):
                    # else if - рекурсивно парсим как вложенный if
                    if self.debug:
                        print(f"      Found ELSE IF")
                    
                    # Используем оставшиеся строки начиная с текущей
                    remaining_lines = lines[i:]
                    else_if_node, else_if_lines = self._parse_if_statement(
                        remaining_lines, else_line_num, file_name
                    )
                    if else_if_node:
                        false_body = ASTNode(type='false_body', line=else_line_num, column=1)
                        false_body.children.append(else_if_node)
                        if_node.children.append(false_body)
                    
                    lines_consumed = i + else_if_lines
                    
                elif after_else:
                    # Однострочный else
                    if self.debug:
                        print(f"      Single-line ELSE: '{after_else}'")
                    
                    false_body = ASTNode(type='false_body', line=else_line_num, column=1)
                    stmt_node, _ = self._parse_statement([after_else], else_line_num, file_name)
                    if stmt_node:
                        false_body.children.append(stmt_node)
                    if_node.children.append(false_body)
                    lines_consumed = i + 1
                    
                else:
                    # Else на следующей строке
                    if i + 1 < len(lines):
                        else_body_line = lines[i + 1].strip()
                        if self.debug:
                            print(f"      ELSE body on next line: '{else_body_line}'")
                        
                        false_body = ASTNode(type='false_body', line=else_line_num + 1, column=1)
                        stmt_node, _ = self._parse_statement([else_body_line], else_line_num + 1, file_name)
                        if stmt_node:
                            false_body.children.append(stmt_node)
                        if_node.children.append(false_body)
                        lines_consumed = i + 2
                    else:
                        # Пустой else
                        if self.debug:
                            print(f"      Empty ELSE")
                        
                        false_body = ASTNode(type='false_body', line=else_line_num, column=1)
                        if_node.children.append(false_body)
                        lines_consumed = i + 1
                
                break  # Выходим из цикла, нашли else
            else:
                # Если строка не пустая и не начинается с else, это не часть if-else конструкции
                if self.debug:
                    print(f"      Line doesn't start with 'else', stopping search")
                break
            
            i += 1
        
        if not found_else and self.debug:
            print(f"      No ELSE found")
        
        if self.debug:
            print(f"      IF statement complete, total lines consumed: {lines_consumed}")
            print(f"      IF node has children: {[c.type for c in if_node.children]}")
        
        return if_node, lines_consumed
    def _parse_while_statement(self, lines: List[str], line_num: int, 
                              file_name: str) -> Tuple[Optional[ASTNode], int]:
        first_line = lines[0]
        
        pattern = r'while\s*\((.*?)\)'
        match = re.search(pattern, first_line)
        if not match:
            self.errors.append(ParsingError(
                file_name=file_name,
                line=line_num,
                column=1,
                message="Некорректный оператор while"
            ))
            return None, 1
        
        condition = match.group(1).strip()
        
        while_node = ASTNode(type='while_statement', line=line_num, column=1)
        
        cond_node = ASTNode(type='condition', line=line_num, column=first_line.find('(') + 2)
        cond_node.children.append(ASTNode(
            type='expression',
            value=condition,
            line=line_num,
            column=first_line.find('(') + 2
        ))
        while_node.children.append(cond_node)
        
        body_text, lines_consumed = self._extract_block_body(lines, line_num, file_name)
        if body_text:
            body_node = ASTNode(type='body', line=line_num, column=first_line.find(')') + 2)
            body_statements = self._parse_statement_list(body_text, line_num + 1, file_name)
            body_node.children.extend(body_statements)
            while_node.children.append(body_node)
        
        return while_node, lines_consumed
    
    def _extract_block_body(self, lines: List[str], line_num: int, 
                           file_name: str) -> Tuple[Optional[str], int]:
        first_line = lines[0]
        
        open_brace_pos = first_line.find('{')
        if open_brace_pos == -1:
            if len(lines) > 1 and lines[1].strip().startswith('{'):
                first_line = lines[1]
                open_brace_pos = first_line.find('{')
                start_line = 1
            else:
                after_paren = first_line[first_line.find(')') + 1:].strip()
                if after_paren:
                    return after_paren, 1
                return None, 1
        else:
            start_line = 0
        
        brace_count = 0
        lines_consumed = start_line
        body_lines = []
        
        for i in range(start_line, len(lines)):
            current_line = lines[i]
            if i == start_line:
                line_part = current_line[open_brace_pos:]
            else:
                line_part = current_line
            
            for char in line_part:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                
                if brace_count == 0:
                    body_text = '\n'.join(body_lines).strip()
                    return body_text, lines_consumed + 1
            
            if i == start_line:
                body_lines.append(current_line[open_brace_pos + 1:])
            else:
                body_lines.append(current_line)
            
            lines_consumed += 1
        
        self.errors.append(ParsingError(
            file_name=file_name,
            line=line_num,
            column=1,
            message="Незакрытый блок"
        ))
        return None, lines_consumed
    def _parse_do_while_statement(self, lines: List[str], line_num: int, 
                                 file_name: str) -> Tuple[Optional[ASTNode], int]:
        full_text_lines = []
        brace_count = 0
        in_do_block = False
        lines_consumed = 0
        condition_line = ""
        do_line = lines[0].strip()
        
        if '{' in do_line:
            do_pos = do_line.find('do')
            open_brace_pos = do_line.find('{', do_pos)
            if open_brace_pos != -1:
                brace_count = 1
                in_do_block = True
        else:
            if do_line == 'do':
                in_do_block = True
            else:
                pass
        
        full_text_lines.append(lines[0])
        lines_consumed += 1
        
        i = 1
        while i < len(lines):
            current_line = lines[i].strip()
            full_text_lines.append(lines[i])
            lines_consumed += 1
            
            if in_do_block:
                brace_count += current_line.count('{')
                brace_count -= current_line.count('}')

                if brace_count == 0:
                    if 'while' in current_line:
                        pattern = r'while\s*\((.*?)\)'
                        match = re.search(pattern, current_line)
                        if match:
                            condition_line = match.group(1).strip()
                        break
                    elif i + 1 < len(lines) and 'while' in lines[i + 1]:
                        next_line = lines[i + 1].strip()
                        pattern = r'while\s*\((.*?)\)'
                        match = re.search(pattern, next_line)
                        if match:
                            condition_line = match.group(1).strip()
                            full_text_lines.append(lines[i + 1])
                            lines_consumed += 1
                        break
            else:
                if i + 1 < len(lines) and 'while' in lines[i + 1]:
                    next_line = lines[i + 1].strip()
                    pattern = r'while\s*\((.*?)\)'
                    match = re.search(pattern, next_line)
                    if match:
                        condition_line = match.group(1).strip()
                        full_text_lines.append(lines[i + 1])
                        lines_consumed += 1
                    break
            
            i += 1
        
        if not condition_line:
            self.errors.append(ParsingError(
                file_name=file_name,
                line=line_num,
                column=1,
                message="Некорректный оператор do-while: отсутствует условие"
            ))
            return None, lines_consumed
        

        full_text = '\n'.join(full_text_lines)
        

        do_pos = full_text.find('do')
        if '{' in full_text[do_pos:]:

            body_start = full_text.find('{', do_pos) + 1
            body_end = full_text.rfind('}', 0, full_text.find('while'))
            body_text = full_text[body_start:body_end].strip()
        else:
            after_do = full_text[do_pos + 2:].strip()
            while_pos = after_do.find('while')
            if while_pos != -1:
                body_text = after_do[:while_pos].strip()
            else:
                body_text = ""
        do_while_node = ASTNode(
            type='do_while_statement',
            line=line_num,
            column=1
        )
        
        cond_node = ASTNode(
            type='condition',
            line=line_num + lines_consumed - 1,
            column=full_text.rfind('(') + 2
        )
        cond_node.children.append(ASTNode(
            type='expression',
            value=condition_line,
            line=line_num + lines_consumed - 1,
            column=full_text.rfind('(') + 2
        ))
        do_while_node.children.append(cond_node)
        
        if body_text:
            body_node = ASTNode(
                type='body',
                line=line_num,
                column=full_text.find('do') + 3
            )
            
            if '{' in full_text[do_pos:]:
                body_lines = body_text.split('\n')
                body_line_num = line_num + full_text[:body_start].count('\n')
                
                j = 0
                while j < len(body_lines):
                    body_line = body_lines[j].strip()
                    
                    if not body_line:
                        j += 1
                        body_line_num += 1
                        continue
                    
                    stmt_node, consumed = self._parse_statement(
                        body_lines[j:], 
                        body_line_num, 
                        file_name
                    )
                    if stmt_node:
                        body_node.children.append(stmt_node)
                    
                    j += consumed
                    body_line_num += consumed
            else:
                stmt_node, _ = self._parse_statement([body_text], line_num, file_name)
                if stmt_node:
                    body_node.children.append(stmt_node)
            
            do_while_node.children.append(body_node)
        
        return do_while_node, lines_consumed
    def _parse_statement_list(self, text: str, start_line: int, 
                             file_name: str) -> List[ASTNode]:
        statements = []
        
        lines = text.split('\n')
        line_num = start_line
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                i += 1
                line_num += 1
                continue
            
            stmt_node, lines_consumed = self._parse_statement(lines[i:], line_num, file_name)
            if stmt_node:
                statements.append(stmt_node)
            
            i += lines_consumed
            line_num += lines_consumed
        
        return statements
    
    def _parse_expression_list(self, args_str: str, line_num: int) -> List[ASTNode]:
        args = []
        
        arg_parts = []
        current_arg = []
        paren_count = 0
        bracket_count = 0
        brace_count = 0
        in_string = False
        string_char = None  # ' или "
        
        i = 0
        while i < len(args_str):
            char = args_str[i]
            
            # Обработка строковых литералов
            if not in_string and (char == '"' or char == "'"):
                in_string = True
                string_char = char
                current_arg.append(char)
            elif in_string and char == string_char and args_str[i-1] != '\\':
                in_string = False
                current_arg.append(char)
            elif in_string:
                current_arg.append(char)
            else:
                # Обработка скобок
                if char == '(':
                    paren_count += 1
                    current_arg.append(char)
                elif char == ')':
                    paren_count -= 1
                    current_arg.append(char)
                elif char == '[':
                    bracket_count += 1
                    current_arg.append(char)
                elif char == ']':
                    bracket_count -= 1
                    current_arg.append(char)
                elif char == '{':
                    brace_count += 1
                    current_arg.append(char)
                elif char == '}':
                    brace_count -= 1
                    current_arg.append(char)
                elif char == ',' and paren_count == 0 and bracket_count == 0 and brace_count == 0:
                    arg_parts.append(''.join(current_arg).strip())
                    current_arg = []
                else:
                    current_arg.append(char)
            
            i += 1
        
        if current_arg:
            arg_parts.append(''.join(current_arg).strip())
        
        for arg in arg_parts:
            if arg:
                args.append(ASTNode(
                    type='expression',
                    value=arg,
                    line=line_num,
                    column=1
                ))
        
        return args
    
   
    
    def _parse_function_call(self, line: str, line_num: int) -> Optional[ASTNode]:
        """Парсинг вызова функции (может быть частью выражения)"""
        line = line.strip()
        
        # Ищем вызов функции в любом месте строки
        pattern = r'(\w+)\s*\((.*?)\)'
        matches = list(re.finditer(pattern, line))
        
        if not matches:
            return None
        
        # Берем последний вызов (самый вложенный)
        match = matches[-1]
        
        node = ASTNode(type='call', line=line_num, column=line.find(match.group(1)) + 1)
        
        node.children.append(ASTNode(
            type='function_name',
            value=match.group(1),
            line=line_num,
            column=line.find(match.group(1)) + 1
        ))
        
        args_str = match.group(2)
        if args_str.strip():
            args = self._parse_expression_list(args_str, line_num)
            for arg in args:
                node.children.append(arg)
        
        return node
    
    def _parse_for_statement(self, lines: List[str], line_num: int, 
                    file_name: str) -> Tuple[Optional[ASTNode], int]:
        """Разбор оператора for"""
        print(f"\n    [DEBUG] Parsing FOR statement at line {line_num}")
        print(f"      First line: '{lines[0]}'")
        
        # Собираем весь текст for оператора
        full_text_lines = []
        brace_count = 0
        paren_count = 0
        lines_consumed = 0
        found_for = False
        
        for i in range(len(lines)):
            current_line = lines[i]
            full_text_lines.append(current_line)
            lines_consumed += 1
            
            # Проверяем, нашли ли мы for в этой строке
            if 'for' in current_line and not found_for:
                found_for = True
            
            # Считаем скобки
            if found_for:
                for char in current_line:
                    if char == '(':
                        paren_count += 1
                    elif char == ')':
                        paren_count -= 1
                    elif char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
            
            # Завершаем сбор, когда все скобки закрыты
            if found_for and paren_count == 0 and brace_count == 0 and i > 0:
                break
        
        full_text = '\n'.join(full_text_lines).strip()
        print(f"      Full for text: '{full_text}'")
        
        # Извлекаем содержимое for
        for_match = re.search(r'for\s*\((.*?)\)\s*(.*)', full_text, re.DOTALL)
        
        if not for_match:
            self.errors.append(ParsingError(
                file_name=file_name,
                line=line_num,
                column=1,
                message="Некорректный оператор for"
            ))
            return None, lines_consumed
        
        for_parts_str = for_match.group(1).strip()
        body_text = for_match.group(2).strip()
        
        print(f"      For parts string: '{for_parts_str}'")
        print(f"      Body text: '{body_text}'")
        
        # Разделяем на 3 части: init; condition; increment
        parts = []
        current_part = []
        in_paren = 0
        
        for char in for_parts_str:
            if char == '(':
                in_paren += 1
                current_part.append(char)
            elif char == ')':
                in_paren -= 1
                current_part.append(char)
            elif char == ';' and in_paren == 0:
                part_str = ''.join(current_part).strip()
                if part_str:
                    parts.append(part_str)
                current_part = []
            else:
                current_part.append(char)
        
        # Добавляем последнюю часть
        if current_part:
            part_str = ''.join(current_part).strip()
            if part_str:
                parts.append(part_str)
        
        print(f"      Split into {len(parts)} parts: {parts}")
        
        # Должно быть ровно 3 части
        if len(parts) < 3:
            while len(parts) < 3:
                parts.append("")
        
        init_expr = parts[0] if len(parts) > 0 else ""
        condition_expr = parts[1] if len(parts) > 1 else ""
        increment_expr = parts[2] if len(parts) > 2 else ""
        
        print(f"      For parts: init='{init_expr}', condition='{condition_expr}', increment='{increment_expr}'")
        
        # Создаем узел for
        for_node = ASTNode(type='for_statement', line=line_num, column=1)
        
        # Добавляем init
        if init_expr:
            init_node = ASTNode(type='init', line=line_num, column=full_text.find(init_expr) + 1)
            init_node.children.append(ASTNode(
                type='expression',
                value=init_expr,
                line=line_num,
                column=full_text.find(init_expr) + 1
            ))
            for_node.children.append(init_node)
        
        # Добавляем condition
        if condition_expr:
            cond_node = ASTNode(type='condition', line=line_num, column=full_text.find(condition_expr) + 1)
            cond_node.children.append(ASTNode(
                type='expression',
                value=condition_expr,
                line=line_num,
                column=full_text.find(condition_expr) + 1
            ))
            for_node.children.append(cond_node)
        
        # Добавляем increment
        if increment_expr:
            inc_node = ASTNode(type='increment', line=line_num, column=full_text.find(increment_expr) + 1)
            inc_node.children.append(ASTNode(
                type='expression',
                value=increment_expr,
                line=line_num,
                column=full_text.find(increment_expr) + 1
            ))
            for_node.children.append(inc_node)
        
        # Обрабатываем тело
        if body_text:
            print(f"      Processing body: '{body_text}'")
            
            # Убираем внешние фигурные скобки если есть
            if body_text.startswith('{'):
                # Находим парную закрывающую скобку
                brace_counter = 1
                body_end_pos = 1
                
                while body_end_pos < len(body_text) and brace_counter > 0:
                    if body_text[body_end_pos] == '{':
                        brace_counter += 1
                    elif body_text[body_end_pos] == '}':
                        brace_counter -= 1
                    body_end_pos += 1
                
                if brace_counter == 0:
                    body_text = body_text[1:body_end_pos-1].strip()
                else:
                    body_text = body_text[1:].strip()
            
            print(f"      Body text after processing: '{body_text}'")
            
            if body_text:
                body_node = ASTNode(type='body', line=line_num, column=full_text.find(body_text) + 1)
                
                # Парсим тело как список statements
                print(f"      Calling _parse_statement_list")
                body_statements = self._parse_statement_list(body_text, line_num + 1, file_name)
                print(f"      Parsed {len(body_statements)} statements")
                
                for stmt in body_statements:
                    body_node.children.append(stmt)
                
                for_node.children.append(body_node)
                print(f"      Added body with {len(body_statements)} statements")
            else:
                print(f"      Empty body after processing")
                # Добавляем пустое тело
                body_node = ASTNode(type='body', line=line_num, column=full_text.find('{') + 2)
                for_node.children.append(body_node)
        else:
            print(f"      No body text")
        
        print(f"      FOR statement complete, total lines consumed: {lines_consumed}")
        print(f"      For node has {len(for_node.children)} children")
        
        return for_node, lines_consumed
    
    def _extract_condition(self, line: str) -> Optional[str]:
        """Извлекает полное условие из if/while с учетом вложенных скобок"""
        if not line.strip().startswith(('if ', 'while ')):
            return None
        
        # Находим начало условия
        open_paren_pos = line.find('(')
        if open_paren_pos == -1:
            return None
        
        # Ищем парную закрывающую скобку
        paren_count = 0
        i = open_paren_pos
        
        while i < len(line):
            char = line[i]
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
                if paren_count == 0:
                    # Нашли парную закрывающую скобку
                    return line[open_paren_pos + 1:i].strip()
            i += 1
        
        return None