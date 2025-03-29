import datetime

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from ._base import Base
from ._metagraphblock import MetagraphBlock


class NeuronRegistration(Base):
    __tablename__ = 'neuronregistrations'

    block: Mapped[int] = mapped_column(
        ForeignKey(MetagraphBlock.block),
        nullable=False,
        name="block"
    )

    coldkey: Mapped[str] = mapped_column(
        String,
        index=True,
        nullable=False,
        name="coldkey"
    )

    hotkey: Mapped[str] = mapped_column(
        String,
        index=True,
        nullable=False,
        name="hotkey"
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        name="created_at"
    )

    uid: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        nullable=False,
        name="uid"
    )