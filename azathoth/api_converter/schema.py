from pathlib import Path
from typing import Literal, Optional

import inflection
from autom.engine import AutomSchema


class AutomProjectAPIConvertParams(AutomSchema):
    autom_backend_root_path: Path
    autom_frontend_root_path: Path


FileEnumeratorInput = AutomProjectAPIConvertParams


class EnumeratedFiles(AutomSchema):
    autom_backend_root_path: Path
    autom_frontend_root_path: Path
    src_file_fullpaths: list[Path]


class FileAPIConverterInput(AutomSchema):
    src_file_fullpath: Path
    autom_backend_root_path: Path
    autom_frontend_root_path: Path


FileAPIConvertPlannerInput = FileAPIConverterInput


class FileAPIConvertPlan(AutomSchema):
    src_file_fullpath: Path
    autom_backend_root_path: Path
    autom_frontend_root_path: Path
    function_name_source_dict: dict[str, str]


class FunctionAPIConverterInput(AutomSchema):
    api_function_name: str
    api_function_source: str
    src_file_fullpath: Path
    dst_file_fullpath: Path
    autom_backend_root_path: Path
    autom_frontend_root_path: Path

import re
def camel_to_snake(name):
    # Converts camelCase to snake_case
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

class FunctionConvertKeyResult(AutomSchema):
    api_suffix_route: str
    has_response_model: bool
    response_model: Optional[str]
    has_body_data: bool
    body_data_type: Optional[str]
    has_current_user: bool
    other_params: Optional[dict[str, Literal["string", "number", "boolean"]]]

    def to_frontend_code(self, router_name: str, function_name: str) -> str:
        classes: list[str] = []
        # Handle response model classes
        if self.has_response_model:
            classes_in_response_model = self.response_model.split('[')
            classes.extend([class_name.strip(" ]") for class_name in classes_in_response_model])

        # Handle body data type classes
        if self.has_body_data:
            classes_in_body_data = self.body_data_type.split('[')
            classes.extend([class_name.strip(" ]") for class_name in classes_in_body_data])

        # Add response model to import section if present
        imports_section = ""
        if classes:
            imports_section = f'\nimport {{ {", ".join(classes)} }} from "@/types";'

        # Generate function parameters based on otherParams, has_body_data, and has_current_user
        params = []
        params_types = []
        if self.other_params:
            for param_name, param_type in self.other_params.items():
                param_ts_type = "string" if param_type == "string" else param_type
                params.append(param_name)
                params_types.append(f'{param_name}: {param_ts_type}')

        # Add bodyData and accessToken if necessary
        if self.has_body_data:
            params.append('bodyData')
            params_types.append(f'bodyData: {self.body_data_type}')
        if self.has_current_user:
            params.append('accessToken')
            params_types.append('accessToken: string')

        # Generate parameters for the function signature
        params_str = ', '.join(params)
        params_types_str = ', '.join(params_types)

        # Convert camelCase keys to snake_case for API route placeholders, or use plain route if no other_params
        if self.other_params:
            route_with_placeholders = self.api_suffix_route.format(**{camel_to_snake(param): f'${{{param}}}' for param in self.other_params})
        else:
            route_with_placeholders = self.api_suffix_route  # Use plain route if no parameters

        # Prepare authorization header if current user is required
        authorization_header = ""
        if self.has_current_user:
            authorization_header = '\n        "Authorization": `Bearer ${{accessToken}}`,'

        # Prepare body data part
        body_data_part = ""
        if self.has_body_data:
            body_data_part = '\n      body: JSON.stringify(bodyData),'

        # Ensure the response model uses <> for generic types instead of []
        response_model = self.response_model.replace('[', '<').replace(']', '>') if self.has_response_model else 'void'

        # Generate final code
        return f"""
"use server";

import {{ cache }} from "react";

import {{ BACKEND_API_URL }} from "@/config";{imports_section}

export const {inflection.camelize(function_name, uppercase_first_letter=False)} = cache(
  async ({{
    {params_str}
  }}: {{
    {params_types_str}
  }}): Promise<{response_model}> => {{
    const response = await fetch(`${{BACKEND_API_URL}}/{router_name}/{route_with_placeholders.strip('/')}`, {{
      method: "POST",
      headers: {{
        "Content-Type": "application/json",{authorization_header}
      }},{body_data_part}
    }});

    if (!response.ok) {{
      const errorData = await response.json();
      throw new Error(errorData?.detail);
    }}

    return await response.json();
  }}
);
""".strip() + '\n'
