#pragma once

#include <istream>
#include <ostream>

#include "Calculator.h"

namespace calc {

class Repl {
public:
    explicit Repl(Calculator& calculator);

    void run(std::istream& in, std::ostream& out, std::ostream& err);
    static void printHelp(std::ostream& out);

private:
    Calculator& calculator_;
};

}  // namespace calc
