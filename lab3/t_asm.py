# debug_asm.py
def generate_simple_windows_asm() -> str:
    """Генерирует простой рабочий ассемблерный код для Windows"""
    
    return '''
; Простой калькулятор для Windows x64
; nasm -f win64 calculator.asm
; gcc calculator.obj -o calculator.exe

default rel
global main
extern printf, scanf, exit

section .data
    fmt_input   db "%d %c %d", 0
    fmt_output  db "result: %d", 10, 0
    msg_prompt  db "Enter expression (e.g., 5 + 3): ", 0

section .bss
    num1    resd 1
    num2    resd 1
    op      resb 1
    result  resd 1

section .text

; Функция calculate
calculate:
    push rbp
    mov rbp, rsp
    
    ; Загрузка значений
    mov eax, [num1]
    mov ebx, [num2]
    mov cl, [op]
    
    ; Проверка оператора
    cmp cl, '+'
    je .add_op
    cmp cl, '-'
    je .sub_op
    cmp cl, '*'
    je .mul_op
    cmp cl, '/'
    je .div_op
    jmp .end_calc
    
.add_op:
    add eax, ebx
    jmp .store_result
    
.sub_op:
    sub eax, ebx
    jmp .store_result
    
.mul_op:
    imul eax, ebx
    jmp .store_result
    
.div_op:
    xor edx, edx
    idiv ebx
    
.store_result:
    mov [result], eax
    
.end_calc:
    ; Вывод результата
    mov rcx, fmt_output
    mov edx, [result]
    call printf
    
    mov rsp, rbp
    pop rbp
    ret

; Главная функция
main:
    push rbp
    mov rbp, rsp
    
    ; Вывод приглашения
    mov rcx, msg_prompt
    call printf
    
    ; Ввод данных
    mov rcx, fmt_input
    mov rdx, num1
    mov r8, op
    mov r9, num2
    call scanf
    
    ; Вызов функции calculate
    call calculate
    
    ; Возврат 0
    xor eax, eax
    
    mov rsp, rbp
    pop rbp
    ret
'''

# Сохраняем в файл
with open('simple_calculator.asm', 'w') as f:
    f.write(generate_simple_windows_asm())

print("Файл simple_calculator.asm создан")
print("Для сборки выполните:")
print("  nasm -f win64 simple_calculator.asm")
print("  gcc simple_calculator.obj -o calculator.exe")