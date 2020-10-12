from datetime import datetime

from sqlalchemy import create_engine, JSON

from sqlalchemy import Column, Integer, String, Date, JSON,ForeignKey
from sqlalchemy.orm import relationships
from crud import recreate_database, Base
from sqlalchemy.dialects.postgresql import json
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

    def __repr__(self):
        return "<Sample(sample_id='{}', patient_id='{}', batch_id='{}', cohort_id='{}')>" \
            .format(self.sample_id, self.patient_id, self.batch_id, self.cohort_id)


class Raw_data(Base):
    __tablename__ = 'raw_data'
    id = Column(Integer, primary_key=True)  # automatically generated pkey
    sample_id = Column(Integer, ForeignKey('sample.id'), nullable=False)
    qc_tool = Column(String(50), nullable=False)
    metrics = Column(JSON, nullable=False)

    def __repr__(self):
        return "<Sample(sample_id='{}', qc_tool='{}'>" \
            .format(self.sample_id, self.qc_tool)


class Multiqc_report(Base):
    __tablename__ = 'multiqc_report'
    id = Column(Integer, primary_key=True)  # automatically generated pkey
    multiqc_report_id = Column(Integer, nullable=False)
    # multiqc_report = Column(HTML) # not sure how to do
    batch_id = Column(Integer, ForeignKey('batch.id'), nullable=False)
    cohort_id = Column(Integer, ForeignKey('cohort.id'), nullable=False)

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

recreate_database()
'''


class Raw_Data(Base):
    #__abstract__ = True
    __tablename__ = 'Raw Data'
    PS_ID = Column(String, nullable= False, primary_key= True)
    QC_tools = Column(String)
    JASON = Column(JSON)

    def __repr__(self):
        return "<Raw_Data(PS_ID='{}', QC_tools='{}', JASON={})>" \
            .format(self.PS_ID, self.QC_tools, self.JASON)
        #print(Raw_Data)

class MuitiQC_results(Base):
    #__abstract__ = True
    __tablename__ = 'MuitiQC_results'
    MuitiQC_ID = Column(String, primary_key=True,nullable= False)
    MuitiQC_html_path = Column(String)
    Cohort_ID = Column(String)
    Batch_ID = Column(Integer)

    def __repr__(self):
        return "< MuitiQC_results(MuitiQC_ID='{}', MuitiQC_html_path='{}', Cohort_ID='{}',Batch_ID='{}')>" \
            .format(self.MuitiQC_ID, self.MuitiQC_html_path, self.Cohort_ID,self.Batch_ID)

class Samples(Base):
    __tablename__ = 'Samples'
    PS_ID = Column(String, primary_key=True, nullable=False)
    Sample_ID = Column(String)
    Patient_ID = Column(String)
    Cohort_ID = Column(String)
    Batch_ID = Column(Integer)
    File_path = Column(String)

    def __repr__(self):
        return "<Samples(PS_ID='{}', Sample_ID = '{}',Patient_ID = '{}', Cohort_ID = '{}',Batch_ID = '{}',File_Path = '{}')>" \
            .format(self.PS_ID, self.Sample_ID, self.Patient_ID,self.Cohort_ID,self.Batch_ID,self.File_path)

class Patient(Base):
    __tablename__ = 'Patient'
    Patient_ID = Column(String,primary_key= True)
    Cohort_ID = Column(String)
    Batch_ID = Column(Integer)
    Date = Column(Date)
    name = Column(String)
    age = Column(Integer)

    def __repr__(self):
        return "<Patient(Patient_ID = '{}', Cohort_ID = '{}',Batch_ID = '{}',Date = '{}',name = '{}',age = '{}')>" \
            .format(self.Patient_ID,self.Cohort_ID,self.Batch_ID,self.Da,self.name,self.age)




class Batch(Base):
    __tablename__ = 'Batch'
    Batch_ID = Column(Integer, pimary_key= True)
    Cohort_ID = Column(String)
    Date = Column(Date)
    Flow_cell_ID = Column(String)

    def __repr__(self):
        return "<Batch(Batch_ID='{}', Cohort_ID = '{}',Date = '{}',Flow_cell_ID = '{}')>" \
            .format(self.Batch_ID, self.Cohort_ID, self.Date,self.Flow_cell_ID)


class Cohort(Base):
    __tablename__ = 'Cohort'
    Cohort_ID = Column(String,primary_key= True)
    Disease = Column(Integer)
    Size = Column(Integer)
    Other = Column(String)

    def __repr__(self):
        return "<Cohort(Cohort_ID = '{}',Disease = '{}',Size = '{}',Other = '{}')>" \
            .format(self.Cohort_ID, self.Disease, self.Size,self.Other)

sample1 = Raw_Data(
    PS_ID='human 1 66',
    QC_tools='picard',
    JASON="key1: value1, key2: value2"
)
session.add(sample1)
session.commit()
print(sample1)



'''