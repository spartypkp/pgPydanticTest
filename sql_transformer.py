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

    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            # If the file modified is this file, don't do anything
            if "watchDawg" in event.src_path:
                return
            # Temporary
            if "_" in event.src_path:
                return
            
            self.queue.put(event)

def worker(queue):
    while True:
        event = queue.get()
        if event is None:  # None is sent as a signal to stop the worker
            break
        assert(LOGGER is not None)
        # Your callback function goes here
        print(f"Detected change in: {event.src_path}")

        # Call apply_codemod.py with the detected filename
        try:
            apply_codemod_to_file(event.src_path)
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
            assign_name = assign_name[0].upper() + assign_name[1:]
            # Create a new AnnAssign node with the modified annotation
            new_annotation = cst.Annotation(
                    annotation=cst.Subscript(     
                        value=cst.Name(value="List"),
                        slice=[
                            cst.SubscriptElement(
                                slice=cst.Index(value=cst.Name(value=assign_name))
                            )
                        ],        
                    )
                )
            return cst.AnnAssign(
                target=updated_node.targets[0].target,
                annotation=new_annotation,
                value=updated_node.value,
                equal=cst.AssignEqual(),
            )
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
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)')
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


if __name__ == "__main__":
    main()