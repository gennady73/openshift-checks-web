from __future__ import absolute_import

from jobstores.base import BaseJobStore, JobLookupError, ConflictingIdError, BaseCredentialStore
from apscheduler.util import maybe_ref, datetime_to_utc_timestamp, utc_timestamp_to_datetime
# from apscheduler.job import Job
from models.job_log import JobLog, JobLogTable, Base
from datetime import datetime

try:
    import cPickle as pickle
except ImportError:  # pragma: nocover
    import pickle

try:
    from sqlalchemy import (
        create_engine, Table, Column, MetaData, Unicode, Boolean, String, Float, Integer, Text, DateTime, LargeBinary,
        select, and_, tuple_)
    from sqlalchemy.exc import IntegrityError
    from sqlalchemy.sql.expression import null
    from sqlalchemy.orm import sessionmaker, Session
except ImportError:  # pragma: nocover
    raise ImportError('SQLAlchemyJobStore requires SQLAlchemy installed')


class SQLAlchemyJobStore(BaseJobStore):
    def __init__(self, url=None, engine=None, metadata=None, pickle_protocol=None, tablename='apscheduler_job_logs', tableschema=None, engine_options=None):
        self.pickle_protocol = pickle_protocol
        metadata = metadata or MetaData()

        if engine:
            self.engine = engine
        elif url:
            self.engine = create_engine(url, **(engine_options or {}))
        else:
            raise ValueError('Need either "engine" or "url" defined')

        # Bind the engine to the metadata of the Base class so that the
        # declaratives can be accessed through a DBSession instance
        # Base.metadata.bind = self.engine
        # DBSession = sessionmaker(bind=self.engine)
        # self.session = DBSession()

        #self.jobs_t = JobLogTable.__new__(JobLogTable)
        # self.jobs_tt = Table(
        #     tablename, metadata,
        #     Column('id', Unicode(191), primary_key=True),
        #     # Column('next_run_time', Float(25), index=True),
        #     Column('paused', Boolean, nullable=False),
        #     Column('jobstore', String, nullable=False),
        #     Column('max_log_entries', Integer, nullable=False),
        #     #logs = relationship("JobLog", back_populates="job"),
        #     schema=tableschema,
        #     tablename='job'
        # )

        self.jobs_t = Table(
            tablename, metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('job_id', Unicode(191), index=True, nullable=False),
            Column('run_count', Integer),
            Column('fail_count', Integer),
            Column('event', Text),
            Column('timestamp', DateTime, default=datetime.utcnow),
            Column('log_state', LargeBinary, nullable=False),
            schema=tableschema
        )

    def start(self, alias):
        super(SQLAlchemyJobStore, self).start(alias)
        # Create tables if they don't exist
        # Base.metadata.create_all(self.engine)
        self.jobs_t.create(self.engine, True)

    def lookup_job(self, job_id, timestamp=None):
        if timestamp is not None:
            selectable = select(self.jobs_t.c.log_state).where(self.jobs_t.c.job_id == job_id
                                                               and self.jobs_t.c.timestamp == timestamp)
        else:
            selectable = select(self.jobs_t.c.log_state).where(self.jobs_t.c.job_id == job_id)

        with self.engine.begin() as connection:
            log_state = connection.execute(selectable).scalar()
            return self._reconstitute_job(log_state) if log_state else None

    def get_all_jobs_by_id(self, job_id):
        conditions = (tuple_(self.jobs_t.c.job_id) == tuple_(job_id))  # [] # [self.jobs_t.c.job_id == job_id]
        jobs = self._get_jobs(conditions)
        # self._fix_paused_jobs_sorting(jobs)
        return jobs

    def get_all_jobs(self):
        jobs = self._get_jobs()
        # self._fix_paused_jobs_sorting(jobs)
        return jobs

    def add_job(self, job):
        insert = self.jobs_t.insert().values(**{
            'job_id': job.job_id,
            'run_count': job.run_count,
            'fail_count': job.fail_count,
            'event': pickle.dumps(job.event, self.pickle_protocol),
            # 'timestamp': datetime_to_utc_timestamp(job.timestamp) if job.timestamp is not None else datetime.utcnow(),
            'timestamp': job.timestamp if job.timestamp is not None else datetime.utcnow(),
            'log_state': pickle.dumps(job.__getstate__(), self.pickle_protocol)
        })
        with self.engine.begin() as connection:
            try:
                connection.execute(insert)
            except IntegrityError:
                raise ConflictingIdError(job.id)

    def update_job(self, job):
        update = self.jobs_t.update().values(**{
            'run_count': job.run_count,
            'fail_count': job.fail_count,
            'event': job.event,
            'timestamp': datetime_to_utc_timestamp(job.timestamp) if job.timestamp is not None else datetime.utcnow(),
            'log_state': pickle.dumps(job.__getstate__(), self.pickle_protocol)
        }).where(self.jobs_t.c.job_id == job.job_id)
        with self.engine.begin() as connection:
            result = connection.execute(update)
            if result.rowcount == 0:
                raise JobLookupError(job.id)

    def remove_job(self, job_id):
        delete = self.jobs_t.delete().where(self.jobs_t.c.job_id == job_id)
        with self.engine.begin() as connection:
            result = connection.execute(delete)
            if result.rowcount == 0:
                raise JobLookupError(job_id)

    def remove_all_jobs(self):
        delete = self.jobs_t.delete()
        with self.engine.begin() as connection:
            connection.execute(delete)

    def shutdown(self):
        self.engine.dispose()

    def _reconstitute_job(self, log_state):
        log_state = pickle.loads(log_state)
        log_state['jobstore'] = self
        job = JobLog.__new__(JobLog)
        job.__setstate__(log_state)
        #job._scheduler = self._scheduler
        job._jobstore_alias = self._alias
        return job

    def _get_jobs(self, *conditions):
        jobs = []
        selectable = select(self.jobs_t.c.id, self.jobs_t.c.log_state).\
            order_by(self.jobs_t.c.job_id)
        selectable = selectable.where(and_(*conditions)) if conditions else selectable
        failed_job_ids = set()
        with self.engine.begin() as connection:
            for row in connection.execute(selectable):
                try:
                    jobs.append(self._reconstitute_job(row.log_state))
                except BaseException:
                    self._logger.exception('Unable to restore job "%s" -- removing it', row.id)
                    failed_job_ids.add(row.id)

            # Remove all the jobs we failed to restore
            if failed_job_ids:
                delete = self.jobs_t.delete().where(self.jobs_t.c.id.in_(failed_job_ids))
                connection.execute(delete)

        return jobs

    def __repr__(self):
        return '<%s (url=%s)>' % (self.__class__.__name__, self.engine.url)

