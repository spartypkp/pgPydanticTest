from test_models import SelectNodesParams, SelectNodesResult, SelectNodesfrom test_models import SelectNodesAgainParams, SelectNodesAgainResult, SelectNodesAgain
from test_models import SelectNodesParams, SelectNodesResult, SelectNodes




def main():
    print("File for testing pgtyped-pydantic")

    result: SelectNodesResult = sql(
    """SELECT * FROM us_federal_ecfr""", SelectNodes)

    result: SelectNodesAgainResult = sql("""SELECT * FROM us_federal_ecfr""", SelectNodesAgain)
    
    print(result) 


if __name__ == "__main__":
    main()
