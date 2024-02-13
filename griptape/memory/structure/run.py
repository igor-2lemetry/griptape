import uuid
from attr import define, field, Factory
from griptape.mixins import SerializableMixin
from datetime import datetime


@define
class Run(SerializableMixin):
    id: str = field(default=Factory(lambda: uuid.uuid4().hex), kw_only=True, metadata={"serializable": True})
    added_at: datetime = field(default=Factory(lambda: datetime.now()), kw_only=True)
    input: str = field(kw_only=True, metadata={"serializable": True})
    output: str = field(kw_only=True, metadata={"serializable": True})
