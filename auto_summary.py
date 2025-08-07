
from pathlib import Path
from typing import List, Optional
import ollama
import os

def find_all_python_files(directory: str, exclude_dirs: Optional[List[str]] = None) -> List[Path]:
    """
    Finds all Python files in the given directory and its subdirectories.
    
    Parameters:
    - directory (str): The path to the root directory to search for Python files.
    - exclude_dirs (Optional[List[str]], optional): A list of directories to exclude from the search. Defaults to None.

    Returns:
    List[Path]: A list of Path objects representing the found Python files.
    """
    # Initialize an empty list to store all Python file paths
    all_py_files = []
    
    # Convert exclude_dirs to a set for faster lookup
    exclude_dirs = set(exclude_dirs or [])  
    
    # Iterate over all files in the directory and its subdirectories with rglob
    for path in Path(directory).rglob("*.py"):
        """
        Check if any part of the path is in the excluded directories
        
        We use `any` with a generator expression to check if any part of the path's parts are in exclude_dirs.
        This ensures we don't include files in excluded directories even if they're not directly inside those dirs.
        """
        if not any(part in exclude_dirs for part in path.parts):
            # If no excluded directory is found, add the file to all_py_files
            all_py_files.append(path)
    temp=[x for x in all_py_files ] #if x.name not in ['auto_comment_functions.py','auto_orchestrator.py']]
    return temp

def describe_directory_structure(directory: str, output_path: str, exclude_dirs: Optional[List[str]] = None, max_depth=3, show_file_preview=False, preview_lines=3):
    """
    Recursively reads a directory and generates a structured, LLM-friendly description.
    
    Args:
        directory (str): The root path to analyze.
        output (str): The path to write output to
        max_depth (int): Maximum directory depth to include.
        show_file_preview (bool): If True, include a preview of the first few lines of each file.
        preview_lines (int): Number of lines to preview per file if show_file_preview is True.
        
    Returns:
        str: A structured text description of the directory.
    """
    output = []

    def walk_dir(current_path, indent_level=0):
        if indent_level > max_depth:
            return

        items = sorted(os.listdir(current_path))
        for item in items:
            full_path = os.path.join(current_path, item)
            indent = '  ' * indent_level

            if os.path.isdir(full_path):
                if (item in exclude_dirs) or (item.startswith('.')):
                    continue
                output.append(f"{indent}- {item}/")
                walk_dir(full_path, indent_level + 1)

            else:
                if item.startswith('.'):
                    continue    
                
                output.append(f"{indent}- {item}")
                if show_file_preview and item.endswith(('.py', '.md', '.txt')):
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            preview = ''.join(f.readlines()[:preview_lines]).strip()
                            if preview:
                                output.append(f"{indent}    Preview:\n{indent}    \"\"\"\n{indent}    {preview}\n{indent}    \"\"\"")
                    except Exception as e:
                        output.append(f"{indent}    [Preview Error: {e}]")

    output.append(f"# Directory structure for `{os.path.basename(os.path.abspath(directory))}`")
    walk_dir(directory)
    output='\n'.join(output)
    
    directory_desc_path=Path(output_path) / "README_1_directory_structure.txt"
    with open(directory_desc_path, "w", encoding="utf-8") as f:
        f.write(output)

