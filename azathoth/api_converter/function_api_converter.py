from autom.utils import SingleLLMUsage
from autom.official import BaseOpenAIWorker
from autom.engine import AgentWorker, AutomSchema, Request, Response

from azathoth.common import FileContent
from .schema import FunctionAPIConverterInput
from .prompt import function_api_converter_system_prompt, function_api_converter_user_input_prompt


class FunctionAPIConverter(BaseOpenAIWorker, AgentWorker):
    @classmethod
    def define_input_schema(cls) -> AutomSchema | None:
        return FunctionAPIConverterInput

    @classmethod
    def define_output_schema(cls) -> AutomSchema | None:
        return FileContent

    def invoke(self, req: Request) -> Response:
        from pydantic import BaseModel
        class Output(BaseModel):
            frontend_code: str

        req_body: FunctionAPIConverterInput = req.body
        api_function_source = req_body.api_function_source

        resp = Response[FileContent].from_worker(self)
        chat_completion = self.openai_client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": function_api_converter_system_prompt.format()},
                    {"role": "user", "content": function_api_converter_user_input_prompt.format(
                        src_filepath=req_body.src_file_fullpath.as_posix(),
                        api_function_source=api_function_source,
                        dst_filepath=req_body.dst_file_fullpath.as_posix(),
                    )},
                ],
                response_format=Output,
            )
        resp.add_llm_usage(SingleLLMUsage.from_openai_chat_completion(chat_completion))
        parsed = chat_completion.choices[0].message.parsed
        if parsed is None:
            raise RuntimeError(f"Failed to parse the response from OpenAI: {chat_completion.choices[0].message}. Request: {req}")

        resp.body = FileContent(
            filepath=req_body.dst_file_fullpath,
            content=parsed.frontend_code,
        )
        return resp.success()


__all__ = [
    'FunctionAPIConverter',
]
