from uuid import UUID

from decimal import Decimal

from sqlalchemy import (
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .enums import AccountType, EntryType
from .mixins import UUIDPrimaryKeyMixin, TimestampMixin

class Base(DeclarativeBase):
    pass


class OrmAccount(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "accounts"

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    type: Mapped[AccountType] = mapped_column(
        PG_ENUM(AccountType, name="account_type"), nullable=False
    )

    entries: Mapped[list["OrmTransactionEntry"]] = relationship(
        back_populates="account", lazy="select"
    )


class OrmTransaction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "transactions"

    description: Mapped[str] = mapped_column(String(1000), nullable=False)

    entries: Mapped[list["OrmTransactionEntry"]] = relationship(
        back_populates="transaction", lazy="selectin"
    )


class OrmTransactionEntry(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "transaction_entries"

    transaction_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    type: Mapped[EntryType] = mapped_column(
        PG_ENUM(EntryType, name="entry_type"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    transaction: Mapped["OrmTransaction"] = relationship(back_populates="entries")
    account: Mapped["OrmAccount"] = relationship(back_populates="entries")
