from sqlalchemy import String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column

Base = declarative_base()


class Plugin(Base):
    """Database model for storing plugin information."""

    __tablename__ = "core_plugins"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant: Mapped[str] = mapped_column(String(32))

    name: Mapped[str] = mapped_column(String(32))
    version: Mapped[str] = mapped_column(String(16))

    menu_name: Mapped[str] = mapped_column(String(16))

    description: Mapped[str] = mapped_column(String(10_000))
    url: Mapped[str] = mapped_column(String(256))
    is_iframe: Mapped[bool] = mapped_column(default=False)
    is_autoinstalled: Mapped[bool] = mapped_column(default=False)

    def __repr__(self):
        return (
            f"<Plugin(id={self.id}, tenant='{self.tenant}', name='{self.name}', "
            f"version='{self.version}', menu_name='{self.menu_name}')>"
        )
