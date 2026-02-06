.section .data
str_0: .asciz "Enter expression: "
str_1: .asciz "%d %c %d"
str_2: .asciz "result: %d\n"

.section .text
.globl main

# ==================================================
# Function: main
# Return type: int
# Local variables: ['num1', 'num2', 'op', 'result']
# ==================================================
main:
    addi sp, sp, -48
    sd ra, 32(sp)
    sd s0, 40(sp)
    addi s0, sp, 0
    sd zero, 0(sp)  # num1 = 0
    sd zero, 8(sp)  # num2 = 0
    sd zero, 16(sp)  # op = 0
    sd zero, 24(sp)  # result = 0
.Lmain_block_0:
    # Variable num1 declared
    # Variable num2 declared
    # Variable op declared
    # Variable result declared
    j .Lmain_block_2
.Lmain_block_2:
    li a0, 1  # while(1) condition
    bne a0, zero, .Lmain_block_4
    j .Lmain_block_3
.Lmain_block_4:
    la a0, str_0
    jal ra, printf
    la a0, str_1
    addi a1, sp, 0  # &num1
    addi a2, sp, 16  # &op
    addi a3, sp, 8  # &num2
    jal ra, scanf
    j .Lmain_block_5
.Lmain_block_5:
    ld a0, 16(sp)  # load op
    li a1, 43
    beq a0, a1, .Lmain_block_7
    j .Lmain_block_8
.Lmain_block_7:
    ld a0, 0(sp)  # load num1
    ld a1, 8(sp)
    add a0, a0, a1
    sd a0, 24(sp)  # store in result
    j .Lmain_block_6
.Lmain_block_6:
    la a0, str_2
    ld a1, 24(sp)  # result
    jal ra, printf
    j .Lmain_block_2
.Lmain_block_8:
    j .Lmain_block_9
.Lmain_block_9:
    ld a0, 16(sp)  # load op
    li a1, 45
    beq a0, a1, .Lmain_block_11
    j .Lmain_block_12
.Lmain_block_11:
    ld a0, 0(sp)  # load num1
    ld a1, 8(sp)
    sub a0, a0, a1
    sd a0, 24(sp)  # store result
    j .Lmain_block_10
.Lmain_block_10:
    j .Lmain_block_6
.Lmain_block_12:
    j .Lmain_block_13
.Lmain_block_13:
    ld a0, 16(sp)  # load op
    li a1, 42
    beq a0, a1, .Lmain_block_15
    j .Lmain_block_16
.Lmain_block_15:
    ld a0, 0(sp)  # load num1
    ld a1, 8(sp)
    mul a0, a0, a1
    sd a0, 24(sp)  # store in result
    j .Lmain_block_14
.Lmain_block_14:
    j .Lmain_block_10
.Lmain_block_16:
    j .Lmain_block_17
.Lmain_block_17:
    ld a0, 16(sp)  # load op
    li a1, 47
    beq a0, a1, .Lmain_block_19
    j .Lmain_block_18
.Lmain_block_19:
    ld a0, 0(sp)  # load num1
    ld a1, 8(sp)
    div a0, a0, a1
    sd a0, 24(sp)  # store in result
    j .Lmain_block_18
.Lmain_block_18:
    j .Lmain_block_14
.Lmain_block_3:
    j .Lmain_block_1
.Lmain_block_1:
main_exit:
    ld ra, 32(sp)
    ld s0, 40(sp)
    addi sp, sp, 48
    ret
