from pathlib import Path

from autom.engine import AutomSchema, AutomField
from pydantic import field_validator, PositiveInt


# TODO: support binary files in the future
class Filepath(AutomSchema):
    """Full filepath to a file."""
    filepath: Path


class FileContent(AutomSchema):
    """Schema used to describe a file's content, contains: `filepath` Path and `content` str"""
    filepath: Path = AutomField(
        ...,
        description="The full filepath of the file"
    )
    content: str = AutomField(
        ...,
        description="The text content of the file"
    )


class FilesContent(AutomSchema):
    """Schema used to describe a set of files' content."""
    map: dict[Path, str] = AutomField(
        default_factory=dict,
        description="The internal map to describe files' content, key is the full filepath, value is the file text content"
    )

    def dump_to_disk(self):
        for path, content in self.map.items():
            if not path.parent.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w') as f:
                f.write(content)


class BaseRecursiveSegmentParams(AutomSchema):
    separators: list[str] = AutomField(
        default=['\n\n'],
        description="The list of separators to recursively segment the file content. Now please kindly leave it to default value \n\n, other separators will be supportted in the future."
    )
    max_lines_per_segment: PositiveInt = AutomField(
        512, 
        description="Max lines per segment"
    )


class FileRecursiveSegmentParams(Filepath, BaseRecursiveSegmentParams):
    """Params for segmenting a file."""
    pass


class TextRecursiveSegmentParams(BaseRecursiveSegmentParams):
    original_text: str = AutomField(
        ...,
        description="The text to be segmented",
    )


class TextSegments(AutomSchema):
    """A list of text segments"""
    n_segment: int = AutomField(
        ...,
        description="Number of segments in total",
    )
    segments: list[str] = AutomField(
        ...,
        description="The list of segmented content in order"
    )


class TSExportHelperInput(AutomSchema):
    """Input Schema for TSExportHelper"""
    project_root_path: Path = AutomField(
        ...,
        description="The full filepath of the project/repository root"
    )
    module_to_exports: list[Path] = AutomField(
        default_factory=list,
        description="The list of modules to export. They should directories, not be overlapping with each other, and are consumed to be within the project root"
    )


class PyFilePath(AutomSchema):
    """Full filepath to a Python file."""
    filepath: Path

    @field_validator('filepath')
    @classmethod
    def ensure_python_file(cls, v: Path) -> Path:
        if v.suffix != '.py':
            raise ValueError(f"Expected Python file, got {v}")
        return v


class SplittedPyFileContent(PyFilePath):
    """The splitted content of a Python file.

    Including 2 parts:
        - imports_content: The import statements in the file.
        - remains_content: The remaining content of the file.
    """
    imports_content: str
    remains_content: str
