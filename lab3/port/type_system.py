class TypeSystem:
    """Система типов для языка"""
    
    # Базовые типы
    BUILTIN_TYPES = {
        'int': {
            'size': 4,
            'signed': True,
            'asm_prefix': 'dword',
            'register_size': 32,
        },
        'float': {
            'size': 4,
            'signed': True,
            'asm_prefix': 'dword',
            'register_size': 32,
        },
        'double': {
            'size': 8,
            'signed': True,
            'asm_prefix': 'qword',
            'register_size': 64,
        },
        'char': {
            'size': 1,
            'signed': True,
            'asm_prefix': 'byte',
            'register_size': 8,
        },
        'bool': {
            'size': 1,
            'signed': False,
            'asm_prefix': 'byte',
            'register_size': 8,
        },
        'void': {
            'size': 0,
            'signed': False,
            'asm_prefix': None,
            'register_size': 0,
        },
        'string': {
            'size': 8,
            'signed': False,
            'asm_prefix': 'qword',
            'register_size': 64,
        },
    }
    
    @staticmethod
    def is_valid_type(type_name: str) -> bool:
        """Проверяет, является ли тип допустимым"""
        return type_name in TypeSystem.BUILTIN_TYPES
    
    @staticmethod
    def get_type_info(type_name: str) -> dict:
        """Возвращает информацию о типе"""
        return TypeSystem.BUILTIN_TYPES.get(type_name, {
            'size': 4,
            'signed': True,
            'asm_prefix': 'dword',
            'register_size': 32,
        })
    
    @staticmethod
    def get_size(type_name: str) -> int:
        """Возвращает размер типа в байтах"""
        return TypeSystem.get_type_info(type_name)['size']
    
    @staticmethod
    def get_asm_prefix(type_name: str) -> str:
        """Возвращает префикс для ассемблера"""
        return TypeSystem.get_type_info(type_name)['asm_prefix']
    
    @staticmethod
    def can_implicit_cast(from_type: str, to_type: str) -> bool:
        """Проверяет возможность неявного преобразования типов"""
        # Правила неявного преобразования
        cast_rules = {
            'int': ['float', 'double'],
            'float': ['double'],
            'char': ['int', 'float', 'double'],
        }
        
        if from_type == to_type:
            return True
        
        return to_type in cast_rules.get(from_type, [])
