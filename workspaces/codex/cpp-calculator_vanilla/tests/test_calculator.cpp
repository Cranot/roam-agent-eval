#define DOCTEST_CONFIG_IMPLEMENT_WITH_MAIN
#include <doctest/doctest.h>

#include <cmath>
#include <string>

#include "Calculator.h"
#include "Token.h"

TEST_CASE("operator precedence and grouping") {
    calc::Calculator calculator;

    CHECK(calculator.evaluate("2 + 3 * 4") == doctest::Approx(14.0));
    CHECK(calculator.evaluate("(2 + 3) * 4") == doctest::Approx(20.0));
    CHECK(calculator.evaluate("2^3^2") == doctest::Approx(512.0));
}

TEST_CASE("unary minus") {
    calc::Calculator calculator;

    CHECK(calculator.evaluate("-5") == doctest::Approx(-5.0));
    CHECK(calculator.evaluate("-(3+2)") == doctest::Approx(-5.0));
    CHECK(calculator.evaluate("-2^2") == doctest::Approx(-4.0));
}

TEST_CASE("built-in functions") {
    calc::Calculator calculator;

    CHECK(calculator.evaluate("sin(pi / 2)") == doctest::Approx(1.0));
    CHECK(calculator.evaluate("sqrt(9)") == doctest::Approx(3.0));
    CHECK(calculator.evaluate("log10(100)") == doctest::Approx(2.0));
    CHECK(calculator.evaluate("min(5, 2, 7)") == doctest::Approx(2.0));
    CHECK(calculator.evaluate("max(5, 2, 7)") == doctest::Approx(7.0));
}

TEST_CASE("assignment and constants") {
    calc::Calculator calculator;

    CHECK(calculator.evaluate("x = 3.14") == doctest::Approx(3.14));
    CHECK(calculator.evaluate("x * 2") == doctest::Approx(6.28));
    CHECK(calculator.evaluate("e") == doctest::Approx(std::exp(1.0)));
}

TEST_CASE("history references") {
    calc::Calculator calculator;

    CHECK(calculator.evaluate("10") == doctest::Approx(10.0));
    CHECK(calculator.evaluate("20") == doctest::Approx(20.0));
    CHECK(calculator.evaluate("$1 + $2") == doctest::Approx(30.0));
}

TEST_CASE("clear errors") {
    calc::Calculator calculator;

    CHECK_THROWS_WITH_AS(
        calculator.evaluate("foo(1)"),
        "Unknown function 'foo'",
        calc::EvalError
    );

    try {
        (void)calculator.evaluate("2 + * 3");
        FAIL("expected parse error");
    } catch (const calc::ParseError& ex) {
        const std::string message = ex.what();
        CHECK(message.find("Unexpected token '*'") != std::string::npos);
        CHECK(message.find("position") != std::string::npos);
    }
}
