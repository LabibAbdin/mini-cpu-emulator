; array_stats.asm - finds the sum (R0) and maximum (R1) of an array in memory

.data 100: 4, 8, 42, 15, 16, 23   ; six numbers stored at addresses 100-105

        MOV R0, #0          ; sum = 0
        LDR R1, [R2, #100]  ; max = first element (R2 is 0 here)
        MOV R2, #100        ; pointer to the current element
        MOV R3, #6          ; elements left

loop:   CMP R3, #0
        BEQ done
        LDR R4, [R2]        ; value = memory[pointer]
        ADD R0, R0, R4      ; sum = sum + value
        CMP R4, R1
        BLT next            ; skip if value < max
        MOV R1, R4          ; otherwise max = value
next:   ADD R2, R2, #1      ; move to the next element
        SUB R3, R3, #1
        B loop

done:   HALT