def summarize_directory(directory: str, exclude_dirs: Optional[List[str]] = None, model: str = "llama3.1:8b"):
    """
    Summarizes what the directory of code does.
    
    Parameters:
    - directory (str): The path to the root directory to summarize.
    - exclude_dirs (Optional[List[str]], optional): A list of directories to exclude from the summary. Defaults to None.
    - model (str, optional): The model to use for summarization. Defaults to "llama3.1:8b".

    Returns:
    None
    """
    
    describe_directory_structure(directory)
    
    # Initialize an empty string to store the summary text
    summary_txt = ""
    
    for py_file in find_all_python_files(directory, exclude_dirs):
        try:
            """
            Read the contents of each Python file and summarize it using LLM.
            
            We use a `try`-`except` block to catch any errors that might occur during this process.
            """
            with open(py_file, "r", encoding="utf-8") as f:
                code = f.read()
            # Construct a prompt for the LLM based on the file's contents
            prompt = f"""You're a Python code summarizer. Read the file content and briefly describe at a high level what it contains in 1–3 sentences. You wrote this code and are certain about your summary.
    {code[:2000]}
            
            """
            response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}])
            # Get the summary from the LLM's response
            file_summary = response["message"]["content"].strip()

            prompt = f"""You're a Python code summarizer. Read the file content and scan for any user defined function calling or any other detailed processes. Keep track of the order of function calls. Additionally Describe the identified processes in 2–4 sentences. You wrote this code and are certain about your summary.
    {code[:2000]}
            
            """
            response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}])
            # Get the summary from the LLM's response
            file_processes = response["message"]["content"].strip()

            # Add the file's summary to the overall summary text
            summary_txt += f"### {py_file.replace('auto_docu_output/','')}\nfile_summary: {file_summary}\nfile_processes: {file_processes}\n\n"

        except Exception as e:
            """
            If an error occurs during summarization, add a placeholder for the file and continue.
            
            This ensures that the function doesn't crash if something goes wrong, but still allows the user to see what happened.
            """
            summary_txt += f"### {py_file.replace('auto_docu_output/','')}\n[Error reading or summarizing file: {e}]\n\n"

    # Write the summary text to a README file in the root directory
    job_summary_path=Path(directory) / "README_3_job_summaries.txt"
    with open(job_summary_path, "w", encoding="utf-8") as f:
        f.write("# Codebase Summary\n\n")
        f.write(summary_txt)
    
    try:
        with open(job_summary_path, "r", encoding="utf-8") as f:
            job_summaries = f.read()
        prompt = f"""You're a Python code summarizer. Read the file that explains what each python script in the directory contains and briefly describe what the entire directory does holistically, in 2–4 sentences. You wrote this code and are certain about your summary.
{job_summaries} 
        """
        response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}])
        directory_summary = response["message"]["content"].strip()

    except Exception as e:
        directory_summary = f"###\n[Error reading or summarizing directory: {e}]\n\n"

    with open(Path(directory) / "README_2_directory_summary.txt", "w", encoding="utf-8") as f:
        f.write("# Directory Summary\n\n")
        f.write(directory_summary)

    print("Summary written to README_summary.txt")

def generate_readme(txt_dir, output_path, model: str = "llama3.1:8b"):
    """
    Reads .txt files from a directory that describe Python files and uses Ollama to generate a README.md.
    
    Args:
        txt_dir (str): Path to the directory containing .txt files.
        output_path (str): Path to save the generated README.md.
        model (str): Name of the Ollama model to use.
    """
    
    # Read all .txt files in the directory
    txt_contents = []
    for filename in sorted(os.listdir(txt_dir)):
        if filename.endswith('.txt'):
            filepath = os.path.join(txt_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                txt_contents.append(f.read())

    if not txt_contents:
        raise ValueError("No .txt files found in the directory.")

    combined_description = "\n\n".join(txt_contents)

    # Craft prompt
    prompt = f"""
You are an expert software documentarian. You are given descriptions of various Python files that are part of a project.
Using the descriptions below, create a professional, helpful, and clean README.md for the project that would be suitable for GitHub.

Descriptions:
{combined_description}

The README should include:
- A project title
- A brief description of what the project does
- Installation or setup instructions (generic, if details are not available)
- An overview of the directory structure
- A section briefly explaining the role of each major Python file
- Usage examples if possible
- Any other relevant GitHub-style sections

Output ONLY the markdown content of the README.
    """

    # Call Ollama
    response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}])
    result = response["message"]["content"].strip()

    # Save the README
    with open(output_path+'/README.md', 'w', encoding='utf-8') as f:
        f.write(result.strip())
    
    print(f"README generated at {output_path}")
