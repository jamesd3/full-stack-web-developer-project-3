from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, Service, Contact, Profile, Album

engine = create_engine('sqlite:///seniorcaredirectory.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Menu for UrbanBurger
service1 = Service(name="Ebenezer Memory Care")

session.add(service1)
session.commit()

contact1 = Contact(phone="1(612)672-7262", email="jrowe3@fairview.org",
                     website="http://www.ebenezermemorycare.org/",
                     address="2722 Park Ave", city="Minneapolis", 
                     state="MN", zipcode="55407", service=service1)

session.add(contact1)
session.commit()


profile1 = Profile(description="Ebenezer helps older adults make their lives more independent, healthful, meaningful, and secure. From Alzheimer's care to dementia care, our compassionate staff is prepared to help with it all.",
                     price_range_min="$$", price_range_max="$$$", service=service1)

session.add(profile1)
session.commit()


print "added menu items!"