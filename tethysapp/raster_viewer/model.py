from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String
from sqlalchemy.orm import sessionmaker

from app import HydroShareRasterViewer

# DB Engine, sessionmaker and base
engine = HydroShareRasterViewer.get_persistent_store_engine('raster_viewer_db')
SessionMaker = sessionmaker(bind=engine)
Base = declarative_base()

class RasterStatistics(Base):
    '''
    Example SQLAlchemy DB Model
    '''
    __tablename__ = 'raster_statistics'

    # Columns
    id = Column(Integer, primary_key=True)
    res_id = Column(String)
    min_val = Column(Float)
    max_val = Column(Float)
    band_id = Column(Integer)
    band_name = Column(String)
    hs_branch = Column(String)

    def __init__(self, res_id, min_val, max_val, band_id, band_name, hs_branch):
        """
        Constructor for a gage
        """
        self.res_id = res_id
        self.min_val = min_val
        self.max_val = max_val
        self.band_id = band_id
        self.band_name = band_name
        self.hs_branch = hs_branch