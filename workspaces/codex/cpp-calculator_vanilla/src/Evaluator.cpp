#include "Evaluator.h"

#include <algorithm>
#include <cmath>
#include <sstream>
#include <vector>

namespace calc {

namespace {

constexpr double kZeroEpsilon = 1e-12;

void requireArgCount(const std::string& name, const std::vector<double>& args, std::size_t expected) {
    if (args.size() != expected) {
        std::ostringstream oss;
        oss << "Function '" << name << "' expects " << expected
            << " argument" << (expected == 1 ? "" : "s")
            << " but got " << args.size();
        throw EvalError(oss.str());
    }
}

void requireAtLeastArgs(const std::string& name, const std::vector<double>& args, std::size_t min_count) {
    if (args.size() < min_count) {
        std::ostringstream oss;
        oss << "Function '" << name << "' expects at least " << min_count
            << " argument" << (min_count == 1 ? "" : "s")
            << " but got " << args.size();
        throw EvalError(oss.str());
    }
}

}  // namespace

Evaluator::Evaluator(EvaluationContext& context) : context_(context) {}

double Evaluator::evaluate(const Node& node) {
    return evalNode(node);
}

double Evaluator::evalNode(const Node& node) {
    if (const auto* number = dynamic_cast<const NumberNode*>(&node)) {
        return number->value;
    }

    if (const auto* variable = dynamic_cast<const VariableNode*>(&node)) {
        return context_.getVariable(variable->name);
    }

    if (const auto* history_ref = dynamic_cast<const HistoryRefNode*>(&node)) {
        return context_.getHistoryValue(history_ref->index);
    }

    if (const auto* unary = dynamic_cast<const UnaryNode*>(&node)) {
        return evalUnary(*unary);
    }

    if (const auto* binary = dynamic_cast<const BinaryNode*>(&node)) {
        return evalBinary(*binary);
    }

    if (const auto* call = dynamic_cast<const CallNode*>(&node)) {
        return evalCall(*call);
    }

    if (const auto* assignment = dynamic_cast<const AssignmentNode*>(&node)) {
        const double value = evalNode(*assignment->expression);
        context_.setVariable(assignment->name, value);
        return value;
    }

    throw EvalError("Unsupported expression node");
}

double Evaluator::evalUnary(const UnaryNode& node) {
    const double operand = evalNode(*node.operand);

    switch (node.op) {
        case UnaryOp::Negate:
            return -operand;
    }

    throw EvalError("Unsupported unary operator");
}

double Evaluator::evalBinary(const BinaryNode& node) {
    const double lhs = evalNode(*node.left);
    const double rhs = evalNode(*node.right);

    switch (node.op) {
        case BinaryOp::Add:
            return lhs + rhs;
        case BinaryOp::Subtract:
            return lhs - rhs;
        case BinaryOp::Multiply:
            return lhs * rhs;
        case BinaryOp::Divide:
            if (std::abs(rhs) < kZeroEpsilon) {
                throw EvalError("Division by zero");
            }
            return lhs / rhs;
        case BinaryOp::Modulo:
            if (std::abs(rhs) < kZeroEpsilon) {
                throw EvalError("Modulo by zero");
            }
            return std::fmod(lhs, rhs);
        case BinaryOp::Power:
            return std::pow(lhs, rhs);
    }

    throw EvalError("Unsupported binary operator");
}

double Evaluator::evalCall(const CallNode& node) {
    std::vector<double> args;
    args.reserve(node.args.size());
    for (const auto& arg : node.args) {
        args.push_back(evalNode(*arg));
    }

    const std::string& fn = node.name;

    if (fn == "sin") {
        requireArgCount(fn, args, 1);
        return std::sin(args[0]);
    }
    if (fn == "cos") {
        requireArgCount(fn, args, 1);
        return std::cos(args[0]);
    }
    if (fn == "tan") {
        requireArgCount(fn, args, 1);
        return std::tan(args[0]);
    }
    if (fn == "sqrt") {
        requireArgCount(fn, args, 1);
        return std::sqrt(args[0]);
    }
    if (fn == "log") {
        requireArgCount(fn, args, 1);
        return std::log(args[0]);
    }
    if (fn == "log10") {
        requireArgCount(fn, args, 1);
        return std::log10(args[0]);
    }
    if (fn == "abs") {
        requireArgCount(fn, args, 1);
        return std::abs(args[0]);
    }
    if (fn == "ceil") {
        requireArgCount(fn, args, 1);
        return std::ceil(args[0]);
    }
    if (fn == "floor") {
        requireArgCount(fn, args, 1);
        return std::floor(args[0]);
    }
    if (fn == "min") {
        requireAtLeastArgs(fn, args, 1);
        return *std::min_element(args.begin(), args.end());
    }
    if (fn == "max") {
        requireAtLeastArgs(fn, args, 1);
        return *std::max_element(args.begin(), args.end());
    }

    std::ostringstream oss;
    oss << "Unknown function '" << fn << "'";
    throw EvalError(oss.str());
}

}  // namespace calc
