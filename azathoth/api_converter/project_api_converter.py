from autom.engine import (
    AutomSchema, Request, Response, SocketCall, SocketRequestBody,
    AgentWorker, PluggerWorker, DispatchBridgeWorker, GraphAgentWorker, AutomGraph, Node, Link,
)
from autom import autom_registry
from autom.official import HolderAgentWorker, IdentityBridgeWorker, NullPlugger

from azathoth.common import (
    TSExportHelperInputAggregator, FilesDumper,
    FilesContentFilesContentCollectPlugger, FilesContentAggregator, TSExportHerlper, FilesContentFilesContentPlugger,
)
from .file_api_converter import FileAPIConverter
from .schema import AutomProjectAPIConvertParams, EnumeratedFiles, FileAPIConverterInput, FileEnumeratorInput


class InnerAPIConverter(GraphAgentWorker):
    @classmethod
    def define_graph(cls) -> AutomGraph:
        graph = AutomGraph()

        entry_node = Node.from_worker(HolderAgentWorker().with_schema(AutomProjectAPIConvertParams))
        entry_enumerator_bridge = Link.from_worker(IdentityBridgeWorker())
        enumerator = Node.from_worker(AutomProjectAPIFileEnumerator())
        enumerator_file_api_converter_dispatch_bridge = Link.from_worker(EnumeratorFileAPIConverterDispatchBridgeWorker())
        file_api_converter = Node.from_worker(FileAPIConverter())
        file_api_converter_exit_collecto_plugger = Link.from_worker(FilesContentFilesContentCollectPlugger())
        files_content_aggregator = Node.from_worker(FilesContentAggregator())

        graph.add_node(entry_node)
        graph.add_node(enumerator)
        graph.add_node(file_api_converter)
        graph.add_node(files_content_aggregator)

        graph.bridge(entry_node, enumerator, entry_enumerator_bridge)
        graph.bridge(enumerator, file_api_converter, enumerator_file_api_converter_dispatch_bridge)
        graph.plug(file_api_converter, files_content_aggregator, file_api_converter_exit_collecto_plugger)

        graph.set_entry_node(entry_node)
        graph.set_exit_node(files_content_aggregator)

        return graph

 
@autom_registry(is_internal=False)
class AutomProjectAPIConverter(GraphAgentWorker):
    @classmethod
    def define_graph(cls) -> AutomGraph:
        graph = AutomGraph()

        entry_node = Node.from_worker(HolderAgentWorker().with_schema(AutomProjectAPIConvertParams))
        entry_inner_api_converter_bridge = Link.from_worker(IdentityBridgeWorker())
        inner_api_converter = Node.from_worker(InnerAPIConverter())
        inner_api_converter_api_files_dumper_bridge = Link.from_worker(IdentityBridgeWorker())
        api_files_dumper = Node.from_worker(FilesDumper())
        api_files_dumper_ts_export_aggregator_plugger = Link.from_worker(NullPlugger())
        api_files_dumper_exit_plugger = Link.from_worker(FilesContentFilesContentPlugger())
        entry_ts_export_aggregator_plugger = Link.from_worker(APIConverterTSExportHelperPlugger())
        ts_export_aggregator = Node.from_worker(TSExportHelperInputAggregator())
        ts_export_aggregator_ts_export_helper_bridge = Link.from_worker(IdentityBridgeWorker())
        ts_export_helper = Node.from_worker(TSExportHerlper())
        ts_export_helper_index_files_dumper_bridge = Link.from_worker(IdentityBridgeWorker())
        index_files_dumper = Node.from_worker(FilesDumper())
        index_files_dumper_exit_plugger = Link.from_worker(FilesContentFilesContentPlugger())
        exit_aggregator = Node.from_worker(FilesContentAggregator())

        graph.add_node(entry_node)
        graph.add_node(inner_api_converter)
        graph.add_node(api_files_dumper)        
        graph.add_node(ts_export_aggregator)
        graph.add_node(ts_export_helper)
        graph.add_node(index_files_dumper)
        graph.add_node(exit_aggregator)

        graph.bridge(entry_node, inner_api_converter, entry_inner_api_converter_bridge)
        graph.bridge(inner_api_converter, api_files_dumper, inner_api_converter_api_files_dumper_bridge)
        graph.plug(api_files_dumper, exit_aggregator, api_files_dumper_exit_plugger)
        graph.plug(api_files_dumper, ts_export_aggregator, api_files_dumper_ts_export_aggregator_plugger)
        graph.plug(entry_node, ts_export_aggregator, entry_ts_export_aggregator_plugger)
        graph.bridge(ts_export_aggregator, ts_export_helper, ts_export_aggregator_ts_export_helper_bridge)
        graph.bridge(ts_export_helper, index_files_dumper, ts_export_helper_index_files_dumper_bridge)
        graph.plug(index_files_dumper, exit_aggregator, index_files_dumper_exit_plugger)

        graph.set_entry_node(entry_node)
        graph.set_exit_node(exit_aggregator)

        return graph


class APIConverterTSExportHelperPlugger(PluggerWorker):
    @classmethod
    def define_input_schema(cls) -> AutomSchema | None:
        return AutomProjectAPIConvertParams

    def invoke(self, req: Request) -> Response:
        req_body: AutomProjectAPIConvertParams = req.body
        return Response[SocketRequestBody].from_worker(self).success(
            body=SocketRequestBody(
                calls=[
                    SocketCall(
                        socket_name="set_project_root_path",
                        data=req_body.autom_frontend_root_path,
                    ),
                    SocketCall(
                        socket_name="set_module_to_exports",
                        data=[req_body.autom_frontend_root_path / 'lib/apis/'],
                    ),
                ]
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
