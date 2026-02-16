#pragma once

#include "AST.h"
#include "Context.h"

namespace calc {

class Evaluator {
public:
    explicit Evaluator(EvaluationContext& context);

    double evaluate(const Node& node);

private:
    EvaluationContext& context_;

    double evalNode(const Node& node);
    double evalUnary(const UnaryNode& node);
    double evalBinary(const BinaryNode& node);
    double evalCall(const CallNode& node);
};

}  // namespace calc
