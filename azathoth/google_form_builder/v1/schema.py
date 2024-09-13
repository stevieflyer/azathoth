from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from autom import AutomSchema, AutomField, autom_registry


class QuestionaireDesignRequirement(AutomSchema):
    user_requirement: str = AutomField(
        ...,
        description="User requirement on the form design",
    )


class Item(AutomSchema):
    """An Item is a single question or piece of content in a form.
    
    Here, in version 1, it is a Option Question.
    """
    index: int = AutomField(
        ...,
        description="Index of the item, starting from 0.",
    )
    is_multiple_choice: bool = AutomField(
        ...,
        description="Whether the item is a multiple choice question",
    )
    question_body: str = AutomField(
        ...,
        description="The question body",
    )
    choices: list[str] = AutomField(
        ...,
        description="The choices for the question, each choice is a string",
    )

    def to_google_forms_api_item(self):
        """Convert the Item to a Google Forms API item create object
        
        Returns:
            dict: The Google Forms API item create object
        """
        return {
            "item": {
                "title": self.question_body,
                "questionItem": {
                    "question": {
                        "required": True,
                        "choiceQuestion": {
                            "type": "RADIO" if not self.is_multiple_choice else "CHECKBOX",
                            "options": [{"value": choice} for choice in self.choices],
                            "shuffle": False,
                        },
                    }
                },
            },
            "location": {"index": self.index},
        }


@autom_registry(is_internal=False)
class QuestionaireDesign(AutomSchema):
    title: str
    description: str
    items: list[Item]

    def create_google_form(self, access_token: str):
        """Dump the FormDesign to a Google Form

        Args:
            access_token (str): The access token to access Google Forms API
        """
        form_service = build('forms', 'v1', credentials=Credentials(token=access_token))

        new_form = {
            "info": {
                "title": self.title,
                "documentTitle": self.title,
            }
        }
        new_questions = {
            "requests": [
                {
                    "createItem": item.to_google_forms_api_item()
                }
                for item in self.items
            ]
        }

        try:
            result = form_service.forms().create(body=new_form).execute()
        except Exception as e:
            raise RuntimeError(f"Failed to create the form: {e}. Request body: {new_form}")
        try:
            form_service.forms().batchUpdate(formId=result["formId"], body=new_questions).execute()
        except Exception as e:
            raise RuntimeError(f"Failed to add questions to the form: {e}. Request body: {new_questions}")

        return GoogleFormsCreateFormResponse.model_validate(result)


@autom_registry(is_internal=False)
class GoogleFormsInfo(AutomSchema):
    title: str
    documentTitle: str


@autom_registry(is_internal=False)
class GoogleFormsCreateFormResponse(AutomSchema):
    formId: str
    info: GoogleFormsInfo
    settings: dict
    revisionId: str
    responderUri: str
    
    @property
    def edit_url(self):
        return f'https://docs.google.com/forms/d/{self.formId}/edit'

    @property
    def respond_url(self):
        return self.responderUri


__all__ = [
    'QuestionaireDesignRequirement',
    'QuestionaireDesign',
    'Item',
    'GoogleFormsInfo',
    'GoogleFormsCreateFormResponse',
]
