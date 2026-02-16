#include "Context.h"

#include <cmath>
#include <sstream>

namespace calc {

EvaluationContext::EvaluationContext() {
    variables_["pi"] = std::acos(-1.0);
    variables_["e"] = std::exp(1.0);
}

bool EvaluationContext::hasVariable(const std::string& name) const {
    return variables_.find(name) != variables_.end();
}

double EvaluationContext::getVariable(const std::string& name) const {
    const auto it = variables_.find(name);
    if (it == variables_.end()) {
        std::ostringstream oss;
        oss << "Unknown variable '" << name << "'";
        throw EvalError(oss.str());
    }
    return it->second;
}

void EvaluationContext::setVariable(const std::string& name, double value) {
    if (name == "pi" || name == "e") {
        std::ostringstream oss;
        oss << "Cannot assign to constant '" << name << "'";
        throw EvalError(oss.str());
    }
    variables_[name] = value;
}

void EvaluationContext::pushHistory(double value) {
    history_.push_back(value);
}

double EvaluationContext::getHistoryValue(int one_based_index) const {
    if (one_based_index <= 0 || static_cast<std::size_t>(one_based_index) > history_.size()) {
        std::ostringstream oss;
        oss << "History reference '$" << one_based_index << "' out of range";
        throw EvalError(oss.str());
    }
    return history_[static_cast<std::size_t>(one_based_index - 1)];
}

const std::vector<double>& EvaluationContext::history() const {
    return history_;
}

}  // namespace calc
