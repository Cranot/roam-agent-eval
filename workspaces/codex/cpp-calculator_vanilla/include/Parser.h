#pragma once

#include <cstddef>
#include <vector>

#include "AST.h"
#include "Token.h"

namespace calc {

class Parser {
public:
    explicit Parser(std::vector<Token> tokens);

    NodePtr parseStatement();

private:
    std::vector<Token> tokens_;
    std::size_t pos_ = 0;

    const Token& current() const;
    const Token& peek(std::size_t offset = 1) const;
    bool check(TokenType type) const;
    bool match(TokenType type);
    const Token& advance();
    const Token& expect(TokenType type);

    [[noreturn]] void throwUnexpected(const Token& token) const;

    NodePtr parseExpression();
    NodePtr parseAdditive();
    NodePtr parseMultiplicative();
    NodePtr parseUnary();
    NodePtr parsePower();
    NodePtr parsePrimary();
};

}  // namespace calc
