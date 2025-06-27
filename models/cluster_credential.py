# models/cluster_credential.py
from sqlalchemy import Column, Integer, Unicode, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class ClusterCredential(Base):
    __tablename__ = 'cluster_credential'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Unicode(128), nullable=False, unique=True)  # Cluster name
    server = Column(Unicode(512), nullable=False)             # API URL
    token = Column(Unicode(2048), nullable=False)             # Access token
    user = Column(Unicode(128), nullable=True)                # Corresponding user
    namespace = Column(Unicode(128), nullable=True)           # Default namespace
    insecure = Column(Boolean, default=False)                 # Skip TLS verification
    sa = Column(Unicode(128), nullable=True)                  # Service account, optional
    certificate = Column(Text, nullable=True)                 # Login certificate for SA

    created_at = Column(DateTime, default=datetime.utcnow())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "server": self.server,
            "token": self.token,
            "user": self.user,
            "namespace": self.namespace,
            "insecure": self.insecure,
            "sa": self.sa,
            "certificate": self.certificate,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
