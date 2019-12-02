import attr

from .base import BaseModel

@attr.s
class Document(BaseModel):
    _id = attr.ib()
    hash = attr.ib()
    doc = attr.ib()
    organisation = attr.ib()


@attr.s
class PolicyDocMode(BaseModel):
    _id = attr.ib()
    doc = attr.ib()



