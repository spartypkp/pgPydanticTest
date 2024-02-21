import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from typing_extensions import NewType

class selectFederalRows:
	""" 
	BLAH BLA
	"""

	""" 'SelectFederalRows' parameters type """
	SelectFederalRowsParams = NewType('SelectFederalRowsParams', None)

	""" 'SelectFederalRows' return type """
	class SelectFederalRowsResult (BaseModel):
		BAD: Optional[List[str]]




	def run(self, params: SelectFederalRowsParams) -> List[SelectFederalRowsResult]:
		""" 
		Method to run the sql query.
		"""
		return []

