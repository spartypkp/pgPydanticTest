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
class ExpansionScalarList(BaseModel):
    """
    param_name: The name of the parameter in the SQL string, which denotes the list of scalars being inserted.
    Use this class when a dynamically inserted variable should be a list of scalars."""
    param_name: str

class ExpansionModel(BaseModel):
    """
    param_name: The name of the parameter in the SQL string, which denotes the object being inserted.
    pydantic_type: The Pydantic model that the object should be an instance of.
    source_file: The file that the Pydantic model is defined in.
    Use this class when dynamically inserted variables are being represented by a single object in the SQL string.
    """
    param_name: str
    pydantic_type: Any
    source_file: str

    @computed_field
    @property
    def model_fields(self) -> List[str]:
        # Return the names of the fields in the Pydantic model
        return self.pydantic_type.__fields__.keys()
    
class ExpansionModelList(BaseModel):
    """
    param_name: The name of the parameter in the SQL string, which denotes the object being inserted.
    pydantic_type: The Pydantic model that the object should be an instance of.
    source_file: The file that the Pydantic model is defined in.
    Use this class when dynamically inserted variables are being represented by a single object in the SQL string, however you want to insert multiple.
    """
    param_name: str
    pydantic_type: Any
    source_file: str


    @computed_field
    @property
    def model_fields(self) -> List[str]:
        # Return the names of the fields in the Pydantic model
        return self.pydantic_type.__fields__.keys()
    
