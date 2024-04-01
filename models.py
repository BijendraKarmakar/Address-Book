from sqlalchemy import Column, Integer, String, Float
from database import Base


# Will inherit this class for all the database operation on address table

class Address(Base):
    __tablename__ = "address"
    id = Column(Integer, primary_key=True, index=True)
    city = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)