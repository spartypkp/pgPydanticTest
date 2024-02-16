from test_models import SelectRowsParams, SelectRowsResult, SelectRows
from watchdog import sql

def main():
    print("File for testing pgtyped-pydantic")

    result: SelectRowsResult = sql("SELECT * FROM us_federal_ecfr;", SelectRows) # This should work. d
    
    print(result) 


if __name__ == "__main__":
    main()
