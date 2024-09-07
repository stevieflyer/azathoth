backend_system_prompt = '''
请你协助我将我的后端项目(基于 Python)中的 pydantic schema, enum, literal  等数据类型转换为前端项目(基于 TypeScript)中的 TypeScript type。

我先给你一些示例：

【例子 1】
【【输入】】
<src_file_relpath>
app/schemas/entities.py

<code_segment>
from datetime import datetime
from typing import Optional, Annotated

from pydantic import EmailStr, Field, StringConstraints, model_validator
from autom.engine.integration_auth import name_regexp, qualifier_regexp, IntegrationAuthSecretMeta
from autom.engine.project import qualifier_regexp, ProjectPublicity, ProjectRunnableStatus, ProjectGitStatus

from .base import MyBaseModel
from .enum import RegistryPublicity, IntegrationAuthStatusLiteral, SecretStatusLiteral, WorkerIntegrationAuthorizationLiteral


# User Related
class UserBase(MyBaseModel):
    """Base schema for User. Without hashed password field."""
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., description="User username")
    dev_enabled: bool = Field(False, description="Flag to indicate if user is enabled for development")
    dev_github_username: Optional[str] = Field(None, description="User's linked GitHub username")
    dev_developer_id: Annotated[
        Optional[str],
        StringConstraints(
            min_length=1,
            max_length=39,
            pattern=r"^[a-zA-Z0-9_]+$",
        )
    ] = Field(default=None, description="Username in the Autom system, should be unique and follow GitHub username conventions")
    avatar_url: str = Field(..., description="URL to user's avatar")
    created_at: datetime = Field(..., description="Date and time the user was created")
    updated_at: datetime = Field(..., description="Date and time the user was last updated")
    initialized: bool = Field(False, description="Flag to indicate if user has been initialized. Turn to `True` after user finished 'start-my-journey' page guidance.")
    is_admin: bool = Field(False, description="Flag to indicate if user is an admin")


class UserSafe(UserBase):
    """Schema for User without sensitive information."""
    id: int = Field(..., description="User ID in the database")

    @property
    def qualifier(self) -> str:
        if self.dev_developer_id:
            return self.dev_developer_id
        return f"explorer-{{self.id}}"


class User(UserSafe):
    """Schema for User with additional hashed password field."""
    hashed_password: str = Field(..., description="Hashed password of the user")

【【输出】】
import {{ ProjectPublicity, ProjectRunnableStatus, ProjectGitStatus, IntegrationAuthSecretMeta }} from "./autom_entities";
import {{ RegistryPublicity, IntegrationAuthStatusLiteral, SecretStatusLiteral, WorkerIntegrationAuthorizationLiteral }} from "./enum";

// User
export type UserBase = {{
  email: string;
  username: string;
  dev_enabled: boolean;
  dev_developer_id?: string;
  dev_github_username?: string;
  avatar_url: string;
  created_at: string;
  updated_at: string;
  initialized: boolean;
  is_admin: boolean;
}};

export type UserSafe = UserBase & {{
  id: number;
}};

export type User = UserSafe & {{
  hashed_password: string;
}};

【例子 1 结束】

【例子 2】

【【输入】】
<src_file_relpath>
app/schemas/entities.py

<code_segment>
# IntegrationAuthMeta Related
class BIntegrationAuthSecretMeta(IntegrationAuthSecretMeta):
    pass


class BIntegrationAuthMetaBriefBase(MyBaseModel):
    name: str = Field(..., pattern=name_regexp, description="Human readable name of the integration")
    qualifier: str = Field(..., pattern=qualifier_regexp, description="Unique identifier for the integration")
    description: str = Field("", description="The description of the integration.")
    external_link: Optional[str] = Field(None, description="The external link to the official website of the integration.")
    # other fields defined in backend
    icon_img: Optional[str] = Field(None, description="URL to the icon image of the integration")
    tags: list[str] = Field(default_factory=list, description="Tags of the integration")

【【输出】】
// IntegrationAuthMeta Related
export type BIntegrationAuthSecretMeta = IntegrationAuthSecretMeta;

export type BIntegrationAuthMetaBriefBase = {
  name: string;
  qualifier: string;
  description?: string; // default to ""
  external_link?: string; // default to None
  icon_img?: string; // default to None
  tags: string[]; // default to []
};

【例子 2 结束】

【例子 3】
【【输入】】
<src_file_relpath>
app/schemas/enum.py

<code_segment>
from enum import IntEnum
from typing import Literal

class RegistryPublicity(IntEnum):
    private = 0
    public = 1


IntegrationAuthStatusLiteral = Literal["none", "authorized", "expired", "unauthorized"]
【【输出】】
export enum RegistryPublicity {{
  private = 0,
  public = 1,
}}

export type IntegrationAuthStatusLiteral = "none" | "authorized" | "expired" | "unauthorized";
【例子 3 结束】

下面，轮到你了！请注意, 跟例子中唯一不同的一点要求是：我需要你以 json 的形式返回， 格式类似: {{ "converted_segment": "..." }}。

我再次重申你的工作职责：请你协助我将我的后端项目(基于 Python)中的 pydantic schema, enum, literal  等数据类型转换为前端项目(基于 TypeScript)中的 TypeScript type。

你应该从例子中已经知道了一些我要你完成这项工作的特别注意事项：

- 对于 Optional 的字段, 请总是使用 ? 语法将其标注为可选字段。（不允许使用 | undefined 这种含糊不清的写法）
- 请使用 typescript 中的 built-in type, 例如: string, number, Record, etc...对于 pydantic 中的各种 field, 例如： PositiveInt, EmailStr 等, 请将其转换为 typescript 中的基础类型, 例如: number, string 等。
- 对于请求体相关的 schema, 例如: **ReqBody, **Create, **Update 这种, 当其 pydantic schema 中有 default/default_factory(或者说可以不填的) 时, 在 typescript type 中请使用 ? 语法将其标注为可选字段(因为我在前端传参时实际可以不传), 并在其后注释 // default to ...
- 对于返回体相关的 schema, 例如: **Base, **Detail 这种, 有 default 值的则不应当使用 ?, 因为它总是会有一个值返回回来。
- 后端 pydantic schema 中的各种 field 信息以外的内容, 例如 model_validator, 其它方法等, 你都应当忽略，因为这不影响 typescript type 的生成。
- 如果你收到的代码中含有 import 语句, 请你将其中的**相对**路径 import(项目内 import 而非第三方库 import)转换为前端项目中的相对路径 import。
- 如果你收到的代码中不含有 import 语句, 请你生成的代码中也千万不要包含 import 语句! 并且你可以总是假设前端项目中已经有了这些 import 语句, 所有涉及到的你没看见的类型, 你都可以认为在前方已经定义过了可以直接使用。
- 如果你收到的代码里不含有任何需要转换的东西，都是无关的东西, 请直接返回 {{ "converted_segment": "" }}。
- 对于从 autom.engine.integration_auth 和 autom.engine.project 中 import 的内容, 请将其转换为前端项目中的相对路径 import, 并且 import 路径为 .autom_entities 或者 ../autom_entities(因为这两个第三方库的 schema 被放到了这个位置)。
- 对于所有的相对路径 import, 请使用完全相同的相对路径进行 import, 例如 from ./base, from ./enum, from ../entities, from ../base, from ../enum 等等。具体是使用 .. 还是 . 请与后端代码保持完全一致。
- 例子3中没有 import 语句, 你不需要生成 import 语句。但是如果例子 3 开头有 import 语句，你就必须按照上述注意事项考虑在生成的代码中包括 import 语句！
'''.strip()

user_input_promt = '''
【输入】
<src_file_relpath>
{src_file_relpath}

<code_segment>
{code_segment}

【输出】
'''.strip()


__all__ = [
    'user_input_promt',
    'backend_system_prompt',
]