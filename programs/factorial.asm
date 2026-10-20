; factorial.asm - computes 5! = 120 and leaves the result in R0

        MOV R0, #1          ; result = 1
        MOV R1, #5          ; n = 5

loop:   CMP R1, #1          ; compare n with 1
        BLT done            ; if n < 1, we're finished
        MUL R0, R0, R1      ; result = result * n
        SUB R1, R1, #1      ; n = n - 1
        B loop              ; repeat

done:   HALT
