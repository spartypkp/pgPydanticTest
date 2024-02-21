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
import subprocess
import libcst as cst
from libcst.codemod import CodemodContext
from libcst.metadata import ParentNodeProvider
import psycopg
from psycopg.types.json import Jsonb
from psycopg.rows import class_row, dict_row
from typing import List, Any, Optional, TypeVar, Callable, Union, get_args, get_origin
import pydantic
import logging
import os
from model_transformer import ModelTransformer, add_module
DIR = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(DIR)
sys.path.append(parent)

LOGGER = None

def main():
    
    with open('config.json') as f:
        config = json.load(f)
    f.close()
    srcDir = config['srcDir']
    create_logger(verbose=True)
    
    LOGGER.info(f"Starting watchDawg program.")
    LOGGER.debug(f"srcDir: {srcDir}")
    start_watching(srcDir)

class PyFileEventHandler(FileSystemEventHandler):
    def __init__(self, queue):
        self.queue = queue
        self.previous_write_file = ""

    def on_modified(self, event):
        if "config.json" in event.src_path:
            raise Exception("config.json was modified. Please restart the program.")
        if event.src_path.endswith('.py'):
            # If the file modified is this file, don't do anything
            if "watchDawg" in event.src_path:
                return
            # Temporary
            if "_" in event.src_path:
                return
            
            self.queue.put(event)

def worker(queue):
    previous_write_file = ""
    while True:
        event = queue.get()
        if event is None:  # None is sent as a signal to stop the worker
            break
        assert(LOGGER is not None)
        # Your callback function goes here
        LOGGER.info(f"Detected change in: {event.src_path}")
        
        if event.src_path == previous_write_file:
            LOGGER.critical(f"Change corresponds to previous write: {previous_write_file}. Skipping.")
            previous_write_file = ""
            queue.task_done()
            continue

        # Call apply_codemod.py with the detected filename
        try:
            target_write_file = apply_codemod_to_file(event.src_path)
            previous_write_file = target_write_file
        except Exception as e:
            # If the type of the Exception is SyntaxError, then the file is already processed. This should be ignored
            if type(e) == SyntaxError:
                LOGGER.info(f"File already processed: {event.src_path}. Skipping.")
            else:
                LOGGER.exception(f"Error applying codemod to file: {event.src_path}. Error: {e}")
            
        
        queue.task_done()

