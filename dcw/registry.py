import docker

class DCWRegistry:
    def __init__(self, name: str, url: str, username: str = None, password: str = None) -> None:
        self.name = name
        self.url = url
        self.username = username
        self.password = password

