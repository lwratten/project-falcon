from sqlalchemy import Column, Integer, String, Date, ForeignKey, Table, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref

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

    patient_id = Column(Integer, ForeignKey("patient.id", ondelete="CASCADE"), nullable=True)
    batch_id = Column(Integer, ForeignKey("batch.id", ondelete="CASCADE"), nullable=False)
    cohort_id = Column(String, ForeignKey("cohort.id", ondelete="CASCADE"), nullable=False)
    # Non-unique sample ID/name given in input.
    sample_name = Column(String, nullable=False)
    flowcell_lane = Column(String, nullable=False)
    library_id = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    centre = Column(String, nullable=False)
    reference_genome = Column(String, nullable=False)
    type = Column(String, nullable=False)
    description = Column(Text)    

    # relationship(raw data-sample many to 1)
    raw_data = relationship("RawData", backref="sample")

    def __repr__(self):
        return """<id='{}', sample_name='{}', patient_id='{}', batch_id='{}', cohort_id='{}', 
                flowcell_lane='{}', library_id='{}', platform='{}', centre='{}', reference_genome='{}', type='{}', description='{}')>""" \
                .format(self.id, self.sample_name, self.patient_id, self.batch_id, self.cohort_id,
                        self.flowcell_lane, self.library_id, self.platform, self.centre, self.reference_genome, self.type, self.description)


class RawData(Base):
    __tablename__ = 'raw_data'

    id = Column(Integer, primary_key=True, nullable=False)

    sample_id = Column(Integer, ForeignKey('sample.id', ondelete="CASCADE"), nullable=False)
    qc_tool = Column(String(50), nullable=False)
    metrics = Column(JSONB, nullable=False)

    def __repr__(self):
        return "<RawData(id = '{}', sample_id='{}', qc_tool='{}',metrics = '{}'>" \
            .format(self.id, self.sample_id, self.qc_tool, self.metrics)


PatientBatch = Table("PatientBatch", Base.metadata,
                     Column("patient_id", Integer, ForeignKey("patient.id", ondelete="CASCADE")),
                     Column("batch_id", Integer, ForeignKey("batch.id", ondelete="CASCADE")),
                     )


class Patient(Base):
    __tablename__ = 'patient'

    id = Column(Integer, primary_key=True, nullable=False)

    cohort_id = Column(String, ForeignKey('cohort.id', ondelete="CASCADE"), nullable=False)
    age = Column(Integer)
    gender = Column(String(10))

    # Sample-Patient many to 1
    samples = relationship("Sample", backref="patient")
    # Batch-Patient many to many
    batches = relationship("Batch", secondary=PatientBatch, backref="patient")

    def __repr__(self):
        return "<Patient(id='{}', age='{}, gender='{}'>" \
            .format(self.id, self.age, self.gender)


class Batch(Base):
    __tablename__ = 'batch'

    id = Column(Integer, primary_key=True, nullable=False)

    cohort_id = Column(String, ForeignKey('cohort.id', ondelete="CASCADE"), nullable=False)

    batch_name = Column(String, nullable=False)
    path = Column(String, nullable=False)
    description = Column(Text)

    # Batch-Patients many to many
    patients = relationship("Patient", secondary=PatientBatch, backref=backref("batch", cascade = "all, delete"))
    # Sample-Batch many to 1
    samples = relationship("Sample", backref=backref("batch", cascade = "all, delete"))

    def __repr__(self):
        return "<Batch(id='{}', batch_name='{}', cohort_id='{}', path='{}', description='{}'>" \
            .format(self.id, self.batch_name, self.cohort_id, self.path, self.description)


class Cohort(Base):
    __tablename__ = 'cohort'

    id = Column(String, primary_key=True, nullable=False)

    description = Column(Text)

    # relationship(batch-cohort, patient-cohort, multiqc-cohort, sample-cohort many to 1)
    batches = relationship("Batch", backref=backref("cohort", cascade = "all, delete"))
    patients = relationship("Patient", backref=backref("cohort", cascade = "all, delete"))
    samples = relationship("Sample", backref=backref("cohort", cascade = "all, delete"))

    def __repr__(self):
        return "<Cohort(id='{}'，disease='{}，size='{}''>" \
            .format(self.id, self.disease, self.size)

def get_tables():
    tables = []
    for name, model_class in Base._decl_class_registry.items():
        try:
            tables.append(model_class.__tablename__)
        except:
            # Sometimes there is an object that's not a model class in this iteration.
            continue
    return tables
