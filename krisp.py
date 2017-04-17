#!/usr/bin/env python

import glob
import os
import pprint
import re
import shlex
import sys
import traceback
import uuid


DEBUG = False
def debug(obj):
    if DEBUG:
        pprint.pprint(obj)


def lex(program):
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


def num(n):
    try:
        return int(n)
    except ValueError:
        try:
            return float(n)
        except ValueError:
            raise Exception, "Unable to convert " + str(n) + " to a number"


def defined(key, genv, lenv):
    return str(key) in lenv or str(key) in genv


def lookup(key, genv, lenv):
    result = key
    while str(result) in lenv or str(result) in genv:
        if str(result) in lenv:
            result = lenv[str(result)]
        elif str(result) in genv:
            result = genv[str(result)]
    return result


def evaluate(ast, genv, lenv):
    debug("evaluate ast: " + str(ast))
    if isinstance(ast, list):
        function = evaluate(ast[0], genv, lenv) if isinstance(ast[0], list) else str(ast[0])

        if defined(function, genv, lenv):
            func = lookup(function, genv, lenv)
            f_lenv = func[2].copy()
            for i, arg in enumerate(func[0]):
                f_lenv[arg] = evaluate(ast[i + 1], genv, lenv)
            return evaluate(func[1], genv, f_lenv)

        elif function == "+":
            return num(evaluate(ast[1], genv, lenv)) + num(evaluate(ast[2], genv, lenv))

        elif function == "-":
            return num(evaluate(ast[1], genv, lenv)) - num(evaluate(ast[2], genv, lenv))

        elif function == "*":
            return num(evaluate(ast[1], genv, lenv)) * num(evaluate(ast[2], genv, lenv))

        elif function == "/":
            return num(evaluate(ast[1], genv, lenv)) / num(evaluate(ast[2], genv, lenv))

        elif function == "=":
            if isinstance(ast[1], list) and isinstance(ast[2], list):
                return ast[1] == ast[2]
            else:
                return num(evaluate(ast[1], genv, lenv)) == num(evaluate(ast[2], genv, lenv))

        elif function == "def":
            genv[str(ast[1])] = evaluate(ast[2], genv, lenv)
            return None

        elif function == "do":
            result = None
            for i in range(1, len(ast)):
                result = evaluate(ast[i], genv, lenv)
            return result

        elif function == "let":
            lenv[str(ast[1])] = evaluate(ast[2], genv, lenv)
            return None

        elif function == "fn":
            name = str(uuid.uuid4())
            genv[name] = (ast[1], ast[2], lenv)
            return name

        elif function == "if":
            if evaluate(ast[1], genv, lenv):
                return evaluate(ast[2], genv, lenv)
            else:
                return evaluate(ast[3], genv, lenv)

        elif function == "print":
            print str(evaluate(ast[1], genv, lenv))
            return None

        elif function == "list":
            result = []
            for i in range(1, len(ast)):
                result.append(evaluate(ast[i], genv, lenv))
            return result

        elif function == "first":
            return evaluate(ast[1], genv, lenv)[0]

        elif function == "rest":
            return evaluate(ast[1], genv, lenv)[1:]

        elif function == "conj":
            result = evaluate(ast[1], genv, lenv)
            result.append(evaluate(ast[2], genv, lenv))
            return result

        else:
            raise Exception, "Function: " + function + " not defined"
    else:
        value = lookup(ast, genv, lenv)
        return value


def remove_comments(infile):
    program = ""
    for line in infile.readlines():
        program += re.sub(r';.*', '', line.rstrip('\n'))
    return program


def run_file(filename, genv):
    try:
        with open(filename, 'r') as infile:
            program = remove_comments(infile)
            ast = parse(lex(program))[0]
            debug(ast)
            evaluate(ast, genv, {})

    except Exception, ex:
        print "Error: " + str(ex)
        traceback.print_exc()
        sys.exit(1)


def load_libs(genv):
    libs = glob.glob("lib/*.kp")
    libs.sort()
    for lib in libs:
        debug("loading: " + lib)
        run_file(lib, genv)


def run_tests():
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
        run_tests()
    else:
        genv = {}
        load_libs(genv)
        for arg in sys.argv[1:]:
            run_file(arg, genv)


if __name__ == "__main__":
    main()
