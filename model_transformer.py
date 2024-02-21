import libcst as cst
from typing import List

	
class ModelTransformer(cst.CSTTransformer):
    
	def __init__(self, updated_nodes: list):
		self.updated_nodes = updated_nodes
    
	def on_visit(self, node: cst.CSTNode) -> bool:
		return True
	
	def on_leave(self, original_node: cst.CSTNode, updated_node: cst.CSTNode) -> cst.CSTNode:
		#print(f"Visiting node: {original_node}")
		#print(f"Length of updated_nodes: {len(self.updated_nodes)}")
		if len(self.updated_nodes) == 0:
			return updated_node
		
		if isinstance(original_node, cst.ClassDef):
			removal_index = -1
			for i, node in enumerate(self.updated_nodes):
				#print(type(node))
				#print(node)

				if node.name.value == original_node.name.value:
					#print(f"Found a match: {node.name.value} == {original_node.name.value}")
					removal_index = i
					updated_node = node
					break
			if removal_index != -1:
				self.updated_nodes.pop(removal_index)
			else:
				pass
		return updated_node

def add_module(to_add: List[cst.Module], module_to_update: cst.Module):
    # Append the new modules to the end of the existing module
    new_body = list(module_to_update.body)
    for new_module in to_add:
        new_body.append(new_module)
    module_to_update = module_to_update.with_changes(body=tuple(new_body))
    return module_to_update



def apply_codemod_to_file(modules_to_add: List[cst.Module]):
	source_code = ""
	with open("generated_models.py", "r") as file:
		source_code = file.read()
	

	 # Parse the source code into a CST
	tree = cst.parse_module(source_code)
	
    # Apply the codemod
	transformer = ModelTransformer(updated_nodes=modules_to_add)
	modified_tree = tree.visit(transformer)

	modified_tree = add_module(modules_to_add, modified_tree)

	
	#print(f"\n\n\n\nModified code:\n{modified_tree.code}")

	with open("generated_models.py", "w") as file:
		file.write(modified_tree.code)
	file.close()


		