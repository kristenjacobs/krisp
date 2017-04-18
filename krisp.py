#!/usr/bin/env python

import glob
import os
import pprint
import re
import shlex
import sys
import traceback
import uuid


def enter(obj, depth):
    for _ in range(0, depth):
        print " ",
    print ">>",
    print obj


def leave(obj, depth):
    for _ in range(0, depth):
        print " ",
    print "<<",
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


def lookup(key, genv, lenv):
    result = key
    while str(result) in lenv or str(result) in genv:
        if str(result) in lenv:
            result = lenv[str(result)]
        elif str(result) in genv:
            result = genv[str(result)]
    return result


def evaluate(ast, genv, lenv, tracing, depth):
    if tracing:
        enter(ast, depth)

    result = None
    if isinstance(ast, list):
        function = lookup(evaluate(ast[0], genv, lenv, tracing, depth+1), genv, lenv)

        if isinstance(function, tuple):
            f_lenv = function[2].copy()
            for i, arg in enumerate(function[0]):
                f_lenv[arg] = evaluate(ast[i + 1], genv, lenv, tracing, depth+1)
            result = evaluate(function[1], genv, f_lenv, tracing, depth+1)

        elif function == "def":
            genv[str(ast[1])] = evaluate(ast[2], genv, lenv, tracing, depth+1)
            result = None

        elif function == "do":
            result = None
            for i in range(1, len(ast)):
                result = evaluate(ast[i], genv, lenv, tracing, depth+1)
            result = result

        elif function == "let":
            lenv[str(ast[1])] = evaluate(ast[2], genv, lenv, tracing, depth+1)
            result = None

        elif function == "fn":
            name = str(uuid.uuid4())
            genv[name] = (ast[1], ast[2], lenv)
            result = name

        elif function == "if":
            if evaluate(ast[1], genv, lenv, tracing, depth+1):
                result = evaluate(ast[2], genv, lenv, tracing, depth+1)
            else:
                result = evaluate(ast[3], genv, lenv, tracing, depth+1)

        elif function == "trace":
            result = evaluate(ast[1], genv, lenv, True, 0)

        elif function == "print":
            print str(evaluate(ast[1], genv, lenv, tracing, depth+1))
            result = None

        elif function == "env":
            env = genv.copy()
            env.update(lenv)
            pprint.pprint(env)
            result = None

        elif function == "+":
            result = num(evaluate(ast[1], genv, lenv, tracing, depth+1)) + \
                     num(evaluate(ast[2], genv, lenv, tracing, depth+1))

        elif function == "-":
            result = num(evaluate(ast[1], genv, lenv, tracing, depth+1)) - \
                     num(evaluate(ast[2], genv, lenv, tracing, depth+1))

        elif function == "*":
            result = num(evaluate(ast[1], genv, lenv, tracing, depth+1)) * \
                     num(evaluate(ast[2], genv, lenv, tracing, depth+1))

        elif function == "/":
            result = num(evaluate(ast[1], genv, lenv, tracing, depth+1)) / \
                     num(evaluate(ast[2], genv, lenv, tracing, depth+1))

        elif function == "%":
            result = num(evaluate(ast[1], genv, lenv, tracing, depth+1)) % \
                     num(evaluate(ast[2], genv, lenv, tracing, depth+1))

        elif function == "=":
            lhs = evaluate(ast[1], genv, lenv, tracing, depth+1)
            rhs = evaluate(ast[2], genv, lenv, tracing, depth+1)
            if isinstance(lhs, list) and isinstance(rhs, list):
                result = lhs == rhs
            else:
                result = num(lhs) == num(rhs)

        elif function == "<":
            result = num(evaluate(ast[1], genv, lenv, tracing, depth+1)) < \
                     num(evaluate(ast[2], genv, lenv, tracing, depth+1))

        elif function == "<=":
            result = num(evaluate(ast[1], genv, lenv, tracing, depth+1)) <= \
                     num(evaluate(ast[2], genv, lenv, tracing, depth+1))

        elif function == ">":
            result = num(evaluate(ast[1], genv, lenv, tracing, depth+1)) > \
                     num(evaluate(ast[2], genv, lenv, tracing, depth+1))

        elif function == ">=":
            result = num(evaluate(ast[1], genv, lenv, tracing, depth+1)) >= \
                     num(evaluate(ast[2], genv, lenv, tracing, depth+1))

        elif function == "list":
            result = []
            for i in range(1, len(ast)):
                result.append(evaluate(ast[i], genv, lenv, tracing, depth+1))

        elif function == "first":
            result = evaluate(ast[1], genv, lenv, tracing, depth+1)[0]

        elif function == "rest":
            result = evaluate(ast[1], genv, lenv, tracing, depth+1)[1:]

        elif function == "cons":
            result = evaluate(ast[1], genv, lenv, tracing, depth+1)
            result.insert(0, evaluate(ast[2], genv, lenv, tracing, depth+1))

        elif function == "conj":
            result = evaluate(ast[1], genv, lenv, tracing, depth+1)
            result.append(evaluate(ast[2], genv, lenv, tracing, depth+1))

        else:
            raise Exception, "Function: " + function + " not defined"
    else:
        result = lookup(ast, genv, lenv)

    if tracing:
        leave(result, depth)
    return result


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
            evaluate(ast, genv, {}, False, 0)

    except Exception, ex:
        print "Error: " + str(ex)
        traceback.print_exc()
        sys.exit(1)


def load_libs(genv):
    libs = glob.glob("lib/*.kp")
    libs.sort()
    for lib in libs:
        run_file(lib, genv)


def main():
    if len(sys.argv) >= 2:
        genv = {}
        load_libs(genv)
        for arg in sys.argv[1:]:
            run_file(arg, genv)
    else:
        print "Invalid arguments. Usage:"
        print "  ./krisp.py <file1.kp> <file2.kp> ...etc"
        sys.exit(1)


if __name__ == "__main__":
    main()
