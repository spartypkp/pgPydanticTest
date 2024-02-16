# Pydantic models generated for queries found in /Users/s/VSCodeProjects/pgPydanticTest/test.py
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict

from typing_extensions import NewType

""" 'SelectNodes' parameters type """
SelectNodesParams = NewType('SelectNodesParams', None)

""" 'SelectNodes' return type """
class SelectNodesResult (BaseModel):
  addendum: Optional[List[str]]
  addendum_metadata: Optional[Dict[str, Any]]
  addendum_references: Optional[Dict[str, Any]]
  agency: Optional[str]
  alias: Optional[str]
  authority: Optional[str]
  citation: str
  core_metadata: Optional[Dict[str, Any]]
  core_references: Optional[Dict[str, Any]]
  date_created: Optional[datetime]
  date_modified: Optional[datetime]
  dates: Optional[Dict[str, Any]]
  definitions: Optional[Dict[str, Any]]
  direct_children: Optional[List[str]]
  history: Optional[str]
  hyde: Optional[List[str]]
  hyde_embedding: Optional[str]
  id: str
  incoming_references: Optional[Dict[str, Any]]
  level_classifier: str
  lineage: Optional[List[str]]
  lineage_embedding: Optional[str]
  link: Optional[str]
  node_name: Optional[str]
  node_text: Optional[List[str]]
  node_type: str
  number: Optional[str]
  parent: Optional[str]
  processing: Optional[Dict[str, Any]]
  siblings: Optional[List[str]]
  source: Optional[str]
  status: Optional[str]
  summary: Optional[str]
  summary_embedding: Optional[str]
  text_embedding: Optional[str]
  top_level_title: Optional[str]
  topics: Optional[Dict[str, Any]]


""" 'SelectNodes' query type """
class SelectNodesQuery (BaseModel):
  params: SelectNodesParams
  result: SelectNodesResult




from apply_codemod import pydantic_insert, pydantic_select, pydantic_update
def SelectNodes(params: SelectNodesParams) -> SelectNodesResult:
    return True # Will figure this out later



# Pydantic models generated for queries found in /Users/s/VSCodeProjects/pgPydanticTest/test.py
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict

from typing_extensions import NewType

""" 'SelectNodesAgain' parameters type """
SelectNodesAgainParams = NewType('SelectNodesAgainParams', None)

""" 'SelectNodesAgain' return type """
class SelectNodesAgainResult (BaseModel):
  addendum: Optional[List[str]]
  addendum_metadata: Optional[Dict[str, Any]]
  addendum_references: Optional[Dict[str, Any]]
  agency: Optional[str]
  alias: Optional[str]
  authority: Optional[str]
  citation: str
  core_metadata: Optional[Dict[str, Any]]
  core_references: Optional[Dict[str, Any]]
  date_created: Optional[datetime]
  date_modified: Optional[datetime]
  dates: Optional[Dict[str, Any]]
  definitions: Optional[Dict[str, Any]]
  direct_children: Optional[List[str]]
  history: Optional[str]
  hyde: Optional[List[str]]
  hyde_embedding: Optional[str]
  id: str
  incoming_references: Optional[Dict[str, Any]]
  level_classifier: str
  lineage: Optional[List[str]]
  lineage_embedding: Optional[str]
  link: Optional[str]
  node_name: Optional[str]
  node_text: Optional[List[str]]
  node_type: str
  number: Optional[str]
  parent: Optional[str]
  processing: Optional[Dict[str, Any]]
  siblings: Optional[List[str]]
  source: Optional[str]
  status: Optional[str]
  summary: Optional[str]
  summary_embedding: Optional[str]
  text_embedding: Optional[str]
  top_level_title: Optional[str]
  topics: Optional[Dict[str, Any]]


""" 'SelectNodesAgain' query type """
class SelectNodesAgainQuery (BaseModel):
  params: SelectNodesAgainParams
  result: SelectNodesAgainResult




from apply_codemod import pydantic_insert, pydantic_select, pydantic_update
def SelectNodesAgain(params: SelectNodesAgainParams) -> SelectNodesAgainResult:
    return True # Will figure this out later


