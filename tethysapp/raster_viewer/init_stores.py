# Put your persistent store initializer functions in here
from .model import engine, SessionMaker, Base, RasterStatistics

def init_raster_viewer_db(first_time):
    """
    An example persistent store initializer function
    """
    # Create tables
    Base.metadata.create_all(engine)

    # Initial data
    if first_time:
        # Make session
        session = SessionMaker()

        # res 1
        res_1 = RasterStatistics(res_id="res_id_1",
                                min_val=1,
                                max_val=10,
                                mean_val=2,
                                std_val=20,
                                min_2nd_val=2,
                                max_2nd_val=20,
                                band_id = 1,
                                band_name="band_1",
                                hs_branch="www",
                                no_data_val=-987654321)
        session.add(res_1)

        # res 2
        res_2 = RasterStatistics(res_id="res_id_1",
                                min_val=2,
                                max_val=20,
                                mean_val=2,
                                std_val=20,
                                min_2nd_val=2,
                                max_2nd_val=20,
                                band_id=2,
                                band_name="band_2",
                                hs_branch="www",
                                no_data_val=--987654321)
        session.add(res_2)


        session.commit()