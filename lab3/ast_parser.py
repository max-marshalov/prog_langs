
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
        body_node = ASTNode(type='function_body', line=start_line, column=1)
        
        if not body_text.strip():
            return body_node
        
        lines = body_text.split('\n')
        
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
                body_node.children.append(stmt_node)
            
            i += lines_consumed
            line_num += lines_consumed
        
        return body_node
    
    def _parse_statement(self, lines: List[str], line_num: int, 
                    file_name: str) -> Tuple[Optional[ASTNode], int]:
        """Разбор оператора с поддержкой объявления с инициализацией"""
        line = lines[0].strip()
        
        if not line:
            return None, 1
        
        line = line.rstrip(';')
        
        if '(' in line and ')' in line:
            pattern = r'^(\w+)\s*\((.*)\)\s*$'
            match = re.match(pattern, line)
            
            if match:
                func_name = match.group(1)
                args_str = match.group(2)
                
                if func_name not in ['if', 'while', 'for', 'do', 'return', 'break', 'continue']:
                    
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
        
        if '->' in line and '=' in line and not line.startswith('function '):
            arrow_pos = line.find('->')
            eq_pos = line.find('=')
            
            if arrow_pos < eq_pos:
                var_part = line[:eq_pos].strip()
                value_part = line[eq_pos+1:].strip()
                
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
        
        
        
        elif '(' in line and ')' in line and not line.startswith('if') and not line.startswith('while'):
            has_operator = any(op in line for op in ['+', '-', '*', '/', '%', '==', '!=', '<', '>', '<=', '>=', '&&', '||'])
            
            if not has_operator:
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
        first_line = lines[0].strip()
        
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
        if_node = ASTNode(type='if_statement', line=line_num, column=1)
        
        cond_node = ASTNode(type='condition', line=line_num, column=first_line.find('(') + 2)
        cond_node.children.append(ASTNode(
            type='expression',
            value=condition,
            line=line_num,
            column=first_line.find('(') + 2
        ))
        if_node.children.append(cond_node)
        
        after_if = first_line[match.end():].strip()
        
        if after_if and after_if.startswith('{'):
            body_text, body_lines = self._extract_block_body(lines, line_num, file_name)
            if body_text:
                true_body = ASTNode(type='true_body', line=line_num, column=first_line.find(')') + 2)
                true_body_children = self._parse_statement_list(body_text, line_num + 1, file_name)
                for child in true_body_children:
                    true_body.children.append(child)
                if_node.children.append(true_body)
            
            lines_consumed = body_lines
            
        else:
            if after_if:
                true_body = ASTNode(type='true_body', line=line_num, column=first_line.find(')') + 2)
                stmt_node, _ = self._parse_statement([after_if], line_num, file_name)
                if stmt_node:
                    true_body.children.append(stmt_node)
                if_node.children.append(true_body)
                lines_consumed = 1
            else:
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
        
        i = lines_consumed
        found_else = False
        
        while i < len(lines) and not found_else:
            current_line = lines[i].strip()
            
            if not current_line:
                i += 1
                continue
            
            if current_line.startswith('else'):
                found_else = True
                else_line = current_line
                else_line_num = line_num + i
                
                after_else = else_line[4:].strip() if len(else_line) > 4 else ""
                
                if after_else and after_else.startswith('{'):
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
                    false_body = ASTNode(type='false_body', line=else_line_num, column=1)
                    stmt_node, _ = self._parse_statement([after_else], else_line_num, file_name)
                    if stmt_node:
                        false_body.children.append(stmt_node)
                    if_node.children.append(false_body)
                    lines_consumed = i + 1
                    
                else:
                    if i + 1 < len(lines):
                        else_body_line = lines[i + 1].strip()
                        false_body = ASTNode(type='false_body', line=else_line_num + 1, column=1)
                        stmt_node, _ = self._parse_statement([else_body_line], else_line_num + 1, file_name)
                        if stmt_node:
                            false_body.children.append(stmt_node)
                        if_node.children.append(false_body)
                        lines_consumed = i + 2
                    else:
                        false_body = ASTNode(type='false_body', line=else_line_num, column=1)
                        if_node.children.append(false_body)
                        lines_consumed = i + 1
                
                break
            else:
                break
            
            i += 1
        
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
        full_text_lines = []
        brace_count = 0
        paren_count = 0
        lines_consumed = 0
        found_for = False
        
        for i in range(len(lines)):
            current_line = lines[i]
            full_text_lines.append(current_line)
            lines_consumed += 1
            
            if 'for' in current_line and not found_for:
                found_for = True
            
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
            
            if found_for and paren_count == 0 and brace_count == 0 and i > 0:
                break
        
        full_text = '\n'.join(full_text_lines).strip()
        
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
        
        if current_part:
            part_str = ''.join(current_part).strip()
            if part_str:
                parts.append(part_str)
        
        if len(parts) < 3:
            while len(parts) < 3:
                parts.append("")
        
        init_expr = parts[0] if len(parts) > 0 else ""
        condition_expr = parts[1] if len(parts) > 1 else ""
        increment_expr = parts[2] if len(parts) > 2 else ""
        
        for_node = ASTNode(type='for_statement', line=line_num, column=1)
        
        if init_expr:
            init_node = ASTNode(type='init', line=line_num, column=full_text.find(init_expr) + 1)
            init_node.children.append(ASTNode(
                type='expression',
                value=init_expr,
                line=line_num,
                column=full_text.find(init_expr) + 1
            ))
            for_node.children.append(init_node)
        
        if condition_expr:
            cond_node = ASTNode(type='condition', line=line_num, column=full_text.find(condition_expr) + 1)
            cond_node.children.append(ASTNode(
                type='expression',
                value=condition_expr,
                line=line_num,
                column=full_text.find(condition_expr) + 1
            ))
            for_node.children.append(cond_node)
        
        if increment_expr:
            inc_node = ASTNode(type='increment', line=line_num, column=full_text.find(increment_expr) + 1)
            inc_node.children.append(ASTNode(
                type='expression',
                value=increment_expr,
                line=line_num,
                column=full_text.find(increment_expr) + 1
            ))
            for_node.children.append(inc_node)
        
        if body_text:
            if body_text.startswith('{'):
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
            
            if body_text:
                body_node = ASTNode(type='body', line=line_num, column=full_text.find(body_text) + 1)
                body_statements = self._parse_statement_list(body_text, line_num + 1, file_name)
                
                for stmt in body_statements:
                    body_node.children.append(stmt)
                
                for_node.children.append(body_node)
            else:
                body_node = ASTNode(type='body', line=line_num, column=full_text.find('{') + 2)
                for_node.children.append(body_node)
        
        return for_node, lines_consumed
        
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