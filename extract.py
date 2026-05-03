import ast
import os
from collections import defaultdict

def extract_nodes(filepath):
    with open(filepath, 'r') as f:
        source = f.read()
    
    lines = source.splitlines()
    tree = ast.parse(source)
    
    nodes = []
    for node in tree.body:
        start = node.lineno - 1
        end = getattr(node, "end_lineno", node.lineno)
        # Look backwards for decorators
        if hasattr(node, "decorator_list") and node.decorator_list:
            start = node.decorator_list[0].lineno - 1
            
        nodes.append({
            "type": type(node).__name__,
            "name": getattr(node, "name", None),
            "start": start,
            "end": end,
            "node": node
        })
    return lines, nodes

def build():
    lines, nodes = extract_nodes("server.py")
    
    # We will manually map the functions/classes to files.
    # To do this safely, we can just print out the node names and their line ranges
    # and then I can write the logic.
    for n in nodes:
        name = n["name"] if n["name"] else n["type"]
        print(f"{name}: {n['start']} - {n['end']}")

if __name__ == "__main__":
    build()
