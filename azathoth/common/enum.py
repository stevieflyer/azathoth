from enum import StrEnum


class ProgrammingLanguage(StrEnum):
    python = 'python'
    typescript = 'typescript'


class RepoEnum(StrEnum):
    AUTOM = 'autom'
    BACKEND = 'backend'
    FRONTEND = 'frontend'

    @property
    def repo_language(self) -> ProgrammingLanguage:
        if self == RepoEnum.AUTOM or self == RepoEnum.BACKEND:
            return ProgrammingLanguage.python
        else:
            return ProgrammingLanguage.typescript


__all__ = [
    'ProgrammingLanguage',
    'RepoEnum',
]
