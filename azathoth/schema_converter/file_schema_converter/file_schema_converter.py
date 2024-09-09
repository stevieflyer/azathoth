from autom.logger import autom_logger
from autom.official import HolderAgentWorker, IdentityBridgeWorker
from autom.engine import (
    Request, Response, BridgeWorker, PluggerWorker, AggregatorWorker,
    DispatchBridgeWorker, CollectPluggerWorker, AutomSchema, BatchRequestSchema,
    AutomGraph, Node, Link, GraphAgentWorker, Socket, SocketCall, SocketRequestBody,
)

from azathoth.common import (
    PyFilePath, SplittedPyFileContent, TextSegments,
    PyImportsRemainsSplitter, TextRecursiveSegmentParamsAggregator, TextRecursiveSegmenter, FileContentAggregator,
)
from ..segment_schema_converter import SegmentSchemaConverter, SegmentSchemaConvertParams, ConvertedSchemaSegment
from .schema import ConvertedImportsContent, FileSchemaConvertParams
from .schema_import_converter import SchemaImportConvertParamsAggregator, SchemaImportConverter


class FileSchemaConverter(GraphAgentWorker):
    """The basic unit of Schema Attacher Agent.

    SchemaAttacherUnit translate only 1 schema file and attach it to the other schema file in another project.
    """
    @classmethod
    def define_graph(cls) -> AutomGraph:
        graph = AutomGraph()

        entry_node = Node.from_worker(HolderAgentWorker().with_schema(FileSchemaConvertParams))
        entry_descarte_aggregator_plugger = Link.from_worker(EntryDescartePlugger())
        entry_text_segmenter_aggregator_plugger = Link.from_worker(FileSchemaConvertParamsTextSegmenterPlugger())
        entry_exit_plugger = Link.from_worker(FileSchemaConvertParamsFileContentPlugger())
        entry_import_converter_aggregator_plugger = Link.from_worker(EntryImportConvertParamsPlugger())

        entry_py_splitter_bridge = Link.from_worker(FileSchemaConvertParamsPySplitterBridge())        
        py_splitter = Node.from_worker(PyImportsRemainsSplitter())
        py_splitter_import_converter_aggregator_plugger = Link.from_worker(PySplitterImportConvertParamsPlugger())

        import_converter_aggregator = Node.from_worker(SchemaImportConvertParamsAggregator())
        import_converter_aggregator_import_converter_bridge = Link.from_worker(IdentityBridgeWorker())
        import_converter = Node.from_worker(SchemaImportConverter())
        import_converter_exit_plugger = Link.from_worker(ImportConverterFileContentPlugger())

        py_splitter_text_segmenter_plugger = Link.from_worker(PySplitterTextSegmenterPlugger())
        text_segmenter_aggregator = Node.from_worker(TextRecursiveSegmentParamsAggregator())
        text_segmenter_aggregator_text_segmenter_bridge = Link.from_worker(IdentityBridgeWorker())
        text_segmenter = Node.from_worker(TextRecursiveSegmenter())
        text_segmenter_descartes_aggregator_plugger = Link.from_worker(TextSegmentsDescartePlugger())
        descartes_aggregator = Node.from_worker(DescarteDataAggregator())
        descartes_aggregator_segment_converter_dispatch_bridge = Link.from_worker(DescarteSegmentConverterDispatchBridge())
        segment_converter = Node.from_worker(SegmentSchemaConverter())
        segment_converter_exit_collect_plugger = Link.from_worker(SegmentConverterFileContentCollectPlugger())
        exit_aggregator = Node.from_worker(FileContentAggregator())

        graph.add_node(entry_node)
        graph.add_node(py_splitter)
        graph.add_node(import_converter_aggregator)
        graph.add_node(import_converter)
        graph.add_node(text_segmenter_aggregator)
        graph.add_node(text_segmenter)
        graph.add_node(descartes_aggregator)
        graph.add_node(segment_converter)
        graph.add_node(exit_aggregator)

        graph.plug(entry_node, descartes_aggregator, entry_descarte_aggregator_plugger)
        graph.plug(entry_node, text_segmenter_aggregator, entry_text_segmenter_aggregator_plugger)
        graph.plug(entry_node, exit_aggregator, entry_exit_plugger)
        graph.plug(entry_node, import_converter_aggregator, entry_import_converter_aggregator_plugger)
        graph.bridge(entry_node, py_splitter, entry_py_splitter_bridge)

        # (1) imports conversion
        graph.plug(py_splitter, import_converter_aggregator, py_splitter_import_converter_aggregator_plugger)
        graph.bridge(import_converter_aggregator, import_converter, import_converter_aggregator_import_converter_bridge)
        graph.plug(import_converter, exit_aggregator, import_converter_exit_plugger)

        # (2) remains conversion
        graph.plug(py_splitter, text_segmenter_aggregator, py_splitter_text_segmenter_plugger)
        graph.bridge(text_segmenter_aggregator, text_segmenter, text_segmenter_aggregator_text_segmenter_bridge)
        graph.plug(text_segmenter, descartes_aggregator, text_segmenter_descartes_aggregator_plugger)
        graph.bridge(descartes_aggregator, segment_converter, descartes_aggregator_segment_converter_dispatch_bridge)
        graph.plug(segment_converter, exit_aggregator, segment_converter_exit_collect_plugger)

        graph.set_entry_node(entry_node)
        graph.set_exit_node(exit_aggregator)

        return graph


