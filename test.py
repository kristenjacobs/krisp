#!/usr/bin/env python

import glob
import os
import sys
from subprocess import Popen, PIPE


def get_expected_output(test):
    expected_output = ""
    with open(test, 'r') as testfile:
        for line in testfile.readlines():
            if line.startswith(";;"):
                expected_output += line[2:]
    return expected_output


def run_test(test):
    process = Popen(["./krisp.py", test], stdout=PIPE)
    (output, _) = process.communicate()
    process.wait()
    return output


def main():
    tests = glob.glob("tests/*.kp")
    tests.sort()
    for test in tests:
        print "%-50s ... " % test,
        if run_test(test) == get_expected_output(test):
            print "PASSED"
        else:
            print "***** FAILED *****"


if __name__ == "__main__":
    main()
