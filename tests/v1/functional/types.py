import dataclasses
from typing import Annotated

UserType = Annotated[str, "user"]
HostType = Annotated[str, "host"]
PortType = Annotated[int, "port"]


@dataclasses.dataclass
class Config:
    user: str
    host: str
    port: int