class FileSchemaConvertParamsFileContentPlugger(PluggerWorker):
    @classmethod
    def define_input_schema(cls) -> AutomSchema | None:
        return FileSchemaConvertParams
    
    def invoke(self, req: Request) -> Response:
        req_body: FileSchemaConvertParams = req.body
        return Response[SocketRequestBody].from_worker(self).success(
            body=SocketRequestBody(
                calls=[
                    SocketCall(
                        socket_name='set_filepath',
                        data=req_body.dst_filepath,
                    )
                ]
            )
        )


class FileSchemaConvertParamsPySplitterBridge(BridgeWorker):
    @classmethod
    def define_input_schema(cls) -> AutomSchema | None:
        return FileSchemaConvertParams
    
    @classmethod
    def define_output_schema(cls) -> AutomSchema | None:
        return PyFilePath

    def invoke(self, req: Request) -> Response:
        req_body: FileSchemaConvertParams = req.body

        return Response[PyFilePath].from_worker(self).success(
            body=PyFilePath(filepath=req_body.src_filepath)
        )


class EntryImportConvertParamsPlugger(PluggerWorker):
    @classmethod
    def define_input_schema(cls) -> AutomSchema | None:
        return FileSchemaConvertParams

    def invoke(self, req: Request) -> Response:
        req_body: FileSchemaConvertParams = req.body

        return Response[SocketRequestBody].from_worker(self).success(
            body=SocketRequestBody(
                calls=[
                    SocketCall(
                        socket_name='set_src_filepath',
                        data=req_body.src_filepath,
                    ),
                    SocketCall(
                        socket_name='set_src_root_path',
                        data=req_body.src_root_path,
                    ),
                    SocketCall(
                        socket_name='set_dst_filepath',
                        data=req_body.dst_filepath,
                    ),
                    SocketCall(
                        socket_name='set_dst_root_path',
                        data=req_body.dst_root_path,
                    ),
                ]
            )
        )


class PySplitterImportConvertParamsPlugger(PluggerWorker):
    @classmethod
    def define_input_schema(cls) -> AutomSchema | None:
        return SplittedPyFileContent

    def invoke(self, req: Request) -> Response:
        req_body: SplittedPyFileContent = req.body
        
        return Response[SocketRequestBody].from_worker(self).success(
            body=SocketRequestBody(
                calls=[
                    SocketCall(
                        socket_name='set_imports_content',
                        data=req_body.imports_content,
                    )
                ]
            )
        )


class ImportConverterFileContentPlugger(PluggerWorker):
    @classmethod
    def define_input_schema(cls) -> AutomSchema | None:
        return ConvertedImportsContent

    def invoke(self, req: Request) -> Response:
        req_body: ConvertedImportsContent = req.body
        return Response[SocketRequestBody].from_worker(self).success(
            body=SocketRequestBody(
                calls=[
                    SocketCall(
                        socket_name='add_indexed_segment',
                        data={
                            0: req_body.converted_imports_content,
                        }
                    )
                ]
            )
        )


class PySplitterTextSegmenterPlugger(PluggerWorker):
    @classmethod
    def define_input_schema(cls) -> AutomSchema | None:
        return SplittedPyFileContent
    
    def invoke(self, req: Request) -> Response:
        req_body: SplittedPyFileContent = req.body
        return Response[SocketRequestBody].from_worker(self).success(
            body=SocketRequestBody(
                calls=[
                    SocketCall(
                        socket_name='set_original_text',
                        data=req_body.remains_content,
                    )
                ]
            )
        )


