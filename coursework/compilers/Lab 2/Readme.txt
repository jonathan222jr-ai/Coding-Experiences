Parser Lab 2 – ReadMe

Objective

The goal of this assignment is to complete the partially implemented
LL(1) recursive-descent parser in parser.cpp. The parser validates
whether an input program follows the grammar defined in grammarLL1.txt
and counts the number of variables, functions, and statements in valid
programs.

------------------------------------------------------------------------

Steps to Complete the Assignment

1. Examine the Project Structure

The project contains several components:

-   scanner.cpp and token.cpp – lexical analyzer from the previous
    project.
-   first_plus.cpp – FIRST+ table used for LL(1) parsing decisions.
-   parser.cpp – recursive descent parser with missing functions.
-   parser.h – declarations of grammar functions.
-   grammarLL1.txt – grammar rules and FIRST+ sets.
-   Makefile – used to compile the project.
-   test/ – contains test programs for verifying the parser.

------------------------------------------------------------------------

2. Study the Grammar

Open grammarLL1.txt and review the grammar rules.

Each grammar rule corresponds to a function in parser.cpp.

Example:

Grammar rule: –> int | void | binary | decimal

Corresponding parser function: bool Parser::type_name(void)

The parser functions follow the structure of these grammar productions.

------------------------------------------------------------------------

3. Implement Missing Functions in parser.cpp

Search for all TODO comments in parser.cpp.

For each missing function:

1.  Find the corresponding rule in grammarLL1.txt.
2.  Use check_first_plus_set() to determine which production should be
    followed.
3.  Match tokens using:
    -   current_word.get_token_type()
    -   current_word.get_token_name()
4.  When a token is successfully matched, call: get_next_word() to
    advance to the next token.
5.  If the production requires other non-terminals, call the
    corresponding parser functions.
6.  If no production matches, set: fail_state = true; and return false.

------------------------------------------------------------------------

4. Handle EPSILON Productions

Some grammar rules include an epsilon (empty) production.

Example: –> left_bracket right_bracket | EPSILON

For epsilon cases, the parser should simply return true without
consuming any tokens.

------------------------------------------------------------------------

5. Maintain Required Counts

The parser must count:

-   variables
-   functions
-   statements

These counts are stored in:

-   variable_count
-   function_count
-   statement_count

Variable Counting

Variables are counted when declared through <data_decls> or identifier
lists.

Function Counting

Functions are counted only for function definitions, not declarations.
A function is counted when a function body beginning with { is parsed.

Statement Counting

Each time a <statement> rule is successfully parsed, statement_count is
incremented.

------------------------------------------------------------------------

6. Fix the Compiler in the Makefile

The provided Makefile referenced an outdated compiler:

/usr/bin/g++-4.8

This was replaced with:

CC = g++

to allow compilation on modern systems.

------------------------------------------------------------------------

7. Compile the Parser

Navigate to the C++ directory and run:

make clean
make

This compiles all source files and creates the executable:

bin/parser

------------------------------------------------------------------------

8. Extract the Test Programs

Inside the test directory, extract the provided test cases:

mkdir all_tests
tar -xf all_tests.tar -C all_tests

------------------------------------------------------------------------

9. Run the Parser

The parser expects the input file name as an argument.

Example:

./bin/parser ../test/all_tests/example.c

To run all test programs:

for f in ../test/all_tests/*; do
echo “===== $f ====="  ./bin/parser "$f”
done

------------------------------------------------------------------------

10. Verify Results

Compare the output of the parser with the expected results provided in
RESULTS.txt.

Correct programs should output:

pass variable function statement

Incorrect programs should output:

error

------------------------------------------------------------------------

Completion

After implementing all missing parser functions, compiling the program,
and verifying the output against the provided test results, the parser
successfully validates programs according to the LL(1) grammar and
correctly reports the counts for variables, functions, and statements.