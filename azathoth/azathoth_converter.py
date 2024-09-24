from pathlib import Path

from autom.engine import GraphAgentWorker, AutomGraph, AutomSchema, BridgeWorker

from .schema_converter import AutomProjectSchemaConvertParams


class AzathothParams(AutomSchema):
    autom_engine_root_path: Path
    autom_backend_root_path: Path
    autom_frontend_root_path: Path


class AzathothSchemaConverterBridge(BridgeWorker):
    @classmethod
    def define_input_schema(cls) -> AutomSchema | None:
        return AzathothParams

    @classmethod
    def define_output_schema(cls) -> AutomSchema | None:
        return AutomProjectSchemaConvertParams


class AzathothConverter(GraphAgentWorker):
    @classmethod
    def define_graph(cls) -> AutomGraph:
        graph = AutomGraph()
        
        return graph
