
from sqlalchemy import Column, Integer, String, Date, JSON,ForeignKey
from sqlalchemy.orm import relationship
from crud import *

### User defined classes which correspond to database tables
### instances of these classes (objects) correspond to their table rows

class Sample(Base):
    __tablename__ = 'sample'  # the __tablename__ attribute corresponds to the table name in the DB
    id = Column(Integer, primary_key=True)  # automatically generated pkey
    sample_id = Column(Integer,
                       nullable=False)  # actual id of sample (not guarenteed to be unique, hence id column required)
    patient_id = Column(Integer, ForeignKey('patient.id'), nullable=False)
    batch_id = Column(Integer, ForeignKey('batch.id'), nullable=False)
    cohort_id = Column(Integer, ForeignKey('cohort.id'), nullable=False)
    path = Column(String(100), nullable=False)


    #relationship(raw data-sample many to 1)
    raw_data = relationship("Raw_data", backref = "sample")

    def __repr__(self):
        return "<Sample(id = '{}', sample_id='{}', patient_id='{}', batch_id='{}', cohort_id='{}')>" \
            .format(self.id, self.sample_id, self.patient_id, self.batch_id, self.cohort_id)


class Raw_data(Base):
    __tablename__ = 'raw_data'
    id = Column(Integer, primary_key=True)  # automatically generated pkey
    sample_id = Column(Integer, ForeignKey('sample.id'), nullable=False)
    qc_tool = Column(String(50), nullable=False)
    metrics = Column(JSON, nullable=False)

    def __repr__(self):
        return "<Sample(id = '{}', sample_id='{}', qc_tool='{}'>" \
            .format(self.id, self.sample_id, self.qc_tool)


class Multiqc_report(Base):
    __tablename__ = 'multiqc_report'
    id = Column(Integer, primary_key=True)  # automatically generated pkey
    multiqc_report_id = Column(Integer, nullable=False)
    # multiqc_report = Column(HTML) # not sure how to do
    batch_id = Column(Integer, ForeignKey('batch.id'), nullable=False)
    cohort_id = Column(Integer, ForeignKey('cohort.id'), nullable=False)

    #relationship(batch-multiqc 1 to 1)
    batch_multiqc = relationship("Batch", uselist=False, back_populates="multiqc_batch")

    def __repr__(self):
        return "<Sample(sample_id='{}', patient_id='{}', batch_id='{}', cohort_id='{}')>" \
            .format(self.sample_id, self.patient_id, self.batch_id, self.cohort_id)


class Patient(Base):
    __tablename__ = 'patient'
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, nullable=False)  # actual id of patient (not guarenteed to be unique)
    batch_id = Column(Integer, ForeignKey('batch.id'), nullable=False)
    cohort_id = Column(Integer, ForeignKey('cohort.id'), nullable=False)
    full_name = Column(String(100))
    age = Column(Integer)
    gender = Column(String(10))

    #relationship(sample-patient many to 1)
    samples = relationship("Sample", backref='sample')

    def __repr__(self):
        return "<Sample(patient_id='{}', batch_id='{}', cohort_id='{}'>" \
            .format(self.patient_id, self.batch_id, self.cohort_id)


class Batch(Base):
    __tablename__ = 'batch'
    id = Column(Integer, primary_key=True)
    batch_id = Column(Integer, nullable=False)  # actual id of batch (not guarenteed to be unique)
    cohort_id = Column(Integer, ForeignKey('cohort.id'), nullable=False)
    flow_cell_id = Column(Integer, nullable=False)
    date = Column(Date)  # date patient sample was taken
    facility = Column(String(50))

    #relationship(batch-multiqc 1 to 1, patient-batch many to 1)
    patients = relationship("Patient", backref="patient")
    samples = relationship("Sample", backref = 'sample')
    multiqc_batch = relationship("Multiqc_report", uselist = False, back_populates = "batch_multiqc")

    def __repr__(self):
        return "<Sample(batch_id='{}', flow_cell_id='{}', date='{}'>" \
            .format(self.batch_id, self.flow_cell_id, self.date)



class Cohort(Base):
    __tablename__ = 'cohort'
    id = Column(Integer, primary_key=True)
    cohort_id = Column(Integer, nullable=False)  # actual id of cohort (not guarenteed to be unique)
    disease = Column(String(50))
    size = Column(Integer)

    def __repr__(self):
        return "<Sample(cohort_id='{}', disease='{}'>" \
            .format(self.cohort_id, self.disease)

    #relationship(batch-cohort, patient-cohort, multiqc-cohort, sample-cohort many to 1)
    batches = relationship("Batch", backref = "batch")
    patients = relationship("Patient", backref="patient")
    multiqc = relationship("Multiqc_report", backref="multiqc_report")
    samples = relationship("Sample", backref='sample')
recreate_database()

