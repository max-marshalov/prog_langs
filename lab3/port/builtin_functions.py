class BuiltinFunctions:
    """Информация о встроенных функциях"""
    
    STANDARD_FUNCTIONS = {
        'printf': {
            'return_type': 'int',
            'parameters': [('format', 'string')],
            'variadic': True  # может принимать переменное число аргументов
        },
        'scanf': {
            'return_type': 'int',
            'parameters': [('format', 'string')],
            'variadic': True
        },
        'malloc': {
            'return_type': 'void*',
            'parameters': [('size', 'int')]
        },
        'free': {
            'return_type': 'void',
            'parameters': [('ptr', 'void*')]
        },
        'strlen': {
            'return_type': 'int',
            'parameters': [('str', 'string')]
        },
        # Добавьте другие функции по мере необходимости
    }
    
    @staticmethod
    def is_standard_function(name: str) -> bool:
        return name in BuiltinFunctions.STANDARD_FUNCTIONS
    
    @staticmethod
    def get_function_info(name: str) -> dict:
        return BuiltinFunctions.STANDARD_FUNCTIONS.get(name, {
            'return_type': 'int',  # по умолчанию
            'parameters': [],
            'variadic': False
        })