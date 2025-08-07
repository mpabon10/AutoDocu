from pathlib import Path
from typing import List, Optional
from auto_comment_functions import auto_comment
from auto_docstring_functions import generate_docstring_suggestions
from auto_summary import find_all_python_files, describe_directory_structure, summarize_directory, generate_readme


def orchestrate_all(directory: str, exclude_dirs: Optional[List[str]] = None, commenting_style: str = 'moderate', model: str = "llama3.1:8b"):
    """
    Orchestrates the commenting and summarization of a directory.
    
    Parameters:
    - directory (str): The path to the root directory to comment and summarize.
    - exclude_dirs (Optional[List[str]], optional): A list of directories to exclude from commenting and summarization. Defaults to None.
    - commenting_style (str, optional): The style of commenting to apply. Defaults to 'moderate'.
    - model (str, optional): The model to use for commenting and summarizing. Defaults to "llama3.1:8b".

    Returns:
    None
    """
    commenting_style=commenting_style.replace('commenting','')

    auto_docu_path=Path(directory+'/auto_docu_output')
    print(f"Scanning directory: {directory}")
    
    #default directories to exclude
    exclude_dirs=exclude_dirs+['venv','__pycache__']

    # Find all Python files in the directory and its subdirectories
    all_files = find_all_python_files(directory, exclude_dirs)
    
    for f in all_files:
        print(f.name)
        
    print("\nAdding {"+commenting_style+"} comments...")
    
    # Comment each file using auto_comment
    for file_path in all_files:
        print(str(file_path))
        auto_comment(file_path, auto_docu_path, model=model, commenting_style=commenting_style)
        
    print("\nGenerating docstrings...")
    
    # Generate docstrings for each commented file using generate_docstring_suggestions
    all_files = find_all_python_files(str(auto_docu_path))

    for file_path in all_files:
        print(str(file_path))
        generate_docstring_suggestions(str(file_path), str(auto_docu_path),  model=model)

    print("\n Describing directory...")
    describe_directory_structure(directory, auto_docu_path, exclude_dirs)

    print("\nSummarizing directory...")
    summarize_directory(auto_docu_path, model=model, exclude_dirs=exclude_dirs)
    
    print("Creating comprehensive README file...")
    generate_readme(auto_docu_path,auto_docu_path)

    print("\nDone!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Auto-document a Python project directory using Ollama.")
    parser.add_argument("directory", type=str, help="Path to the directory you want to process.")
    parser.add_argument(
        "--exclude_dirs", nargs="*", default=["__pycache__", "venv", ".git"],
        help="List of subdirectories to exclude."
    )
    parser.add_argument(
        "--commenting_style", type=str, default="moderate",
        help="Commenting style: 'minimal', 'moderate', or 'verbose'."
    )
    parser.add_argument(
        "--model", type=str, default="llama3.1:8b",
        help="Ollama model to use (e.g., 'llama3.1:8b', 'mistral', etc.)."
    )

    args = parser.parse_args()

    orchestrate_all(
        directory=args.directory,
        exclude_dirs=args.exclude_dirs,
        commenting_style=args.commenting_style,
        model=args.model
    )