.section .data
str_0: .asciz "fib value: "
str_1: .asciz "%d"
str_2: .asciz "%d\n"

.section .text
.globl main

# ==================================================
# Function: fib
# Return type: int
# Local variables: ['n', 't1', 't2']
# ==================================================
fib:
    addi sp, sp, -40
    sd ra, 24(sp)
    sd s0, 32(sp)
    addi s0, sp, 0
    sd a0, 0(sp)  # save n
    sd zero, 8(sp)  # t1 = 0
    sd zero, 16(sp)  # t2 = 0
.Lfib_block_0:
    j .Lfib_block_2
.Lfib_block_2:
    ld a0, 0(sp)  # load n
    li a1, 0
    beq a0, a1, .Lfib_block_4
    j .Lfib_block_3
.Lfib_block_4:
    ld a0, 0(sp)  # load n
    j fib_exit
    j .Lfib_block_3
.Lfib_block_3:
    j .Lfib_block_5
.Lfib_block_5:
    ld a0, 0(sp)  # load n
    li a1, 1
    beq a0, a1, .Lfib_block_7
    j .Lfib_block_8
.Lfib_block_7:
    ld a0, 0(sp)  # load n
    j fib_exit
    j .Lfib_block_6
.Lfib_block_6:
    j .Lfib_block_1
.Lfib_block_1:
.Lfib_block_8:
    # Variable t1 declared
    # Variable t2 declared
    ld a0, 0(sp)  # load n
    addi a0, a0, -1
    sd a0, 8(sp)  # store t1
    ld a0, 0(sp)  # load n
    addi a0, a0, -2
    sd a0, 16(sp)  # store t2
    ld a0, 8(sp)  # load t1 (already n-1)
    jal ra, fib
    sd a0, 8(sp)  # save fib(n-1)
    ld a0, 16(sp)  # load t2 (already n-2)
    jal ra, fib
    ld t0, 8(sp)  # restore fib(n-1)
    add a0, t0, a0  # a0 = fib(n-1) + fib(n-2)
    j fib_exit
    j .Lfib_block_6
fib_exit:
    ld ra, 24(sp)
    ld s0, 32(sp)
    addi sp, sp, 40
    ret

# ==================================================
# Function: main
# Return type: int
# Local variables: ['a', 'result']
# ==================================================
main:
    addi sp, sp, -32
    sd ra, 16(sp)
    sd s0, 24(sp)
    addi s0, sp, 0
    sd zero, 0(sp)  # a = 0
    sd zero, 8(sp)  # result = 0
.Lmain_block_9:
    # Variable a declared
    # Variable result declared
    la a0, str_0
    jal ra, printf
    la a0, str_1
    addi a1, sp, 0  # &a
    jal ra, scanf
    ld a0, 0(sp)  # a
    jal ra, fib
    sd a0, 8(sp)  # result = результат
    la a0, str_2
    ld a1, 8(sp)  # result
    jal ra, printf
    j .Lmain_block_10
.Lmain_block_10:
main_exit:
    ld ra, 16(sp)
    ld s0, 24(sp)
    addi sp, sp, 32
    ret
