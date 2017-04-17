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

def number(n):
    try:
        return int(n)
    except ValueError:
        try:
            return float(n)
        except ValueError:
            raise Exception, "Unable to convert " + str(n) + " to a number"


def defined(key, global_env, local_env):
    return str(key) in local_env or str(key) in global_env


def lookup(key, global_env, local_env):
    result = key
    while str(result) in local_env or str(result) in global_env:
        if str(result) in local_env:
            result = local_env[str(result)]
        elif str(result) in global_env:
            result = global_env[str(result)]
    return result


def evaluate(ast, global_env, local_env):
    debug("evaluate ast: " + str(ast))
    if isinstance(ast, list):
        if isinstance(ast[0], list):
            function = evaluate(ast[0], global_env, local_env)
        else:
            function = str(ast[0])

        if defined(function, global_env, local_env):
            args = lookup(function, global_env, local_env)[0]
            body = lookup(function, global_env, local_env)[1]
            env = lookup(function, global_env, local_env)[2]
            i = 1
            f_local_env = env.copy()
            for arg in args:
                f_local_env[arg] = evaluate(ast[i], global_env, local_env)
                i += 1
            return evaluate(body, global_env, f_local_env)

        elif function == "+":
            return number(evaluate(ast[1], global_env, local_env)) + \
                   number(evaluate(ast[2], global_env, local_env))

        elif function == "-":
            return number(evaluate(ast[1], global_env, local_env)) - \
                   number(evaluate(ast[2], global_env, local_env))

        elif function == "*":
            return number(evaluate(ast[1], global_env, local_env)) * \
                   number(evaluate(ast[2], global_env, local_env))

        elif function == "/":
            return number(evaluate(ast[1], global_env, local_env)) / \
                   number(evaluate(ast[2], global_env, local_env))

        elif function == "=":
            if isinstance(ast[1], list) and isinstance(ast[2], list):
                return ast[1] == ast[2]
            else:
                return number(evaluate(ast[1], global_env, local_env)) == \
                       number(evaluate(ast[2], global_env, local_env))

        elif function == "def":
            global_env[str(ast[1])] = evaluate(ast[2], global_env, local_env)
            return None

        elif function == "do":
            result = None
            for i in range(1, len(ast)):
                result = evaluate(ast[i], global_env, local_env)
            return result

        elif function == "let":
            local_env[str(ast[1])] = evaluate(ast[2], global_env, local_env)
            return None

        elif function == "fn":
            name = str(uuid.uuid4())
            global_env[name] = (ast[1], ast[2], local_env)
            return name

        elif function == "if":
            if evaluate(ast[1], global_env, local_env):
                return evaluate(ast[2], global_env, local_env)
            else:
                return evaluate(ast[3], global_env, local_env)

        elif function == "print":
            print str(evaluate(ast[1], global_env, local_env))
            return None

        elif function == "list":
            result = []
            for i in range(1, len(ast)):
                result.append(evaluate(ast[i], global_env, local_env))
            return result

        elif function == "first":
            return evaluate(ast[1], global_env, local_env)[0]

        elif function == "rest":
            return evaluate(ast[1], global_env, local_env)[1:]

        elif function == "conj":
            result = evaluate(ast[1], global_env, local_env)
            result.append(evaluate(ast[2], global_env, local_env))
            return result

        else:
            raise Exception, "Function: " + function + " not defined"
    else:
        value = lookup(ast, global_env, local_env)
        return value


def remove_comments(infile):
    program = ""
    for line in infile.readlines():
        program += re.sub(r';.*', '', line.rstrip('\n'))
    return program


def run_file(filename, global_env):
    try:
        with open(filename, 'r') as infile:
            program = remove_comments(infile)
            ast = parse(lex(program))[0]
            debug(ast)
            evaluate(ast, global_env, {})

    except Exception, ex:
        print "Error: " + str(ex)
        traceback.print_exc()
        sys.exit(1)


def load_libs(global_env):
    libs = glob.glob("lib/*.kp")
    libs.sort()
    for lib in libs:
        debug("loading: " + lib)
        run_file(lib, global_env)


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
        global_env = {}
        load_libs(global_env)
        for arg in sys.argv[1:]:
            run_file(arg, global_env)


if __name__ == "__main__":
    main()
