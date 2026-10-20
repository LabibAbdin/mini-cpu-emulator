; fibonacci.asm - writes the first 10 Fibonacci numbers to memory[0..9]
; Run with: python main.py programs/fibonacci.asm --memory 0 9

        MOV R0, #0          ; a = 0
        MOV R1, #1          ; b = 1
        MOV R2, #0          ; address to write to
        MOV R3, #10         ; how many numbers are left

loop:   CMP R3, #0
        BEQ done            ; stop when count reaches 0
        STR R0, [R2]        ; memory[address] = a
        ADD R4, R0, R1      ; next = a + b
        MOV R0, R1          ; a = b
        MOV R1, R4          ; b = next
        ADD R2, R2, #1      ; address = address + 1
        SUB R3, R3, #1      ; count = count - 1
        B loop

done:   HALT
