; Calculator - Generated from your code
; For Windows x64
; Build: nasm -f win64 calculator.asm && gcc calculator.obj -o calculator.exe

default rel
global main
extern printf, scanf, exit, _getch

section .data
    str_0 db "Enter value: ", 0
    str_1 db "%d", 0
    str_2 db "%d", 13, 10, 0

section .bss
    ; Global variables

section .text

; ==================================================
; Function: main
; Return type: int
; Local variables: ['a']
; ==================================================
main:
    push rbp
    mov rbp, rsp
    sub rsp, 16
    mov dword [rbp-8], 0 ; a = 0
.Lmain_block_0:
    ; Variable a declared at [rbp-8]
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
    lea rdx, [rbp-8] ; &a
    sub rsp, 32  ; shadow space
    call scanf
    add rsp, 32
    ; Call printf
    lea rcx, [str_2]
    mov rdx, [rbp-8] ; a
    sub rsp, 32  ; shadow space
    call printf
    add rsp, 32
    jmp .Lmain_block_2
.Lmain_block_3:
    jmp .Lmain_block_1
.Lmain_block_1:
.main_exit:
    xor eax, eax  ; return 0
    mov rsp, rbp
    pop rbp
    ret
