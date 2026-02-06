# Makefile для генератора ассемблера

PYTHON = python3
SRC_DIR = test_files
OUTPUT_DIR = output
BUILD_DIR = build

# Примеры для сборки
EXAMPLES = $(wildcard $(SRC_DIR)/*.simple)

.PHONY: all clean build-linux build-win test help

all: calculator-linux calculator-win calculator-riscv  fibonacci-linux fibonacci-win fibonacci-riscv

calculator-riscv:
	@mkdir -p $(OUTPUT_DIR) $(BUILD_DIR)
	$(PYTHON) main.py $(SRC_DIR)/calculator.simple --output $(OUTPUT_DIR) --generator riscv
	@if [ -f "$(OUTPUT_DIR)/calculator_riscv.s" ]; then \
		echo "Ассемблирование RISC-V..."; \
		riscv64-linux-gnu-gcc -o $(BUILD_DIR)/calculator_riscv $(OUTPUT_DIR)/calculator_riscv.s -static -lc; \
		echo "Исполняемый файл RISC-V : $(BUILD_DIR)/calculator_riscv"; \
		echo "Для запуска: qemu-riscv64 $(BUILD_DIR)/calculator_riscv"; \
	fi

fibonacci-riscv:
	@mkdir -p $(OUTPUT_DIR) $(BUILD_DIR)
	$(PYTHON) main.py $(SRC_DIR)/fib.simple --output $(OUTPUT_DIR) --generator riscv
	@if [ -f "$(OUTPUT_DIR)/fib_riscv.s" ]; then \
		echo "Ассемблирование RISC-V..."; \
		riscv64-linux-gnu-gcc -o $(BUILD_DIR)/fib_riscv $(OUTPUT_DIR)/fib_riscv.s -static -lc; \
		echo "Исполняемый файл RISC-V : $(BUILD_DIR)/fib_riscv"; \
		echo "Для запуска: qemu-riscv64 $(BUILD_DIR)/fib_riscv"; \
	fi
# Сборка конкретного файла для Linux
calculator-linux:
	@mkdir -p $(OUTPUT_DIR) $(BUILD_DIR)
	$(PYTHON) main.py $(SRC_DIR)/calculator.simple --output $(OUTPUT_DIR) --generator linux
	@if [ -f "$(OUTPUT_DIR)/calculator_linux.asm" ]; then \
		echo "Компиляция NASM..."; \
		nasm -f elf64 $(OUTPUT_DIR)/calculator_linux.asm -o $(BUILD_DIR)/calculator_linux.o; \
		echo "Линковка GCC..."; \
		gcc -no-pie $(BUILD_DIR)/calculator_linux.o -o $(BUILD_DIR)/calculator_linux; \
		echo "Исполняемый файл создан: $(BUILD_DIR)/calculator_linux"; \
	fi

# Сборка конкретного файла для Windows
calculator-win:
	@mkdir -p $(OUTPUT_DIR) $(BUILD_DIR)
	$(PYTHON) main.py $(SRC_DIR)/calculator.simple --output $(OUTPUT_DIR) --generator win
	@if [ -f "$(OUTPUT_DIR)/calculator_win.asm" ]; then \
		echo "Компиляция NASM для Windows..."; \
		nasm -f win64 $(OUTPUT_DIR)/calculator_win.asm -o $(BUILD_DIR)/calculator_win.obj; \
		echo "Линковка для Windows..."; \
		gcc $(BUILD_DIR)/calculator_win.obj -o $(BUILD_DIR)/calculator_win.exe; \
		echo "Исполняемый файл создан: $(BUILD_DIR)/calculator_win.exe"; \
	fi

# Сборка конкретного файла для Linux
fibonacci-linux:
	@mkdir -p $(OUTPUT_DIR) $(BUILD_DIR)
	$(PYTHON) main.py $(SRC_DIR)/fib.simple --output $(OUTPUT_DIR) --generator linux
	@if [ -f "$(OUTPUT_DIR)/fib_linux.asm" ]; then \
		echo "Компиляция NASM..."; \
		nasm -f win64 $(OUTPUT_DIR)/fib_linux.asm -o $(BUILD_DIR)/fib_linux.o; \
		echo "Линковка GCC..."; \
		gcc $(BUILD_DIR)/fib_linux.o -o $(BUILD_DIR)/fib_linux; \
		echo "Исполняемый файл создан: $(BUILD_DIR)/fib_linux"; \
	fi

fibonacci-win:
	@mkdir -p $(OUTPUT_DIR) $(BUILD_DIR)
	$(PYTHON) main.py $(SRC_DIR)/fib.simple --output $(OUTPUT_DIR) --generator linux
	@if [ -f "$(OUTPUT_DIR)/fib_win.asm" ]; then \
		echo "Компиляция NASM..."; \
		nasm -f elf64 $(OUTPUT_DIR)/fib_win.asm -o $(BUILD_DIR)/fib_win.o; \
		echo "Линковка GCC..."; \
		gcc -no-pie $(BUILD_DIR)/fib_win.obj -o $(BUILD_DIR)/fib_win.exe; \
		echo "Исполняемый файл создан: $(BUILD_DIR)/fib_linux"; \
	fi
# Очистка
clean:
	rm -rf $(OUTPUT_DIR) $(BUILD_DIR)
	rm -f *.asm *.o *.obj *.exe

# Помощь
help:
	@echo "Доступные команды:"
	@echo ""
	@echo "  make all            		- Собрать все примеры"
	@echo ""
	@echo "  make calculator-linux 		- Собрать calculator для Linux"
	@echo "  make calculator-win 		- Собрать calculator для Windows"
	@echo "  make fibonacci-linux       - Собрать fibonacci для Linux"
	@echo ""
	@echo ""
	@echo "  make clean          		- Очистить выходные файлы"
	@echo "  make help           		- Показать эту справку"