class FileSchemaConvertParamsTextSegmenterPlugger(PluggerWorker):
    @classmethod
    def define_input_schema(cls) -> AutomSchema | None:
        return FileSchemaConvertParams

    def invoke(self, req: Request) -> Response:
        req_body: FileSchemaConvertParams = req.body
        return Response[SocketRequestBody].from_worker(self).success(
            body=SocketRequestBody(
                calls=[
                    SocketCall(
                        socket_name='set_max_lines_per_segment',
                        data=req_body.max_lines_per_segment,
                    )
                ]
            )
        )


class DescarteData(AutomSchema):
    file_schema_convert_params: FileSchemaConvertParams
    text_segments: TextSegments


class DescarteDataAggregator(AggregatorWorker):
    @classmethod
    def define_output_schema(cls) -> AutomSchema | None:
        return DescarteData

    @classmethod
    def define_socket_list(cls) -> list[Socket]:
        return [
            Socket(
                name='set_file_schema_convert_params',
                input_type=FileSchemaConvertParams,
                socket_handler=cls._set_file_schema_convert_params,
            ),
            Socket(
                name='set_text_segments',
                input_type=TextSegments,
                socket_handler=cls._set_text_segments,
            )
        ]

    def _set_file_schema_convert_params(self, data: FileSchemaConvertParams):
        self._output_as_dict['file_schema_convert_params'] = data

    def _set_text_segments(self, data: TextSegments):
        self._output_as_dict['text_segments'] = data


class EntryDescartePlugger(PluggerWorker):
    @classmethod
    def define_input_schema(cls) -> AutomSchema | None:
        return FileSchemaConvertParams
    
    def invoke(self, req: Request) -> Response:
        req_body: FileSchemaConvertParams = req.body
        return Response[SocketRequestBody].from_worker(self).success(
            body=SocketRequestBody(
                calls=[
                    SocketCall(
                        socket_name='set_file_schema_convert_params',
                        data=req_body
                    )
                ]
            )
        )


class TextSegmentsDescartePlugger(PluggerWorker):
    @classmethod
    def define_input_schema(cls) -> AutomSchema | None:
        return TextSegments

    def invoke(self, req: Request) -> Response:
        req_body: TextSegments = req.body
        return Response[SocketRequestBody].from_worker(self).success(
            body=SocketRequestBody(
                calls=[
                    SocketCall(
                        socket_name='set_text_segments',
                        data=req_body
                    )
                ]
            )
        )


class DescarteSegmentConverterDispatchBridge(DispatchBridgeWorker):
    @classmethod
    def define_src_schema(cls) -> AutomSchema:
        return DescarteData

    @classmethod
    def define_dst_schema(cls) -> AutomSchema:
        return SegmentSchemaConvertParams

    def dispatch(self, req: Request) -> dict[int, Response]:
        req_body: DescarteData = req.body
        batch_responses: dict[int, Response[SegmentSchemaConvertParams]] = {}

        for i, segment in enumerate(req_body.text_segments.segments):
            batch_responses[i] = Response[SegmentSchemaConvertParams].from_worker(self).success(
                body=SegmentSchemaConvertParams(
                    src_repo_enum=req_body.file_schema_convert_params.src_repo_enum,
                    src_filepath=req_body.file_schema_convert_params.src_filepath,
                    src_root_path=req_body.file_schema_convert_params.src_root_path,
                    dst_repo_enum=req_body.file_schema_convert_params.dst_repo_enum,
                    dst_filepath=req_body.file_schema_convert_params.dst_filepath,
                    dst_root_path=req_body.file_schema_convert_params.dst_root_path,
                    segment=segment,
                )
            )
            autom_logger.info(f"[DescarteSegmentConverterDispatchBridge] dipatch response {i}: {batch_responses[i]}")

        return batch_responses


class SegmentConverterFileContentCollectPlugger(CollectPluggerWorker):
    @classmethod
    def define_src_schema(cls) -> AutomSchema:
        return ConvertedSchemaSegment

    def invoke(self, req: Request[BatchRequestSchema]) -> Response:
        req_body: BatchRequestSchema[ConvertedSchemaSegment] = req.body
        calls = []

        for i, req_item in req_body.batch_requests.items():
            req_item_body: ConvertedSchemaSegment = req_item.body
            calls.append(
                SocketCall(
                    socket_name='add_indexed_segment',
                    data={
                        i + 1: req_item_body.converted_schema
                    }
                )
            )

        return Response[SocketRequestBody].from_worker(self).success(
            body=SocketRequestBody(
                calls=calls
            )
        )
