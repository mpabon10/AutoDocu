import ollama
from pathlib import Path

def get_auto_docu_path(src: Path, new_branch_root: Path):
    """
    get file path under new_branch_root (e.g. "A/D") *including* the intermediate folders (here "B"). for file at src_path (e.g. "A/B/C.py") 
    """

    if not src.is_file():
        raise FileNotFoundError(f"{src!r} does not exist")

    # 1. Identify the project root ("A") and the subpath under it ("B")
    project_root = Path(src.parts[0]).parent                   # => Path("A")
    sub_dirs     = src.parent.relative_to(project_root) # => Path("B")

    # 2. Build the destination directory: new_branch_root / sub_dirs
    dst_dir = new_branch_root / sub_dirs          # => Path("A/D/B")
    dst_dir.mkdir(parents=True, exist_ok=True)

    # 3. Copy the file itself into dst_dir
    dst_file = dst_dir / src.name                       # => Path("A/D/B/C.py")

    return dst_file


def clean_markdown_code_fence(file_path: Path) -> None:
    """
    Removes a leading line containing "'''python" and a trailing line containing "'''" from the file.
    
    Parameters:
    - file_path (Path): The path to the file to clean. The file is modified in place.

    Returns:
    None
    """
    # Read the entire file into memory as a list of lines
    lines = file_path.read_text(encoding="utf-8").splitlines()
    
    if lines and lines[0].strip().lower() == "```python":
        """
        If the first line starts with "'''python", remove it from the beginning of the list.
        
        We use `strip` to remove leading/trailing whitespace before comparing, and convert to lowercase for case-insensitive comparison.
        """
        lines = lines[1:]

    if lines and lines[-1].strip() == "```":
        """
        If the last line is just "'''", remove it from the end of the list.
        
        Again, we use `strip` to remove leading/trailing whitespace before comparing.
        """
        lines = lines[:-1]

    # Write the cleaned-up lines back to the file
    file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def auto_comment(file_path: Path, auto_docu_root: Path, model: str = "llama3.1:8b", commenting_style: str = "moderate"):
    """
    Adds inline comments to a Python file using LLM.
    
    Comments are added above complex logic blocks or functions.
    
    Parameters:
    - file_path (Path): The path to the file to comment.
    - model (str, optional): The model to use for commenting. Defaults to "llama3.1:8b".
    - commenting_style (str, optional): The style of commenting to apply. Defaults to "moderate".

    Returns:
    Path: The path to the commented version of the file.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        # Read the entire file into memory
        original_code = f.read()

    #determine existing commenting style
    prompt = f""" You are a Python commenting assistant. Read the following code and determine what commenting style is applied.
    Just reply a single phrase between 1 and 3 words long (ex. extensive, light) that describes the verbosity of commenting that you find in this file, no explanations or details.    
    ```python
    {original_code}
    """

    try:
        """
        Send the prompt to the LLM and get back the commented code.

        We use a `try`-`except` block to catch any errors that might occur during this process.
        """
        response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}])
        # Get the commented code from the LLM's response
        existing_commenting = (response["message"]["content"]).replace('commenting','')
        print(existing_commenting)
    except Exception as e:
        """
        If an error occurs during reading code, print the error and do not add comments to code.
        
        This ensures that the function doesn't crash if something goes wrong, but still allows the user to see what happened.
        """
        print(f"[Error reading code {file_path.name}]: {e}")
        existing_commenting='unknown'

    #deterine if existing 
    prompt = f"""Answer how similar or different the phrase {existing_commenting} is from the phrase {commenting_style} in terms of code commenting verbosity.
    Simply reply with very different, different, similar, or very similar. Just give your answer. No explanation is needed.
    """
        
    try:
        """
        Send the prompt to the LLM and get back the commented code.

        We use a `try`-`except` block to catch any errors that might occur during this process.
        """
        response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}])
        # Get the commented code from the LLM's response
        commenting_diff_scale = (response["message"]["content"]).lower()
        needs_commenting=True if 'different' in commenting_diff_scale else False
        print("commenting_diff_scale: " + commenting_diff_scale)
        print("needs_commenting: "+ str(needs_commenting))
    except Exception as e:
        """
        If an error occurs during reading code, print the error and do not add comments to code.
        
        This ensures that the function doesn't crash if something goes wrong, but still allows the user to see what happened.
        """
        print(f"[Error reading code {file_path.name}]: {e}")
        needs_commenting=False

    if needs_commenting:
        # Construct a prompt for the LLM based on the commenting style and model
        prompt = f""" You are a Python commenting assistant. 
        Read the following code and return the same code, but remove the existing comments
        Return ONLY the modified code with comments removed. Do not summarize or explain. 
        ```python
        {original_code}
        """
        try:
            """
            Send the prompt to the LLM and get back the commented code.
            
            We use a `try`-`except` block to catch any errors that might occur during this process.
            """
            response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}])
            # Get the commented code from the LLM's response
            un_commented_code = response["message"]["content"]

            # Create a new path for the commented version of the file
            
            new_path = get_auto_docu_path(file_path,auto_docu_root)
            
            with open(new_path, "w", encoding="utf-8") as f:
                # Write the commented code to the new file
                f.write(un_commented_code)
            
            clean_markdown_code_fence(new_path)  # Remove leading/trailing Markdown code fences
            print(f"Original comments removed from {new_path.name}")
        except Exception as e:
            """
            If an error occurs during commenting, print the error and return None.
            
            This ensures that the function doesn't crash if something goes wrong, but still allows the user to see what happened.
            """
            print(f"[Error commenting {file_path.name}]: {e}")

        with open(new_path, "r", encoding="utf-8") as f:
                # Write the commented code to the new file
                un_commented_code=f.read()
        # Construct a prompt for the LLM based on the commenting style and model
        prompt = f""" You are a Python commenting assistant. 
        Read the following code and return the same code, but with {commenting_style} inline comments.
        Return ONLY the modified code with comments. Do not summarize or explain. 
        ```python
        {un_commented_code}
        """
        try:
            """
            Send the prompt to the LLM and get back the commented code.
            
            We use a `try`-`except` block to catch any errors that might occur during this process.
            """
            response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}])
            # Get the commented code from the LLM's response
            commented_code = response["message"]["content"]

            # Create a new path for the commented version of the file
            
            new_path = get_auto_docu_path(file_path,auto_docu_root)
            
            with open(new_path, "w", encoding="utf-8") as f:
                # Write the commented code to the new file
                f.write(commented_code)
            
            clean_markdown_code_fence(new_path)  # Remove leading/trailing Markdown code fences
            print(f"New comments added to {new_path.name}")

        except Exception as e:
            """
            If an error occurs during commenting, print the error and return None.
            
            This ensures that the function doesn't crash if something goes wrong, but still allows the user to see what happened.
            """
            print(f"[Error commenting {file_path.name}]: {e}")
        
    else:
        print(f"No Comments style change needed for {new_path.name}")
        new_path = get_auto_docu_path(file_path,auto_docu_root)
        with open(new_path, "w", encoding="utf-8") as f:
            # Write the commented code to the new file
            f.write(original_code)
            

