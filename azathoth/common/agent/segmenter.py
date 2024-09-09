from typing import Type
from autom.engine import Request, Response, AgentWorker, AggregatorWorker, Socket
from autom.engine.graph.base.worker import AutomSchema

from ..schema import FileRecursiveSegmentParams, TextSegments, TextRecursiveSegmentParams


# TODO: use langchain recursive text splitter in the future
class FileRecursiveSegmenter(AgentWorker):
    """File Segmenter to split a file into segments. User can specify `max_lines_per_segment` and `separators`.

    Segmenter will first split the file by separators recursively until each segment has less than `max_lines_per_segment`. Too short segments will be merged until the segment has at most `max_lines_per_segment` lines.
    """
    @classmethod
    def define_input_schema(cls):
        return FileRecursiveSegmentParams

    @classmethod
    def define_output_schema(cls):
        return TextSegments

    def invoke(self, req: Request) -> Response:
        req_body: FileRecursiveSegmentParams = req.body

        src_file_path = req_body.src_file_fullpath
        with open(src_file_path, 'r') as f:
            content = f.read()

        segments = recursive_segment_text(content, req_body.separators, req_body.max_lines_per_segment)
        return Response[TextSegments].from_worker(self).success(body=segments)


class TextRecursiveSegmenter(AgentWorker):
    """Text Segmenter to split a text into segments. User can specify `max_lines_per_segment` and `separators`.
    
    RecursiveSegmenter will first split the text by separators recursively until each segment has less than `max_lines_per_segment`. Too short segments will be merged until the segment has at most `max_lines_per_segment` lines.
    """
    @classmethod
    def define_input_schema(cls):
        return TextRecursiveSegmentParams

    @classmethod
    def define_output_schema(cls):
        return TextSegments

    def invoke(self, req: Request) -> Response:
        req_body: TextRecursiveSegmentParams = req.body
        segments = recursive_segment_text(req_body.original_text, req_body.separators, req_body.max_lines_per_segment)
        return Response[TextSegments].from_worker(self).success(body=segments)


class TextRecursiveSegmentParamsAggregator(AggregatorWorker):
    @classmethod
    def define_output_schema(cls) -> type[AutomSchema] | None:
        return TextRecursiveSegmentParams

    @classmethod
    def define_socket_list(cls) -> list[Socket]:
        return [
            Socket(
                name='set_max_lines_per_segment',
                input_type=int,
                socket_handler=cls._set_max_lines_per_segment,
            ),
            Socket(
                name='set_original_text',
                input_type=str,
                socket_handler=cls._set_original_text,
            )
        ]
    
    def _set_max_lines_per_segment(self, max_lines_per_segment: int):
        self._output_as_dict['max_lines_per_segment'] = max_lines_per_segment

    def _set_original_text(self, original_text: str):
        self._output_as_dict['original_text'] = original_text


def recursive_segment_text(text: str, separators: list[str], max_lines_per_segment: int) -> TextSegments:
    """
    Recursively segment the given text using the first separator in the list until
    each segment has at most `max_lines_per_segment`. Segments that are too small
    will be merged until they meet the line limit.

    TODO: Extend functionality to handle multiple separators.
    """
    separator: str = separators[0]  # TODO: Extend to handle multiple separators
    segments_raw = text.split(separator)
    segments = []
    current_segment = []
    current_lines = 0

    # Iterate over the raw segments
    for segment in segments_raw:
        lines_in_segment = segment.count('\n') + 1  # Calculate lines in this segment

        if current_lines + lines_in_segment > max_lines_per_segment:
            # If the current segment exceeds max_lines_per_segment, append the current_segment
            segments.append(separator.join(current_segment))
            current_segment = []
            current_lines = 0

        if lines_in_segment > max_lines_per_segment:
            print(f"Warning: A segment exceeds max_lines_per_segment with {lines_in_segment} lines.")

        # Add the segment and update line count
        current_segment.append(segment)
        current_lines += lines_in_segment

    # Append the final segment if any content remains
    if current_segment:
        segments.append(separator.join(current_segment))

    return TextSegments(
        n_segment=len(segments),
        segments=segments
    )


__all__ = [
    'FileRecursiveSegmenter',
    'TextRecursiveSegmenter',
    'TextRecursiveSegmentParamsAggregator',
]
