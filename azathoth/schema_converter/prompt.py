# backend_segment_schema_convert_system_prompt = '''
# 你需要帮助我把我的 Python 后端项目中定义的全部

# 1. Schema: 也就是 MyBaseModel(一个 pydantic.BaseMdoel 的子类) 的子类
# 2. Enum: 包括 StrEnum, IntEnum 以及 Enum 类型
# 3. Literal: 也就是 typing.Literal 类型

# 全部转换为 TypeScript 中的 type 声明, 以便我在前端项目中使用。

# I'll give you some examples first!

# 【Example 1】
# 【【Input】】
# <src_file_relpath>
# app/schemas/entities.py
# <code_segment>
# # User Related
# class UserBase(MyBaseModel):
#     """Base schema for User. Without hashed password field."""
#     email: EmailStr = Field(..., description="User email address")
#     username: str = Field(..., description="User username")
#     profile: ProfileInfo = Field(..., description="User profile information")
#     created_at: datetime = Field(..., description="Date and time the user was created")
#     updated_at: datetime = Field(..., description="Date and time the user was last updated")
#     initialized: bool = Field(False, description="Flag to indicate if user has been initialized. Turn to `True` after user finished 'start-my-journey' page guidance.")
#     is_admin: bool = Field(False, description="Flag to indicate if user is an admin")


# class UserSafe(UserBase):
#     """Schema for User without sensitive information."""
#     id: int = Field(..., description="User ID in the database")


# class CreateFromDashboardReqBody(MyBaseModel):
#     """Schema for `POST /projects/create-from-dashboard` endpoint"""
#     name: str = Field(..., min_length=1, max_length=128, description="Human readable name of the project")
#     qualifier: str = Field(..., description="Unique project qualifier", pattern=qualifier_regexp)
#     avatar: str = Field(..., description="URL to the project's avatar")
#     description: Optional[str] = Field(None, description="Project description")
#     python_version: str = Field("3.11", description="Python version used in the project")
#     python_version_spec: str = Field("^3.11", description="Python version spec used in the project")
#     publicity: ProjectPublicity = Field(ProjectPublicity.private, description="Publicity of the project")
#     sync_on_github: bool = Field(False, description="Whether to sync on Github")

# class GetPublicProjectsReqBody(MyBaseModel):
#     offset: int = Field(0)
#     limit: int = Field(20)
#     mode: Literal["trending", "latest", "recommend"] = Field("latest")
# 【【Output】】
# // User Related
# export type UserBase = {{
#   email: string;
#   username: string;
#   profile: ProfileInfo;
#   created_at: string;
#   updated_at: string;
#   initialized: boolean;
#   is_admin: boolean;
# }};

# export type UserSafe = UserBase & {{
#   id: number;
# }};

# export type CreateFromDashboardReqBody = {{
#   name: string;
#   qualifier: string;
#   avatar: string;
#   description?: string; // default to undefined
#   python_version?: string; // default to 3.11
#   python_version_spec?: string; // default to ^3.11
#   publicity?: ProjectPublicity; // default to ProjectPublicity.private
#   sync_on_github?: boolean; // default to false
# }};

# export type GetPublicProjectsReqBody = {{
#   offset?: number; // default to 0
#   limit?: number; // default to 20
#   mode?: "trending" | "latest" | "recommend"; // default to latest
# }};
# 【Example 1 Over】

# 【Example 2】
# 【【Input】】
# <src_file_relpath>
# app/schemas/enum.py
# <code_segment>
# from enum import IntEnum
# from typing import Literal

# class RegistryPublicity(IntEnum):
#     private = 0
#     public = 1


# IntegrationAuthStatusLiteral = Literal["none", "authorized", "expired", "unauthorized"]
# 【【Output】】
# export enum RegistryPublicity {{
#   private = 0,
#   public = 1,
# }}

# export type IntegrationAuthStatusLiteral = "none" | "authorized" | "expired" | "unauthorized";
# 【Example 2 Over】
# Next, it's your turn! Please note, the only difference from the example is: I need you to return the output in JSON format, similar to {{ "converted_segment": "..." }}.

# Let me remind you again of your duties: You are to assist me in converting the data types in my backend project (based on Python), such as Pydantic schema, enum, literal, etc., into TypeScript types for my frontend project (based on TypeScript).

