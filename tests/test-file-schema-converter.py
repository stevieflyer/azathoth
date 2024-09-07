from pathlib import Path
from autom.engine import Request
from autom.logger import autom_logger
from azathoth import FileSchemaConverter, FileSchemaConverterInput, RepoEnum

autom_logger.setLevel("INFO")

file_schema_converter = FileSchemaConverter()
file_schema_converter.fill_integration_auth_by_dict({
    'openai_chatgpt': {
        'api_key': '***'
    }
})

resp = file_schema_converter.on_serve(
    req=Request[FileSchemaConverterInput](
        sender='user',
        body=FileSchemaConverterInput(
            src_repo_enum=RepoEnum.BACKEND,
            src_repo_root=Path('/home/steve/workspace/autom-backend'),
            src_file_relpath=Path('app/schemas/entities.py'),
            dst_repo_enum=RepoEnum.FRONTEND,
            dst_repo_root=Path('/home/steve/workspace/autom-frontend'),
            dst_file_relpath=Path('types/entities.ts'),
           )
    )
)
print(resp.model_dump_json(indent=4))