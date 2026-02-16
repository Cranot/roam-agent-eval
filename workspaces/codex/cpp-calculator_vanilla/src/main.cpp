#include <algorithm>
#include <cctype>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>

#include "Calculator.h"
#include "Repl.h"
#include "Token.h"

namespace {

std::string trim(std::string input) {
    const auto not_space = [](unsigned char ch) { return !std::isspace(ch); };

    auto start = std::find_if(input.begin(), input.end(), not_space);
    if (start == input.end()) {
        return "";
    }

    auto end = std::find_if(input.rbegin(), input.rend(), not_space).base();
    return std::string(start, end);
}

void printUsage(const char* program_name) {
    std::cout << "Usage:\n";
    std::cout << "  " << program_name << "                 Start interactive REPL\n";
    std::cout << "  " << program_name << " --file <path>   Evaluate expressions from file\n";
    std::cout << "  " << program_name << " <expression>    Evaluate a single expression\n";
}

int evaluateFile(const std::string& path) {
    std::ifstream file(path);
    if (!file) {
        std::cerr << "Failed to open file: " << path << "\n";
        return 1;
    }

    calc::Calculator calculator;
    std::string line;
    std::size_t line_number = 0;
    bool has_error = false;

    while (std::getline(file, line)) {
        ++line_number;
        const std::string expr = trim(line);
        if (expr.empty() || expr[0] == '#') {
            continue;
        }

        try {
            const double value = calculator.evaluate(expr);
            std::cout << std::setprecision(15) << value << "\n";
        } catch (const calc::CalcError& ex) {
            std::cerr << "Line " << line_number << ": " << ex.what() << "\n";
            has_error = true;
        }
    }

    return has_error ? 1 : 0;
}

int evaluateSingleExpression(int argc, char** argv) {
    std::ostringstream oss;
    for (int i = 1; i < argc; ++i) {
        if (i > 1) {
            oss << ' ';
        }
        oss << argv[i];
    }

    calc::Calculator calculator;
    try {
        const double value = calculator.evaluate(oss.str());
        std::cout << std::setprecision(15) << value << "\n";
        return 0;
    } catch (const calc::CalcError& ex) {
        std::cerr << ex.what() << "\n";
        return 1;
    }
}

}  // namespace

int main(int argc, char** argv) {
    if (argc == 1) {
        calc::Calculator calculator;
        calc::Repl repl(calculator);
        repl.run(std::cin, std::cout, std::cerr);
        return 0;
    }

    const std::string first_arg = argv[1];

    if (first_arg == "--help" || first_arg == "-h") {
        printUsage(argv[0]);
        return 0;
    }

    if (first_arg == "--file" || first_arg == "-f") {
        if (argc < 3) {
            std::cerr << "Missing file path for --file\n";
            printUsage(argv[0]);
            return 1;
        }
        return evaluateFile(argv[2]);
    }

    return evaluateSingleExpression(argc, argv);
}
