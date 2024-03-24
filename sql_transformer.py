import sys
import libcst as cst
import libcst.matchers as m
import subprocess
import time
import threading
from queue import Queue
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import json
# apply_codemod.py
import sys
import re
import subprocess
import libcst as cst
from libcst.codemod import CodemodContext
from libcst.metadata import ParentNodeProvider
import psycopg
from psycopg import sql as ps_sql
from psycopg.types.json import Jsonb
from psycopg.rows import class_row, dict_row
from typing import List, Any, Optional, TypeVar, Callable, Union, get_args, get_origin, Dict
import pydantic
from pydantic import BaseModel, computed_field
import logging
import inspect
import importlib


import os
from model_transformer import ModelTransformer, add_module
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)


# Making impossible states impossible: Talk recommended by Sean

def main():
    pass
# Credit to SeanGrove for the original version of this codemod, G.O.A.T.
# ================================= CODE MOD ========================================

class SQLTransformer(cst.CSTTransformer):

    def __init__(self, filepath: str):
        self.node_stack = []
        self.filepath = filepath
        self.filepath_without_extension = filepath.replace(".py", "")
        self.filename = filepath.split("/")[-1]
        self.filename_without_extension = self.filename.replace(".py", "")
        self.local_cache = {}
        self.imports = {}
        self.custom_imports = {}
        # LOGGER.info(f"SQLTransformer initialized for file: {self.filename}")

    def visit_Import(self, node: cst.Import) -> None:
        for alias in node.names:
            self.imports[alias.evaluated_alias] = alias.name.value

    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
        
        if node.module is not None:
            module_name = node.module.value
            class_names = []
            for name in node.names:
                if name.asname is not None:
                    class_names.append(name.asname)
                else:
                    class_names.append(name.name.value)
            self.imports[module_name] = class_names

    def handle_assignment(self, node: Union[cst.Assign, cst.AnnAssign]) -> None:
        self.node_stack.append(node)

    def visit_Assign(self, node: cst.Assign) -> None:
        self.handle_assignment(node)
        # LOGGER.debug(f"Visiting Assign: {node.targets[0].target.value}")

    def visit_AnnAssign(self, node: cst.AnnAssign) -> None:
        self.handle_assignment(node)
        # LOGGER.debug(f"Visiting AnnAssign: {node.target.value}")
        # LOGGER.debug(f"Current Annotation: {node.annotation.annotation.value}")

        
    
    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        
        
        if check_for_valid_sql_invocation(original_node):
            cst_string = original_node.args[0].value
            custom_model_imports = []
            if isinstance(cst_string, cst.FormattedString):
                string_construction = []
                parameter_expansions = []

                for part in cst_string.parts:
                    #print(part)
                    if isinstance(part, cst.FormattedStringExpression):
                        class_name, is_wrapped = analyze_formatted_string_expression(part)
                        # Try and access the last word in the last string in string_construction
                        variable_name = None
                        is_primitive_type = False
                        if string_construction:
                            last_string = string_construction[-1]
                            
                            
                            if last_string[-1] != " ":
                                variable_name = last_string.split()[-1]
                                
                        
                        # If class name denotes a primitive type
                        if class_name in ["int", "str", "float", "bool"]:
                            is_primitive_type = True
                            if not variable_name:
                                raise ValueError(f"Variable name not found for primitive Type: {class_name}")
                        else:
                            if not variable_name:
                                variable_name = class_name.lower()
                        
                        string_to_replace = f":{variable_name}"
                        parameter_expansion = f"  @param {variable_name} -> "
                        if is_wrapped:
                            parameter_expansion += "("
                        if is_primitive_type:
                            parameter_expansion += "..."
                        else:
                            # Import the module and class dynamically
                            # First, analyze the imports in the file we are transforming
                            # Find the module the class is imported from, or if it is defined in the same file
                            # Then, import the module and class dynamically
                            
                            if class_name not in ["int", "str", "float", "bool"]:
                                module_name = self.filename_without_extension
                                for k,v in self.imports.items():
                                    if class_name in v:
                                        module_name = k
                                        if module_name not in self.custom_imports:
                                            self.custom_imports[module_name] = []
                                        if class_name not in self.custom_imports[module_name]:
                                            self.custom_imports[module_name].append(class_name)
                                        break
                                
                                
                                module = importlib.import_module(module_name)
                                class_type = getattr(module, class_name)
                                
                                field_representation = f"({', '.join(class_type.__fields__.keys())})"
                                parameter_expansion += field_representation
                                if is_wrapped:
                                    parameter_expansion += "..."
                                
                        
                        if is_wrapped:
                            parameter_expansion += ")"
                        
                        
                        string_construction.append(string_to_replace)
                        parameter_expansions.append(parameter_expansion)
                    else:
                        string_construction.append(part.value)
                sql_string = ''.join(string_construction)                        
            else:
                sql_string = updated_node.args[0].value.value.lstrip('"').rstrip('"')
            
            
            #print(f" - Final SQL String: {sql_string}")
                
            if sql_string[-1] != ";":
                sql_string += ";"

            # Inside the Call Node, this gets the parent Assign node
            if self.node_stack:
                last_assign = self.node_stack[-1]
                
            

            # Generate the SQL key for this invocation
            if isinstance(last_assign, cst.AnnAssign):
                assign_name_raw = last_assign.target.value.lstrip('"').rstrip('"')
            else:
                assign_name_raw = last_assign.targets[0].target.value.lstrip('"').rstrip('"')
            
            assign_name = pascal_case(assign_name_raw)

            native_sql = f"/* @name {assign_name} \n"
            native_sql += '\n'.join(parameter_expansions) + "\n*/\n"
            native_sql += sql_string
            print(native_sql)
            
            # Example SQL String: INSERT INTO stupid_test_table (name, age, email) VALUES myaccount<class 'model_library.Account'>;
            # Example SQL String: INSERT INTO stupid_test_table (name, age, email) VALUES <class 'model_library.Account'>;
    
            # The regex pattern to match Python class string representations
            


            sql_hash = hash(sql_string)
        
            # LOGGER.debug(f"SQL key: {sql_key}")
            invocation_metadata = {
                "query_name": assign_name,
                "sql_string": sql_string,
                "native_sql": native_sql,
                "file_defined_in": self.filename,
                "custom_model_imports": set()
            }
            self.local_cache[sql_hash] = invocation_metadata

           
        return updated_node
    
    def leave_Assign(self, original_node: cst.Assign, updated_node: cst.Assign) -> cst.Assign:
        self.node_stack.pop()
        if (
            isinstance(updated_node.value, cst.Call)
            and isinstance(updated_node.value.func, cst.Name)
            and updated_node.value.func.value == "sql"
        ):
            # Get the name of the variable being assigned
            assign_name = original_node.targets[0].target.value.lstrip('"').rstrip('"')
            assign_name = pascal_case(assign_name)
            
            # Create a new AnnAssign node with the modified annotation
            new_annotation = cst.Annotation(  cst.Name(value=assign_name))
            
            return cst.AnnAssign(
                target=updated_node.targets[0].target,
                annotation=new_annotation,
                value=updated_node.value,
                equal=cst.AssignEqual(),
            )
        return updated_node
    
    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        
        
        converted_filename = self.filename_without_extension + "_temp.sql"
        if len(self.local_cache.keys()) == 0:
            # LOGGER.info(f"No new or updated SQL invocations found in file.")
            return updated_node
        with open(converted_filename, "w") as f:
            write_string = ""
            for k,v in self.local_cache.items():
                write_string += v["native_sql"] + "\n\n"
                
                
                
            # LOGGER.debug(f"Writing to _temp.sql file: {write_string}")
            f.write(write_string)
        f.close()
        # Run pgtyped-pydantic to regenerate models
        cfg = 'config.json'
        file_override = converted_filename
        
        
        # Running repository as python subprocess
        command = ['npx', 'pgtyped-pydantic', '-c', cfg, '-f', file_override]
        process = subprocess.run(command, capture_output=True)
       

        # Retrieve the updated models from process.stdout, convert to string
        raw_string = process.stdout.decode('utf-8')
        print(raw_string)

        raw_errors = process.stderr.decode('utf-8')
        print(raw_errors)
        
        #LOGGER.debug(f"Raw pgtyped-pydantic output: {raw_string}")
        # LOGGER.debug(f"Raw pgtyped-pydantic errors: {raw_errors}")
        updated_model_classes_raw = raw_string.replace("    ", "\t").split("### EOF ###")
        # LOGGER.debug(f"Updated model classes: {updated_model_classes_raw}")
        updated_model_classes_raw.pop()
        updated_model_classes: List[cst.ClassDef] = []
        for i, model in enumerate(updated_model_classes_raw):
            # LOGGER.debug(f"Model {i}: {model}")
            as_module = cst.parse_module(model)
            as_class = as_module.body[0]
            updated_model_classes.append(as_class)

        custom_model_imports_str = ""
        for k,v in self.custom_imports.items():
            custom_model_imports_str += f"from {k} import {', '.join(v)}\n"
        
        with open("config.json", "r") as f:
            config = json.load(f)
        f.close()
        output_mode = config["outputMode"]
        skip_model_transformer = False
        # "default" Mode: Write the updated modesl to a new file, corresponding to each scanned file
        if output_mode != "monorepo":
            # LOGGER.debug(f"Output mode: {output_mode}")
            output_filename = f"{self.filename_without_extension}_models"
            try:
                with open(f"{output_filename}.py", "r") as f:
                    source_code = f.read()
                f.close()
                source_code = custom_model_imports_str + "\n" + source_code
                # LOGGER.debug(f"Retrieved source code from {output_filename}.py")
            except:
                source_code = "from typing import List, Optional, Dict, Any, Union\nimport datetime\nfrom pydantic import BaseModel\nfrom typing_extensions import NewType\nfrom psycopg.rows import class_row\nimport psycopg\nfrom sql_transformer import sql_executor\n\n"
                for mod in updated_model_classes_raw:
                    source_code += mod
                if custom_model_imports_str not in source_code:
                    source_code = custom_model_imports_str + "\n" + source_code
                # File does not exist yet, create it
                with open(f"{output_filename}.py", "w") as f:
                    f.write(source_code)
                f.close()
                skip_model_transformer = True
                # LOGGER.debug(f"Created new file: {output_filename}.py. Wrote updated models to file. SKIPPING MODEL TRANSFORMER")
            

        
        # "monorepo" Mode: Write the updated models to a single file, corresponding to all scanned files
        else:
            source_code = ""
            with open("generated_models.py", "r") as file:
                source_code = file.read()
            file.close()
            # LOGGER.debug(f"Retrieved source code from generated_models.py")
            output_filename = "generated_models"
        
        # Run the model transformer to update the already created _models file
        if not skip_model_transformer:
            # Parse the source code into a CST
            intermediate_tree = cst.parse_module(source_code)
            
            # Apply the codemod
            model_transformer = ModelTransformer(updated_classes=updated_model_classes)
            updated_intermediate_tree = intermediate_tree.visit(model_transformer)

            updated_intermediate_tree = add_module(updated_model_classes, updated_intermediate_tree)

            
            #print(f"\n\n\n\nModified code:\n{modified_tree.code}")
            
            with open(f"{output_filename}.py", "w") as file:
                file.write(updated_intermediate_tree.code)
            file.close()
        

        # Regardless of output mode, update the imports in the scanned file
        names = []
        for k, v in self.local_cache.items():
             
            
            names.append(cst.ImportAlias(name=cst.Name(v["query_name"])))
            
        new_import = cst.ImportFrom(
            module=cst.Name(output_filename),
            names=names,
        )
        # If nothing was added, return the original node
        if len(names) == 0:
            return original_node


        # Add a newline after the imports
        new_imports = [new_import, cst.EmptyLine(), cst.EmptyLine()]
        # Remove the temporary file
        os.remove(converted_filename)
        updated_node = updated_node.with_changes(body=new_imports + list(updated_node.body))
        return updated_node
    