import logging
import base64
# from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Unicode, Text, Boolean
# from sqlalchemy.exc import IntegrityError
# from sqlalchemy.sql import select, and_

from models import ClusterCredential

LOGGER = logging.getLogger('cluster.store')


class ClusterCredentialStore(BaseCredentialStore):
    def __init__(self, url=None, engine=None, metadata=None, tablename='cluster_credential', engine_options=None):
        metadata = metadata or MetaData()

        if engine:
            self._engine = engine
        elif url:
            self._engine = create_engine(url, **(engine_options or {})) #  "sqlite:///clusters.db"
        else:
            raise ValueError('Need either "engine" or "url" defined')

        self._session = sessionmaker(bind=self._engine)

    def start(self, alias):
        super().start(alias)
        # Create tables if they don't exist
        ClusterCredential.metadata.create_all(self._engine)

    def _validate_certificate(self, cert_data):
        if not cert_data or not cert_data.strip():
            raise ValueError("Certificate cannot be empty")
        # Could add PEM format validation logic here later
        LOGGER.debug("Certificate validation passed")

    def add_credential(self, credential):
        if credential.certificate:
            self._validate_certificate(credential.certificate)
        with self._session() as session:
            session.add(credential)
            session.commit()
            LOGGER.info(f"Added credential for cluster: {credential.name}")

    def update_credential(self, credential):
        if credential.certificate:
            self._validate_certificate(credential.certificate)
        with self._session() as session:
            existing = session.get(ClusterCredential, credential.id)
            if not existing:
                raise ValueError(f"Credential with ID {credential.id} not found")
            for attr, value in vars(credential).items():
                if attr.startswith('_'): continue  # skip internal SQLAlchemy fields
                setattr(existing, attr, value)
            session.commit()
            LOGGER.info(f"Updated credential for cluster: {credential.name}")

    def delete_credential(self, credential_id):
        with self._session() as session:
            credential = session.get(ClusterCredential, credential_id)
            if not credential:
                raise ValueError(f"Credential with ID {credential_id} not found")
            session.delete(credential)
            session.commit()
            LOGGER.info(f"Deleted credential with ID: {credential_id}")

    def get_credential(self, credential_id):
        with self._session() as session:
            return session.get(ClusterCredential, credential_id)

    def list_credentials(self):
        with self._session() as session:
            return session.query(ClusterCredential).all()

    def shutdown(self):
        if self._engine:
            self._engine.dispose()

    def __repr__(self):
        return '<%s (url=%s)>' % (self.__class__.__name__, self._engine.url)