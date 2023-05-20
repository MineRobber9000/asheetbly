# asheetbly Specification - 0.x

asheetbly (stylized in all lowercase) is an assembly language in spreadsheet form. (Think BANCStar but on purpose.)

## Addresses

asheetbly memory is best understood in terms of the spreadsheet as a whole. Code execution flows down the rows, from A1 until a HALT is reached or a JUMP directs code execution elsewhere. Addresses are referred to using A1 notation (from left to right, A1 is (1,1) to Z1 being (26,1), then AA1 is (27,1) to AZ1 is (52,1), etc).

## Architecture

The asheetbly VM is a stack-based virtual machine. Instructions manipulate the stack and the spreadsheet.

## Instructions

Instructions are encoded by their names, with arguments being in the cells to their right (so an instruction in A1 has its first argument in B1, its second in C1, etc).

### Memory

#### LOAD_CELL,A1

```
A B -> A B C
where C is the value at A1
```

Places the value at the given address on top of the stack.

#### STORE_CELL,A1

```
A B -> A
where B is stored at A1
```

Pops the value from the top of the stack and stores it at the given address.

### Stack Operations

#### DROP

```
A B -> A
```

Pops the value from the top of the stack and discards it.

#### DUP

```
A B -> A B B
```

Duplicates the value from the top of the stack.

#### OVER

```
A B -> A B A
```

Duplicates the value from the spot just behind the top of the stack.

#### SWAP

```
A B -> B A
```

Swaps the two values at the top of the stack.

### Arithmetic

Attempts to perform arithmetic with strings will cause an error.

#### ADD

```
A B -> C
where C = A+B
```

#### SUB

```
A B -> C
where C=A-B
```

#### MULT

```
A B -> C
where C=A*B
```

#### DIV

```
A B -> C
where C=A/B
```

#### FDIV

```
A B -> C
where C=A/B, floored
```

#### MOD

```
A B -> C
where C=A%B
```

### String Operations

Unlike with arithmetic, string operations will work on float values, albeit with possible unexpected side effects.

#### UPPER

```
A -> B
where B is A, but uppercased
```

#### LOWER

```
A -> B
where B is A, but lowercased
```

#### CONCAT

```
A B -> C
where C is A and B concatenated
```

### I/O Operations

#### IN,PROMPT

```
A B -> A B C
where C is user input
```

Accepts input from the user. If prompt is provided, it is used.

#### OUT

```
A B -> A
where B is output to the screen
```

Outputs the top value on the stack to the screen.

### Control Flow

Conditional control flow is done with the COND flag, which can be set to true or false (it begins the program's execution as false).

#### TEST

```
A B -> A B
COND = (B==0)
```

Sets the COND flag according to whether the value at the top of the stack is 0 or not.

#### COMPARE,[A1]

```
if A1 provided:
A B -> A B
COND = (B==[A1])

else:
A B -> A B
COND = (A==B)
```

Compares either the top two items on the stack or the top item on the stack to a given address, and sets the COND flag accordingly.

#### LT,[A1]

```
if A1 provided:
A B -> A B
COND = (B<[A1])

else:
A B -> A B
COND = (A<B)
```

Like COMPARE, but less than instead of equal to.

#### GT,[A1]

```
if A1 provided:
A B -> A B
COND = (B>[A1])

else:
A B -> A B
COND = (A>B)
```

Like LT, but greater than instead of less than.

#### INVERT_COND

```
COND = !COND
```

Inverts COND.

#### JUMP,A1

Unconditionally jumps to A1.

#### JUMP_IF,A1

Jumps to A1 if the COND flag is set.

#### CALL,A1,[N]

Calls the subroutine at A1 with N arguments (defaulting to 0). (Arguments are essentially values at the top of the stack that will be available to the subroutine.)

#### CALL_IF,A1,[N]

Same as CALL, but only if the COND flag is set.

#### RETURN

Returns from a subroutine. Errors if a subroutine was not called.

### Random Number Generation

#### RAND,[M],[N]

Generates a random floating-point number between M and N (defaulting to 0 and 1 respectively).

#### RANDINT,M,[N]

Generates a random integer between M and N. If N is not defined, a number between 1 and M inclusive will be generated. If N is defined, a number between M and N inclusive will be generated.

### HALT

Stops execution of the program. (If execution reaches an empty or float cell, HALT will be the assumed opcode.)
