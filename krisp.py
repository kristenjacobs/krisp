#!/usr/bin/env python

import glob
import shlex
import sys
import traceback
import os


DEBUG = False


def debug(string):
    if DEBUG:
        print string


def tokenise(program):
    return shlex.split(program.replace('(', ' ( ').replace(')', ' ) '))


def parse(tokens):
    ast = []
    while len(tokens) > 0:
        token = tokens.pop(0)
        if token == "(":
            ast.append(parse(tokens))
        elif token == ")":
            break
        else:
            ast.append(token)
    return ast


def evaluate(ast, env):
    debug("evaluate: " + str(ast))
    if isinstance(ast, list):
        i = 0
        result = None
        while i < len(ast):
            if isinstance(ast[i], list):
                result = evaluate(ast[i], env)
                i += 1
            else:
                function = str(ast[i])
                if function in env:
                    debug("Evaluating function: " + str(function))
                    i += 1
                    args = env[function][0]
                    body = env[function][1]
                    f_env = env.copy()
                    for arg in args:
                        f_env[arg] = evaluate(ast[i], env)
                        i += 1
                    result = evaluate(body, f_env)

                elif function == "+":
                    debug("Evaluating +")
                    result = int(evaluate(ast[i + 1], env)) + \
                             int(evaluate(ast[i + 2], env))
                    i += 3
                elif function == "-":
                    debug("Evaluating -")
                    result = int(evaluate(ast[i + 1], env)) - \
                             int(evaluate(ast[i + 2], env))
                    i += 3
                elif function == "*":
                    debug("Evaluating *")
                    result = int(evaluate(ast[i + 1], env)) * \
                             int(evaluate(ast[i + 2], env))
                    i += 3
                elif function == "/":
                    debug("Evaluating /")
                    result = int(evaluate(ast[i + 1], env)) / \
                             int(evaluate(ast[i + 2], env))
                    i += 3
                elif function == "let":
                    debug("Evaluating let")
                    env[str(ast[i + 1])] = evaluate(ast[i + 2], env)  
                    result = None
                    i += 3
                elif function == "fn":
                    debug("Evaluating fn")
                    env[str(ast[i + 1])] = (ast[i + 2], ast[i + 3])
                    result = None
                    i += 4

                elif function == "print":
                    debug("Evaluating print")
                    print str(evaluate(ast[i + 1], env))
                    result = None
                    i += 2
                else:
                    raise Exception, "Function: " + function + " not defined"
        return result
    else:
        if ast in env:
            return env[ast]
        else:
            return ast


def process(program):
    try:
        tokens = tokenise(program)
        debug("The tokens are: " + str(tokens))
        ast = parse(tokens)
        debug("The AST is: " + str(ast))
        evaluate(ast, {})

    except Exception, ex:
        print "Error: " + str(ex)
        traceback.print_exc()
        sys.exit(1)


def runtests():
    tests = glob.glob("tests/*.kp")
    tests.sort()
    for test in tests:    
        print "%-50s ... " % test,
        os.system("./krisp.py " + test + " > " + test + ".log 2>&1")
        if os.system("diff " + test + ".expect " + test + ".log > /dev/null") == 0:
            print "PASSED"
        else:     
            print "***** FAILED *****"


def main():
    if len(sys.argv) == 1:
        runtests()
    else:
        with open(sys.argv[1], 'r') as infile:
            contents = infile.read().rstrip('\n')
            process(contents)


if __name__ == "__main__":
    main()
