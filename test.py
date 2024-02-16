from test_models import SelectNodesParams, SelectNodesResult, SelectNodes
from test_models import SelectNodesParams, SelectNodesResult, SelectNodes
from test_models import SelectNodesParams, SelectNodesResult, SelectNodes
from test_models import SelectNodesParams, SelectNodesResult, SelectNodes
from test_models import SelectNodesParams, SelectNodesResult, SelectNodes
from test_models import SelectNodesParams, SelectNodesResult, SelectNodes
from test_models import SelectNodesParams, SelectNodesResult, SelectNodes
from test_models import SelectNodesParams, SelectNodesResult, SelectNodes
result: SelectNodesResult = sql(
 """SELECT * FROM us_federal_ecfr""", SelectNodes)
print(result)