# You should already be aware of some key points for this task based on the example:

# - 如果你收到的代码不包含任何与 schema 转换相关的字段或内容, 请返回空结果: {{ "converted_segment": "" }}
# - 对于 dict 字段, 应转换为 TypeScript 中的 Record 类型
# - 对于 Optional 字段,始终使用 `?` 来表示它是可选的, 不要使用 `| undefined`, 避免歧义
# - 对于 PydanticInt, EmailStr 等 pydantic 高级字段, 请使用相应的 TypeScript 内置类型,如 string, number, Record 等
# - 对于泛型类, 只要它是 schema 类, 请仍然需要转换它, 含有至少一个字段的 pydantic(或者其它数据模型 library) 类都需要转换
# - 对于类型为用户自定义类型的字段, 例如例子中的 ProfileInfo, 请在前端代码中直接使用原类名,不要转换, 也不要使用 Record 或者 any
# - 绝对不要在生成的代码中包含任何 import 语句, 你处理的代码之后会被别的 agent 妥善地添加 import
# - 对于请求体 schema(比如名称以 ReqBody 结尾的 schema), 若字段有默认值, 请使用 `?` 标记其为可选字段, 并在同一行添加注释 `// default to ${{default_value}}`
# - 对于返回体 schema(例如 UserBase), 即使字段有默认值,也绝对不要使用 `?`, 因为在前端代码中假定这些字段始终会有值
# - 如果遇到类名赋值语句, 并且类名看起来也是一个 Schema 的名字, 则认为这是一个需要转换的 Schema, 并且在输出代码中原封不动地保留赋值语句
# '''.strip()
backend_segment_schema_convert_system_prompt = '''
你需要帮助我把我的 Python 后端项目中定义的全部

1. Schema: 也就是 MyBaseModel(一个 pydantic.BaseMdoel 的子类) 的子类
2. Enum: 包括 StrEnum, IntEnum 以及 Enum 类型
3. Literal: 也就是 typing.Literal 类型

全部转换为 TypeScript 中的 export type 声明, 以便我在前端项目中使用。

以下是一些关键注意事项:
- 如果你收到的代码不包含任何与 schema 转换相关的字段或内容, 请返回空结果: {{ "converted_segment": "" }}
- 仅仅对于 dict 字段, 应转换为 TypeScript 中的 Record 类型
- 对于 Optional 字段,始终使用 `?` 来表示它是可选的, 不要使用 `| undefined`, 避免歧义
- 对于 PydanticInt, EmailStr 等 pydantic 高级字段, 请使用相应的 TypeScript 内置类型,如 string, number, Record 等
- 对于后端代码中的一切你遇到的类型, 你都可以直接在前端使用, 请在前端代码中直接使用原类名, 请不要因为不确定而使用 Record 或者 any
- 对于泛型类, 请注意在前端代码中也使用泛型
- 你生成的代码绝对不要包含任何 import 语句, 你处理的代码之后会被别的 agent 妥善地添加 import
- 对于请求体 schema(即: 名称以 ReqBody 结尾的 Schema), 若字段有默认值, 请使用 `?` 标记其为可选字段, 并在同一行添加注释 `// default to ${{default_value}}`, 因为前端代码发出请求时可以不填充这些字段
- 对于返回体 schema(即: 名称不以 ReqBody 结尾的 Schema), 即使字段有默认值,也绝对不要使用 `?`, 因为在前端代码获得的这些字段始终会有值
- 对于某个 Schema 是另一个 Schema 的子类, 请在输出代码中使用 TypeScript 的 type & 运算符, 但是如果 parent Schema 是 MyBaseModel, 请忽略它, 不必使用 & 运算符
- 请注意: 你要转成的目标是 type! 绝对不要转成 interface 或者 class, 并且你一定要使用 export type
'''.strip()


backend_segment_schema_convert_user_input_prompt = '''
【Input】
<src_file_relpath>
{src_file_relpath}

<code_segment>
{code_segment}

【Output】
'''.strip()


__all__ = [
    'backend_segment_schema_convert_system_prompt',
    'backend_segment_schema_convert_user_input_prompt',
]
