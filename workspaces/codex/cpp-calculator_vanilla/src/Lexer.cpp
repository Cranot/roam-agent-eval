#include "Lexer.h"

#include <cctype>
#include <cstdlib>
#include <sstream>

namespace calc {

Lexer::Lexer(std::string input) : input_(std::move(input)) {}

std::vector<Token> Lexer::tokenize() {
    std::vector<Token> tokens;

    while (!isAtEnd()) {
        skipWhitespace();
        if (isAtEnd()) {
            break;
        }

        const char c = currentChar();
        const std::size_t token_pos = pos_;

        if (std::isdigit(static_cast<unsigned char>(c)) || (c == '.' && std::isdigit(static_cast<unsigned char>(peekChar())))) {
            tokens.push_back(lexNumber());
            continue;
        }

        if (isIdentifierStart(c)) {
            tokens.push_back(lexIdentifier());
            continue;
        }

        if (c == '$') {
            tokens.push_back(lexHistoryRef());
            continue;
        }

        advance();
        Token token;
        token.position = token_pos;
        token.lexeme = std::string(1, c);

        switch (c) {
            case '+': token.type = TokenType::Plus; break;
            case '-': token.type = TokenType::Minus; break;
            case '*': token.type = TokenType::Star; break;
            case '/': token.type = TokenType::Slash; break;
            case '%': token.type = TokenType::Percent; break;
            case '^': token.type = TokenType::Caret; break;
            case '(': token.type = TokenType::LParen; break;
            case ')': token.type = TokenType::RParen; break;
            case ',': token.type = TokenType::Comma; break;
            case '=': token.type = TokenType::Assign; break;
            default: {
                std::ostringstream oss;
                oss << "Unexpected token '" << c << "' at position " << token_pos;
                throw ParseError(oss.str());
            }
        }

        tokens.push_back(token);
    }

    tokens.push_back(Token{TokenType::End, "", pos_, 0.0, 0});
    return tokens;
}

bool Lexer::isAtEnd() const {
    return pos_ >= input_.size();
}

char Lexer::currentChar() const {
    return isAtEnd() ? '\0' : input_[pos_];
}

char Lexer::peekChar(std::size_t offset) const {
    const std::size_t idx = pos_ + offset;
    return idx < input_.size() ? input_[idx] : '\0';
}

void Lexer::advance() {
    if (!isAtEnd()) {
        ++pos_;
    }
}

void Lexer::skipWhitespace() {
    while (!isAtEnd() && std::isspace(static_cast<unsigned char>(currentChar()))) {
        advance();
    }
}

Token Lexer::lexNumber() {
    const std::size_t start = pos_;
    bool has_digits = false;

    while (std::isdigit(static_cast<unsigned char>(currentChar()))) {
        has_digits = true;
        advance();
    }

    if (currentChar() == '.') {
        advance();
        while (std::isdigit(static_cast<unsigned char>(currentChar()))) {
            has_digits = true;
            advance();
        }
    }

    if (!has_digits) {
        std::ostringstream oss;
        oss << "Unexpected token '" << currentChar() << "' at position " << start;
        throw ParseError(oss.str());
    }

    if (currentChar() == 'e' || currentChar() == 'E') {
        const std::size_t exp_start = pos_;
        advance();
        if (currentChar() == '+' || currentChar() == '-') {
            advance();
        }

        std::size_t exp_digits = 0;
        while (std::isdigit(static_cast<unsigned char>(currentChar()))) {
            ++exp_digits;
            advance();
        }

        if (exp_digits == 0) {
            std::ostringstream oss;
            oss << "Invalid number at position " << exp_start;
            throw ParseError(oss.str());
        }
    }

    const std::string lexeme = input_.substr(start, pos_ - start);

    Token token;
    token.type = TokenType::Number;
    token.lexeme = lexeme;
    token.position = start;
    token.number_value = std::stod(lexeme);
    return token;
}

Token Lexer::lexIdentifier() {
    const std::size_t start = pos_;
    while (isIdentifierPart(currentChar())) {
        advance();
    }

    Token token;
    token.type = TokenType::Identifier;
    token.lexeme = input_.substr(start, pos_ - start);
    token.position = start;
    return token;
}

Token Lexer::lexHistoryRef() {
    const std::size_t start = pos_;
    advance();

    std::size_t digits = 0;
    while (std::isdigit(static_cast<unsigned char>(currentChar()))) {
        ++digits;
        advance();
    }

    if (digits == 0) {
        std::ostringstream oss;
        oss << "Unexpected token '$' at position " << start;
        throw ParseError(oss.str());
    }

    const std::string text = input_.substr(start + 1, digits);

    Token token;
    token.type = TokenType::HistoryRef;
    token.lexeme = "$" + text;
    token.position = start;
    token.history_index = std::stoi(text);
    return token;
}

bool Lexer::isIdentifierStart(char c) {
    return std::isalpha(static_cast<unsigned char>(c)) || c == '_';
}

bool Lexer::isIdentifierPart(char c) {
    return std::isalnum(static_cast<unsigned char>(c)) || c == '_';
}

}  // namespace calc
