# models/job_log.py

from sqlalchemy import Column, Integer, Unicode, DateTime, Text, LargeBinary
# v1.3-1.4: from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime, timezone

class Base(DeclarativeBase):
    pass


class JobLogTable(Base):
    __tablename__ = 'apscheduler_job_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Unicode(191), index=True, nullable=False)
    run_count = Column(Integer)
    fail_count = Column(Integer)
    event = Column(Text)
    timestamp = Column(DateTime, default=datetime.now(timezone.utc))
    log_state = Column(LargeBinary, nullable=False)

    def __repr__(self):
        return f"<JobLog(job_id='{self.job_id}', run_count={self.run_count}, fail_count={self.fail_count}," \
               f"timestamp={self.timestamp})>"


class JobLog(object):

    __slots__ = ('_jobstore_alias', 'id', 'job_id', 'run_count', 'fail_count', 'event', 'timestamp',
                 'log_state')

    def __init__(self, job_id, timestamp, run_count=0, fail_count=0):
        super(JobLog, self).__init__()
        self._jobstore_alias = None
        self.job_id = job_id
        self.run_count = run_count
        self.fail_count = fail_count
        self.timestamp = timestamp
        self.event = None
        self.log_state = None
        self.id = None

    def __getstate__(self):
        return {
            'version': 1,
            'id': self.id,
            'job_id': self.job_id,
            'run_count': self.run_count,
            'fail_count': self.fail_count,
            'event': self.event,
            'timestamp': self.timestamp,
            'log_state': self.log_state
        }

    def __setstate__(self, state):
        if state.get('version', 1) > 1:
            raise ValueError('Job has version %s, but only version 1 can be handled' %
                             state['version'])

        self.id = state['id']
        self.job_id = state['job_id']
        self.run_count = state['run_count']
        self.fail_count = state['fail_count']
        self.event = state['event']
        self.timestamp = state['timestamp']
        self.log_state = state['log_state']


