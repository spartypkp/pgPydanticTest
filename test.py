from watchDawg import sql
from typing import List


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
    # select_result = sql("SELECT * FROM us_federal_ecfr WHERE node_type = 'content' AND status is NULL LIMIT 5;", "SelectFederalRows") try againnnnnnnnnnnnnnnnnnnn
    select_federal_rows = sql("SELECT * FROM us_federal_ecfr WHERE node_type = 'content_type' AND status is NULL LIMIT 5;")
    result = select_federal_rows.run()

    
    # print(f"\n\n======== Test SQL Select ========")
    # print(f"Type of result: {type(select_result)}")
    # print(f"Lenght of result: {len(select_result)}")
    # print(f"Type of first element in result: {type(select_result[0])}")
    # print(f"Last element in result: {select_result[-1]}")


    # Test Regular SQL commands
    # sql("CREATE TABLE stupid_test_table ( )")

    # Test SQL INSERT - single row
    # insert_result = sql("INSERT INTO stupid_test_table (idk how to do this);", "InsertStupidTestTable")
    



if __name__ == "__main__":
    main()
