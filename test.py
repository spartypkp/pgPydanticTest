from test_models import SelectFederalRowsParams, SelectFederalRowsResult, SelectFederalRows
from watchdog import sql
from typing import List, Optional, Union


def main():
    print("File for testing pgtyped-pydantic")

    result: Union[List[SelectFederalRowsResult], None] = sql("SELECT * FROM us_federal_ecfr LIMIT 10;", SelectFederalRows)   
    
    print(result)


if __name__ == "__main__":
    main()