def start_watching(path):
    queue = Queue()
    event_handler = PyFileEventHandler(queue)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()

    worker_thread = threading.Thread(target=worker, args=(queue,))
    worker_thread.start()

    try:
        while observer.is_alive():
            observer.join(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

    # Stop the worker thread
    queue.put(None)
    worker_thread.join()


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
        LOGGER.info(f"SQLTransformer initialized for file: {self.filename}")

    
    def handle_assignment(self, node: Union[cst.Assign, cst.AnnAssign]) -> None:
        self.node_stack.append(node)

    def visit_Assign(self, node: cst.Assign) -> None:
        self.handle_assignment(node)
        LOGGER.debug(f"Visiting Assign: {node.targets[0].target.value}")

    def visit_AnnAssign(self, node: cst.AnnAssign) -> None:
        self.handle_assignment(node)
        LOGGER.debug(f"Visiting AnnAssign: {node.target.value}")
        LOGGER.debug(f"Current Annotation: {node.annotation.annotation.value}")

        
    
    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        
        
        if check_for_valid_sql_invocation(original_node):
            
            sql_string = updated_node.args[0].value.value.lstrip('"').rstrip('"')
            LOGGER.debug(f"Found SQL string: {sql_string}")

            # Inside the Call Node, this gets the parent Assign node
            if self.node_stack:
                last_assign = self.node_stack[-1]
                
            

            # Generate the SQL key for this invocation
            if isinstance(last_assign, cst.AnnAssign):
                assign_name_raw = last_assign.target.value.lstrip('"').rstrip('"')
            else:
                assign_name_raw = last_assign.targets[0].target.value.lstrip('"').rstrip('"')
            LOGGER.debug(f"Assign name raw: {assign_name_raw}")
            assign_name = pascal_case(assign_name_raw)
            LOGGER.debug(f"Pascal Assign name: {assign_name}")
            sql_hash = hash(sql_string)

            # sql_key:
            # federal_rows,test.py
            # sql_class = sql("SELECT * FROM table;")
            # result = sql_class.invoke()
            files_used_in = []

            sql_key = assign_name
            LOGGER.debug(f"SQL key: {sql_key}")
            invocation_metadata = {
                "sql_hash": sql_hash,
                "sql_string": sql_string,
                "native_sql": "",
                "file_defined_in": self.filename,
                "files_used_in": files_used_in
            }
            cache = None
            # Check if the sql_key is in the cache.json file
            with open("cache.json", "r") as f:
                text = f.read()
                cache = json.loads(text)
                LOGGER.debug(f"Loaded cache: {cache}")
                # Case 1: not a completely new invocation
                if sql_key in cache:
                    LOGGER.debug(f"Cache for sql_key: {sql_key} exists:\n{cache[sql_key]}")
                    # Case 2: Changed sql, New invocation should override old invocation

                    if cache[sql_key]["sql_string"] != sql_string:
                        LOGGER.debug(f"Case 2: Changed sql, New invocation should override old invocation")
                        LOGGER.critical(f"Warning! You are overriding an existing SQL invocation, which will regenerate the models. If you want to keep the old models with the same name, please change the variable name you are assinging to.")
                        # Update the invocation_metadata in cache.json
                        cache[sql_key] = invocation_metadata
                    # Case 3: Unchanged invocation, maybe update files_used_in
                    else:
                        LOGGER.debug(f"Case 3: Unchanged invocation, Do nothing")      
                        target_files_used_in = cache[sql_key]["files_used_in"]
                        # Case: File not already in files_used_in
                        if self.filename not in target_files_used_in:
                            cache[sql_key]["files_used_in"].append(self.filename)
                        # Case: File already in files_used_in, duplicate invocation of same sql in same file
                        else:
                            pass

                        return updated_node
                # Case 4: Completely new invocation
                else:
                    LOGGER.debug(f"Case 4: Completely new invocation")
                    cache[sql_key] = invocation_metadata

            native_sql = f"/* @name {sql_key} */\n{sql_string}"
            
            cache[sql_key]["native_sql"] = native_sql
            
            self.local_cache[sql_key] = invocation_metadata

            LOGGER.info(f"Updated cache: {cache}")
            with open("cache.json", "w") as f:
                f.write(json.dumps(cache))
           
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
            LOGGER.info(f"No new or updated SQL invocations found in file.")
            return updated_node
        with open(converted_filename, "w") as f:
            write_string = ""
            for k,v in self.local_cache.items():
                write_string += v["native_sql"] + "\n\n"
            LOGGER.debug(f"Writing to _temp.sql file: {write_string}")
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
        raw_errors = process.stderr.decode('utf-8')
        
        #LOGGER.debug(f"Raw pgtyped-pydantic output: {raw_string}")
        LOGGER.debug(f"Raw pgtyped-pydantic errors: {raw_errors}")
        updated_model_classes_raw = raw_string.replace("    ", "\t").split("### EOF ###")
        LOGGER.debug(f"Updated model classes: {updated_model_classes_raw}")
        updated_model_classes_raw.pop()
        updated_model_classes: List[cst.ClassDef] = []
        for i, model in enumerate(updated_model_classes_raw):
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
            LOGGER.debug(f"Output mode: {output_mode}")
            output_filename = f"{self.filename_without_extension}_models"
            try:
                with open(f"{output_filename}.py", "r") as f:
                    source_code = f.read()
                f.close()
                LOGGER.debug(f"Retrieved source code from {output_filename}.py")
            except:
                source_code = "from typing import List, Optional, Dict, Any, NewType\nimport datetime\nfrom pydantic import BaseModel\nfrom typing_extensions import NewType\n\n"
                for mod in updated_model_classes:
                    source_code += mod.code
                # File does not exist yet, create it
                with open(f"{output_filename}.py", "w") as f:
                    f.write(source_code)
                f.close()
                skip_model_transformer = True
                LOGGER.debug(f"Created new file: {output_filename}.py. Wrote updated models to file. SKIPPING MODEL TRANSFORMER")

        
        # "monorepo" Mode: Write the updated models to a single file, corresponding to all scanned files
        else:
            source_code = ""
            with open("generated_models.py", "r") as file:
                source_code = file.read()
            file.close()
            LOGGER.debug(f"Retrieved source code from generated_models.py")
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
    if len(args) != 1:
        return False
    # Ensure that the function being called is `sql` and that the first argument is a string literal
    if not m.matches(func_call, m.Name("sql")) or not m.matches(args[0].value, m.SimpleString()):
        return False
    return True


def apply_codemod_to_file(filepath: str) -> str:
    with open(filepath, "r") as f:
        source_code = f.read()

    # Parse the source code into a CST
    tree = cst.parse_module(source_code)

    # Apply the codemod
    transformer = SQLTransformer(filepath)
    modified_tree = tree.visit(transformer)
    LOGGER.info(f"Finished applying codemod to file: {filepath}")
    if source_code == modified_tree.code:
        LOGGER.info(f"No changes made to file: {filepath}")
        return ""
    
    LOGGER.debug(f"\n\n\n\nModified code:\n{modified_tree.code}")

    # Write the modified code back to the correct file, based on config
    with open("config.json", "r") as f:
        config = json.load(f)
    f.close()
    generate_new_file = config["write_changes_to_new_file"]
    LOGGER.debug(f"Write modified file to new file: {generate_new_file}")

    filepath_without_extension = transformer.filepath_without_extension
    if generate_new_file:
        target_write_file = f"{filepath_without_extension}_processed.py"
    else:
        target_write_file = f"{filepath_without_extension}.py"

    LOGGER.debug(f"Writing modified code to: {target_write_file}")
    with open(target_write_file, "w") as f:
        f.write(modified_tree.code)
    f.close()
    return target_write_file

def create_logger(verbose=False):
    global LOGGER
    # Ensure the logs directory exists
    os.makedirs(os.path.join(DIR, 'logs'), exist_ok=True)

    # Create or get the LOGGER
    LOGGER = logging.getLogger("watchDawg")

    # Optionally clear existing handlers to prevent duplicate messages
    LOGGER.handlers = []

    # Set the logging level
    LOGGER.setLevel(logging.DEBUG)

    # Create handlers (file and console)
    file_handler = logging.FileHandler(f"{DIR}/logs/watchDawg.log", mode="w")

    # Create a logging format
    formatter = logging.Formatter('%(name)s - %(levelname)s - %(asctime)s: \n%(message)s \nSource:(%(filename)s:%(lineno)d)\n')
    file_handler.setFormatter(formatter)

    # Add file handler to the LOGGER
    LOGGER.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    console_handler.filter(lambda record: record.levelno >= logging.INFO)
    if verbose:
        # Create console handler with a higher log level
        console_handler.setLevel(logging.DEBUG)
        console_handler.filter(lambda record: record.levelno >= logging.DEBUG)

    # Add console handler to the LOGGER
    LOGGER.addHandler(console_handler)
    LOGGER.info("Logger Created")


def pascal_case(name: str) -> str:
    # Example input: "select_federal_rows"
    # Example output: "SelectFederalRows"
    return "".join(map(str.title, name.split("_")))
    
if __name__ == "__main__":
    main()