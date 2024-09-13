from pathlib import Path

from autom.engine import GraphAgentWorker, Node, Link, AutomGraph, AutomSchema, BridgeWorker
from autom.engine.graph.graph import AutomGraph
from autom.official import HolderAgentWorker

from .api_converter import AutomProjectAPIConvertParams
from .action_converter import AutomProjectActionConvertParams
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
