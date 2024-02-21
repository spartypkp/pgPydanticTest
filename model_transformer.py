import libcst as cst



def main():
	with open("test_models.py", "r") as file:
		text = file.read()
	code = cst.parse_module(code)

	with open("generated_models.py", "r") as file:
		text = file.read()
	generated_models = cst.parse_module(text)

	transformer = SQLTransformer(updated_nodes = [code])
	code.visit(generated_models)

	with open("generated_models.py", "w") as file:
		file.write(generated_models.code)
	
		
class SQLTransformer(cst.CSTTransformer):
    
	def __init__(self, updated_nodes: list):
		self.updated_nodes = updated_nodes
    
	def on_leave(self, original_node: cst.CSTNode, updated_node: cst.CSTNode) -> cst.CSTNode:
		print(f"Visiting node: {original_node}")

		if isinstance(original_node, cst.ClassDef):
			for node in self.updated_nodes:
				if node.name.value == original_node.name.value:

					updated_node = node
					break
			self.updated_nodes.remove(updated_node)

		return updated_node


		
if __name__ == "__main__":
    main()
		