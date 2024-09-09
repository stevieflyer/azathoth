import re
import os
import ast
from os import PathLike
from pathlib import Path

from pydantic import BaseModel, Field


class PythonParts(BaseModel):
    code: str
    file_path: Path
    project_root: Path
    imports: list[str]
    function_name_header_dict: dict[str, str] = Field(default_factory=dict)

    @property
    def n_functions(self):
        return len(self.function_headers)

    def get_function_name_source_dict(self, with_dependencies: bool = False) -> dict[str, str]:
        """Get the function name source dict

        Args:
            with_dependencies (bool, optional): Whether to include the dependencies. Defaults to False.

        Returns:
            dict[str, str]: The function name source dict
        """
        function_name_source_dict: dict[str, str] = {}
        for function_name, function_header in self.function_name_header_dict.items():
            if with_dependencies:
                function_source = extract_function_dependencies(
                    function_header=function_header,
                    imports=self.imports,
                    project_root=self.project_root
                ).to_string()
            else:
                function_source = function_header
            function_name_source_dict[function_name] = function_source
        return function_name_source_dict


class FunctionHeaderWithDependencies(BaseModel):
    function_header: str
    dependencies: list[str]

    def to_string(self):
        return self.function_header + "\n\n" +  "\n\n".join(self.dependencies)


def extract_python_parts(file_path: PathLike, project_root: PathLike) -> PythonParts:
    """Extract parts of a Python file using AST.

    Args:
        file_path (PathLike): The path to the Python file.

    Returns:
        (PythonParts): The extracted parts of the Python file.
    """
    file_path = Path(file_path)
    project_root = Path(project_root)

    with open(file_path, 'r', encoding='utf-8') as file:
        file_content = file.read()

    # Parse the content into an AST
    tree = ast.parse(file_content)

    # To store the import statements and function signatures
    import_parts = []
    function_name_header_dict = {}

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
            # Handle import statements
            import_parts.append(ast.unparse(node))
        elif isinstance(node, ast.FunctionDef):
            # Handle function definitions (without body)
            decorators = [f"@{ast.unparse(decorator)}" for decorator in node.decorator_list]
            func_name = node.name
            args = ast.unparse(node.args)
            return_type = ast.unparse(node.returns) if node.returns else None
            docstring = ast.get_docstring(node)

            # Format the function signature
            func_signature = f"def {func_name}({args}) -> {return_type if return_type else 'None'}:\n    pass"

            # Combine decorators, function signature, and docstring
            function_output = "\n".join(decorators) + "\n" + func_signature

            # If there's a docstring, add it as well
            if docstring:
                docstring_lines = f'"""{docstring}"""\n    pass'
                function_output = function_output.replace("pass", docstring_lines)

            # Store the result in the dictionary with function name as the key
            function_name_header_dict[func_name] = function_output.strip()

    return PythonParts(
        code=file_content,
        file_path=file_path,
        project_root=project_root,
        imports=import_parts,
        function_name_header_dict=function_name_header_dict,
    )


class ImportsInfo(BaseModel):
    imports: list[str] = Field(default_factory=list, description="The list of import modules.")
    import_froms: dict[str, list[str]] = Field(default_factory=dict, description="The dict of import modules from a module.")


def extract_imports_info(imports_content: str) -> ImportsInfo:
    """
    Extract import statements from valid Python import lines and categorize
    them into 'imports' and 'import_froms'.
    """
    imports_info = ImportsInfo()
    
    # Split content by lines
    lines = imports_content.splitlines()

    for line in lines:
        line = line.strip()

        # Skip empty lines and lines that don't start with 'import' or 'from'
        if not line or (not line.startswith('import') and not line.startswith('from')):
            continue

        # Handle 'from module import ...' statements
        if line.startswith('from'):
            match = re.match(r'^from\s+([\w\.]+)\s+import\s+(.+)', line)
            if match:
                module, qualifiers = match.groups()
                qualifiers_list = [q.strip() for q in qualifiers.split(',')]
                imports_info.import_froms[module] = qualifiers_list
        
        # Handle 'import module' statements
        elif line.startswith('import'):
            match = re.match(r'^import\s+([\w\.]+)', line)
            if match:
                module = match.group(1)
                imports_info.imports.append(module)

    return imports_info


def find_class_source_in_file(file_path: PathLike, class_names: list[str]) -> list[str]:
    """Find class definitions in a Python file.

    If the class name is found in the file, the class definition will be extracted; Else, an empty list will be returned.

    Args:
        file_path (PathLike): The path to the Python file.
        class_names (list[str]): The list of class names to search for.

    Returns:
        list[str]: The list of class definitions found in the file.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        file_content = file.read()

    # Parse the content into an AST
    tree = ast.parse(file_content)

    class_definitions = []

    # Iterate through the AST nodes and find class definitions
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef) and node.name in class_names:
            class_definitions.append(ast.unparse(node))

    return class_definitions


def find_class_source_in_directory(directory: PathLike, class_names: list[str]) -> list[str]:
    """Find class definitions in Python files within a directory.

    Args:
        directory (PathLike): The path to the directory.
        class_names (list[str]): The list of class names to search for.

    Returns:
        list[str]: The list of class definitions found in the directory.
    """
    class_definitions = []

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                definitions = find_class_source_in_file(file_path, class_names)
                if definitions:
                    class_definitions.extend(definitions)

    return class_definitions


def extract_function_dependencies(function_header: str, imports: list[str], project_root: PathLike) -> FunctionHeaderWithDependencies:
    # Parse the function_part into an AST
    tree = ast.parse(function_header)
    dependency_classes = set()

    # Extract argument types from the function signature
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            for arg in node.args.args:
                if arg.annotation:
                    arg_type = ast.unparse(arg.annotation)
                    dependency_classes.add(arg_type)

    # Filter out unwanted classes like BackgroundTasks, Depends, Session
    excluded_classes = {"BackgroundTasks", "Depends", "Session"}
    dependency_classes = dependency_classes - excluded_classes

    # Find the source of the imported classes
    class_sources = {}
    for imp in imports:
        # Split the import statement to match the dependencies
        if "import" in imp:
            imported_items = imp.split("import")[-1].strip().split(", ")
            for item in imported_items:
                item = item.split(" as ")[0].strip()
                if item in dependency_classes:
                    # Handle the possibility that the import is from a module (folder)
                    source_folder = imp.split("from")[-1].split("import")[0].strip().replace(".", "/")
                    full_source_folder = (project_root / source_folder).resolve()

                    if full_source_folder.is_dir():
                        # Search for the class definition in the entire module folder
                        class_definitions = find_class_source_in_directory(full_source_folder, [item])
                        if class_definitions:
                            class_sources[item] = class_definitions
                    else:
                        # Assume it's a single file import
                        full_source_path = full_source_folder.with_suffix(".py")
                        if full_source_path.exists():
                            class_sources[item] = find_class_source_in_file(full_source_path, [item])

    # Collect the found class definitions
    dependency_parts = []
    for class_name, definitions in class_sources.items():
        dependency_parts.extend(definitions)

    return FunctionHeaderWithDependencies(
        function_header=function_header,
        dependencies=dependency_parts
    )
