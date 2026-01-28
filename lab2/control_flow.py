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
    parameters: List[str] = field(default_factory=list)

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
        
        for child in func_node.children:
            if child.type == 'function_name':
                func_name = child.value
            elif child.type == 'return_type':
                return_type = child.value
        
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
                signature={'return_type': return_type, 'parameters': []},
                cfg=cfg,
                source_file=file_name,
                return_type=return_type
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
            signature={'return_type': return_type, 'parameters': []},
            cfg=cfg,
            source_file=file_name,
            return_type=return_type
        )
        
        self.functions.append(func_info)
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

            elif stmt.type == 'function_call' or stmt.type == 'call':  # <-- ИСПРАВЛЕНО ЗДЕСЬ!
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
        expr = ' '.join(expr.split())
        
        if '(' in expr and ')' in expr:
            func_match = expr[:expr.find('(')].strip()
            args_str = expr[expr.find('(')+1:expr.rfind(')')].strip()
            
            args = []
            if args_str:
                for arg in args_str.split(','):
                    arg = arg.strip()
                    if arg:
                        arg_op = self._parse_expression(arg, line, column, func_name, file_name)
                        args.append(arg_op)
            
            if func_name != func_match:
                if func_name not in self.call_graph:
                    self.call_graph[func_name] = set()
                self.call_graph[func_name].add(func_match)
            
            return Operation(
                type=OperationType.CALL,
                value=func_match,
                args=args,
                line=line,
                column=column
            )
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
            ('||', OperationType.OR)
        ]
        
        for op_str, op_type in ops:
            if op_str in expr:
                parts = expr.split(op_str, 1)
                if len(parts) == 2:
                    left_expr = parts[0].strip()
                    right_expr = parts[1].strip()
                    
                    left_op = self._parse_expression(left_expr, line, column, func_name, file_name)
                    right_op = self._parse_expression(right_expr, line, column, func_name, file_name)
                    
                    return Operation(
                        type=op_type,
                        left=left_op,
                        right=right_op,
                        line=line,
                        column=column
                    )
        
        if self._is_number(expr):
            return Operation(
                type=OperationType.NOOP,
                value=expr,
                line=line,
                column=column
            )
        
        if (expr.startswith('"') and expr.endswith('"')) or (expr.startswith("'") and expr.endswith("'")):
            return Operation(
                type=OperationType.NOOP,
                value=expr,
                line=line,
                column=column
            )
        
        if expr.lower() in ['true', 'false']:
            return Operation(
                type=OperationType.NOOP,
                value=expr.lower(),
                line=line,
                column=column
            )
        
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