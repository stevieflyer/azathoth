import re

from autom.engine import AutomSchema, Request, Response, AgentWorker

from ..schema import PyFilePath, SplittedPyFileContent


class PyImportsRemainsSplitter(AgentWorker):
    """Python File Handler to split imports and remains content."""
    @classmethod
    def define_input_schema(cls) -> AutomSchema | None:
        return PyFilePath

    @classmethod
    def define_output_schema(cls) -> AutomSchema | None:
        return SplittedPyFileContent

    def invoke(self, req: Request) -> Response:
        req_body: PyFilePath = req.body
        file_path = req_body.filepath

        imports_content = []
        remains_content = []
        is_import_section = False

        # Define regex patterns for `import` and `from ... import` statements
        import_pattern = re.compile(r'^(import|from)\s+.*')

        with file_path.open('r', encoding='utf-8') as f:
            lines = f.readlines()

        current_import_block = []

        for line in lines:
            stripped_line = line.strip()

            # Handle multiline imports by checking for parentheses
            if import_pattern.match(stripped_line) or is_import_section:
                current_import_block.append(line)

                if "(" in stripped_line and not ")" in stripped_line:
                    is_import_section = True  # Start of multiline import
                elif ")" in stripped_line:
                    is_import_section = False  # End of multiline import
                    imports_content.extend(current_import_block)
                    current_import_block = []
                elif not is_import_section:
                    imports_content.extend(current_import_block)
                    current_import_block = []

            else:
                remains_content.append(line)

        # If there's leftover import block content, add it to imports
        if current_import_block:
            imports_content.extend(current_import_block)

        return Response[SplittedPyFileContent].from_worker(self).success(
            body=SplittedPyFileContent(
                filepath=req_body.filepath,
                imports_content="".join(imports_content),
                remains_content="".join(remains_content)
            )
        )


__all__ = [
    'PyImportsRemainsSplitter',
]
