from os import PathLike
from pathlib import Path

from autom.engine import AutomSchema, Request, Response, AgentWorker

from ..schema import TSExportHelperInput, FilesContent


class TSExportHerlper(AgentWorker):
    @classmethod
    def define_input_schema(cls) -> AutomSchema | None:
        return TSExportHelperInput
    
    @classmethod
    def define_output_schema(cls) -> AutomSchema | None:
        return FilesContent

    def invoke(self, req: Request) -> Response:
        req_body: TSExportHelperInput = req.body
        
        map: dict[Path, str] = {}
        for module_path in req_body.module_to_exports:
            module_file_map = add_index_ts(module_path)
            map.update(module_file_map)

        return Response[FilesContent].from_worker(self).success(
            body=FilesContent(map=map)
        )


def add_index_ts(module_dir: PathLike) -> dict[Path, str]:
    return add_index_ts_recursive(module_dir, {})


def add_index_ts_recursive(path: PathLike, file_map: dict[Path, str]) -> dict[Path, str]:
    path = Path(path)
    if not path.exists() or not path.is_dir():
        raise ValueError(f"Path {path} does not exist or is not a directory")

    qualifiers = []
    for f in path.iterdir():
        if f.is_file() and f.suffix == ".ts" and f.name != "index.ts":
            qualifiers.append(f.stem)
        elif f.is_dir():
            qualifiers.append(f.name)
            add_index_ts_recursive(f, file_map)

    index_ts_path = path / "index.ts"
    index_ts_content = "\n".join([f'export * from "./{q}";' for q in qualifiers]) + "\n"
    file_map[index_ts_path] = index_ts_content

    return file_map


__all__ = [
    'TSExportHerlper',
]
