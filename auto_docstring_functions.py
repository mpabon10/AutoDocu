import ollama  # Importing Ollama for generating docstrings using LLaMA model
import ast   # Importing Abstract Syntax Trees (AST) module for parsing Python code
import os    # Importing OS module for file operations
from typing import List, Tuple  # Importing type hints for function arguments and return types
from auto_comment_functions import get_auto_docu_path

def extract_functions_missing_docstrings(file_path: str) -> Tuple[str, List[Tuple[ast.FunctionDef, str]]]:
    """
    Parses a Python file and extracts functions missing docstrings.
    
    Args:
        file_path (str): Path to the Python file to analyze.

    Returns:
        Tuple[str, List[Tuple[ast.FunctionDef, str]]]: A tuple containing the full source code and a list of tuples,
            where each tuple contains an AST FunctionDef node and the source code of the function.
    """
    with open(file_path, "r", encoding="utf-8") as f:  # Open file in read mode with UTF-8 encoding
        source = f.read()  # Read entire file into a string

    tree = ast.parse(source)  # Parse Python code into an Abstract Syntax Tree (AST)
    lines = source.splitlines()  # Split source code into individual lines

    missing = []  # Initialize list to store functions with missing docstrings
    for node in ast.walk(tree):  # Iterate over all nodes in the AST
        if isinstance(node, ast.FunctionDef) and ast.get_docstring(node) is None:  # Check if node is a FunctionDef with no docstring
            func_lines = lines[node.lineno - 1 : node.end_lineno]  # Get source code of function as a list of lines
            func_src = "\n".join(func_lines)  # Join source code lines into a single string
            missing.append((node, func_src))  # Append tuple containing FunctionDef node and source code to list

    return source, missing  # Return full source code and list of functions with missing docstrings

def suggest_docstring_with_ollama(function_code: str, model: str = "llama3.1:8b") -> str:
    """
    Uses Ollama to generate a docstring for a given function.
    
    Args:
        function_code (str): Source code of the function as a string
        model (str, optional): LLaMA model version (default: "llama3.1:8b")

    Returns:
        str: Generated docstring using Ollama's LLaMA model
    """
    prompt = f"""You are a helpful Python documentation assistant. Read the following Python 
    function and write a clear, concise google style docstring in triple quotes. Only output 
    the docstring starting your reply with triple quotes.
    ```python
    {function_code}
    ```"""
    # Send prompt to Ollama model and get response
    response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}])  
    # Return generated docstring from Ollama's response
    return response["message"]["content"]  

def insert_docstrings(source: str, func_nodes: List[Tuple[ast.FunctionDef, str]], docstrings: List[str]) -> str:
    """
    Inserts the generated docstrings into the source code.
    
    Args:
        source (str): Full source code as a string
        func_nodes (List[Tuple[ast.FunctionDef, str]]): List of tuples containing FunctionDef nodes and their source code
        docstrings (List[str]): List of generated docstrings for functions

    Returns:
        str: Modified source code with inserted docstrings
    """
    lines = source.splitlines()  # Split source code into individual lines

    # Reverse so inserting docstrings doesn't affect line numbers of later functions
    for (node, _), doc in reversed(list(zip(func_nodes, docstrings))):
        insert_line = node.body[0].lineno  # Get line number where docstring should be inserted
        indent = " " * (node.col_offset + 4)  # Calculate indentation level for docstring lines
        doc_lines = [indent + line for line in doc.strip().splitlines()]  # Split docstring into individual lines and add indentation
        lines.insert(insert_line - 1, "\n".join(doc_lines))  # Insert docstring lines before corresponding function

    return "\n".join(lines)  # Join modified source code back into a single string

def generate_docstring_suggestions(file_path: str, auto_docu_root: str, model: str = "llama3.1:8b"):
    """
    Generates suggested docstring for functions with missing docstrings in a given Python file.
    
    Args:
        file_path (str): Path to the Python file to analyze
        model (str, optional): LLaMA model version (default: "llama3.1:8b")

    Returns:
        None

    Modifies:
        If a new file with inserted docstrings is desired, it is written to disk.
    """
    source, missing_funcs = extract_functions_missing_docstrings(file_path)  # Extract functions with missing docstrings
    docstrings = []  # Initialize list to store generated docstrings for functions

    for node, func_src in missing_funcs:
        print("=" * 80)  # Print separator line
        print(f"Function: {node.name} (Line {node.lineno})")  # Print function name and line number
        print("- Suggested Docstring -")  # Print header for suggested docstring
        try:
            doc = suggest_docstring_with_ollama(func_src, model=model)  # Generate docstring using Ollama's LLaMA model
            print(doc)  # Print generated docstring
            docstrings.append(doc)  # Append generated docstring to list
        except Exception as e:  # Catch any exceptions during docstring generation
            print(f"[Error generating docstring] {e}")  # Print error message
            docstrings.append('"""TODO: Add docstring"""')  # Append default docstring with TODO comment
        print()  # Print newline for next function

    if missing_funcs:

        new_source = insert_docstrings(source, missing_funcs, docstrings)  # Insert generated docstrings into source code            
        with open(file_path, "w", encoding="utf-8") as f:  # Open new file in write mode with UTF-8 encoding
            f.write(new_source)  # Write modified source code to new file
        print(f"\n✅ Docstrings added to: {file_path}")  # Print success message
      
    else:
        print("No functions missing docstrings found.")  # Print no-functions-missing-docstrings-found message if no functions are missing docstrings
