"""Sample invalid Python code with ruff violations."""

import sys  # F401: unused import
import os  # F401: unused import
import json


def bad_function():
    unused_var = 42  # F841: assigned but never used
    another_unused = "test"  # F841: assigned but never used
    return None


def comparison_issues(value):
    if value == True:  # E712: comparison to True should be 'if value:'
        return "yes"
    if value == None:  # E711: comparison to None should be 'if value is None:'
        return "nothing"
    return "no"


def undefined_name():
    return undefined_variable  # F821: undefined name


class DuplicateDefinition:
    def method(self):  # F811: will be redefined
        return 1

    def method(self):  # F811: redefinition
        return 2
