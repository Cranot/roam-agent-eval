#pragma once

#include <memory>
#include <string>
#include <utility>
#include <vector>

namespace calc {

enum class UnaryOp {
    Negate
};

enum class BinaryOp {
    Add,
    Subtract,
    Multiply,
    Divide,
    Modulo,
    Power
};

struct Node {
    virtual ~Node() = default;
};

using NodePtr = std::unique_ptr<Node>;

struct NumberNode final : Node {
    explicit NumberNode(double value_in) : value(value_in) {}
    double value;
};

struct VariableNode final : Node {
    explicit VariableNode(std::string name_in) : name(std::move(name_in)) {}
    std::string name;
};

struct HistoryRefNode final : Node {
    explicit HistoryRefNode(int index_in) : index(index_in) {}
    int index;
};

struct UnaryNode final : Node {
    UnaryNode(UnaryOp op_in, NodePtr operand_in)
        : op(op_in), operand(std::move(operand_in)) {}

    UnaryOp op;
    NodePtr operand;
};

struct BinaryNode final : Node {
    BinaryNode(BinaryOp op_in, NodePtr left_in, NodePtr right_in)
        : op(op_in), left(std::move(left_in)), right(std::move(right_in)) {}

    BinaryOp op;
    NodePtr left;
    NodePtr right;
};

struct CallNode final : Node {
    CallNode(std::string name_in, std::vector<NodePtr> args_in)
        : name(std::move(name_in)), args(std::move(args_in)) {}

    std::string name;
    std::vector<NodePtr> args;
};

struct AssignmentNode final : Node {
    AssignmentNode(std::string name_in, NodePtr expression_in)
        : name(std::move(name_in)), expression(std::move(expression_in)) {}

    std::string name;
    NodePtr expression;
};

}  // namespace calc
