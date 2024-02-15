# Pydantic models generated for queries found in test.py
from pydantic import BaseModel, Field
from typing import Optional, List

from typing_extensions import NewType

""" 'SelectNodes' parameters type """
SelectNodesParams = NewType('SelectNodesParams', None)

""" 'SelectNodes' return type """
class SelectNodesResult (BaseModel):
  node_addendum: Optional[str]
  node_citation: Optional[str]
  node_direct_children: Optional[List[str]]
  node_hyde: Optional[List[str]]
  node_hyde_embedding: Optional[str]
  node_id: str
  node_incoming_references: Optional[Dict[str, Any]]
  node_level_classifier: Optional[str]
  node_link: Optional[str]
  node_name: Optional[str]
  node_name_embedding: Optional[str]
  node_order: float
  node_parent: Optional[str]
  node_references: Optional[Dict[str, Any]]
  node_siblings: Optional[List[str]]
  node_summary: Optional[str]
  node_summary_embedding: Optional[str]
  node_tags: Optional[Dict[str, Any]]
  node_text: Optional[List[str]]
  node_text_embedding: Optional[str]
  node_top_level_title: Optional[str]
  node_type: Optional[str]


""" 'SelectNodes' query type """
class SelectNodesQuery (BaseModel):
  params: SelectNodesParams
  result: SelectNodesResult




from apply_codemod import pydantic_insert, pydantic_select, pydantic_update
def SelectNodes(params: SelectNodesParams) -> SelectNodesResult:
    return True # Will figure this out later


