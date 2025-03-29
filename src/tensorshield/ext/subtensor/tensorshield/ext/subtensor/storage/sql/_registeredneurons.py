from libtensorshield.types import SS58Address
from sqlalchemy import text
from sqlalchemy import Boolean
from sqlalchemy import Double
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped

from ._base import Base


class RegisteredNeuron(Base):
    __tablename__ = 'registeredneurons'

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text('false'),
        default=False,
        name='active'
    )

    coldkey: Mapped[SS58Address] = mapped_column(
        String,
        nullable=False,
        name='coldkey'
    )

    consensus: Mapped[float] = mapped_column(
        Double,
        nullable=False,
        server_default=text('0.0'),
        default=0.0,
        name='consensus'
    )

    dividends: Mapped[float] = mapped_column(
        Double,
        nullable=False,
        server_default=text('0.0'),
        default=0.0,
        name='dividends'
    )

    emission: Mapped[float] = mapped_column(
        Double,
        nullable=False,
        server_default=text('0.0'),
        default=0.0,
        name='emission'
    )

    host: Mapped[str] = mapped_column(
        String,
        nullable=False,
        server_default=text("'0.0.0.0'"),
        default='0.0.0.0',
        name='host'
    )

    hotkey: Mapped[SS58Address] = mapped_column(
        String,
        nullable=False,
        name='hotkey'
    )

    incentive: Mapped[float] = mapped_column(
        Double,
        nullable=False,
        server_default=text('0.0'),
        default=0.0,
        name='incentive'
    )

    netuid: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        primary_key=True,
        name='netuid'
    )

    port: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text('0'),
        default=0,
        name='port'
    )

    rank: Mapped[float] = mapped_column(
        Double,
        nullable=False,
        server_default=text('0.0'),
        default=0.0,
        name='rank'
    )

    stake: Mapped[float] = mapped_column(
        Double,
        nullable=False,
        server_default=text('0.0'),
        default=0.0,
        name='stake'
    )

    total_stake: Mapped[float] = mapped_column(
        Double,
        nullable=False,
        server_default=text('0.0'),
        default=0.0,
        name='total_stake'
    )

    trust: Mapped[float] = mapped_column(
        Double,
        nullable=False,
        server_default=text('0.0'),
        default=0.0,
        name='trust'
    )

    updated: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text('0'),
        default=0,
        name='updated'
    )

    validator_permit: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text('false'),
        default=False,
        name='validator_permit'
    )

    vrust: Mapped[float] = mapped_column(
        Double,
        nullable=False,
        server_default=text('0.0'),
        default=0.0,
        name='vrust'
    )

    uid: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        nullable=False,
        name='uid'
    )