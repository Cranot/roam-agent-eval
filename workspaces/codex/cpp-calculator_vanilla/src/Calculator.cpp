#include "Calculator.h"

#include "Evaluator.h"
#include "Lexer.h"
#include "Parser.h"

namespace calc {

double Calculator::evaluate(const std::string& expression) {
    Lexer lexer(expression);
    Parser parser(lexer.tokenize());
    Evaluator evaluator(context_);

    auto ast = parser.parseStatement();
    const double value = evaluator.evaluate(*ast);
    context_.pushHistory(value);
    return value;
}

const std::vector<double>& Calculator::history() const {
    return context_.history();
}

const EvaluationContext& Calculator::context() const {
    return context_;
}

}  // namespace calc
