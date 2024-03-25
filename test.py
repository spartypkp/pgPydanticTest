from test_models import SqlInsertAccount

from test_models import SqlInsertAccount

from test_models import SqlInsertAccount

from pydantic import BaseModel
from runtime import sql, db_connect
from sql_transformer import col
from typing import List, Annotated
import libcst as cst
from model_library import Account


# Look up snapshot testing, pyTest Snapshot

def main():
    
    ### Automatic Parameter Expansions
    # This is a demonstration of the automatic parameter expansions that the SQL transformer will perform.
    # These expansions are based on the SQL comment syntax that the original pgtyped library uses for SQL files.
    # Named parameters are required only for primitive types, pydantic models use the name of the model as the parameter name.

    # CREATE TABLE account_table (
    #     name TEXT,
    #     age INTEGER,
    #     email TEXT
    # );


    ## Array spread
    # SQL comment syntax: @param paramName -> (...)    
    # ages = [24, 25, 26]
    # sql_insert_basic = sql(f"SELECT * FROM account_table WHERE age in ages{[int]}")
    # print(sql_insert_basic)      
    
    ## Object pick
    # SQL comment syntax: @param paramName -> (name, age, email) dsflssd
    
    sql_insert_account: SqlInsertAccount = sql(f"INSERT INTO account_table (name, age, email) VALUES {[Account]};")
    print(sql_insert_account) 
    

    ## Array spread and pick   
    # SQL comment syntax: @param paramName -> ((name, age, email)...)
    # sql_insert_accounts: SqlInsertAccounts = sql(f"INSERT INTO account_table (name, age, email) VALUES {Account};")

    
    # print(sql_insert_accounts)
    exit(1)
    
    ## Save, then actually Run this file before uncommenting the rest of the code below. Follow on queries need this stupid table.
    # create_test_table: CreateTestTable = sql("CREATE TABLE IF NOT EXISTS stupid_test_table (name TEXT, age INTEGER, email TEXT);")
    # create_test_table.run(create_test_table.params(), db_connect())

    
    ##  Testing dynamic model insertion - single Pydantic model
    # Let's say I want to insert a single account into the database.
    # I could hardcode the values, but I want to insert a Pydantic model dynamically instead.

   

# def test_psycopg_query_builder():
#     new_account_list = [Account(name="Will3", age=26, email="hired@letsgo.com"), Account(name="Sean3", age=42, email="just@kidding.com")]
#     composed_query = sql_query_builder("INSERT INTO stupid_test_table (account.fields) VALUES list(account);", new_account_list, ExpansionModelList(param_name="account", pydantic_type=Account, source_file="model_library.py"))


    
    

    



if __name__ == "__main__":
    main()
