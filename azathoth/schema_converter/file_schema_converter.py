from autom.official import HolderAgentWorker
from autom.engine import (
    DispatchBridgeWorker, CollectPluggerWorker, AutomSchema, BatchRequestSchema,
    Request, Response, AgentWorker, BridgeWorker, PluggerWorker, AggregatorWorker,
    AutomGraph, Node, Link, GraphAgentWorker, Socket, SocketCall, SocketRequestBody,
)

from .schema import *
from .segment_schema_converter import SegmentSchemaConverter


# File Schema Converter
class FileSchemaConverterOutputAggregator(AggregatorWorker):
    @classmethod
    def define_output_schema(cls):
        return FileSchemaConverterOutput

    @classmethod
    def define_socket_list(cls) -> list[Socket]:
        return [
            Socket(
                name='set_by_file_schema_converter_input',
                input_type=FileSchemaConverterInput,
                socket_handler=cls._set_by_file_schema_converter_input
            ),
            Socket(
                name='set_src_file_content',
                input_type=str,
                socket_handler=cls._set_src_file_content
            ),
            Socket(
                name='append_to_dst_file_content',
                input_type=dict,
                socket_handler=cls._add_dst_file_content
            )
        ]

    def _set_by_file_schema_converter_input(self, data: FileSchemaConverterInput):
        for key, value in data.model_dump().items():
            self._output_as_dict[key] = value

    def _set_src_file_content(self, data: str):
        self._output_as_dict['src_file_content'] = data

    def _add_dst_file_content(self, data: dict[int, str]):
        if 'dst_file_content_dict' not in self._output_as_dict:
            self._output_as_dict['dst_file_content_dict'] = {}
        self._output_as_dict['dst_file_content_dict'].update(data)
    
    def build_output_from_dict(self):
        output_schema = self.output_schema
        self._output_as_dict['dst_file_content'] = '\n\n'.join([content for _, content in sorted(self._output_as_dict['dst_file_content_dict'].items())])
        self._output_as_dict.pop('dst_file_content_dict')
        return output_schema.model_validate(self._output_as_dict)


class EntryFileSegmenterBridgeWorker(BridgeWorker):
    @classmethod
    def define_input_schema(cls) -> AutomSchema | None:
        return FileSchemaConverterInput

    @classmethod
    def define_output_schema(cls) -> AutomSchema | None:
        return FileSegmenterInput

    def invoke(self, req: Request) -> Response:
        req_body: FileSchemaConverterInput = req.body
        return Response[FileSegmenterInput].from_worker(self).success(
            body=FileSegmenterInput(
                src_repo_enum=req_body.src_repo_enum,
                src_repo_root=req_body.src_repo_root,
                src_file_relpath=req_body.src_file_relpath,
                dst_repo_enum=req_body.dst_repo_enum,
                dst_repo_root=req_body.dst_repo_root,
                dst_file_relpath=req_body.dst_file_relpath,
                max_lines_per_segment=512
            )
        )


class FileSchemaConverterEntryExitPluggerWorker(PluggerWorker):
    @classmethod
    def define_input_schema(cls) -> type[AutomSchema] | None:
        return FileSchemaConverterInput
    
    def invoke(self, req: Request) -> Response:
        req_body: FileSchemaConverterInput = req.body
        src_file_fullpath = req_body.src_file_fullpath
        if not src_file_fullpath.exists() or not src_file_fullpath.is_file():
            raise FileNotFoundError(f"Source file not found or invalid: {src_file_fullpath}")
        with open(req_body.src_file_fullpath, 'r') as f:
            src_file_content = f.read()

        return Response[SocketRequestBody].from_worker(self).success(
            body=SocketRequestBody(
                calls=[
                    SocketCall(
                        socket_name='set_by_file_schema_converter_input',
                        data=req_body,
                    ),
                    SocketCall(
                        socket_name='set_src_file_content',
                        data=src_file_content,
                    )
                ]
            )
        )


class SegmenterSegmentConverterDispatchBridgeWorker(DispatchBridgeWorker):
    @classmethod
    def define_src_schema(cls) -> AutomSchema:
        return FileSegmenterOutput

    @classmethod
    def define_dst_schema(cls) -> AutomSchema:
        return SegmentSchemaConverterInput
    
    def dispatch(self, req: Request) -> dict[int, Response]:
        req_body: FileSegmenterOutput = req.body
        batch_responses: dict[int, Response[SegmentSchemaConverterInput]] = {}

        for i, segment in enumerate(req_body.segments):
            batch_responses[i] = Response[SegmentSchemaConverterInput].from_worker(self).success(
                body=SegmentSchemaConverterInput(
                    src_repo_enum=req_body.src_repo_enum,
                    src_repo_root=req_body.src_repo_root,
                    src_file_relpath=req_body.src_file_relpath,
                    dst_repo_enum=req_body.dst_repo_enum,
                    dst_repo_root=req_body.dst_repo_root,
                    dst_file_relpath=req_body.dst_file_relpath,
                    segment=segment,
                )
            )

        return batch_responses


