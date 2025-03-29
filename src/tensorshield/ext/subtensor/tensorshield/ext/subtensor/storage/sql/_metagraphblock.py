import datetime

from sqlalchemy import text
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped

from ._base import Base


class MetagraphBlock(Base):
    __tablename__ = 'metagraphblocks'

    netuid: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        primary_key=True,
        name='netuid'
    )

    block: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        primary_key=True,
        name='block'
    )

    synced: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text('NOW'),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        name='synced'
    )