from autom.logger import autom_logger
from autom.utils import SingleLLMUsage
from autom.official import BaseOpenAIWorker
from autom.engine import AutomSchema, AgentWorker, Request, Response

from .schema import FormDesignRequirements, FormDesign
from .prompt import form_builder_system_prompt, form_builder_user_input_prompt


class GoogleFormBuilder(BaseOpenAIWorker, AgentWorker):
    @classmethod
    def define_input_schema(cls) -> AutomSchema | None:
        return FormDesignRequirements

    @classmethod
    def define_output_schema(cls) -> AutomSchema | None:
        return FormDesign

    def invoke(self, req: Request) -> Response:
        req_body: FormDesignRequirements = req.body

        resp = Response[FormDesign].from_worker(self)
        chat_completion = self.openai_client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": form_builder_system_prompt.format()},
                    {"role": "user", "content": form_builder_user_input_prompt.format(
                        user_requirement=req_body.user_requirement,
                    )},
                ],
                response_format=FormDesign,
            )
        resp.add_llm_usage(SingleLLMUsage.from_openai_chat_completion(chat_completion))
        resp.body = chat_completion.choices[0].message.parsed
        if resp.body is None:
            raise RuntimeError(f"Failed to parse the response from OpenAI chat completion: {chat_completion}")
        try:
            resp_body: FormDesign = resp.body
            autom_logger.info(f"[GoogleFormBuilder] Form Design accomeplished! Pushing to Google Forms...")
            form_create_response = resp_body.to_google_form(
                access_token=self.integration_auth_manager.get(
                    integration_qualifier='google_forms',
                    secret_qualifier='api_key',
                    required=True,
                )
            )
            autom_logger.info(f"[GoogleFormBuilder] Form created successfully! Response Url: {form_create_response.respond_url}, or edit it at {form_create_response.edit_url}")
        except Exception as e:
            autom_logger.error(f"[GoogleFormBuilder] Failed to push the form to Google Forms: {e}")
            raise e

        return resp.success()


__all__ = [
    'GoogleFormBuilder',
]
