import re

from autom.utils import SingleLLMUsage
from autom.official import BaseOpenAIWorker
from autom.engine import AgentWorker, AutomSchema, Request, Response

from azathoth.common import FileContent
from .schema import FunctionAPIConverterInput, FunctionConvertKeyResult
from .prompt import function_api_converter_system_prompt, function_api_converter_user_input_prompt


ignored_other_params = set(['db', 'body_data', 'current_user', 'weaviate_client', 'background_tasks'])


class FunctionAPIConverter(BaseOpenAIWorker, AgentWorker):
    @classmethod
    def define_input_schema(cls) -> AutomSchema | None:
        return FunctionAPIConverterInput

    @classmethod
    def define_output_schema(cls) -> AutomSchema | None:
        return FileContent

    def invoke(self, req: Request) -> Response:
        req_body: FunctionAPIConverterInput = req.body
        api_function_source = req_body.api_function_source
        src_relpath = req_body.src_file_fullpath.relative_to(req_body.autom_backend_root_path)
        match = re.search(r'app/api/v1/endpoints/(.+)\.py$', str(src_relpath))
        if match:
            router_name = match.group(1)
        else:
            raise RuntimeError(f"Failed to extract router name from source file path: {src_relpath}")

        resp = Response[FileContent].from_worker(self)
        chat_completion = self.openai_client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": function_api_converter_system_prompt.format()},
                    {"role": "user", "content": function_api_converter_user_input_prompt.format(
                        api_function_source=api_function_source,
                    )},
                ],
                response_format=FunctionConvertKeyResult,
            )
        resp.add_llm_usage(SingleLLMUsage.from_openai_chat_completion(chat_completion))
        parsed = chat_completion.choices[0].message.parsed
        if parsed is None:
            raise RuntimeError(f"Failed to parse the response from OpenAI: {chat_completion.choices[0].message}. Request: {req}")

        if parsed.other_params:
            parsed.other_params = {k: v for k, v in parsed.other_params.items() if k not in ignored_other_params}

        resp.body = FileContent(
            filepath=req_body.dst_file_fullpath,
            content=parsed.to_frontend_code(
                router_name=router_name,
                function_name=req_body.api_function_name,
            ),
        )
        return resp.success()


__all__ = [
    'FunctionAPIConverter',
]
