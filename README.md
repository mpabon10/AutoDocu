**AutoDocu: Automated Documentation Generator**
==============================================

**Overview**
-----------

AutoDocu is a tool designed to automate documentation generation for Python projects. It finds all Python files within a specified directory, summarizes their contents using the `ollama` library, extracts functions with missing docstrings, and generates auto-generated documentation files by removing code fences from Markdown files.

**Directory Structure**
------------------------

The AutoDocu project consists of several scripts organized in the following directory structure:

* `auto_comment_functions.py`
* `auto_docstring_functions.py`
* `auto_orchestrator.py`
* `auto_summary.py`
* `requirements.txt`

**Script Overview**
------------------

### auto_orchestrator.py

This script finds all Python files within a specified directory and its subdirectories, excluding certain directories if required. It then summarizes the contents of each Python file using the `ollama` library.

### auto_docstring_functions.py

This script extracts functions with missing docstrings from a given Python file by parsing the code into an Abstract Syntax Tree (AST) and iterating over the AST nodes to find function definitions without docstrings.

### auto_comment_functions.py

This script contains two functions: `get_auto_docu_path` and `clean_markdown_code_fence`. The `get_auto_docu_path` function calculates the destination path for an auto-generated documentation file based on the project's root directory, subdirectories, and source file name. The `clean_markdown_code_fence` function removes code fences from Markdown files.

**Installation**
--------------

To use AutoDocu, ensure you have Python installed on your system (version 3.x recommended). You will also need to install the required dependencies listed in `requirements.txt`.

### Setting up the Project

1. Clone the AutoDocu repository using Git: `git clone https://github.com/your-username/AutoDocu.git`
2. Navigate into the project directory: `cd AutoDocu`
3. Install the required dependencies: `pip install -r requirements.txt`

**Usage Examples**
-----------------

### Generating Documentation

1. Run `auto_orchestrator.py` with your project's root directory as an argument: `python auto_orchestrator.py /path/to/project/root`
2. The script will generate documentation files in the `auto_docu_output` directory.

**Future Work**
---------------

* Implement a user interface for easier configuration and interaction.
* Integrate more advanced features, such as code analysis and suggestion tools.

**Contributing**
--------------

If you'd like to contribute to AutoDocu or suggest improvements, please submit a pull request with your changes.