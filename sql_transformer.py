# apply_codemod.py
import sys

import libcst as cst
import libcst.matchers as m
import json
import subprocess

def main():
    valid_invocation: cst.SimpleStatementLine = cst.parse_statement("select_result = sql(\"SELECT * FROM us_federal_ecfr WHERE node_type = 'content_type' AND status is NULL LIMIT 5;\")")

    
    invalid_invocation = cst.parse_statement("index = \"test\".find(\"t\")")
    
    valid_invocation_assign: cst.Assign = valid_invocation.body[0]
    invalid_invocation_assign = invalid_invocation.body[0]
    # print(valid_invocation_assign)
    # print(type(valid_invocation_assign))
    valid_invocation_call: cst.Call = valid_invocation_assign.value
    invalid_invocation_call = invalid_invocation_assign.value

    parent = valid_invocation_call

    # print(valid_invocation_call)
    # print(type(valid_invocation_call))
    valid_check = check_for_valid_sql_invocation(valid_invocation_call)
    invalid_check = check_for_valid_sql_invocation(invalid_invocation_call)
    print(f"Guranteed good statement is valid: {valid_check}")
    print(f"Guranteed bad statement is valid: {invalid_check}")
    
    #valid_invocation_call = valid_invocation
    #is_valid = check_for_sql_call(test_valid_invocation)
    #print(f"Is valid invocation: {is_valid}")

class SQLTransformer(cst.CSTTransformer):

    def __init__(self, filepath: str):
        self.node_stack = []
        self.filepath = filepath
        self.filepath_without_extension = filepath.replace(".py", "")
        self.filename = filepath.split("/")[-1]
        self.filename_without_extension = self.filename.replace(".py", "")
        self.local_cache = {}

        print("SQLTransformer initialized")
    
    def visit_Assign(self, node: cst.Assign) -> None:
        self.node_stack.append(node)
        print("Visiting Assign")
    
    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        func_call = original_node.func
        
        if check_for_valid_sql_invocation(original_node):
            print("Found sql call")
            sql_string = original_node.args[0].value.value.lstrip('"').rstrip('"')
            print(f"SQL string: {sql_string}")

            # Inside the Call Node, this gets the parent Assign node
            if self.stack:
                last_assign = self.stack[-1]
                
            new_args = list(original_node.args)
            new_args[0] = cst.Arg(value=cst.SimpleString(f'"processed!"'))

            # Generate the SQL key for this invocation
            assign_name = last_assign.value.value.lstrip('"').rstrip('"')
            print(f"Assign name: {assign_name}")
            sql_hash = hash(sql_string)

            # sql_key:
            # federal_rows,test.py
            # sql_class = sql("SELECT * FROM table;")
            # result = sql_class.invoke()
            files_used_in = []

            sql_key = assign_name
            invocation_metadata = {
                "sql_hash": sql_hash,
                "sql_string": sql_string,
                "native_sql": "",
                "file_defined_in": self.filename,
                "files_used_in": files_used_in
            }

            # Check if the sql_key is in the cache.json file
            with open("cache.json", "r") as f:
                cache = json.load(f)
                # Case: not a completely new invocation
                if sql_key in cache:
                    # Case: Changed sql, New invocation should override old invocation
                    if cache["sql_hash"] != sql_hash:
                        # Update the invocation_metadata in cache.json
                        cache[sql_key] = invocation_metadata
                    # Case: Unchanged invocation, Do nothing
                    else:
                        
                        target_files_used_in = cache[sql_key]["files_used_in"]
                        # Case: File not already in files_used_in
                        if self.filename not in target_files_used_in:
                            cache[sql_key]["files_used_in"].append(self.filename)
                        # Case: File already in files_used_in, duplicate invocation of same sql in same file
                        else:
                            pass

                        return updated_node
                # Case: Completely new invocation
                else:
                    cache[sql_key] = invocation_metadata

            native_sql = f" /* {sql_key} */ {sql_string}"
            
            invocation_metadata["native_sql"] = native_sql
            
            self.local_cache[sql_key] = invocation_metadata

            with open("cache.json", "w") as f:
                f.write(json.dump(cache))
           
        return updated_node
    
    def leave_Assign(self, original_node: cst.Assign, updated_node: cst.Assign) -> cst.Assign:
        self.stack.pop()
        if (
            isinstance(updated_node.value, cst.Call)
            and isinstance(updated_node.value.func, cst.Name)
            and updated_node.value.func.value == "sql"
        ):
            # Get the name of the variable being assigned
            assign_name = original_node.targets[0].value.value.lstrip('"').rstrip('"')
            assign_name = assign_name[0].upper() + assign_name[1:] + "Result"
            # Create a new AnnAssign node with the modified annotation
            new_annotation = cst.Annotation(
                    annotation=cst.Subscript(
                        
                        value=cst.Name(value="List"),
                        slice=[
                            cst.SubscriptElement(
                                slice=cst.Index(value=cst.Name(value=f"{assign_name}Result"))
                            )
                        ],
                          
                    )
                )
        assign_name = original_node.targets[0].value.value.lstrip('"').rstrip('"')
        return updated_node
    
    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        
        converted_filename = self.filename_without_extension + "_temp.sql"
        # Run pgtyped-pydantic to regenerate models
        cfg = 'config.json'
        file_override = converted_filename

        
        # Running repository as python subprocess
        command = ['npx', 'pgtyped-pydantic', '-c', cfg, '-f', file_override]
        process = subprocess.run(command, capture_output=True)

        # Retrieve the updated models from process.stdout, convert to string
        raw_string = process.stdout.decode('utf-8')
        updated_model_classes = raw_string.split("*** EOF ***")
        updated_model_classes.pop()

        for updated_model in updated_model_classes:
            print(updated_model)
        exit(1)

        # Parse the updated models into a CST
        updated_models_tree = cst.parse_module(updated_models)

        # Extract each model from the updated models tree
        updated_models = {"params:": None, "result": None, "invoke": None}

        return updated_node
    

def check_for_valid_sql_invocation(node: cst.Call) -> bool:
    """This function checks if a Call node is a valid invocation to the `sql` function."""
    func_call = node.func
    args = node.args

    # Ensure the Call node has a function and arguments
    if len(args) != 1:
        return False
    # Ensure that the function being called is `sql` and that the first argument is a string literal
    if not m.matches(func_call, m.Name("sql")) or not m.matches(args[0].value, m.SimpleString()):
        return False
    return True


def apply_codemod_to_file(filepath: str):
    with open(filepath, "r") as f:
        source_code = f.read()

    # Parse the source code into a CST
    tree = cst.parse_module(source_code)

    # Apply the codemod
    transformer = SQLTransformer(filepath)
    modified_tree = tree.visit(transformer)

    print(f"\n\n\n\nModified code:\n{modified_tree.code}")

    # Write the modified code back to the file
    filename_without_extension = transformer.filepath_without_extension
    with open(f"{filename_without_extension}_processed.py", "w") as f:
        f.write(modified_tree.code)

if __name__ == "__main__":
    main()