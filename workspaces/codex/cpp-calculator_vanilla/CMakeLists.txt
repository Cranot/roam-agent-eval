cmake_minimum_required(VERSION 3.16)
project(cpp_calculator LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(calculator_lib
    src/Calculator.cpp
    src/Context.cpp
    src/Evaluator.cpp
    src/Lexer.cpp
    src/Parser.cpp
    src/Repl.cpp
)

target_include_directories(calculator_lib PUBLIC include)

add_executable(calculator src/main.cpp)
target_link_libraries(calculator PRIVATE calculator_lib)

enable_testing()

include(FetchContent)
FetchContent_Declare(
    doctest
    GIT_REPOSITORY https://github.com/doctest/doctest.git
    GIT_TAG v2.4.11
)
FetchContent_MakeAvailable(doctest)

add_executable(calculator_tests tests/test_calculator.cpp)
target_link_libraries(calculator_tests PRIVATE calculator_lib doctest::doctest)

add_test(NAME calculator_tests COMMAND calculator_tests)
