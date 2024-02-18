from watchDawg import sql
from typing import List, Optional, Union


def main():
    print("File for testing pgtyped-pydantic")

    # Test SQL SELECT,   cmon  plzzzz
    result = sql("SELECT * FROM us_federal_ecfr LIMIT 10;", "SelectFederalRows")
    

    # Test SQL INSERT - single row



    print(f"\n\n======== Test Results ========")
    print(f"Type of result: {type(result)}")
    print(f"Lenght of result: {len(result)}")
    print(f"Type of first element in result: {type(result[0])}")
    print(f"Las element in result: {result[-1]}")



if __name__ == "__main__":
    main()
