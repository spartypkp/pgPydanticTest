from watchdog import sql

def main():
    print("File for testing pgtyped-pydantic")

    result = sql("SELECT * FROM us_federal_ecfr;", "selectRows") # Testing...
    
    print(result) 


if __name__ == "__main__":
    main()
