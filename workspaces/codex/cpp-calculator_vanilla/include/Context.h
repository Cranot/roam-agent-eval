#pragma once

#include <string>
#include <unordered_map>
#include <vector>

#include "Token.h"

namespace calc {

class EvaluationContext {
public:
    EvaluationContext();

    bool hasVariable(const std::string& name) const;
    double getVariable(const std::string& name) const;
    void setVariable(const std::string& name, double value);

    void pushHistory(double value);
    double getHistoryValue(int one_based_index) const;
    const std::vector<double>& history() const;

private:
    std::unordered_map<std::string, double> variables_;
    std::vector<double> history_;
};

}  // namespace calc
