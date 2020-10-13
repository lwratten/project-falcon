
from sqlalchemy import Column, Integer, String, Date, JSON,ForeignKey
from sqlalchemy.orm import relationship
from crud import *
import uuid
### User defined classes which correspond to database tables
### instances of these classes (objects) correspond to their table rows
def generate_uuid():
    return uuid.uuid4().hex

class Sample(Base):
    __tablename__ = 'sample'  # the __tablename__ attribute corresponds to the table name in the DB
    ####when we parse the sample information in to sample table  from the very begining, we do not have qc tools information right? I think we will need to delete the id column in the sample table?
    #id = Column(Integer, primary_key=True)  # automatically generated pkey
    ####Since deleting id column, I set sample_id as pk of Sample table, and set autocrement of the number(so it will have a autocrement integer for every sample, nd will be unique)
    sample_id = Column(Integer,autoincrement= True,primary_key= True,
                       nullable=False)  # actual id of sample (not guarenteed to be unique, hence id column required)
    patient_id = Column(Integer, ForeignKey('patient.patient_id'), nullable=False)
    batch_id = Column(Integer, ForeignKey('batch.batch_id'), nullable=False)
    cohort_id = Column(Integer, ForeignKey('cohort.cohort_id'), nullable=False)
    path = Column(String(100), nullable=False)


    #relationship(raw data-sample many to 1)
    raw_data = relationship("Raw_data", backref = "sample")

    def __repr__(self):
        return "<sample_id='{}', patient_id='{}', batch_id='{}', cohort_id='{}',path = '{}')>" \
            .format(self.sample_id, self.patient_id, self.batch_id, self.cohort_id,self.path)


class Raw_data(Base):
    __tablename__ = 'raw_data'
    id = Column(String, primary_key=True)  # automatically generated pkey
    sample_id = Column(Integer, ForeignKey('sample.sample_id'), nullable=False) # actual id of sample (not guarenteed to be unique, hence id column required)
    qc_tool = Column(String(50), nullable=False)
    metrics = Column(JSON, nullable=False)

    def __repr__(self):
        return "<Raw_data(id = '{}', sample_id='{}', qc_tool='{}',metrics = '{}'>" \
            .format(self.id, self.sample_id, self.qc_tool,self.metrics)


class Multiqc_report(Base):
    __tablename__ = 'multiqc_report'
    id = Column(String, primary_key=True)  # automatically generated pkey
    multiqc_report_id = Column(Integer, nullable=False)
    # multiqc_report = Column(HTML) # not sure how to do
    batch_id = Column(Integer, ForeignKey('batch.batch_id'), nullable=False)
    cohort_id = Column(Integer, ForeignKey('cohort.cohort_id'), nullable=False)

    #relationship(batch-multiqc 1 to 1)
    batch_multiqc = relationship("Batch", uselist=False, back_populates="multiqc_batch")

    def __repr__(self):
        return "<Multiqc_report(sample_id='{}', patient_id='{}', batch_id='{}', cohort_id='{}')>" \
            .format(self.sample_id, self.patient_id, self.batch_id, self.cohort_id)


class Patient(Base):
    __tablename__ = 'patient'
    #id = Column(String, primary_key=True)
    patient_id = Column(Integer, primary_key=True, nullable=False)  # actual id of patient (not guarenteed to be unique)
    batch_id = Column(Integer, ForeignKey('batch.batch_id'), nullable=False)
    cohort_id = Column(Integer, ForeignKey('cohort.cohort_id'), nullable=False)
    full_name = Column(String(100))
    age = Column(Integer)
    gender = Column(String(10))

    #relationship(sample-patient many to 1)
    samples = relationship("Sample", backref='sample')

    def __repr__(self):
        return "<Patient(patient_id='{}', batch_id='{}', cohort_id='{}'>" \
            .format(self.patient_id, self.batch_id, self.cohort_id)


class Batch(Base):
    __tablename__ = 'batch'
    #id = Column(String, primary_key=True)
    batch_id = Column(Integer, primary_key= True, nullable=False)  # actual id of batch (not guarenteed to be unique)
    cohort_id = Column(Integer, ForeignKey('cohort.cohort_id'), nullable=False)
    flow_cell_id = Column(Integer, nullable=False)
    date = Column(Date)  # date patient sample was taken
    facility = Column(String(50))

    #relationship(batch-multiqc 1 to 1, patient-batch many to 1)
    patients = relationship("Patient", backref="patient")
    samples = relationship("Sample", backref = 'sample')
    multiqc_batch = relationship("Multiqc_report", uselist = False, back_populates = "batch_multiqc")

    def __repr__(self):
        return "<Batch(batch_id='{}', flow_cell_id='{}', date='{}'>" \
            .format(self.batch_id, self.flow_cell_id, self.date)



class Cohort(Base):
    __tablename__ = 'cohort'
    #id = Column(String, primary_key=True)
    cohort_id = Column(Integer, primary_key= True, nullable=False)  # actual id of cohort (not guarenteed to be unique)
    disease = Column(String(50))
    size = Column(Integer)

    def __repr__(self):
        return "<Cohort(id='{}'，cohort_id='{}', disease='{}，size='{}''>" \
            .format(self.id,self.cohort_id, self.disease,self.size)

    #relationship(batch-cohort, patient-cohort, multiqc-cohort, sample-cohort many to 1)
    batches = relationship("Batch", backref = "batch")
    patients = relationship("Patient", backref="patient")
    multiqc = relationship("Multiqc_report", backref="multiqc_report")
    samples = relationship("Sample", backref='sample')
recreate_database()

