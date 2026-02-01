; Calculator - Generated from your code
; For Windows x64
; Build: nasm -f win64 calculator.asm && gcc calculator.obj -o calculator.exe

default rel
global main
extern printf, scanf, exit, _getch

section .data
    str_0 db "Enter expression: ", 0
    str_1 db "%d %c %d", 0
    str_2 db "result: %d", 13, 10, 0

section .bss
    ; Global variables

section .text

; ==================================================
; Function: main
; Return type: int
; Local variables: ['num1', 'num2', 'op', 'result']
; ==================================================
main:
    push rbp
    mov rbp, rsp
    sub rsp, 64
    mov dword [rbp-8], 0 ; num1 = 0
    mov dword [rbp-12], 0 ; num2 = 0
    mov byte [rbp-16], 0 ; op = 0
    mov dword [rbp-17], 0 ; result = 0
.Lmain_block_0:
    ; Variable num1 declared at [rbp-8]
    ; Variable num2 declared at [rbp-12]
    ; Variable op declared at [rbp-16]
    ; Variable result declared at [rbp-17]
    jmp .Lmain_block_2
.Lmain_block_2:
    mov eax, 1  ; while(1) condition
    test eax, eax  ; test condition
    jnz .Lmain_block_4  ; jump if true
    jmp .Lmain_block_3 ; jump if false
.Lmain_block_4:
    ; Call printf
    lea rcx, [str_0]
    sub rsp, 32  ; shadow space
    call printf
    add rsp, 32
    ; Call scanf
    lea rcx, [str_1]
    lea rdx, [rbp-8] ; &num1
    lea r8, [rbp-16] ; &op
    lea r9, [rbp-12] ; &num2
    sub rsp, 32  ; shadow space
    call scanf
    add rsp, 32
    jmp .Lmain_block_5
.Lmain_block_5:
    mov eax, [rbp-16] ; load op
    cmp eax, 43 ; compare with '+'
    je .Lmain_block_7  ; jump if equal
    jmp .Lmain_block_8
.Lmain_block_7:
    mov eax, [rbp-8] ; load num1
    add eax, [rbp-12] ; add num2
    mov [rbp-17], eax ; store in result
    jmp .Lmain_block_6
.Lmain_block_6:
    ; Call printf
    lea rcx, [str_2]
    mov rdx, [rbp-17] ; result
    sub rsp, 32  ; shadow space
    call printf
    add rsp, 32
    jmp .Lmain_block_2
.Lmain_block_8:
    jmp .Lmain_block_9
.Lmain_block_9:
    mov eax, [rbp-16] ; load op
    cmp eax, 45 ; compare with '-'
    je .Lmain_block_11  ; jump if equal
    jmp .Lmain_block_12
.Lmain_block_11:
    mov eax, [rbp-8] ; load num1
    sub eax, [rbp-12] ; subtract num2
    mov [rbp-17], eax ; store result
    jmp .Lmain_block_10
.Lmain_block_10:
    jmp .Lmain_block_6
.Lmain_block_12:
    jmp .Lmain_block_13
.Lmain_block_13:
    mov eax, [rbp-16] ; load op
    cmp eax, 42 ; compare with '*'
    je .Lmain_block_15  ; jump if equal
    jmp .Lmain_block_16
.Lmain_block_15:
    mov eax, [rbp-8] ; load num1
    imul eax, [rbp-12] ; multiply by num2
    mov [rbp-17], eax ; store in result
    jmp .Lmain_block_14
.Lmain_block_14:
    jmp .Lmain_block_10
.Lmain_block_16:
    jmp .Lmain_block_17
.Lmain_block_17:
    mov eax, [rbp-16] ; load op
    cmp eax, 47 ; compare with '/'
    je .Lmain_block_19  ; jump if equal
    jmp .Lmain_block_18
.Lmain_block_19:
    mov eax, [rbp-8] ; load num1
    cdq
    idiv dword [rbp-12] ; divide by num2
    mov [rbp-17], eax ; store in result
    jmp .Lmain_block_18
.Lmain_block_18:
    jmp .Lmain_block_14
.Lmain_block_3:
    jmp .Lmain_block_1
.Lmain_block_1:
.main_exit:
    mov rsp, rbp
    pop rbp
    ret
