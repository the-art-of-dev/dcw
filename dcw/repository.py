import enum
import git
import os


class DCWRepositoryType(enum.Enum):
    LOCAL_DIR = 'local-dir',
    GIT = 'git'

class DCWRepository:
    def __init__(self, name: str, url: str, type: DCWRepositoryType) -> None:
        self.name = name
        self.url = url
        self.type = type
        self.__local_path = self.__get_local_path()

    def __get_local_path(self):
        if self.type == DCWRepositoryType.GIT:
            return self.url.split('/').pop().strip('.git')
        elif self.type == DCWRepositoryType.LOCAL_DIR:
            return os.path.join(self.url)
        else:
            raise Exception(f'Repository type {type} not supported!')


    # def __get_git_repo(self):
    #     if type == DCWRepositoryType.GIT:
    #         return git.Repo.clone_from(self.url, self.__local_path)
    #     elif type == DCWRepositoryType.LOCAL_DIR:
    #         return git.Repo(self.__local_path)
    #     else:
    #         raise Exception(f'Repository type {type} not supported!')