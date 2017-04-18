#!/usr/bin/env python

import glob
import os


def main():
    tests = glob.glob("tests/*.kp")
    tests.sort()
    for test in tests:
        print "%-50s ... " % test,
        os.system("./krisp.py " + test + " > " + test + ".log 2>&1")
        if os.system("diff " + test + ".expect " + test + ".log > /dev/null") == 0:
            print "PASSED"
        else:
            print "***** FAILED *****"


if __name__ == "__main__":
    main()
