; Calculator - Generated from your code
; For Windows x64
; Build: nasm -f win64 calculator.asm && gcc calculator.obj -o calculator.exe

default rel
global main
extern printf, scanf, exit, _getch

section .data
    str_0 db "fib value: ", 0
    str_1 db "%d", 0
    str_2 db "%d", 13, 10, 0

section .bss
    ; Global variables

section .text

; ==================================================
; Function: fib
; Return type: int
; Local variables: ['n', 't1', 't2']
; ==================================================
fib:
    push rbp
    mov rbp, rsp
    sub rsp, 64
    mov [rbp+16], rcx ; save n
    mov dword [rbp-8], 0 ; t1 = 0
    mov dword [rbp-12], 0 ; t2 = 0
.Lfib_block_0:
    jmp .Lfib_block_2
.Lfib_block_2:
    mov eax, [rbp+16] ; load n
    cmp eax, 0 ; compare with 0
    je .Lfib_block_4  ; jump if equal
    jmp .Lfib_block_3
.Lfib_block_4:
    mov eax, [rbp+16] ; load n
    jmp .fib_exit
    jmp .Lfib_block_3
.Lfib_block_3:
    jmp .Lfib_block_5
.Lfib_block_5:
    mov eax, [rbp+16] ; load n
    cmp eax, 1 ; compare with 1
    je .Lfib_block_7  ; jump if equal
    jmp .Lfib_block_8
.Lfib_block_7:
    mov eax, [rbp+16] ; load n
    jmp .fib_exit
    jmp .Lfib_block_6
.Lfib_block_6:
    jmp .Lfib_block_1
.Lfib_block_1:
.Lfib_block_8:
    ; Variable t1 declared at [rbp-8]
    ; Variable t2 declared at [rbp-12]
    mov eax, [rbp+16] ; load n
    sub eax, 1
    mov [rbp-8], eax ; store t1
    mov eax, [rbp+16] ; load n
    sub eax, 2
    mov [rbp-12], eax ; store t2
    mov ecx, [rbp-8] ; load t1 for fib
    sub rsp, 32 ; shadow space
    call fib
    add rsp, 32
    push rax ; save result of left call
    mov ecx, [rbp-12] ; load t2 for fib
    sub rsp, 32 ; shadow space
    call fib
    add rsp, 32
    mov ebx, eax ; save result of right call
    pop rax ; restore left result
    add eax, ebx ; add both results
    jmp .fib_exit
    jmp .Lfib_block_6
.fib_exit:
    mov rsp, rbp
    pop rbp
    ret

; ==================================================
; Function: main
; Return type: int
; Local variables: ['a', 'result']
; ==================================================
main:
    push rbp
    mov rbp, rsp
    sub rsp, 48
    mov dword [rbp-8], 0 ; a = 0
    mov dword [rbp-12], 0 ; result = 0
.Lmain_block_9:
    ; Variable a declared at [rbp-8]
    ; Variable result declared at [rbp-12]
    ; Call printf
    lea rcx, [str_0]
    sub rsp, 32  ; shadow space
    call printf
    add rsp, 32
    ; Call scanf
    lea rcx, [str_1]
    lea rdx, [rbp-8] ; &a
    sub rsp, 32  ; shadow space
    call scanf
    add rsp, 32
    mov rcx, [rbp-8] ; a
    sub rsp, 32 ; shadow space
    call fib
    add rsp, 32
    mov [rbp-12], eax ; result = результат
    ; Call printf
    lea rcx, [str_2]
    mov rdx, [rbp-12] ; result
    sub rsp, 32  ; shadow space
    call printf
    add rsp, 32
    jmp .Lmain_block_10
.Lmain_block_10:
.main_exit:
    mov rsp, rbp
    pop rbp
    ret
