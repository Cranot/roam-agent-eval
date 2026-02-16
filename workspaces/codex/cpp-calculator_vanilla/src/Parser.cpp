#include "Parser.h"

#include <sstream>
#include <utility>

namespace calc {

Parser::Parser(std::vector<Token> tokens) : tokens_(std::move(tokens)) {}

NodePtr Parser::parseStatement() {
    NodePtr node;

    if (check(TokenType::Identifier) && peek().type == TokenType::Assign) {
        const std::string name = current().lexeme;
        advance();
        advance();
        node = std::make_unique<AssignmentNode>(name, parseExpression());
    } else {
        node = parseExpression();
    }

    if (!check(TokenType::End)) {
        throwUnexpected(current());
    }

    return node;
}

const Token& Parser::current() const {
    return tokens_[pos_];
}

const Token& Parser::peek(std::size_t offset) const {
    const std::size_t idx = pos_ + offset;
    if (idx >= tokens_.size()) {
        return tokens_.back();
    }
    return tokens_[idx];
}

bool Parser::check(TokenType type) const {
    return current().type == type;
}

bool Parser::match(TokenType type) {
    if (!check(type)) {
        return false;
    }
    advance();
    return true;
}

const Token& Parser::advance() {
    if (pos_ < tokens_.size() - 1) {
        ++pos_;
    }
    return tokens_[pos_ - 1];
}

const Token& Parser::expect(TokenType type) {
    if (!check(type)) {
        throwUnexpected(current());
    }
    return advance();
}

[[noreturn]] void Parser::throwUnexpected(const Token& token) const {
    std::ostringstream oss;
    const std::string shown = token.lexeme.empty() ? "<end>" : token.lexeme;
    oss << "Unexpected token '" << shown << "' at position " << token.position;
    throw ParseError(oss.str());
}

NodePtr Parser::parseExpression() {
    return parseAdditive();
}

NodePtr Parser::parseAdditive() {
    NodePtr node = parseMultiplicative();

    while (true) {
        if (match(TokenType::Plus)) {
            node = std::make_unique<BinaryNode>(BinaryOp::Add, std::move(node), parseMultiplicative());
            continue;
        }
        if (match(TokenType::Minus)) {
            node = std::make_unique<BinaryNode>(BinaryOp::Subtract, std::move(node), parseMultiplicative());
            continue;
        }
        break;
    }

    return node;
}

NodePtr Parser::parseMultiplicative() {
    NodePtr node = parseUnary();

    while (true) {
        if (match(TokenType::Star)) {
            node = std::make_unique<BinaryNode>(BinaryOp::Multiply, std::move(node), parseUnary());
            continue;
        }
        if (match(TokenType::Slash)) {
            node = std::make_unique<BinaryNode>(BinaryOp::Divide, std::move(node), parseUnary());
            continue;
        }
        if (match(TokenType::Percent)) {
            node = std::make_unique<BinaryNode>(BinaryOp::Modulo, std::move(node), parseUnary());
            continue;
        }
        break;
    }

    return node;
}

NodePtr Parser::parseUnary() {
    if (match(TokenType::Minus)) {
        return std::make_unique<UnaryNode>(UnaryOp::Negate, parseUnary());
    }

    return parsePower();
}

NodePtr Parser::parsePower() {
    NodePtr node = parsePrimary();

    if (match(TokenType::Caret)) {
        node = std::make_unique<BinaryNode>(BinaryOp::Power, std::move(node), parseUnary());
    }

    return node;
}

NodePtr Parser::parsePrimary() {
    if (match(TokenType::Number)) {
        return std::make_unique<NumberNode>(tokens_[pos_ - 1].number_value);
    }

    if (match(TokenType::HistoryRef)) {
        return std::make_unique<HistoryRefNode>(tokens_[pos_ - 1].history_index);
    }

    if (match(TokenType::Identifier)) {
        const Token& ident = tokens_[pos_ - 1];

        if (match(TokenType::LParen)) {
            std::vector<NodePtr> args;

            if (!check(TokenType::RParen)) {
                while (true) {
                    args.push_back(parseExpression());
                    if (!match(TokenType::Comma)) {
                        break;
                    }
                }
            }

            expect(TokenType::RParen);
            return std::make_unique<CallNode>(ident.lexeme, std::move(args));
        }

        return std::make_unique<VariableNode>(ident.lexeme);
    }

    if (match(TokenType::LParen)) {
        NodePtr node = parseExpression();
        expect(TokenType::RParen);
        return node;
    }

    throwUnexpected(current());
}

}  // namespace calc
