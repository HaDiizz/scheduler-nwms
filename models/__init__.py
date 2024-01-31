import os
import mongoengine as me

from models.location import Location
from models.host import Host
from models.host import HostList
from models.host import HostDown
from models.host import HostLocation
from models.service import Service
from models.service import ServiceList
from models.service import ServiceDown
from models.access_point import AccessPoint
from models.access_point import AccessPointList
from models.access_point import AccessPointDown
from models.access_point import AccessPointLocation
from dotenv import load_dotenv


load_dotenv()


def init_mongoengine():
    try:
        me.connect(os.environ['MONGODB_NAME'],
                   host=os.environ['MONGODB_HOST'], alias='default')
        print("Successfully connected to MongoDB!")
    except Exception as e:
        print("Failed to connect to MongoDB:", str(e))
