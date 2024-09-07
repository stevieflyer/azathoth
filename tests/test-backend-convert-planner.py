from pathlib import Path
from autom.engine import Request
from autom.logger import autom_logger
from azathoth import BackendSchemaConvertPlanner, AutomProjectSchemaConverterInput

autom_logger.setLevel("INFO")

planner = BackendSchemaConvertPlanner()
resp = planner.on_serve(
    req=Request[AutomProjectSchemaConverterInput](
        sender='user',
        body=AutomProjectSchemaConverterInput(
            autom_root_path=Path('/home/steve/workspace/autom'),
            autom_backend_root_path=Path('/home/steve/workspace/autom-backend'),
            autom_frontend_root_path=Path('/home/steve/workspace/autom-frontend'),
        )
    )
)
print(resp.model_dump_json(indent=4))
