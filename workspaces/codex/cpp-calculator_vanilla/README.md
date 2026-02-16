# C++ Expression Calculator

A mathematical expression parser and interactive calculator implemented in modern C++.

## Features

- Parses and evaluates expressions from string input
- Operators with precedence and associativity: `+`, `-`, `*`, `/`, `%`, `^`
- Parentheses with arbitrary nesting
- Unary minus (for example `-5`, `-(3+2)`)
- Built-in functions:
  - `sin`, `cos`, `tan`, `sqrt`, `log`, `log10`, `abs`, `ceil`, `floor`, `min`, `max`
- Variable assignment and reuse (`x = 3.14`, then `x * 2`)
- Built-in constants: `pi`, `e`
- Expression history references: `$1`, `$2`, ...
- Interactive REPL mode with prompt, `help`, and `history`
- File evaluation mode (`--file <path>`)
- Clear error messages with token and source position
- Supports integer and floating-point arithmetic

## Project Structure

- `include/Lexer.h`, `src/Lexer.cpp`: tokenizer
- `include/AST.h`: AST node definitions
- `include/Parser.h`, `src/Parser.cpp`: recursive descent parser
- `include/Evaluator.h`, `src/Evaluator.cpp`: expression evaluator
- `include/Context.h`, `src/Context.cpp`: variables/constants/history runtime state
- `include/Calculator.h`, `src/Calculator.cpp`: orchestration API
- `include/Repl.h`, `src/Repl.cpp`: interactive REPL
- `src/main.cpp`: CLI entrypoint
- `tests/test_calculator.cpp`: doctest unit tests

## Build

Requirements:

- CMake 3.16+
- C++17 compiler

```bash
cmake -S . -B build
cmake --build build
```

## Run

Interactive REPL:

```bash
./build/calculator
```

Single expression:

```bash
./build/calculator "2 + 3 * 4"
```

File mode:

```bash
./build/calculator --file expressions.txt
```

Show usage:

```bash
./build/calculator --help
```

## Test

```bash
ctest --test-dir build --output-on-failure
```

Or run test binary directly:

```bash
./build/calculator_tests
```

## Example Expressions

```text
x = 3.14
sin(pi / 2)
max(10, 5, 7)
$1 + $2
-(3 + 2) * 4
```
