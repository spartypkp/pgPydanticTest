

from watchDawg import db_connect
from sql_transformer import sql, ExpansionList, ExpansionScalarList, ExpansionObject, ExpansionObjectList
from typing import List
import libcst as cst

# Look up snapshot testing, pyTest Snapshot

def main():
    print("File for testing pgtyped-pydantic")
    print()
    # Test SQL SELECT, modify below comment for quick testing.  try
    # select_result = sql("SELECT * FROM us_federal_ecfr WHERE node_type = 'content' AND status is NULL LIMIT 5;", "SelectFederalRows") try againnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn
    # select_federal_rows = sql("SELECT * FROM us_federal_ecfr WHERE node_type = :node_type AND status is NULL LIMIT :lim;")
    # params = select_federal_rows.params(lim="5", node_type="content")
    # conn = db_connect()
    # select_result = select_federal_rows.run(params, conn)
   
    
    # print(f"\n\n======== Test SQL Select ========")
    # print(f"Type of result: {type(select_result)}")
    # print(f"Length of result: {len(select_result)}")
    # print(f"Type of first element in result: {type(select_result[0])}")
    # print(f"Last element in result: {select_result[-1]}")

    # # Test SQL Create Table, currently broekn
    # stupid_test_table = sql("""
    # CREATE TABLE stupid_test_table (
    #     id SERIAL PRIMARY KEY,
    #     name TEXT,
    #     age INTEGER,
    #     email TEXT
    # );""")

    # create_result = stupid_test_table.run(stupid_test_table.params(), conn)
    # print(f"\n\n======== Test SQL Create Table ========")
    # print(f"Type of result: {type(create_result)}")
    # print(f"Length of result: {len(create_result)}") #

    # Regular insertion,3
    # insert_stupid_person: InsertStupidPerson = sql("""INSERT INTO stupid_test_table (name, age, email) VALUES ('me', '24', 'broke@pleasehireme.com');""")
    # # Dynamic insertion
    # insert_normal_person: InsertNormalPerson = sql("INSERT INTO stupid_test_table (name, age, email) VALUES (:name, :age, :email);")
    # Dyanmic object insertion - single object    
    insert_smart_person = sql("INSERT INTO stupid_test_table (name, age, email) VALUES :account;",
                              ExpansionList(expansions=[
                                ExpansionObject(param_name="account", object_vars=["name", "age", "email"])
                              ]) 
                            )  


    # # Dyanmic object insertion - list of objects.
    # insert_genius_person = sql("INSERT INTO stupid_test_table (name, age, email) VALUES :accounts;",
    #                           ExpansionList(expansions=[
    #                             ExpansionObjectList(param_name="accounts", object_vars=["name", "age", "email"])
    #                           ])
                                        
    #                         )

    # # Passing an array of scalars 
    # select_smart_and_genius = sql("SELECT * FROM stupid_test_table WHERE name in :names;",
    #                                 ExpansionList(expansions=[
    #                                     ExpansionScalarList(param_name="names")
    #                                 ])
    #                             )




    

    # Test SQL INSERT - single row.
    # insert_result = sql("INSERT INTO stupid_test_table (idk how to do this);", "InsertStupidTestTable")
    



if __name__ == "__main__":
    main()
