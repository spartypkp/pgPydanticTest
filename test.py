
from pydantic import BaseModel
from sql_transformer import sql, ExpansionList, ExpansionScalarList, ExpansionModel, ExpansionModelList, db_connect
from typing import List
import libcst as cst
from model_library import Account

# Look up snapshot testing, pyTest Snapshot

def main():

    # Add a stupid comment below and hit save to begin.
    # 
    
    ## Testing simple SQL statements. Ensure your db is hooked up in the config.json file correctly first.
    create_test_table = sql("CREATE TABLE IF NOT EXISTS stupid_test_table (name TEXT, age INTEGER, email TEXT);")
    # Will make params optional in run later. Not ideal for now.
    create_test_table.run(create_test_table.params(), db_connect())



    
    ##  Testing dynamic model insertion - single Pydantic model
    # Let's say I want to insert a single account into the database.
    # I could hardcode the values, but I want to insert a Pydantic model dynamically instead.


    ## WARNING: Your pydantic model MUST be named the corresponding SQL variable. :account -> Account
    insert_single_account = sql("INSERT INTO stupid_test_table (name, age, email) VALUES :account;",
                              ExpansionList(expansions=[
                                ExpansionModel(param_name="account", pydantic_type=Account, source_file="model_library.py")
                              ]) 
                            )
    
    ## Result doesn't matter with insertion, should return an empty List
    # Option 1: Create the paramters beforehand
    single_account = insert_single_account.params(Account(name="Will", age=24, email="hire@me.com"))
    insert_single_account.run(single_account, db_connect())
    # Option 2: Create the parameters on the fly
    insert_single_account.run(Account(name="Sean", age=40, email="cool@dude.com"), db_connect())
    # I'm a fan of Option 1, i think it's cleaner and more readable. But Option 2 is there if you need it.


    ## Testing dynamic model insertion - list of Pydantic models
    # That worked well, but what if I want to insert multiple accounts at once?
    # And, I don't know how many accounts I want to insert or what their values are until runtime.
    # A very common problem, except I want to dynamically use Pydantic models instead of traditional SQL parameters.

    ## WARNING: Your pydantic model MUST be named the corresponding SQL variable. :account -> Account. Passing :accounts here will break the query (trust me)
    insert_multiple_accounts = sql("INSERT INTO stupid_test_table (name, age, email) VALUES :account;",
                                ExpansionList(expansions=[
                                    ExpansionModelList(param_name="account", pydantic_type=Account, source_file="model_library.py")
                                ])
                            )
    ## Result doesn't matter with insertion, should return an empty List
    # Option 1: Create the paramters beforehand
    account_list = [Account(name="Will2", age=25, email="plzhire@me.com"), Account(name="Sean2", age=41, email="light@weight.com")]
    multiple_accounts = insert_multiple_accounts.params(account_list)
    result = insert_multiple_accounts.run(multiple_accounts, db_connect())
    # Option 2: Create the parameters on the fly
    new_account_list = [Account(name="Will3", age=26, email="hired@letsgo.com"), Account(name="Sean3", age=42, email="just@kidding.com")]
    result = insert_multiple_accounts.run(new_account_list, db_connect())



    ## Result does matter with SELECT, should return a list of Pydantic models
    select_all_accounts = sql("SELECT * FROM stupid_test_table;")
    # Use psycopg row factory to return a list of Pydantic models
    new_connection = db_connect(
        row_factory=select_all_accounts.resultType
    )
    select_params = select_all_accounts.params()
    # TODO: Make select_params optional in run if it's not needed
    result = select_all_accounts.run(select_params, new_connection)
    print(result)
    
    

    



if __name__ == "__main__":
    main()