class SegmentConverterExitCollectPluggerWorker(CollectPluggerWorker):
    @classmethod
    def define_src_schema(cls) -> AutomSchema:
        return SegmentSchemaConverterOutput

    def invoke(self, req: Request[BatchRequestSchema]) -> Response:
        req_body: BatchRequestSchema[SegmentSchemaConverterOutput] = req.body
        calls = []
        for key, req_item in req_body.batch_requests.items():
            calls.append(
                SocketCall(
                    socket_name='append_to_dst_file_content',
                    data={key: req_item.body.converted_segment}
                )
            )
        return Response[SocketRequestBody].from_worker(self).success(body=SocketRequestBody(calls=calls))


class FileSchemaConverter(GraphAgentWorker):
    """The basic unit of Schema Attacher Agent.
    
    SchemaAttacherUnit translate only 1 schema file and attach it to the other schema file in another project.
    """
    @classmethod
    def define_graph(cls) -> AutomGraph:
        graph = AutomGraph()
        
        entry_node = Node.from_worker(HolderAgentWorker().with_schema(FileSchemaConverterInput))
        entry_exit_plugger = Link.from_worker(FileSchemaConverterEntryExitPluggerWorker())
        entry_fileSegmenter_bridge = Link.from_worker(EntryFileSegmenterBridgeWorker())
        file_segmenter = Node.from_worker(FileSegmenter())
        segmenter_converter_dispatch_bridge = Link.from_worker(SegmenterSegmentConverterDispatchBridgeWorker())
        segment_converter = Node.from_worker(SegmentSchemaConverter())
        convert_exit_collect_plugger = Link.from_worker(SegmentConverterExitCollectPluggerWorker())
        exit_aggregator = Node.from_worker(FileSchemaConverterOutputAggregator())

        graph.add_node(entry_node)
        graph.add_node(file_segmenter)
        graph.add_node(segment_converter)
        graph.add_node(exit_aggregator)
        
        graph.plug(entry_node, exit_aggregator, entry_exit_plugger)
        graph.bridge(entry_node, file_segmenter, entry_fileSegmenter_bridge)
        graph.bridge(file_segmenter, segment_converter, segmenter_converter_dispatch_bridge)
        graph.plug(segment_converter, exit_aggregator, convert_exit_collect_plugger)

        graph.set_entry_node(entry_node)
        graph.set_exit_node(exit_aggregator)

        return graph


class FileSegmenter(AgentWorker):
    @classmethod
    def define_input_schema(cls):
        return FileSegmenterInput

    @classmethod
    def define_output_schema(cls):
        return FileSegmenterOutput

    def invoke(self, req: Request) -> Response:
        req_body: FileSegmenterInput = req.body
        
        # Read the source file
        src_file_path = req_body.src_file_fullpath
        with open(src_file_path, 'r') as f:
            content = f.read()

        # Split the content by the separator '\n\n'
        segments_raw = content.split('\n\n')
        segments = []
        current_segment = []
        current_lines = 0

        # Iterate over the raw segments
        for segment in segments_raw:
            lines_in_segment = segment.count('\n') + 1  # Calculate lines in this segment

            if current_lines + lines_in_segment > req_body.max_lines_per_segment:
                # If the current segment exceeds max_lines_per_segment, append the current_segment
                segments.append('\n\n'.join(current_segment))
                current_segment = []  # Start a new segment
                current_lines = 0

            if lines_in_segment > req_body.max_lines_per_segment:
                print(f"Warning: A segment exceeds max_lines_per_segment with {lines_in_segment} lines.")
            
            # Add the segment and update line count
            current_segment.append(segment)
            current_lines += lines_in_segment

        # Append the final segment if any content remains
        if current_segment:
            segments.append('\n\n'.join(current_segment))

        # Create the response
        output = FileSegmenterOutput(
            src_repo_enum=req_body.src_repo_enum,
            src_repo_root=req_body.src_repo_root,
            src_file_relpath=req_body.src_file_relpath,
            dst_repo_enum=req_body.dst_repo_enum,
            dst_repo_root=req_body.dst_repo_root,
            dst_file_relpath=req_body.dst_file_relpath,
            max_lines_per_segment=req_body.max_lines_per_segment,
            n_segment=len(segments),
            segments=segments
        )

        return Response[FileSegmenterOutput].from_worker(self).success(body=output)
