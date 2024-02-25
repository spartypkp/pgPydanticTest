from typing import List, Optional, Dict, Any, Union
import datetime
from pydantic import BaseModel
from typing_extensions import NewType
from psycopg.rows import class_row
import psycopg
from sql_transformer import sql_executor


class InsertSmartPerson:
	""" 
	Class to hold all pydantic models for a single SQL query.
	Defined by SQL invocation in test.py.
	Used in files: []
	"""

	
	def __init__(self):
		self.sql_string = """INSERT INTO stupid_test_table (name, age, email) VALUES :account"""
	

	class InsertSmartPersonParams(BaseModel):
		"""'InsertSmartPerson' parameters type"""
		account: Account


	class InsertSmartPersonResult(BaseModel):
		"""'InsertSmartPerson' return type """

		pass # Looking for better ways to handle None, hmu



	def params(self, account: Account) -> InsertSmartPersonParams:
		"""
	Method to set the parameters of the SQL invocation.
		"""
		return self.InsertSmartPersonParams(account = account)



	def run(self, params: InsertSmartPersonParams, connection: psycopg.Connection) -> List[InsertSmartPersonResult]:
		""" 
		Method to run the sql query.
		"""
		connection.row_factory = class_row(self.InsertSmartPersonResult)
		rows: List[self.InsertSmartPersonResult] = sql_executor(sql_query_with_placeholders=self.sql_string, parameters_in_pydantic_class=params, connection=connection)
		return rows
	


