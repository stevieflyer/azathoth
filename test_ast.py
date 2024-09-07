import ast
import os


def extract_headers_and_imports(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        file_content = file.read()
    
    # Parse the content into an AST
    tree = ast.parse(file_content)

    # To store the import statements and function signatures
    import_parts = []
    function_parts = []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
            # Handle import statements
            import_parts.append(ast.unparse(node))
            pass
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
                docstring_lines = f'    """{docstring}"""\n    pass'
                function_output = function_output.replace("pass", docstring_lines)

            # Store the result
            function_parts.append(function_output.strip())  # Use strip to remove extra newline

    return import_parts, function_parts


def find_class_definitions(file_path, class_names):
    print(f"Searching for class definitions in: {file_path}")
    print(f"Looking for classes: {class_names}")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        file_content = file.read()
    
    # Parse the content into an AST
    tree = ast.parse(file_content)

    class_definitions = []

    # Iterate through the AST nodes and find class definitions
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef) and node.name in class_names:
            print(f"Found class definition: {node.name}")
            class_definitions.append(ast.unparse(node))

    return class_definitions


def search_class_in_directory(directory, class_names):
    """Search for class definitions in all Python files in the directory."""
    class_definitions = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                print(f"Searching in file: {file_path}")
                definitions = find_class_definitions(file_path, class_names)
                if definitions:
                    print(f"Found definitions in {file_path}: {definitions}")
                    class_definitions.extend(definitions)
    
    return class_definitions


def extract_function_dependencies(function_part, import_parts, project_root):
    # Parse the function_part into an AST
    tree = ast.parse(function_part)
    dependency_classes = set()

    # Extract argument types from the function signature
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            print(f"Parsing function: {node.name}")
            for arg in node.args.args:
                if arg.annotation:
                    arg_type = ast.unparse(arg.annotation)
                    print(f"Found argument type: {arg_type}")
                    dependency_classes.add(arg_type)
    
    # Filter out unwanted classes like BackgroundTasks, Depends, Session
    excluded_classes = {"BackgroundTasks", "Depends", "Session"}
    dependency_classes = dependency_classes - excluded_classes
    print(f"Filtered dependency classes: {dependency_classes}")

    # Find the source of the imported classes
    class_sources = {}
    for imp in import_parts:
        # Split the import statement to match the dependencies
        if "import" in imp:
            imported_items = imp.split("import")[-1].strip().split(", ")
            print(f"imported_items: {imported_items}")  # Ensure this shows full class names
            for item in imported_items:
                item = item.split(" as ")[0].strip()
                if item in dependency_classes:
                    # Handle the possibility that the import is from a module (folder)
                    source_folder = imp.split("from")[-1].split("import")[0].strip().replace(".", "/")
                    full_source_folder = os.path.join(project_root, source_folder)

                    if os.path.isdir(full_source_folder):
                        # Search for the class definition in the entire module folder
                        print(f"Searching for {item} in {full_source_folder}")
                        class_definitions = search_class_in_directory(full_source_folder, [item])
                        if class_definitions:
                            class_sources[item] = class_definitions
                    else:
                        # Assume it's a single file import
                        full_source_path = f"{full_source_folder}.py"
                        if os.path.exists(full_source_path):
                            print(f"Searching for {item} in {full_source_path}")
                            class_sources[item] = find_class_definitions(full_source_path, [item])

    # Collect the found class definitions
    dependency_parts = []
    for class_name, definitions in class_sources.items():
        print(f"Found definitions for {class_name}")
        dependency_parts.extend(definitions)

    return function_part, dependency_parts


# Usage example
file_path = '/home/steve/workspace/autom-backend/app/api/v1/endpoints/project.py'
import_parts = [
    'from app.schemas import UserSafe, AutomProjectWithOwnerAndStatus, CreateFromDashboardReqBody, MakeCheckPointReqBody'
]
function_part = """
@router.post(
    "/create-from-dashboard", 
    response_model=AutomProjectWithOwnerAndStatus,
)
async def create_project_from_dashboard(
    body_data: CreateFromDashboardReqBody,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserSafe = Depends(get_current_user),
):
    pass
"""

# Project root directory to locate imported files
project_root = '/home/steve/workspace/autom-backend/'

# Call the function
function_output, dependency_parts = extract_function_dependencies(function_part, import_parts, project_root)

# Print results
print("Function Part:\n", function_output)
print("\nDependencies Part:\n", "\n".join(dependency_parts))
