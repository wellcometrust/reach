import json

@attr.s
class BaseModel(object):

    def __init__(self):
        pass

    def from_json(self):
        pass

    def to_json(self):
        pass
