import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from typing_extensions import NewType

class selectFederalRows:
    """ 
	Class to hold all pydantic models for a single SQL query.
	Defined by SQL invocation in test.py.
	Original SQL: "SELECT * FROM us_federal_ecfr WHERE node_type = 'content' AND status is NULL LIMIT 5"
	Used in files: []
	"""

    """ 'SelectFederalRows' parameters type """
    SelectFederalRowsParams = NewType('SelectFederalRowsParams', None)

    """ 'SelectFederalRows' return type """
    class SelectFederalRowsResult (BaseModel):
        addendum: Optional[List[str]]
        addendum_metadata: Optional[Dict[str, Any]]
        addendum_references: Optional[Dict[str, Any]]
        agency: Optional[str]
        alias: Optional[str]
        authority: Optional[str]
        citation: str
        core_metadata: Optional[Dict[str, Any]]
        core_references: Optional[Dict[str, Any]]
        date_created: Optional[datetime.datetime]
        date_modified: Optional[datetime.datetime]
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




    def run(self, params: SelectFederalRowsParams) -> List[SelectFederalRowsResult]:
        """ 
		Method to run the sql query.
		"""
        return []


class selectBadRows:
    """ 
	Class to hold all pydantic models for a single SQL query.
	Defined by SQL invocation in test.py.
	Original SQL: "SELECT * FROM us_federal_ecfr WHERE node_type = 'content' AND status is not NULL LIMIT 5"
	Used in files: []
	"""

    """ 'SelectBadRows' parameters type """
    SelectBadRowsParams = NewType('SelectBadRowsParams', None)

    """ 'SelectBadRows' return type """
    class SelectBadRowsResult (BaseModel):
        addendum: Optional[List[str]]
        addendum_metadata: Optional[Dict[str, Any]]
        addendum_references: Optional[Dict[str, Any]]
        agency: Optional[str]
        alias: Optional[str]
        authority: Optional[str]
        citation: str
        core_metadata: Optional[Dict[str, Any]]
        core_references: Optional[Dict[str, Any]]
        date_created: Optional[datetime.datetime]
        date_modified: Optional[datetime.datetime]
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




    def run(self, params: SelectBadRowsParams) -> List[SelectBadRowsResult]:
        """ 
		Method to run the sql query.
		"""
        return []



