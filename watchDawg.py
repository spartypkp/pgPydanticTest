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
        self.pydantic_models_to_write = []
        self.extracted_sql_queries = {}
        # LOGGER.info(f"Initializing SQLTransformer with filename: {filename}")

    def leave_Call(self, node: cst.Call, updated_node: cst.Call):
        if isinstance(node.func, cst.Name) and node.func.value == "sql":
            
            
            if len(node.args) < 2:
                raise ValueError("The sql function must have two arguments.")
            
            first_arg = node.args[0].value
            second_arg = node.args[1].value

            # Check if the second argument type is already cst.Name, if so, return
            # Denotes this sql tag has already been processed
            if isinstance(first_arg, cst.SimpleString) and isinstance(second_arg, cst.Name):
                raise SyntaxError("This sql tag has already been processed. Skipping.")


            # Not true, cst.Name is indication of processing having already occured. Well, this
            # was true when you coded this. I changed it because fuck it
            LOGGER.debug(f"Type of first_arg: {type(first_arg)}")
            LOGGER.debug(f"Type of second_arg: {type(second_arg)}")
            if not isinstance(first_arg, cst.SimpleString) or not isinstance(second_arg, cst.SimpleString):
                raise ValueError("Both arguments to sql must be strings.")
                
            

            #print(f"First argument to sql: {first_arg.value}")
            #print(f"Second argument to sql: {second_arg.value}")

            
            
            function_name = second_arg.value.lstrip('"').rstrip('"')  # Remove the double quotes
            sql_query = first_arg.value.lstrip('"').rstrip('"')  # Remove the double quotes

            
            

            # Don't look at this
            ts_filename = f"DISGUSTING_test_HACK.ts"
            # Combine the function name comment and the SQL query
            sql_named_query = f"""import {{ sql }} from '@pgtyped-pydantic/runtime';

// Welcome to the worst hack of all time

const {function_name} =sql`\n{sql_query}`;\n\n"""

            # Don't look at this hack either
            with open(ts_filename, "w") as f:
                f.write(sql_named_query)
            #print(f"Writing SQL to {ts_filename}")
            f.close()

            # Define cli args
            cfg = 'config.json'
            file_override = ts_filename
            
            # Running repository as python subprocess
            command = ['npx', 'pgtyped-pydantic', '-c', cfg, '-f', file_override]
            process = subprocess.run(command, capture_output=True)
            
            # Print out the stdout and stderr
            #print(f"stdout: {process.stdout.decode('utf-8')}")
            #print(f"stderr: {process.stderr.decode('utf-8')}")
            # result.stderr contains the stderr output
            generated_file = process.stdout.decode('utf-8').replace("\"DISGUSTING_test_HACK.ts\"", self.filename)
            
            # Nuke the temporary test.ts file hack out of existence (Cover my tracks).
            # This could be dangerous if someone is retarded enough to have another file named DISGUSTING_test_HACK.ts
            subprocess.run(['rm', ts_filename])

            function_name = function_name[0].upper() + function_name[1:]
            


            test_string = " = None"
    
            ## Parse the return type
            result_type = f"{function_name}Result"
            result_type_index = generated_file.find(result_type)
            LOGGER.debug(f"result_type_index: {result_type_index}")

            # If test_string occurs right after result_type_index. throw an error
            
            result_string = f" -> List[{result_type}]"

            
            if generated_file[result_type_index + len(result_type):result_type_index + len(result_type) + len(test_string)] == test_string:
                LOGGER.debug(f"Result type: {result_type} evaluates to None! ")
                result_string = " -> None"
            
            result_type = result_string.split(" -> ")[1].strip()


            ## Parse the parameter type
            # Find the index of params_type in the generated_file
            params_type = f"{function_name}Params"
            params_type_index = generated_file.find(params_type)
            LOGGER.debug(f"params_type_index: {params_type_index}")
            
            # If test_string occurs right after result_type_index. throw an error
            params_string = f"params: {function_name}Params"
            

            LOGGER.debug(f"Text following index: {generated_file[params_type_index + len(params_type):params_type_index + len(params_type) + len(test_string)]}")
            if generated_file[params_type_index + len(params_type):params_type_index + len(params_type) + len(test_string)] == test_string:
                LOGGER.debug(f"Parameter type: f{function_name}Params evaluates to None! ")
                params_string = ""

            if len(params_string) > 0:
                params_type = params_string.split(":")[1].strip()

            LOGGER.debug(f"Adding function call: {function_name} with parameter type: {params_type}, result type: {result_type}")

            ## Add the function name, params type, and result types to the dictionary, SQL string is key
            self.extracted_sql_queries[sql_query] = {
                "function_name": function_name,
                "params_type": params_type,
                "result_type": result_type,
                "sql_query": sql_query
            }

            ## Construct the function call
            import_statment = ""
            function_call = f"""\n{import_statment}
def {function_name}({params_string}){result_string}:
    return True # Will figure this out later\n\n
"""
            generated_file = generated_file +  function_call
            # Track this bad boy for later
            self.pydantic_models_to_write.append(generated_file)
        
            new_args = list(node.args)

            # I'm not going to add this processed tag, since the type of the second argument is already cst.Name
            # new_args[0] = cst.Arg(value=cst.SimpleString(f'"processed!"'))

            if len(node.args) >= 2:
                print("Replacing second argument")
                new_args[1] = cst.Arg(value=cst.Name(function_name))
                return node.with_changes(args=tuple(new_args))
            else:
                print("Adding second argument")
                new_args.append(cst.Arg(value=cst.Name(function_name)))
                return node.with_changes(args=tuple(new_args))

        return updated_node

    # I am considering completely remove this. Return type can be fully inferenced from the function return type.
    # By not hardcoding the return type, I can allow for more flexibility in the set of possibly returned types:
    # ex: we dont know if the user is SELECTing 1 or many rows, List[Type] or Type
    # ex2: Maybe it makes sense to make the return type Optional, if the user is doing an INSERT or UPDATE
    def leave_Assign(self, original_node: cst.Assign, updated_node: cst.Assign):
        # Check if the value being assigned is a call to `sql`
        if (
            isinstance(updated_node.value, cst.Call)
            and isinstance(updated_node.value.func, cst.Name)
            and updated_node.value.func.value == "sql"
        ):
            original_sql = updated_node.value.args[0].value.value.lstrip('"').rstrip('"')
            second_arg = updated_node.value.args[1].value.value
            
            construction_data = self.extracted_sql_queries[original_sql]
            if construction_data["result_type"] == "None":
                constructed_annotation = cst.Annotation(
                    annotation=cst.Subscript(
                        value=cst.Name(value="None"),
                    )
                )
            else:
            
                constructed_annotation = cst.Annotation(
                    annotation=cst.Subscript(
                        value=cst.Name(value="List"),
                        slice=[
                            cst.SubscriptElement(
                                slice=cst.Index(value=cst.Name(value=f"{second_arg}Result"))
                            )
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
        new_imports = []  # List to hold new import nodes

        # Check if the file has already been processed
        for k,v in self.extracted_sql_queries.items():
            function_name = v["function_name"]
            import_from_name = f"{self.filename_without_extension.split('/')[-1]}_models"
            LOGGER.debug(f"Adding import for function: {function_name} from {import_from_name}")

            # Always add the function to the import
            names = [cst.ImportAlias(name=cst.Name(f"{function_name}"))]
            # Check if the Params and Result types are actually needed
            if v["params_type"] != "":
                names.append(cst.ImportAlias(name=cst.Name(f"{function_name}Params")))
            if v["result_type"] != "None":
                names.append(cst.ImportAlias(name=cst.Name(f"{function_name}Result")))
            
            new_import = cst.ImportFrom(
                module=cst.Name(import_from_name),
                names=names,
            )
            
            new_imports.append(new_import)  # Add new import node to the list

        # If nothing was added, return the original node
        if len(new_imports) == 0:
            return original_node
        

        with open(f'{self.filename_without_extension}_models.py', 'w') as f:
            f.write("\n".join(self.pydantic_models_to_write))


        # Add a newline after the imports
        new_imports.append(cst.EmptyLine())
        
        
        # Create a new Module node with the new imports and the original body
        return cst.Module(header=[], body=new_imports + list(updated_node.body))
       

def apply_codemod_to_file(filename: str):
    with open(filename, "r") as f:
        source_code = f.read()

    # Parse the source code into a CST
    tree = cst.parse_module(source_code)

    # Apply the codemod
    transformer = SQLTransformer(filename)
    modified_tree = tree.visit(transformer)


    #print(f"\n\n\n\nModified code:\n{modified_tree.code}")


    # Replace the original file with the modified code
    with open(filename, "w") as f:
        f.write(modified_tree.code)



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

def pydantic_insert(table_name: str, nodes: List[Any], include = None, user: Optional[str] = None):
    # Get the psycopg3 connection object
    conn = db_connect(user)

    with conn.cursor() as cursor:
        for node in nodes:
            # Convert the NodeModel to a dictionary and exclude default values
            if include:
                node_dict = node.model_dump(mode="json",exclude_defaults=True, include=include)
            else:
                node_dict = node.model_dump(mode="json",exclude_defaults=True)

            for key, value in node_dict.items():
                if type(value) == dict:
                    node_dict[key] = Jsonb(node_dict[key])
            

            # Prepare the column names and placeholders
            columns = ', '.join(node_dict.keys())
            placeholders = ', '.join(['%s'] * len(node_dict))

            # Create the INSERT statement using psycopg.sql to safely handle identifiers
            query = psycopg.sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                psycopg.sql.Identifier(table_name),
                psycopg.sql.SQL(columns),
                psycopg.sql.SQL(placeholders)
            )

            # Execute the INSERT statement
            cursor.execute(query, tuple(node_dict.values()))

    # Commit the changes
    conn.commit()
    conn.close()


def pydantic_select(sql_select: str, classType: Optional[Any], user: Optional[str] = None ) -> List[Any]:
    # If they provide a pydantic model, use it for the row factory
    if classType:
        conn = db_connect(user, row_factory=class_row(classType))
    # Otherwise, return the dictionary row factory
    else:
        conn = db_connect(user, row_factory=dict_row)

    cur = conn.cursor()

    # Execute the SELECT statement
    cur.execute(sql_select)

    # Fetch all rows
    rows = cur.fetchall()
    

    # Close the cursor and the connection
    cur.close()
    conn.close()

    return rows


def pydantic_update(table_name: str, nodes: List[Any], where_field: str, include = None, user: Optional[str] = None):
    conn = db_connect(user)
    
    with conn.cursor() as cursor:
        for node in nodes:
            # Convert the NodeModel to a dictionary and exclude where field, include values to update only
            
            if include:
                node_dict = node.model_dump(mode="json",exclude_defaults=True, exclude=[where_field], include=include)
            else:
                node_dict = node.model_dump(mode="json",exclude_defaults=True, exclude=[where_field])

            

            for key, value in node_dict.items():
                if type(value) == dict:
                    node_dict[key] = Jsonb(node_dict[key])
            

            # Prepare the column names and placeholders
            columns = ', '.join(node_dict.keys())
            placeholders = ', '.join(['%s'] * len(node_dict))
            where_value = node_dict[where_field]

            query = psycopg.sql.SQL("UPDATE {} SET ({}) = ({}) WHERE {} = {}").format(
                psycopg.sql.Identifier(table_name),
                psycopg.sql.SQL(columns),
                psycopg.sql.SQL(placeholders),
                psycopg.sql.Identifier(where_field),
                where_value
            )

            # Execute the INSERT statement
            cursor.execute(query, tuple(node_dict.values()))



T = TypeVar('T', bound=Callable[..., Any])
def sql(query: str, func: T) -> T:
    # Get the return type of func
    return_type_class_name = func.__annotations__['return']
    print(f"Return type class name: {return_type_class_name}")
    origin = get_origin(return_type_class_name)
    args = get_args(return_type_class_name)

    # Check if the origin is typing.Optional
    
    arg = args[0]
    pydantic_class = get_args(arg)[0]
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



if __name__ == "__main__":
    main()