# models/cluster_credential.py
from sqlalchemy import Column, Integer, Boolean, String
# v1.3-1.4: from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass


class ClusterCredential(Base):
    __tablename__ = 'cluster_credential'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    server = Column(String(255), nullable=False)
    token = Column(String(2048), nullable=False)
    user = Column(String(255))
    namespace = Column(String(255))
    insecure = Column(Boolean, default=False)
    sa = Column(String(255))
    certificate = Column(String(4096))

    @classmethod
    def from_dict(cls, data):
        columns = list(cls.__table__.columns)
        allowed = {col.name for col in columns}
        filtered = {k: v for k, v in data.items() if k in allowed}
        return cls(**filtered)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "server": self.server,
            "token": self.token,
            "certificate": self.certificate,
            "user": self.user,
            "namespace": self.namespace,
            "insecure": bool(self.insecure),
            "sa": self.sa
        }