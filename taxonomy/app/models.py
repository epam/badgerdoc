from typing import Callable
from uuid import uuid4

from sqlalchemy import (
    VARCHAR,
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy_utils import Ltree, LtreeType

from app.database import Base
from app.errors import CheckFieldError


def default_tree(column_name: str) -> Callable:
    def default_function(context) -> str:
        return Ltree(f"{context.current_parameters.get(column_name)}")

    return default_function


class AssociationTaxonomyJob(Base):
    __tablename__ = "association_taxonomy_job"
    __table_args__ = (
        ForeignKeyConstraint(
            ["taxonomy_id", "taxonomy_version"],
            ["taxonomy.id", "taxonomy.version"],
        ),
    )
    taxonomy_id = Column(VARCHAR)
    taxonomy_version = Column(Integer)

    taxonomy = relationship(
        "Taxonomy",
        foreign_keys="[AssociationTaxonomyJob.taxonomy_id, "
        "AssociationTaxonomyJob.taxonomy_version]",
        back_populates="jobs",
    )
    job_id = Column(VARCHAR, primary_key=True)


class AssociationTaxonomyCategory(Base):
    __tablename__ = "association_taxonomy_category"
    __table_args__ = (
        ForeignKeyConstraint(
            ["taxonomy_id", "taxonomy_version"],
            ["taxonomy.id", "taxonomy.version"],
        ),
    )
    taxonomy_id = Column(VARCHAR, primary_key=True)
    taxonomy_version = Column(Integer, primary_key=True)

    taxonomy = relationship(
        "Taxonomy",
        foreign_keys="[AssociationTaxonomyCategory.taxonomy_id, "
        "AssociationTaxonomyCategory.taxonomy_version]",
        back_populates="categories",
    )
    category_id = Column(VARCHAR, primary_key=True)


class Taxonomy(Base):
    __tablename__ = "taxonomy"

    id = Column(VARCHAR, primary_key=True, default=lambda: uuid4().hex)
    name = Column(VARCHAR, nullable=False)
    version = Column(Integer, primary_key=True)
    tenant = Column(VARCHAR, nullable=True)
    categories = relationship(
        "AssociationTaxonomyCategory",
        back_populates="taxonomy",
    )
    latest = Column(Boolean, nullable=False)
    jobs = relationship("AssociationTaxonomyJob", back_populates="taxonomy")
    taxons = relationship("Taxon", back_populates="taxonomy")


class Taxon(Base):
    __tablename__ = "taxon"

    id = Column(VARCHAR, primary_key=True, default=lambda: uuid4().hex)
    name = Column(VARCHAR, nullable=False)
    tenant = Column(VARCHAR, nullable=True)
    taxonomy_id = Column(VARCHAR)
    taxonomy_version = Column(Integer)
    taxonomy = relationship(
        "Taxonomy",
        foreign_keys="[Taxon.taxonomy_id, Taxon.taxonomy_version]",
        back_populates="taxons",
    )
    parent_id = Column(
        VARCHAR,
        ForeignKey("taxon.id", ondelete="cascade"),
        CheckConstraint("id != parent_id", name="self_parent_id_const"),
        nullable=True,
        index=True,
    )
    parent = relationship(
        "Taxon",
        remote_side=[id],
    )
    tree = Column(LtreeType, nullable=True, default=default_tree("id"))

    __table_args__ = (
        Index("index_taxon_tree", tree, postgresql_using="gist"),
        ForeignKeyConstraint(
            ["taxonomy_id", "taxonomy_version"],
            ["taxonomy.id", "taxonomy.version"],
        ),
    )

    @validates("id")
    def validate_id(self, key, id_):
        if id_ and not id_.replace("_", "").isalnum():
            raise CheckFieldError("Taxon id must be alphanumeric.")
        return id_

    def to_dict(self):
        return {
            "name": self.name,
            "taxonomy_id": self.taxonomy_id,
            "parent_id": self.parent_id,
            "taxonomy_version": self.taxonomy_version,
            "id": self.id,
        }
