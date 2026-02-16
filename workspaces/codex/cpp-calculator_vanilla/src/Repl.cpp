#include "Repl.h"

#include <algorithm>
#include <cctype>
#include <iomanip>
#include <iostream>
#include <string>

#include "Token.h"

namespace calc {

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

}  // namespace

Repl::Repl(Calculator& calculator) : calculator_(calculator) {}

void Repl::run(std::istream& in, std::ostream& out, std::ostream& err) {
    const bool interactive = (&in == &std::cin);

    if (interactive) {
        out << "Calculator REPL. Type 'help' for commands, 'exit' to quit.\n";
    }

    std::string line;
    while (true) {
        if (interactive) {
            out << "calc> " << std::flush;
        }

        if (!std::getline(in, line)) {
            break;
        }

        line = trim(line);
        if (line.empty()) {
            continue;
        }

        if (line == "exit" || line == "quit") {
            break;
        }

        if (line == "help") {
            printHelp(out);
            continue;
        }

        if (line == "history") {
            const auto& history = calculator_.history();
            for (std::size_t i = 0; i < history.size(); ++i) {
                out << "$" << (i + 1) << " = " << std::setprecision(15) << history[i] << "\n";
            }
            continue;
        }

        try {
            const double value = calculator_.evaluate(line);
            out << "= " << std::setprecision(15) << value << "\n";
        } catch (const CalcError& ex) {
            err << ex.what() << "\n";
        }
    }
}

void Repl::printHelp(std::ostream& out) {
    out << "Commands:\n";
    out << "  help      Show this help text\n";
    out << "  history   Show computed results as $1, $2, ...\n";
    out << "  exit      Quit the calculator\n";
    out << "\n";
    out << "Supported operators: +, -, *, /, %, ^\n";
    out << "Functions: sin, cos, tan, sqrt, log, log10, abs, ceil, floor, min, max\n";
    out << "Constants: pi, e\n";
    out << "Variable assignment: x = 3.14\n";
    out << "History references: $1, $2, ...\n";
}

}  // namespace calc
