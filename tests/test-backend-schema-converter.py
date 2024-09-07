
from pathlib import Path
from autom.engine import Request
from autom.logger import autom_logger
from azathoth import BackendSchemaConverter, AutomProjectSchemaConverterInput

autom_logger.setLevel("INFO")

backend_schema_converter = BackendSchemaConverter()
backend_schema_converter.fill_integration_auth_by_dict(values={
    'openai_chatgpt': {
        'api_key': '***'
    }
})

resp = backend_schema_converter.on_serve(
    req=Request[AutomProjectSchemaConverterInput](
        sender='user',
        body=AutomProjectSchemaConverterInput(
            autom_root_path=Path('/home/steve/workspace/autom'),
            autom_backend_root_path=Path('/home/steve/workspace/autom-backend'),
            autom_frontend_root_path=Path('/home/steve/workspace/autom-frontend'),
            max_lines_per_segment=128,
        )
    )
)
print(resp.model_dump_json(indent=4))