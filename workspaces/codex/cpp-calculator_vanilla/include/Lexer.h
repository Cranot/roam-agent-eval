#pragma once

#include <string>
#include <vector>

#include "Token.h"

namespace calc {

class Lexer {
public:
    explicit Lexer(std::string input);

    std::vector<Token> tokenize();

private:
    std::string input_;
    std::size_t pos_ = 0;

    bool isAtEnd() const;
    char currentChar() const;
    char peekChar(std::size_t offset = 1) const;
    void advance();

    void skipWhitespace();
    Token lexNumber();
    Token lexIdentifier();
    Token lexHistoryRef();

    static bool isIdentifierStart(char c);
    static bool isIdentifierPart(char c);
};

}  // namespace calc
