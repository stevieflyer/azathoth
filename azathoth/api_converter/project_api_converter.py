from autom.engine import (
    AutomSchema, Request, Response,
    AgentWorker, BridgeWorker, DispatchBridgeWorker, GraphAgentWorker, AutomGraph, Node, Link,
)
from autom.official import HolderAgentWorker, IdentityBridgeWorker

from azathoth.common import (
    TSExportHelperInput, 
    FilesContentFilesContentCollectPlugger, FilesContentAggregator, TSExportHerlper, FilesContentFilesContentPlugger,
)
from .file_api_converter import FileAPIConverter
from .schema import AutomProjectAPIConverterInput, EnumeratedFiles, FileAPIConverterInput, FileEnumeratorInput


class AutomProjectAPIConverter(GraphAgentWorker):
    @classmethod
    def define_graph(cls) -> AutomGraph:
        graph = AutomGraph()

        entry_node = Node.from_worker(HolderAgentWorker().with_schema(AutomProjectAPIConverterInput))
        entry_ts_export_helper_bridge = Link.from_worker(APIConverterTSExportHelperBridgeWorker())
        ts_export_helper = Node.from_worker(TSExportHerlper())
        ts_export_helper_exit_plugger = Link.from_worker(FilesContentFilesContentPlugger())
        entry_enumerator_bridge = Link.from_worker(IdentityBridgeWorker())
        api_file_enumerator = Node.from_worker(AutomProjectAPIFileEnumerator())
        enumerator_file_api_converter_dispatch_bridge = Link.from_worker(EnumeratorFileAPIConverterDispatchBridgeWorker())
        file_api_converter = Node.from_worker(FileAPIConverter())
        file_api_converter_exit_collect_plugger = Link.from_worker(FilesContentFilesContentCollectPlugger())
        exit_aggregator = Node.from_worker(FilesContentAggregator())

        graph.add_node(entry_node)
        graph.add_node(ts_export_helper)
        graph.add_node(api_file_enumerator)
        graph.add_node(file_api_converter)
        graph.add_node(exit_aggregator)

        graph.bridge(entry_node, ts_export_helper, entry_ts_export_helper_bridge)
        graph.plug(ts_export_helper, exit_aggregator, ts_export_helper_exit_plugger)
        graph.bridge(entry_node, api_file_enumerator, entry_enumerator_bridge)
        graph.bridge(api_file_enumerator, file_api_converter, enumerator_file_api_converter_dispatch_bridge)
        graph.plug(file_api_converter, exit_aggregator, file_api_converter_exit_collect_plugger)

        graph.set_entry_node(entry_node)
        graph.set_exit_node(exit_aggregator)

        return graph


class APIConverterTSExportHelperBridgeWorker(BridgeWorker):
    @classmethod
    def define_input_schema(cls) -> AutomSchema | None:
        return AutomProjectAPIConverterInput

    @classmethod
    def define_output_schema(cls) -> AutomSchema | None:
        return TSExportHelperInput

    def invoke(self, req: Request) -> Response:
        req_body: AutomProjectAPIConverterInput = req.body
        return Response[TSExportHelperInput].from_worker(self).success(
            body=TSExportHelperInput(
                project_root_path=req_body.autom_frontend_root_path,
                module_to_exports=[
                    req_body.autom_frontend_root_path / 'lib/backend_api/',
                ],
            )
        )


class AutomProjectAPIFileEnumerator(AgentWorker):
    @classmethod
    def define_input_schema(cls) -> AutomSchema | None:
        return FileEnumeratorInput

    @classmethod
    def define_output_schema(cls) -> AutomSchema | None:
        return EnumeratedFiles

    def invoke(self, req: Request) -> Response:
        req_body: FileEnumeratorInput = req.body
        endpoints_dir = req_body.autom_backend_root_path / 'app/api/v1/endpoints'
        excluded_files = ["__init__.py", "token.py"]
        
        # iterate over all files in the endpoints directory except for the excluded files using rglob
        src_file_fullpaths = list(endpoints_dir.rglob('*.py'))
        src_file_fullpaths = [f for f in src_file_fullpaths if f.name not in excluded_files]
        
        return Response[EnumeratedFiles].from_worker(self).success(
            body=EnumeratedFiles(
                autom_backend_root_path=req_body.autom_backend_root_path,
                autom_frontend_root_path=req_body.autom_frontend_root_path,
                src_file_fullpaths=src_file_fullpaths,
            )
        )


class EnumeratorFileAPIConverterDispatchBridgeWorker(DispatchBridgeWorker):
    @classmethod
    def define_src_schema(cls) -> AutomSchema:
        return EnumeratedFiles

    @classmethod
    def define_dst_schema(cls) -> AutomSchema:
        return FileAPIConverterInput

    def dispatch(self, req: Request) -> dict[int, Response]:
        req_body: EnumeratedFiles = req.body
        batch_responses: dict[int, Response[FileAPIConverterInput]] = {}

        for i, src_file_fullpath in enumerate(req_body.src_file_fullpaths):
            batch_responses[i] = Response[FileAPIConverterInput].from_worker(self).success(
                body=FileAPIConverterInput(
                    src_file_fullpath=src_file_fullpath,
                    autom_backend_root_path=req_body.autom_backend_root_path,
                    autom_frontend_root_path=req_body.autom_frontend_root_path,
                )
            )

        return batch_responses
