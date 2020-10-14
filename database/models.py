from sqlalchemy import Column, Integer, String, Date, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

"""
SQLAlchemy defined classes which correspond to database tables.
Instances of these classes (objects) correspond to their table rows
"""

# Global Base object maintains a catalog of classes/tables mapped to the database.
# Also, replaces all Column objects with python descriptors.
Base = declarative_base()


class Sample(Base):
    __tablename__ = "sample"

    id = Column(Integer, primary_key=True, nullable=False)

    sample_name = Column(Integer, nullable=False)
    patient_id = Column(Integer, ForeignKey("patient.id"), nullable=True)
    batch_id = Column(Integer, ForeignKey("batch.id"), nullable=False)
    cohort_id = Column(Integer, ForeignKey("cohort.id"), nullable=False)

    # relationship(raw data-sample many to 1)
    raw_data = relationship("RawData", backref="sample")

    def __repr__(self):
        return "<id='{}', sample_name='{}', patient_id='{}', batch_id='{}', cohort_id='{}')>" \
            .format(self.id, self.sample_name, self.patient_id, self.batch_id, self.cohort_id)


class RawData(Base):
    __tablename__ = 'raw_data'

    id = Column(Integer, primary_key=True, nullable=False)

    sample_id = Column(Integer, ForeignKey('sample.id'), nullable=False)
    qc_tool = Column(String(50), nullable=False)
    metrics = Column(JSON, nullable=False)

    def __repr__(self):
        return "<RawData(id = '{}', sample_id='{}', qc_tool='{}',metrics = '{}'>" \
            .format(self.id, self.sample_id, self.qc_tool, self.metrics)


class Patient(Base):
    __tablename__ = 'patient'

    id = Column(Integer, primary_key=True, nullable=False)

    cohort_id = Column(Integer, ForeignKey('cohort.id'), nullable=False)
    age = Column(Integer)
    gender = Column(String(10))

    # relationship(sample-patient many to 1)
    samples = relationship("Sample", backref="patient")

    def __repr__(self):
        return "<Patient(id='{}', cohort_id='{}', age='{}, gender='{}'>" \
            .format(self.id, self.cohort_id, self.age, self.gender)


class Batch(Base):
    __tablename__ = 'batch'

    id = Column(Integer, primary_key=True, nullable=False)

    cohort_id = Column(Integer, ForeignKey('cohort.id'), nullable=False)
    flow_cell_id = Column(Integer, nullable=False)
    date = Column(Date)  # date patient sample was taken
    path = Column(String(100), nullable=False)

    # relationship(batch-multiqc 1 to 1, patient-batch many to 1)
    patients = relationship("Patient", backref="batch")
    samples = relationship("Sample", backref="batch")
    # multiqc_batch = relationship(
    #    "Multiqc_report", uselist=False, back_populates="batch_multiqc")

    def __repr__(self):
        return "<Batch(id='{}', cohort_id='{}', flow_cell_id='{}', path='{}' date='{}'>" \
            .format(self.id, self.cohort_id, self.flow_cell_id, self.path, self.date)


class Cohort(Base):
    __tablename__ = 'cohort'

    id = Column(Integer, primary_key=True, nullable=False)

    disease = Column(String(50))
    size = Column(Integer)

    def __repr__(self):
        return "<Cohort(id='{}'，disease='{}，size='{}''>" \
            .format(self.id, self.disease, self.size)

    # relationship(batch-cohort, patient-cohort, multiqc-cohort, sample-cohort many to 1)
    batches = relationship("Batch", backref="cohort")
    patients = relationship("Patient", backref="cohort")
    #multiqc = relationship("Multiqc_report", backref="cohort")
    samples = relationship("Sample", backref="cohort")
