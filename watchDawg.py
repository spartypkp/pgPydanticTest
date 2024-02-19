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


# Watch for changes in all .py file, until a file that matches the pattern changes
# Regenerate all models using pgtyped-pydantic
    # - This is in leave_call
# For all invocations, change the annotations of the return
    # - This is in leave_assign
# Check the difference between the old model file and new model file
    # - This should be done in leave_module
    # - If there is a difference, then update the _models file, replace the cache,json file key/values for all objects with same file value


# ================================= WATCHDOG ========================================
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

    # Add the filename to the context so we can use it in the transformer
    def __init__(self, filename:str):
        self.filename = filename
        self.filename_without_extension = filename.rsplit(".", 1)[0] if "." in filename else filename
        self.sql_filename = ""
        self.extracted_sql_queries = {}
        # LOGGER.info(f"Initializing SQLTransformer with filename: {filename}")

    def leave_Call(self, node: cst.Call, updated_node: cst.Call):
        if isinstance(node.func, cst.Name) and node.func.value == "sql":
            if len(node.args) < 2:
                raise ValueError("The sql function must have two arguments.")
            
            sql_string = node.args[0].value
            function_name = node.args[1].value.value.lstrip('"').rstrip('"')

            
            LOGGER.debug(f"Type of first_arg: {type(sql_string)}")
            LOGGER.debug(f"Type of second_arg: {type(function_name)}")
            
            if not isinstance(sql_string, cst.SimpleString):
                raise ValueError("Argument to sql must be of type String")
            sql_query = sql_string.value.lstrip('"').rstrip('"')

            hash_id = construct_id(self.filename, sql_query)
            # sql_string_in_ts = f"const {function_name} =sql`\n{sql_query}`;\n\n"
            sql_filename = f"{self.filename_without_extension}_queries.sql"
            self.sql_filename = sql_filename

            sql_string_in_sql = f"/* @name {hash_id} */\n{sql_query}\n\n"
            self.extracted_sql_queries[hash_id] = {
                "sql_string": sql_query,
                "sql_string_in_sql": sql_string_in_sql,
                "function_name": function_name,
            }

        return updated_node

    def leave_Assign(self, original_node: cst.Assign, updated_node: cst.Assign):
        # Check if the value being assigned is a call to `sql`
        if (
            isinstance(updated_node.value, cst.Call)
            and isinstance(updated_node.value.func, cst.Name)
            and updated_node.value.func.value == "sql"
        ):
            original_sql = updated_node.value.args[0].value.value.lstrip('"').rstrip('"')
            hash_id = construct_id(self.filename, original_sql)
            function_name = self.extracted_sql_queries[hash_id]["function_name"]
            
            construction_data = self.extracted_sql_queries[hash_id]
            return_annotation = cst.SubscriptElement(
                            slice=cst.Index(
                                value=cst.Subscript(
                                    value=cst.Name(value="List"),
                                    slice=[
                                        cst.SubscriptElement(
                                            slice=cst.Index(value=cst.Name(value=f"{function_name}Result"))
                                        )
                                    ],
                                )
                            )
                        ),
            
            
            constructed_annotation = cst.Annotation(
                annotation=cst.Subscript(
                    value=cst.Name(value="Callable"),
                    slice=[
                        cst.SubscriptElement(
                            slice=cst.Index(
                                value=cst.Tuple(
                                    elements=[
                                        cst.Element(cst.Annotation(cst.Name("Any"))),
                                    ]
                                )
                            )
                        ),
                        return_annotation
                    ],
                )
            )
                
            
           
            return cst.AnnAssign(
                target=updated_node.targets[0].target,
                annotation=constructed_annotation,
                value=updated_node.value,
                equal=cst.AssignEqual(),
            )

        return updated_node

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:

        # Define cli args
        cfg = 'config.json'
        file_override = self.sql_filename
        
        # Running repository as python subprocess
        command = ['npx', 'pgtyped-pydantic', '-c', cfg, '-f', file_override]
        process = subprocess.run(command, capture_output=True)
                
        # Nuke the temporary test.ts file hack out of existence (Cover my tracks).
        # This could be dangerous if someone is retarded enough to have another file named DISGUSTING_test_HACK.ts
        


        new_imports = []  # List to hold new import nodes

        # Check if the file has already been processed
        for k, v in self.extracted_sql_queries.items():
            function_name = v["function_name"]
            import_from_name = f"{self.filename_without_extension.split('/')[-1]}_models"
            LOGGER.debug(f"Adding import for function: {function_name} from {import_from_name}")

            # Always add the function to the import
            names = [cst.ImportAlias(name=cst.Name(f"{function_name}"))]
            # Check if the Params and Result types are actually needed
            
            names.append(cst.ImportAlias(name=cst.Name(f"{function_name}Params")))  
            names.append(cst.ImportAlias(name=cst.Name(f"{function_name}Result")))
            
            new_import = cst.ImportFrom(
                module=cst.Name(import_from_name),
                names=names,
            )
            
            new_imports.append(new_import)  # Add new import node to the list

        # If nothing was added, return the original node
        if len(new_imports) == 0:
            return original_node


        # Add a newline after the imports
        new_imports.append(cst.EmptyLine())
        
        
        # Create a new Module node with the new imports and the original body
        return cst.Module(header=[], body=new_imports + list(updated_node.body))
       

