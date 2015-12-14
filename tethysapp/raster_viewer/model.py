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
    mean_val = Column(Float)
    std_val = Column(Float)
    min_2nd_val = Column(Float)
    max_2nd_val = Column(Float)
    band_id = Column(Integer)
    band_name = Column(String)
    hs_branch = Column(String)
    no_data_val = Column(Float)

    def __init__(self, res_id, min_val, max_val, mean_val, std_val, min_2nd_val, max_2nd_val, band_id, band_name, hs_branch, no_data_val):
        """
        Constructor for a gage
        """
        self.res_id = res_id
        self.min_val = min_val
        self.max_val = max_val
        self.mean_val = mean_val
        self.std_val = std_val
        self.min_2nd_val = min_2nd_val
        self.max_2nd_val = max_2nd_val
        self.band_id = band_id
        self.band_name = band_name
        self.hs_branch = hs_branch
        self.no_data_val = no_data_val