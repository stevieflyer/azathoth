from pydantic import BaseModel
from autom.utils import SingleLLMUsage
from autom.official import BaseOpenAIWorker
from autom.engine import Request, Response, AgentWorker

from .schema import RepoEnum, SegmentSchemaConvertParams, ConvertedSchemaSegment
from .prompt import backend_segment_schema_convert_system_prompt, backend_segment_schema_convert_user_input_prompt


class SegmentSchemaConverter(BaseOpenAIWorker, AgentWorker):
    """Segment-Level Schema Converter

    Convert a segment of Python code(usually contains pydantic schema, enum, literal, etc.) to TypeScript type definitions.
    """
    @classmethod
    def define_input_schema(cls):
        return SegmentSchemaConvertParams

    @classmethod
    def define_output_schema(cls):
        return ConvertedSchemaSegment

    def invoke(self, req: Request) -> Response:
        class Output(BaseModel):
            converted_segment: str

        req_body: SegmentSchemaConvertParams = req.body
        resp = Response[ConvertedSchemaSegment].from_worker(self)
        if req_body.src_repo_enum == RepoEnum.BACKEND:
            chat_completion = self.openai_client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": backend_segment_schema_convert_system_prompt.format()},
                    {"role": "user", "content": backend_segment_schema_convert_user_input_prompt.format(
                        src_file_relpath=req_body.src_filepath.relative_to(req_body.src_root_path).as_posix(),
                        code_segment=req_body.segment,
                    )},
                ],
                response_format=Output,
            )
            resp.add_llm_usage(SingleLLMUsage.from_openai_chat_completion(chat_completion))
            resp.body = ConvertedSchemaSegment(
                converted_schema=chat_completion.choices[0].message.parsed.converted_segment,
            )
        else:
            raise NotImplementedError

        return resp


__all__ = [
    'SegmentSchemaConverter',
]
