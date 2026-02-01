; Calculator - Generated from your code
; For Windows x64
; Build: nasm -f win64 calculator.asm && gcc calculator.obj -o calculator.exe

default rel
global main
extern printf, scanf, exit, _getch

section .data
    str_0 db "value: ", 0
    str_1 db "%d", 0
    str_2 db "%d", 13, 10, 0

section .bss
    ; Global variables

section .text

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
.Lmain_block_0:
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
    call sum
    add rsp, 32
    mov [rbp-12], eax ; result = результат
    ; Call printf
    lea rcx, [str_2]
    mov rdx, [rbp-12] ; result
    sub rsp, 32  ; shadow space
    call printf
    add rsp, 32
    jmp .Lmain_block_1
.Lmain_block_1:
.main_exit:
    mov rsp, rbp
    pop rbp
    ret

; ==================================================
; Function: sum
; Return type: int
; Local variables: ['n', 'temp']
; ==================================================
sum:
    push rbp
    mov rbp, rsp
    sub rsp, 48
    mov [rbp+16], rcx ; save n
    mov dword [rbp-8], 0 ; temp = 0
.Lsum_block_2:
    jmp .Lsum_block_4
.Lsum_block_4:
    mov eax, [rbp+16] ; load n
    cmp eax, 1 ; compare with 1
    je .Lsum_block_6  ; jump if equal
    jmp .Lsum_block_7
.Lsum_block_6:
    mov eax, [rbp+16] ; load n
    jmp .sum_exit
    jmp .Lsum_block_5
.Lsum_block_5:
    jmp .Lsum_block_3
.Lsum_block_3:
.Lsum_block_7:
    ; Variable temp declared at [rbp-8]
    mov eax, [rbp+16] ; load n
    sub eax, 1
    mov [rbp-8], eax ; store temp
    mov eax, [rbp+16] ; load n
    push rax ; save n
    mov ecx, [rbp-8] ; load temp for sum
    sub rsp, 32 ; shadow space
    call sum
    add rsp, 32
    mov ebx, eax ; save sum(temp) result
    pop rax ; restore n
    add eax, ebx ; n + sum(temp)
    jmp .sum_exit
    jmp .Lsum_block_5
.sum_exit:
    mov rsp, rbp
    pop rbp
    ret
