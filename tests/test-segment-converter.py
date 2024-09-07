from pathlib import Path

from autom import Request
from autom.logger import autom_logger

from azathoth import SegmentSchemaConverterInput, SegmentSchemaConverter, RepoEnum

autom_logger.setLevel("INFO")

segment='''
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
        return f"explorer-{self.id}"


class User(UserSafe):
    """Schema for User with additional hashed password field."""
    hashed_password: str = Field(..., description="Hashed password of the user")


class UserCreate(MyBaseModel):
    """Schema for creating a new User."""
    email: EmailStr = Field(..., description="User's email address. Unique.")
    username: str
    hashed_password: str
    avatar_url: str = Field(..., description="URL to user's avatar.")


class UserUpdate(MyBaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    hashed_password: Optional[str] = None
    dev_enabled: Optional[bool] = None
    dev_developer_id: Annotated[
        Optional[str],
        StringConstraints(
            min_length=1,
            max_length=39,
            pattern=r"^[a-zA-Z0-9_]+$",
        )
    ] = None
    dev_github_username: Optional[str] = None
    avatar_url: Optional[str] = None
    initialized: Optional[bool] = None


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


class BIntegrationAuthMetaBase(BIntegrationAuthMetaBriefBase):
    secret_metas: list[BIntegrationAuthSecretMeta]

    @model_validator(mode='after')
    def ensure_non_empty_secret_metas(cls, v):
        if not v.secret_metas:
            raise ValueError('Integration must have at least one secret meta')
        return v

    def get_secret_meta_by_qualifier(self, qualifier: str) -> Optional[BIntegrationAuthSecretMeta]:
        for secret_meta in self.secret_metas:
            if secret_meta.qualifier == qualifier:
                return secret_meta
        return None


class BIntegrationAuthMetaBrief(BIntegrationAuthMetaBriefBase):
    id: int = Field(..., description="ID of the integration")


class BIntegrationAuthMeta(BIntegrationAuthMetaBase):
    id: int = Field(..., description="ID of the integration")


class BIntegrationAuthMetaBriefWithStatus(BIntegrationAuthMetaBrief):
    user_id: int = Field(..., description="ID of the user")
    status: IntegrationAuthStatusLiteral = Field(..., description="Status of the integration")


class BIntegrationAuthMetaCreate(BIntegrationAuthMetaBase):
    pass


# IntegrationAuthStatus Related
class IntegrationAuthStatusBase(MyBaseModel):
    user_id: int = Field(..., description="ID of the user")
    integration_id: int = Field(..., description="ID of the integration")
    status: IntegrationAuthStatusLiteral = Field(..., description="Status of the integration")


class IntegrationAuthStatus(IntegrationAuthStatusBase):
    id: int = Field(..., description="ID of the status")
    created_at: datetime = Field(..., description="Date and time the status was created")
    updated_at: datetime = Field(..., description="Date and time the status was last updated")


class IntegrationAuthStatusCreate(IntegrationAuthStatusBase):
    pass


# IntegrationAuthSecret Related
class IntegrationAuthSecretBase(MyBaseModel):
    user_id: int = Field(..., description="ID of the user")
    integration_id: int = Field(..., description="ID of the integration")
    qualifier: str = Field(..., pattern=qualifier_regexp, description="Unique identifier for the secret")
    # TODO: migrate `value`` from str to SecretStr in the future
    value: str = Field(..., description="Value of the secret")
    # TODO: migrate `refresh_token` from str to SecretStr in the future
    refresh_token: Optional[str] = Field(None, description="Refresh token of the secret")
    status: SecretStatusLiteral = Field("empty", description="Status of the secret, empty or filled")
    expires_at: Optional[datetime] = Field(None, description="Date and time the secret expires")


class IntegrationAuthSecretCreate(IntegrationAuthSecretBase):
    pass


class IntegrationAuthSecret(IntegrationAuthSecretBase):
    id: int = Field(..., description="ID of the secret")
    created_at: datetime = Field(..., description="Date and time the secret was created")
    updated_at: datetime = Field(..., description="Date and time the secret was last updated")



# Worker Integration Authorization Related
class WorkerIntegrationAuthorizationBase(MyBaseModel):
    user_id: int = Field(..., description="ID of the user")
    worker_meta_id: int = Field(..., description="ID of the worker")
    integration_auth_meta_id: int = Field(..., description="ID of the integration")
    worker_qualifier: str = Field(..., description="Qualifier of the worker")
    integration_qualifier: str = Field(..., description="Qualifier of the integration")
    status: WorkerIntegrationAuthorizationLiteral = Field("authorized", description="Status of the worker integration authorization")


class WorkerIntegrationAuthorizationCreate(WorkerIntegrationAuthorizationBase):
    pass


class WorkerIntegrationAuthorizationUpsert(WorkerIntegrationAuthorizationCreate):
    pass


class WorkerIntegrationAuthorizationUpdate(MyBaseModel):
    user_id: int = Field(None, description="ID of the user")
    worker_meta_id: int = Field(None, description="ID of the worker")
    integration_auth_meta_id: int = Field(None, description="ID of the integration")
    status: WorkerIntegrationAuthorizationLiteral = Field(None, description="Status of the worker integration authorization")


class WorkerIntegrationAuthorization(WorkerIntegrationAuthorizationBase):
    id: int = Field(..., description="ID of the worker integration authorization")
    created_at: datetime = Field(..., description="Date and time the worker integration authorization was created")
    updated_at: datetime = Field(..., description="Date and time the worker integration authorization was last updated")


# AutomProjectStatus Related
class AutomProjectStatusBase(MyBaseModel):
    project_id: int = Field(..., description="ID of the project")

    runnable_status: ProjectRunnableStatus = Field(ProjectRunnableStatus.new_born, description="Runnable status of the project")
    last_runnable_status: Optional[ProjectRunnableStatus] = Field(None, description="Last runnable status of the project")
    runnable_status_exception: Optional[str] = Field(None, description="Exception message for the last runnable status")

    git_status: Optional[ProjectGitStatus] = Field(None, description="Sync status of the project")
    last_git_status: Optional[ProjectGitStatus] = Field(None, description="Last git status of the project")
    git_status_exception: Optional[str] = Field(None, description="Exception message for the last git status")


class AutomProjectStatus(AutomProjectStatusBase):
    id: int = Field(..., description="ID of the status")


class AutomProjectStatusCreate(AutomProjectStatusBase):
    pass


class AutomProjectStatusUpdate(MyBaseModel):
    runnable_status: Optional[ProjectRunnableStatus] = Field(None, description="Runnable status of the project")
    last_runnable_status: Optional[ProjectRunnableStatus] = Field(None, description="Last runnable status of the project")
    runnable_status_exception: Optional[str] = Field(None, description="Exception message for the last runnable status")
    git_status: Optional[ProjectGitStatus] = Field(None, description="Sync status of the project")
    last_git_status: Optional[ProjectGitStatus] = Field(None, description="Last git status of the project")
    git_status_exception: Optional[str] = Field(None, description="Exception message for the last git status")


# AutomProject Related
class AutomProjectBrief(MyBaseModel):
    """Brief version of Autom Project"""
    id: int = Field(..., description="Project ID in the database")
    name: str = Field(..., min_length=1, max_length=128, description="Human readable name of the project")
    qualifier: str = Field(..., description="Unique project qualifier", pattern=qualifier_regexp)
    owner_id: int = Field(..., description="ID of the project owner")
    owner_qualifier: str = Field(..., description="Unique owner qualifier", pattern=qualifier_regexp)
    owner_email: str = Field(..., description="Email of the project owner")
    python_version: str = Field(default="3.11", description="Python version used in the project")
    python_version_spec: str = Field(default="^3.11", description="Python version spec used in the project")
    publicity: ProjectPublicity = Field(ProjectPublicity.private, description="Publicity of the project in Autom Community")
    github_repo_url: Optional[str] = Field(None, description="URL to the project's GitHub repository")
    is_env_initialized: bool = Field(False, description="Flag to indicate if the project environment is initialized")
    is_git_initialized: bool = Field(False, description="Flag to indicate if the project's GitHub repository is initialized")
    is_git_latest: bool = Field(False, description="Flag to indicate if the project's GitHub repository is latest")
    is_initial_populated: bool = Field(False, description="Flag to indicate if the project is initially populated")
    last_git_checkpoint_oid: Optional[str] = Field(None, description="OID of the last git checkpoint")
    last_git_checkpoint_title: Optional[str] = Field(None, description="Title of the last git checkpoint")
    # fields only in autom-backend
    created_at: datetime = Field(..., description="Date and time the project was created")
    updated_at: datetime = Field(..., description="Date and time the project was last updated")
    avatar: str = Field(..., description="URL to the project's avatar")


class AutomProjectCreate(MyBaseModel):
    """Schema for creating a new AutomProject."""
    name: str = Field(..., min_length=1, max_length=128, description="Human readable name of the project")
    qualifier: str = Field(..., description="Unique project qualifier", pattern=qualifier_regexp)
    description: Optional[str] = Field(None, description="Project description")
    owner_id: int = Field(..., description="ID of the project owner")
    owner_qualifier: str = Field(..., description="Unique owner qualifier", pattern=qualifier_regexp)
    owner_email: str = Field(..., description="Email of the project owner")
    python_version: str = Field(default="3.11", description="Python version used in the project")
    python_version_spec: str = Field(default="^3.11", description="Python version spec used in the project")
    publicity: ProjectPublicity = Field(ProjectPublicity.private, description="Publicity of the project in Autom Community")
    github_repo_url: Optional[str] = Field(None, description="URL to the project's GitHub repository")
    local_project_dir: Optional[str] = Field(None, description="The absolute path to the project directory on the backend server")
    avatar: str = Field(..., description="URL to the project's avatar")


class AutomProjectBase(AutomProjectCreate):
    """Base schema for AutomProject."""
    owner_qualifier: str = Field(..., description="Unique owner qualifier", pattern=qualifier_regexp)
    owner_email: str = Field(..., description="Email of the project owner")
    is_env_initialized: bool = Field(False, description="Flag to indicate if the project environment is initialized")
    is_git_initialized: bool = Field(False, description="Flag to indicate if the project's GitHub repository is initialized")
    is_git_latest: bool = Field(False, description="Flag to indicate if the project's GitHub repository is latest")
    is_initial_populated: bool = Field(False, description="Flag to indicate if the project is initially populated")
    last_git_checkpoint_oid: Optional[str] = Field(None, description="OID of the last git checkpoint")
    last_git_checkpoint_title: Optional[str] = Field(None, description="Title of the last git checkpoint")
    created_at: datetime = Field(..., description="Date and time the project was created")
    updated_at: datetime = Field(..., description="Date and time the project was last updated")


class AutomProject(AutomProjectBase):
    """Schema for AutomProject with additional ID field."""
    id: int = Field(..., description="Project ID in the database")


class AutomProjectWithStorage(AutomProject):
    local_project_dir: str = Field(..., description="The absolute path to the project directory on the backend server")


class AutomProjectWithOwner(AutomProject):
    owner: UserSafe


class AutomProjectWithOwnerAndStatus(AutomProjectWithOwner):
    status: AutomProjectStatus


class AutomProjectUpdate(MyBaseModel):
    """Schema for updating an existing AutomProject."""
    name: Optional[str] = Field(None, min_length=1, max_length=128, description="Human readable name of the project")
    avatar: Optional[str] = Field(None, description="URL to the project's avatar")
    description: Optional[str] = Field(None, description="Project description")
    python_version: Optional[str] = Field(None, description="Python version used in the project", examples=["3.11", "3.12"])
    python_version_spec: Optional[str] = Field(None, description="Python version spec used in the project")
    github_repo_url: Optional[str] = Field(None, description="URL to the project's GitHub repository. If None, means the project is not a Github project.")
    publicity: Optional[ProjectPublicity] = Field(None, description="Publicity of the project")


# AutomSchemaMeta Related
class AutomSchemaMetaBriefBase(MyBaseModel):
    autom_name: str = Field(..., description="Name of the schema")
    autom_version: str = Field(..., description="Version of the schema")
    autom_class_name: str = Field(..., description="Class name of the schema")
    autom_module_name: str = Field(..., description="Module name of the schema")
    autom_qualifier: str = Field(..., description="Qualifier of the schema")
    publicity: RegistryPublicity = Field(RegistryPublicity.private, description="Publicity of the schema")
    project_id: int = Field(..., description="ID of the project")


class AutomSchemaMetaBase(AutomSchemaMetaBriefBase):
    autom_description: str = Field(..., description="Description of the schema")
    autom_examples: list[dict] = Field(..., description="Examples of the schema")
    autom_model_schema_json: dict = Field(..., description="Model schema JSON of the schema")


class AutomSchemaMetaBrief(AutomSchemaMetaBriefBase):
    id: int = Field(..., description="ID of the schema")


class AutomSchemaMeta(AutomSchemaMetaBase):
    id: int = Field(..., description="ID of the schema")


class AutomSchemaMetaWithProject(AutomSchemaMeta):
    project: AutomProject


class AutomSchemaMetaCreate(AutomSchemaMetaBase):
    pass


# AutomWorkerMeta Related
class AutomWorkerMetaBriefBase(MyBaseModel):
    autom_name: str = Field(..., description="Name of the worker")
    autom_description: str = Field(..., description="Description of the worker")
    autom_version: str = Field(..., description="Version of the worker")
    autom_class_name: str = Field(..., description="Class name of the worker")
    autom_module_name: str = Field(..., description="Module name of the worker")
    autom_qualifier: str = Field(..., description="Qualifier of the worker")
    worker_function_type: str = Field(..., description="Function type of the worker")
    worker_topological_type: str = Field(..., description="Topological type of the worker")
    input_schema_cls_meta: Optional[dict] = Field(None, description="Input schema class meta of the worker")
    output_schema_cls_meta: Optional[dict] = Field(None, description="Output schema class meta of the worker")
    is_graph_worker: bool = Field(..., description="Flag to indicate if the worker is a graph worker")
    # fields besides `AutomWorkerMeta_`
    publicity: RegistryPublicity = Field(RegistryPublicity.private, description="Publicity of the worker")
    project_id: int = Field(..., description="ID of the project")


class AutomWorkerMetaBase(AutomWorkerMetaBriefBase):
    init_params_schema_json: dict = Field(..., description="Init params schema JSON of the worker")
    input_schema_cls_meta: Optional[dict] = Field(None, description="Input schema class meta of the worker")
    output_schema_cls_meta: Optional[dict] = Field(None, description="Output schema class meta of the worker")
    credential_requirements: dict = Field(..., description="Credential requirements of the worker")
    is_graph_worker: bool = Field(..., description="Flag to indicate if the worker is a graph worker")
    graph_topology: Optional[dict] = Field(None, description="Graph topology of the worker")


class AutomWorkerMetaBrief(AutomWorkerMetaBriefBase):
    id: int = Field(..., description="ID of the worker")


class AutomWorkerMeta(AutomWorkerMetaBase):
    id: int = Field(..., description="ID of the worker")


class AutomWorkerMetaWithProject(AutomWorkerMeta):
    project: AutomProject


class AutomWorkerMetaCreate(AutomWorkerMetaBase):
    pass



__all__ = [
    # User
    "UserBase",
    "UserSafe",
    "User",
    "UserCreate",
    "UserUpdate",
    # IntegrationAuthMeta
    "BIntegrationAuthSecretMeta",
    "BIntegrationAuthMetaBriefBase",
    "BIntegrationAuthMetaBase",
    "BIntegrationAuthMetaBrief",
    "BIntegrationAuthMeta",
    "BIntegrationAuthMetaBriefWithStatus",
    "BIntegrationAuthMetaCreate",
    # IntegrationAuthStatus
    "IntegrationAuthStatusBase",
    "IntegrationAuthStatus",
    "IntegrationAuthStatusCreate",
    # IntegrationAuthSecret
    "IntegrationAuthSecretBase",
    "IntegrationAuthSecret",
    "IntegrationAuthSecretCreate",
    # WorkerIntegrationAuthorization
    "WorkerIntegrationAuthorizationBase",
    "WorkerIntegrationAuthorizationCreate",
    "WorkerIntegrationAuthorizationUpdate",
    "WorkerIntegrationAuthorizationUpsert",
    "WorkerIntegrationAuthorization",
    # AutomProjectStatus
    "AutomProjectStatus",
    "AutomProjectStatusBase",
    "AutomProjectStatusCreate",
    "AutomProjectStatusUpdate",
    # AutomProject
    "AutomProject",
    "AutomProjectBase",
    "AutomProjectBrief",
    "AutomProjectCreate",
    "AutomProjectUpdate",
    "AutomProjectWithOwner",
    "AutomProjectWithOwnerAndStatus",
    "AutomProjectWithStorage",
    # AutomSchemaMeta
    "AutomSchemaMetaBrief",
    "AutomSchemaMeta",
    "AutomSchemaMetaBase",
    "AutomSchemaMetaWithProject",
    "AutomSchemaMetaCreate",
    # AutomWorkerMeta
    "AutomWorkerMetaBrief",
    "AutomWorkerMeta",
    "AutomWorkerMetaBase",
    "AutomWorkerMetaWithProject",
    "AutomWorkerMetaCreate",
]
'''


segment_schema_converter = SegmentSchemaConverter()
segment_schema_converter.fill_integration_auth_by_dict(values={
    "openai_chatgpt": {
        "api_key": "***"
    }
})
resp = segment_schema_converter.on_serve(
    req=Request[SegmentSchemaConverterInput](
        sender='user',
        body=SegmentSchemaConverterInput(
        src_repo_enum=RepoEnum.BACKEND,
        src_repo_root=Path("/home/steve/workspace/autom-backend"),
        src_file_relpath=Path("/home/steve/workspace/autom-backend/app/schema/entities.py"),
        dst_repo_enum=RepoEnum.FRONTEND,
        dst_repo_root=Path("/home/steve/workspace/autom-frontend"),
        dst_file_relpath=Path("/home/steve/workspace/autom-frontend/types/entities.ts"),
        segment=segment,
        )
    )
)

print(resp.model_dump_json(indent=4))