class ExpansionList(BaseModel):
    expansions: List[Union[ExpansionScalarList, ExpansionModel, ExpansionModelList]]



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
        # LOGGER.info(f"SQLTransformer initialized for file: {self.filename}")

    
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
            
            sql_string = updated_node.args[0].value.value.lstrip('"').rstrip('"')
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
            
            # Example SQL String: INSERT INTO stupid_test_table (name, age, email) VALUES myaccount<class 'model_library.Account'>;
            # Example SQL String: INSERT INTO stupid_test_table (name, age, email) VALUES <class 'model_library.Account'>;
    
            # The regex pattern to match Python class string representations
            pattern = r"(\w+)?\s*<class '([\w\.]+)'>"

            # Find all matches in the SQL string
            matches = re.findall(pattern, sql_string)

            # For each match, split the match into the variable name, module and class name
            classes = {}
            for match in matches:
                variable_name, class_string = match
                is_primitive_type = True
                module = None
                # Indicates custom class with module name
                if '.' in class_string:
                    module, class_name = class_string.rsplit('.', 1)
                    is_primitive_type = False
                    # Infer the variable name from the custom class name
                    if not variable_name:
                        
                        inferred_variable_name = class_name.lower()
                # Require the variable name for primitive types
                if not variable_name and is_primitive_type:
                    raise ValueError(f"Variable name not found for primitive Type: {class_string}")

                # Check if the class is wrapped in []
                is_wrapped = sql_string[sql_string.index(class_string) - 1] == '[' and sql_string[sql_string.index(class_string) + len(class_string) + 1] == ']'

                # Start construction of a new string to replace the match
                replacement_string = ":"
                parameter_expansion = "@param "
                if not variable_name:
                    replacement_string += inferred_variable_name
                    parameter_expansion += inferred_variable_name
                else:
                    replacement_string += variable_name
                    parameter_expansion += variable_name
                parameter_expansion += " -> "

                # If the class is wrapped in [], start with a (
                if is_wrapped:
                    parameter_expansion += "("

                # If the class is a primitive type, add ... to parameter expansion
                if is_primitive_type:
                    parameter_expansion += "..."
                else:
                    # Import the module and class dynamically to get the fields
                    module = importlib.import_module(module)
                    class_type = getattr(module, class_name)
                    field_representation = f"({', '.join(class_type.__fields__.keys())})"
                    parameter_expansion += field_representation
                
                # If the class is wrapped in [], end with a )
                if is_wrapped:
                    parameter_expansion += ")"

                
                parameter_expansion += "*/\n"
                # Replace the match with the replacement string
                sql_string = sql_string.replace(f"{variable_name}{class_string}", replacement_string)
                # Add the parameter expansion to the native SQL
                native_sql += parameter_expansion
                


                classes[parameter_expansion] = (variable_name, class_name, module, is_wrapped, is_primitive_type)

            print(classes)
            print(native_sql)
            print(sql_string)
            
            native_sql += sql_string
            


            sql_hash = hash(sql_string)
            sql_key = assign_name
            # LOGGER.debug(f"SQL key: {sql_key}")
            invocation_metadata = {
                "sql_hash": sql_hash,
                "sql_string": sql_string,
                "native_sql": "",
                "file_defined_in": self.filename,
            }
            cache = None
            # Check if the sql_key is in the cache.json file
            # with open("cache.json", "r") as f:
            #     text = f.read()
            #     cache = json.loads(text)
            #     # LOGGER.debug(f"Loaded cache: {cache}")
            #     # Case 1: not a completely new invocation
            #     if sql_key in cache:
            #         # LOGGER.debug(f"Cache for sql_key: {sql_key} exists:\n{cache[sql_key]}")
            #         # Case 2: Changed sql, New invocation should override old invocation

            #         if cache[sql_key]["sql_string"] != sql_string:
            #             # LOGGER.debug(f"Case 2: Changed sql, New invocation should override old invocation")
            #             # LOGGER.critical(f"Warning! You are overriding an existing SQL invocation, which will regenerate the models. If you want to keep the old models with the same name, please change the variable name you are assinging to.")
            #             # Update the invocation_metadata in cache.json
            #             cache[sql_key] = invocation_metadata
            #         # Case 3: Unchanged invocation, maybe update files_used_in
            #         else:
            #             # LOGGER.debug(f"Case 3: Unchanged invocation, Do nothing")      
            #             target_files_used_in = cache[sql_key]["files_used_in"]
            #             # Case: File not already in files_used_in
            #             if self.filename not in target_files_used_in:
            #                 cache[sql_key]["files_used_in"].append(self.filename)
            #             # Case: File already in files_used_in, duplicate invocation of same sql in same file
            #             else:
            #                 pass

            #             return updated_node
            #     # Case 4: Completely new invocation
            #     else:
            #         # LOGGER.debug(f"Case 4: Completely new invocation")
            #         cache[sql_key] = invocation_metadata

            
            
            
            # cache[sql_key]["native_sql"] = native_sql
            
            # self.local_cache[sql_key] = invocation_metadata

            # # LOGGER.info(f"Updated cache: {cache}")
            # with open("cache.json", "w") as f:
            #     f.write(json.dumps(cache))
           
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
        
        custom_model_imports = set()
        converted_filename = self.filename_without_extension + "_temp.sql"
        if len(self.local_cache.keys()) == 0:
            # LOGGER.info(f"No new or updated SQL invocations found in file.")
            return updated_node
        with open(converted_filename, "w") as f:
            write_string = ""
            for k,v in self.local_cache.items():
                write_string += v["native_sql"] + "\n\n"
                for model_import in v["custom_model_imports"]:
                    custom_model_imports.add(model_import)
                
                
            # LOGGER.debug(f"Writing to _temp.sql file: {write_string}")
            f.write(write_string)
        f.close()
        # Run pgtyped-pydantic to regenerate models
        cfg = 'config.json'
        file_override = converted_filename
        custom_model_imports = "\n".join(list(custom_model_imports))
        
        # Running repository as python subprocess
        command = ['npx', 'pgtyped-pydantic', '-c', cfg, '-f', file_override]
        process = subprocess.run(command, capture_output=True)
       

        # Retrieve the updated models from process.stdout, convert to string
        raw_string = process.stdout.decode('utf-8')
        raw_errors = process.stderr.decode('utf-8')
        
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
                source_code = custom_model_imports + "\n" + source_code
                # LOGGER.debug(f"Retrieved source code from {output_filename}.py")
            except:
                source_code = "from typing import List, Optional, Dict, Any, Union\nimport datetime\nfrom pydantic import BaseModel\nfrom typing_extensions import NewType\nfrom psycopg.rows import class_row\nimport psycopg\nfrom sql_transformer import sql_executor\n\n"
                for mod in updated_model_classes_raw:
                    source_code += mod
                if custom_model_imports not in source_code:
                    source_code = custom_model_imports + "\n" + source_code
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
            
            
            names.append(cst.ImportAlias(name=cst.Name(k)))
            
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
    if not m.matches(func_call, m.Name("sql")) or not m.matches(args[0].value, m.SimpleString()):
        return False
    # Ensure that the second argument is of type List[Expansion]
    
    if len(args) == 2 and not m.matches(args[1].value.func, m.Name("ExpansionList")):
        return False
    
    return True

def pascal_case(name: str) -> str:
    # Example input: "select_federal_rows"
    # Example output: "SelectFederalRows"
    return "".join(map(str.title, name.split("_")))


def find_python_classes_in_sql(query: str):
    # Regex pattern to match Python class representations, including lists and built-in types
    pattern = r"(\[)?<class '([\w\.]*)(\w+)'>\]?"
    
    matches = re.findall(pattern, query)
    
    extracted_info = []
    for is_list, module_with_class, class_name in matches:
        is_list_bool = bool(is_list)  # Converts non-empty string to True, empty to False
        module_name = module_with_class.rpartition('.')[0]  # Extract module, empty if built-in type
        

        # Dynamically import the class so that it can be used in the SQLTransformer
        module = importlib.import_module(module_name)
        class_ = getattr(module, class_name)

        # If the class is a subclass of Pydantic's BaseModel, create the expansion
        if issubclass(class_, BaseModel):
            class_fields = class_.model_fields.keys()
            class_fields = f"({', '.join(class_fields)})"
            if is_list_bool:
                class_fields = f"({class_fields}...)"
            expansion = f"@param {class_name} -> {class_fields}"
        elif is_list_bool:

            expansion = f"@param {class_name} -> (...)"
        


    return extracted_info
if __name__ == "__main__":
    main()