def check_for_valid_sql_invocation(node: cst.Call) -> bool:
    """This function checks if a Call node is a valid invocation to the `sql` function."""
    func_call = node.func
    args = node.args

    # Ensure the Call node has a function and arguments
    
    if len(args) != 1 and len(args) != 2:
        return False
    # Ensure that the function being called is `sql` and that the first argument is a string literal
    #print(func_call)
    #print(type(args[0].value))

    if not m.matches(func_call, m.Name("sql")) or not m.matches(args[0].value, m.FormattedString()):
        return False
    # Ensure that the second argument is of type List[Expansion]
    
    if len(args) == 2 and not m.matches(args[1].value.func, m.Name("ExpansionList")):
        return False
    
    return True

def pascal_case(name: str) -> str:
    # Example input: "select_federal_rows"
    # Example output: "SelectFederalRows"
    return "".join(map(str.title, name.split("_")))


def analyze_formatted_string_expression(fse: cst.FormattedStringExpression):
    """
    Analyzes a FormattedStringExpression object to find class names and list wrapping.

    Parameters:
    - fse (cst.FormattedStringExpression): The formatted string expression to analyze.

    Returns:
    - Tuple containing:
        - The cst.Name value if found, otherwise None.
        - Boolean indicating if the cst.Name is wrapped in a list.
    """
    class_name = None
    is_wrapped_in_list = False

    # Check if the expression is a List
    if isinstance(fse.expression, cst.List):
        is_wrapped_in_list = True
        # Iterate over elements in the list
        for element in fse.expression.elements:
            if isinstance(element.value, cst.Name):
                # Extract the class name
                class_name = element.value.value
                break  # Assuming only one class name per list for this use case

    return class_name, is_wrapped_in_list
    
if __name__ == "__main__":
    main()