from test_models import SelectNodesParams, SelectNodesResult, SelectNodes
result: SelectNodesResult = sql(
 """SELECT * FROM template_node""", SelectNodes)
print(result)
