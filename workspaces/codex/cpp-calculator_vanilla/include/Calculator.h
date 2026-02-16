#pragma once

#include <string>
#include <vector>

#include "Context.h"

namespace calc {

class Calculator {
public:
    Calculator() = default;

    double evaluate(const std::string& expression);

    const std::vector<double>& history() const;
    const EvaluationContext& context() const;

private:
    EvaluationContext context_;
};

}  // namespace calc
