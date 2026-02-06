# Компилятор Simple

Этот проект компилирует Simple язык программирования в ассемблер для разных платформ.

## Установка зависимостей

Для Linux:
```bash
sudo apt-get install nasm gcc
```

Для Windows:
```bash
# Установить NASM и MinGW
```

Для RISC-V:
```bash
sudo apt-get install gcc-riscv64-linux-gnu qemu-riscv64
```

## Запуск

### Быстрый запуск

Скомпилировать все примеры:
```bash
make all
```

Очистить выходные файлы:
```bash
make clean
```

### Детальные команды

Сборка калькулятора для Linux:
```bash
make calculator-linux
./build/calculator_linux
```

Сборка калькулятора для Windows:
```bash
make calculator-win
./build/calculator_win.exe
```

Сборка калькулятора для RISC-V:
```bash
make calculator-riscv
qemu-riscv64 build/calculator_riscv
```

Сборка чисел Фибоначчи для Linux:
```bash
make fibonacci-linux
./build/fib_linux
```

Сборка чисел Фибоначчи для Windows:
```bash
make fibonacci-win
./build/fib_win.exe
```

Сборка чисел Фибоначчи для RISC-V:
```bash
make fibonacci-riscv
qemu-riscv64 build/fib_riscv
```

### Ручной запуск

Генерация ассемблера:
```bash
python3 main.py test_files/calculator.simple --output output --generator linux
```

Доступные генераторы:
- `linux` - Linux x86-64 (NASM)
- `win` - Windows x86-64 (MASM)  
- `riscv` - RISC-V (GCC)

## Структура проекта

- `test_files/` - исходные файлы Simple
- `output/` - сгенерированные ассемблерные файлы
- `build/` - скомпилированные исполняемые файлы

## Помощь

Показать все доступные команды:
```bash
make help
```
