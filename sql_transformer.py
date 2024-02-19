# apply_codemod.py
import sys

import libcst as cst
import libcst.matchers as m


class SQLTransformer(cst.CSTTransformer):
    def __init__(self):
        print("SQLTransformer initialized")
    
    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        func_call = original_node.func
        if not m.matches(func_call, m.Name("sql")):
            # Oops, this isn't a True/False literal!
            return False

        return updated_node
    
    def leave_Assign(self, original_node: cst.Assign, updated_node: cst.Assign) -> cst.Assign:
        return updated_node
    
    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        return updated_node
    

def check_for_sql_call(node: cst.Call) -> bool:
    print("Checking for sql call")
    func_call = node.func
    if not m.matches(func_call, m.Name("sql")):
        # Oops, this isn't a True/False literal!
        return False
    return True