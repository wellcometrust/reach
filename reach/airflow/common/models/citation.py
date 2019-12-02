import attr

from .base import BaseModel

@attrs
class ModelCitation(BaseModel):
    document_id = attr.ib()
    document_title = attr.ib()
    reference_id = attr.ib()
    extracted_title = attr.ib()
    matched_title = attr.ib()
    similarity = attr.ib()
    match_algorithm = attr.ib()



