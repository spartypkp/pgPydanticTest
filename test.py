



from test_models import InsertSmartPerson

from test_models import InsertStupidPerson

from test_models import SelectFederalRows, StupidTestTable

from watchDawg import db_connect
from sql_transformer import sql
from typing import List
import libcst as cst

# Watch for changes in all .py file
# Regenerate all models using pgtyped-pydantic
    # - This is in leave_call
# For all invocations, change the annotations of the return
    # - This is in leave_assign
# Check the difference between the old model file and new model file
    # - This should be done in leave_module
    # - If there is a difference, then update the _models file, replace the cache,json file key/values for all objects with same file value

    



def main():
    print("File for testing pgtyped-pydantic")
    print()
    # Test SQL SELECT, modify below comment for quick testing.  
    # select_result = sql("SELECT * FROM us_federal_ecfr WHERE node_type = 'content' AND status is NULL LIMIT 5;", "SelectFederalRows") try againnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn
    select_federal_rows: SelectFederalRows = sql("SELECT * FROM us_federal_ecfr WHERE node_type = :node_type AND status is NULL LIMIT :lim;")
    params = select_federal_rows.params(lim="5", node_type="content")
    conn = db_connect()
    select_result = select_federal_rows.run(params, conn)
   
    
    print(f"\n\n======== Test SQL Select ========")
    print(f"Type of result: {type(select_result)}")
    print(f"Length of result: {len(select_result)}")
    print(f"Type of first element in result: {type(select_result[0])}")
    print(f"Last element in result: {select_result[-1]}")

    # Test SQL Create Table, currently broekn
    stupid_test_table: StupidTestTable = sql("""
    CREATE TABLE stupid_test_table (
        id SERIAL PRIMARY KEY,
        name TEXT,
        age INTEGER,
        email TEXT
    );""")

    create_result = stupid_test_table.run(stupid_test_table.params(), conn)
    print(f"\n\n======== Test SQL Create Table ========")
    print(f"Type of result: {type(create_result)}")
    print(f"Length of result: {len(create_result)}")

    insert_stupid_person: InsertStupidPerson = sql("""INSERT INTO stupid_test_table (name, age, email) VALUES ('me', '24', 'broke@pleasehireme.com');""")
    insert_smart_person: InsertSmartPerson = sql("INSERT INTO stupid_test_table (name, age, email) VALUES (:name, :age, :email);")
    insert_genius_person: InsertSmartPerson = sql("INSERT INTO stupid_test_table 0:(name, age, email) VALUES 0:account;")
    




    

    # Test SQL INSERT - single row.
    # insert_result = sql("INSERT INTO stupid_test_table (idk how to do this);", "InsertStupidTestTable")
    



if __name__ == "__main__":
    main()
