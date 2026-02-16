#pragma once

#include <cstddef>
#include <stdexcept>
#include <string>

namespace calc {

class CalcError : public std::runtime_error {
public:
    explicit CalcError(const std::string& message) : std::runtime_error(message) {}
};

class ParseError : public CalcError {
public:
    explicit ParseError(const std::string& message) : CalcError(message) {}
};

class EvalError : public CalcError {
public:
    explicit EvalError(const std::string& message) : CalcError(message) {}
};

enum class TokenType {
    End,
    Number,
    Identifier,
    HistoryRef,
    Plus,
    Minus,
    Star,
    Slash,
    Percent,
    Caret,
    LParen,
    RParen,
    Comma,
    Assign
};

struct Token {
    TokenType type{};
    std::string lexeme;
    std::size_t position{};
    double number_value{};
    int history_index{};
};

}  // namespace calc