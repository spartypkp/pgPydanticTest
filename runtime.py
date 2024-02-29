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
from sql_transformer import ExpansionList, ExpansionScalarList, ExpansionModel, ExpansionModelList


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





def apply_codemod_to_file(filepath: str) -> str:
    with open(filepath, "r") as f:
        source_code = f.read()

    # Parse the source code into a CST
    tree = cst.parse_module(source_code)

    # Apply the codemod
    transformer = SQLTransformer(filepath)
    modified_tree = tree.visit(transformer)
    # LOGGER.info(f"Finished applying codemod to file: {filepath}")
    if source_code == modified_tree.code:
        LOGGER.info(f"No changes made to file: {filepath}")
        return ""
    
    # LOGGER.debug(f"\n\n\n\nModified code:\n{modified_tree.code}")

    # Write the modified code back to the correct file, based on config
    with open("config.json", "r") as f:
        config = json.load(f)
    f.close()
    generate_new_file = config["write_changes_to_new_file"]
    # LOGGER.debug(f"Write modified file to new file: {generate_new_file}")

    filepath_without_extension = transformer.filepath_without_extension
    if generate_new_file:
        target_write_file = f"{filepath_without_extension}_processed.py"
    else:
        target_write_file = f"{filepath_without_extension}.py"

    # LOGGER.debug(f"Writing modified code to: {target_write_file}")
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


import inspect

T = TypeVar('T')
def sql(query: str, expansionList: Optional[ExpansionList] = []) -> T:
    # Get the filename of the file that called this function
    with open("cache.json", "r") as f:
        cache = json.load(f)

    # Get the name of the ClassDef
    class_name = None
    for k, v in cache.items():
        if query == v['sql_string']:
            class_name = k
            break

    if class_name is None:
        raise ValueError(f"No class found for query: {query}")

    # Get the caller's global symbol table
    caller_globals = inspect.stack()[1][0].f_globals

    # Get the class from the caller's global symbol table
    class_def = caller_globals.get(class_name)

    if class_def is None:
        raise ValueError(f"Class {class_name} not found in caller's global symbol table")

    # Initialize and return the class
    return class_def()


# export interface QueryParameters {
#   [paramName: string]:
#     | Scalar
#     | NestedParameters
#     | Scalar[]
#     | NestedParameters[];
# }

def sql_executor(sql_query_with_placeholders:str, parameters_in_pydantic_class: Any, connection: psycopg.Connection):
    # Convert parameters from Pydantic class to dictionary
    if parameters_in_pydantic_class is None:
        parameters = {}
    else:
        parameters = parameters_in_pydantic_class.dict()

    for k,v in parameters.items():
        sql_query_with_placeholders = sql_query_with_placeholders.replace(f":{k}", f"%({k})s")

    if sql_query_with_placeholders[-1] != ";":
        sql_query_with_placeholders += ";"
    print(f"SQL Query: {sql_query_with_placeholders}")
    print(f"Parameters: {parameters}")
    with connection.cursor() as cursor:
        if parameters:
            cursor.execute(sql_query_with_placeholders, parameters)
        else:
            
            cursor.execute(sql_query_with_placeholders)
            print(f"Executed query, no parameters.")
        # Try to fetch rows, for SELECT statements
        try:
            rows = cursor.fetchall()
        # Insert, Update, Delete statements don't return rows
        except:
            rows = []
            connection.commit()
    return rows

def pascal_case(name: str) -> str:
    # Example input: "select_federal_rows"
    # Example output: "SelectFederalRows"
    return "".join(map(str.title, name.split("_")))

# Composable: the base class exposing the common interface
# |__ SQL: a literal snippet of an SQL query
# |__ Identifier: a PostgreSQL identifier or dot-separated sequence of identifiers
# |__ Literal: a value hardcoded into a query
# |__ Placeholder: a %s-style placeholder whose value will be added later e.g. by execute()
# |__ Composed: a sequence of Composable instances.

def sql_query_builder(sql_query: str, parameters: Dict[str, Any], expansions: ExpansionList):
    in_progress_query = sql_query
    replacements = {}
    for expansion in expansions:
        if isinstance(expansion, ExpansionScalarList):
            target_variable = expansion.param_name
            in_progress_query = in_progress_query.replace(f":{target_variable}", f"%({target_variable})s")
            scalar_list_replacement = ', '.join(['%s'] * len(parameters[target_variable]))
            replacements[f"{target_variable}"] = scalar_list_replacement
            in_progress_query = in_progress_query.replace(f":{target_variable}", f"{{{target_variable}}}")
            continue

            
        if isinstance(expansion, ExpansionModel) or isinstance(expansion, ExpansionModelList):
            # What is the name of the pydantic model?
            target_variable = expansion.param_name
            # Field names of the pydantic model
            model_fields = expansion.model_fields

            # Create SQL Identifier for each field
            model_field_replacement = ps_sql.SQL(', ').join(map(ps_sql.Identifier, model_fields))
            # Prepare the query for field replacement
            in_progress_query = in_progress_query.replace(f"{target_variable}.fields", f"{{{target_variable}.fields}}")
            # Add the replacement to the replacements dictionary
            replacements[f"{target_variable}.fields"] = model_field_replacement

            if isinstance(expansion, ExpansionModel):
                model_value_replacement = ', '.join(['%s'] * len(model_fields))
            else:
                model_value_replacement = ', '.join(['(' + ', '.join(['%s'] * len(model_fields)) + ')' for _ in range(len(parameters[target_variable]))])
            in_progress_query = in_progress_query.replace(f"{target_variable}.values", f"{{{target_variable}.values}}")
            replacements[f"{target_variable}.values"] = model_value_replacement
            

            

    model_fields = ["name", "age", "email"]
    q1 = ps_sql.SQL("INSERT INTO my_table ({}) VALUES ({})").format(
    ps_sql.SQL(', ').join(map(ps_sql.Identifier, model_fields)),
    ps_sql.SQL(', ').join(ps_sql.Placeholder() * len(parameters)))
    print(q1.as_string)

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
        print(f"Dbname: {dbname}, Host: {host}, User: {user}, Password: {password}")
		
        if row_factory is not None:
            conn.row_factory = row_factory
        return conn
    except (Exception, psycopg.DatabaseError) as error:
        print(error)
        raise error
    

if __name__ == "__main__":
    main()