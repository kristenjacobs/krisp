#!/usr/bin/env python


from pprint import pprint
import glob
import shlex
import sys
import traceback
import os
import uuid


DEBUG = False


def debug(obj, pp=False):
    if DEBUG:
        if pp:
            pprint(obj)
        else:    
            print str(obj)


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


def lookup(key, env):
    result = key
    while str(result) in env:
        result = env[str(result)]
    return result    


def evaluate(ast, env):
    if isinstance(ast, list):
        if isinstance(ast[0], list):
            function = evaluate(ast[0], env)
        else:
            function = str(ast[0])

        if function in env:
            debug("evaluating function: " + str(function))
            args = lookup(function, env)[0]
            body = lookup(function, env)[1]
            f_env = env.copy()
            i = 1
            for arg in args:
                f_env[arg] = evaluate(ast[i], env)
                i += 1
            return evaluate(body, f_env)

        elif function == "+":
            debug("evaluating +")
            return int(evaluate(ast[1], env)) + \
                   int(evaluate(ast[2], env))

        elif function == "-":
            debug("evaluating -")
            return int(evaluate(ast[1], env)) - \
                   int(evaluate(ast[2], env))

        elif function == "*":
            debug("evaluating *")
            return int(evaluate(ast[1], env)) * \
                   int(evaluate(ast[2], env))

        elif function == "/":
            debug("evaluating /")
            return int(evaluate(ast[1], env)) / \
                   int(evaluate(ast[2], env))

        elif function == "def":
            debug("evaluating def")
            env[str(ast[1])] = evaluate(ast[2], env)  
            return None

        elif function == "do":
            debug("evaluating do")
            result = None
            for i in range(1, len(ast)):
                result = evaluate(ast[i], env)  
            return result

        elif function == "let":
            debug("evaluating let")
            env[str(ast[1])] = evaluate(ast[2], env)  
            return None

        elif function == "fn":
            debug("evaluating fn")
            name = str(uuid.uuid4())
            env[name] = (ast[1], ast[2])
            return name

        elif function == "print":
            debug("evaluating print")
            print str(evaluate(ast[1], env))
            return None
        else:
            raise Exception, "Function: " + function + " not defined"
    else:
        return lookup(ast, env)


def process(program):
    try:
        debug("Tokens")
        tokens = tokenise(program)
        debug(tokens)
        debug("AST")
        ast = parse(tokens)[0]
        debug(ast, True)
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