def apply_codemod_to_file(filename: str):
    with open(filename, "r") as f:
        source_code = f.read()

    # Parse the source code into a CST
    tree = cst.parse_module(source_code)

    print(f"\n\nTree:\n\n{tree}")
    print(type(tree))

    exit(1)

    # Apply the codemod
    transformer = SQLTransformer(filename)
    modified_tree = tree.visit(transformer)

    LOGGER.info(f"\n\n\n{modified_tree.code}")
    # Remove .py extension and add _processed.py to the filename
    new_filename = filename.rsplit(".", 1)[0] + "_processed.py"
    with open(new_filename, "w") as f2:
        f2.write(modified_tree.code)

# ================================= UTILITY FUNCTIONS ========================================

# My personal psycopg functions, which I want to use :)
# For now I'm going to directly execute SQL satements using psycopg3. A more nuanced approach
# May be needed later for advanced queries
def db_connect(row_factory=None):
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        # connect to the PostgreSQL server
        # Get these parameters from config.json file
        with open('config.json') as f:
            db_params = json.load(f)
        f.close()
        dbname = db_params['db']["dbName"]
        host = db_params['db']["host"]
        password = db_params['db']["password"]
        user = db_params['db']["user"]
        conn = psycopg.connect(dbname=dbname,host=host,user=user,password=password,port="5432",client_encoding="utf8")
       
		
        if row_factory is not None:
            conn.row_factory = row_factory
        return conn
    except (Exception, psycopg.DatabaseError) as error:
        print(error)
        raise error



T = TypeVar('T', bound=Callable[..., Any])
def sql(query: str, func: T) -> T:
    # Get the filename of the file that called this function
    filename = sys._getframe(1).f_globals['__file__']
    print(f"Filename: {filename}")
    # Hash the query
    query_hash = hash(query)
    # Get the name
    
    # Check if the function is in cache
    # If it is, return it
    # If it isn't, create it and add it to the cache

    return Callable[..., T]


def sql_executor(query: str, func: T) -> T:
    # Get the return type of func
    return_type_class_name = func.__annotations__['return']
    print(f"Return type class name: {return_type_class_name}")
    print(type(return_type_class_name))
    origin = get_origin(return_type_class_name)
    args = get_args(return_type_class_name)

    # Check if the origin is typing.Optional
    
    arg = args[0]
    print(f"Agrs: {args}")
    pydantic_class = arg
    print(f"Pydantic return model: {pydantic_class}")

    if pydantic_class is None:
        raise ValueError(f"Return type class {return_type_class_name} not found")
    
    conn = db_connect(row_factory=class_row(pydantic_class))
    with conn.cursor() as cursor:
        cursor.execute(query)
        # Try to fetch rows, for SELECT statements
        try:
            rows = cursor.fetchall()
        # Insert, Update, Delete statements don't return rows
        except:
            rows = None
    
    return rows

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



def construct_id(filename, sql):
    return f"{filename}/*/{hash(sql)}"

if __name__ == "__main__":
    main()