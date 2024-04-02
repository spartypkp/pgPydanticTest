from model_library import Account

from typing import List, Optional, Dict, Any, Union
import datetime
from pydantic import BaseModel
from typing_extensions import NewType
from psycopg.rows import class_row
import psycopg
from sql_transformer import sql_executor


class SqlInsertAccount:
	""" 
	Class to hold all pydantic models for a single SQL query.
	Please suggest more useful class methods and properties.
	"""


	class SqlInsertAccountParams(BaseModel):
		"""'SqlInsertAccount' parameters type"""

		account: List[Account]


	class SqlInsertAccountResult(BaseModel):
		"""'SqlInsertAccount' return type """

		pass # Looking for better ways to handle None, hmu



	def params(self, account: List[Account]) -> SqlInsertAccountParams:
		"""
	Method to set the parameters of the SQL invocation.
		"""
		return self.SqlInsertAccountParams(account = account)



	def __init__(self):
		self.sql_string = """INSERT INTO account_table (name, age, email) VALUES :account""" 
		self.paramType = self.SqlInsertAccountParams
		self.resultType = self.SqlInsertAccountResult
		self.definition_file = "test.py" # This is the file where the class is defined
		self.definition_mode = "sql" # Only sql is supported for now
		self.query_ir = """[object Object]"""
		self.query_ast = """[object Object]"""


	def run(self, params: SqlInsertAccountParams, connection: psycopg.Connection) -> List[SqlInsertAccountResult]:
		""" 
		Method to run the sql query.
		"""
		connection.row_factory = class_row(self.SqlInsertAccountResult)
		rows: List[self.SqlInsertAccountResult] = sql_executor(sql_query_with_placeholders=self.sql_string, parameters_in_pydantic_class=params, connection=connection)
		return rows
	


