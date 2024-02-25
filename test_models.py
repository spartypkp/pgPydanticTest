from typing import List, Optional, Dict, Any, Union
import datetime
from pydantic import BaseModel
from typing_extensions import NewType
from psycopg.rows import class_row
import psycopg
from sql_transformer import sql_executor


class SelectFederalRows:
	""" 
	Class to hold all pydantic models for a single SQL query.
	Defined by SQL invocation in test.py.
	Used in files: []
	"""

	def __init__(self):
		self.sql_string = """SELECT * FROM us_federal_ecfr WHERE node_type = :node_type AND status is NULL LIMIT :lim"""

	""" 'SelectFederalRows' parameters type """
	class SelectFederalRowsParams(BaseModel):
		lim: Optional[Union[float, str]]
		node_type: Optional[str]


	""" 'SelectFederalRows' return type """
	class SelectFederalRowsResult(BaseModel):
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


	def params(self, node_type: Optional[str], lim: Optional[Union[float, str]]) -> SelectFederalRowsParams:
		"""
	Method to set the parameters of the SQL invocation.
		"""
		return self.SelectFederalRowsParams(node_type = node_type, lim = lim)



	def run(self, params: SelectFederalRowsParams, connection: psycopg.Connection) -> List[SelectFederalRowsResult]:
		""" 
		Method to run the sql query.
		"""
		connection.row_factory = class_row(self.SelectFederalRowsResult)
		rows: List[self.SelectFederalRowsResult] = sql_executor(sql_query_with_placeholders=self.sql_string, parameters_in_pydantic_class=params, connection=connection)
		return rows
	



class StupidTestTable:
	""" 
	Class to hold all pydantic models for a single SQL query.
	Defined by SQL invocation in test.py.
	Used in files: []
	"""

	def __init__(self):
		self.sql_string = """CREATE TABLE stupid_test_table (
		id SERIAL PRIMARY KEY,
		name TEXT,
		age INTEGER,
		email TEXT
	)"""

	""" 'StupidTestTable' parameters type """
	class StupidTestTableParams(BaseModel):
		pass # Looking for better ways to handle None, hmu



	""" 'StupidTestTable' return type """
	class StupidTestTableResult(BaseModel):
		pass # Looking for better ways to handle None, hmu



	def params(self) -> StupidTestTableParams:
		"""
	Method to set the parameters of the SQL invocation.
		"""
		return self.StupidTestTableParams()



	def run(self, params: StupidTestTableParams, connection: psycopg.Connection) -> List[StupidTestTableResult]:
		""" 
		Method to run the sql query.
		"""
		connection.row_factory = class_row(self.StupidTestTableResult)
		rows: List[self.StupidTestTableResult] = sql_executor(sql_query_with_placeholders=self.sql_string, parameters_in_pydantic_class=params, connection=connection)
		return rows
	



class InsertStupidPerson:
	""" 
	Class to hold all pydantic models for a single SQL query.
	Defined by SQL invocation in test.py.
	Used in files: []
	"""

	def __init__(self):
		self.sql_string = """INSERT INTO stupid_test_table (name, age, email) VALUES ('me', '24', 'broke@pleasehireme.com')"""

	""" 'InsertStupidPerson' parameters type """
	class InsertStupidPersonParams(BaseModel):
		pass # Looking for better ways to handle None, hmu



	""" 'InsertStupidPerson' return type """
	class InsertStupidPersonResult(BaseModel):
		pass # Looking for better ways to handle None, hmu



	def params(self) -> InsertStupidPersonParams:
		"""
	Method to set the parameters of the SQL invocation.
		"""
		return self.InsertStupidPersonParams()



	def run(self, params: InsertStupidPersonParams, connection: psycopg.Connection) -> List[InsertStupidPersonResult]:
		""" 
		Method to run the sql query.
		"""
		connection.row_factory = class_row(self.InsertStupidPersonResult)
		rows: List[self.InsertStupidPersonResult] = sql_executor(sql_query_with_placeholders=self.sql_string, parameters_in_pydantic_class=params, connection=connection)
		return rows
	
class InsertNormalPerson:
	""" 
	Class to hold all pydantic models for a single SQL query.
	Defined by SQL invocation in test.py.
	Used in files: []
	"""

	def __init__(self):
		self.sql_string = """INSERT INTO stupid_test_table (name, age, email) VALUES (:name, :age, :email)"""

	""" 'InsertNormalPerson' parameters type """
	class InsertNormalPersonParams(BaseModel):
		age: Optional[float]
		email: Optional[str]
		name: Optional[str]


	""" 'InsertNormalPerson' return type """
	class InsertNormalPersonResult(BaseModel):
		pass # Looking for better ways to handle None, hmu



	def params(self, name: Optional[str], age: Optional[float], email: Optional[str]) -> InsertNormalPersonParams:
		"""
	Method to set the parameters of the SQL invocation.
		"""
		return self.InsertNormalPersonParams(name = name, age = age, email = email)



	def run(self, params: InsertNormalPersonParams, connection: psycopg.Connection) -> List[InsertNormalPersonResult]:
		""" 
		Method to run the sql query.
		"""
		connection.row_factory = class_row(self.InsertNormalPersonResult)
		rows: List[self.InsertNormalPersonResult] = sql_executor(sql_query_with_placeholders=self.sql_string, parameters_in_pydantic_class=params, connection=connection)
		return rows
	


