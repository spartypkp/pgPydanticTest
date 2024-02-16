from test_models import SelectRowsParams, SelectRowsResult, SelectRows
from test_models import SelectRowsParams, SelectRowsResult, SelectRows
from watchdog import sql
from typing import List, Optional, Union


def main():
    print("File for testing pgtyped-pydantic")

    result: Union[List[SelectRowsResult], None] = sql("SELECT * FROM us_federal_ecfr LIMIT 1;", SelectRows) # Testing
    
    print(result) 


if __name__ == "__main__":
    main()
