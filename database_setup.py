import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
 
Base = declarative_base()
 
class Service(Base):
    __tablename__ = 'service'
   
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
 
class Contact(Base):
    __tablename__ = 'contact'

    id = Column(Integer, primary_key = True)
    phone = Column(String(14))
    email = Column(String(100))
    website = Column(String(100))
    address = Column(String)
    city = Column(String(40))
    state = Column(String(2))
    zipcode = Column(String(250))
    service_id = Column(Integer,ForeignKey('service.id'))
    service = relationship(Service) 

    @property
    def serialize(self):
        return {
        'id' : self.id,
        'phone' : self.phone,
        'email' : self.email,
        'website' : self.website,
        'address' : self.address,
        'city' : self.city,
        'state' : self.state,
        'zipcode' : self.zipcode,
        'service_id' : self.service_id,
        }

class Profile(Base):
    __tablename__ = 'profile'

    id = Column(Integer, primary_key = True)
    description = Column(String)
    price_range_min = Column(String(4))
    price_range_max = Column(String(4))
    service_id = Column(Integer,ForeignKey('service.id'))
    service = relationship(Service) 
 
class Album(Base):
    __tablename__ = 'album'

    id = Column(Integer, primary_key = True)
    photo = Column(String)
    profile_id = Column(Integer,ForeignKey('profile.id'))
    profile = relationship(Profile) 

engine = create_engine('sqlite:///seniorcaredirectory.db')
Base.metadata.create_all(engine)