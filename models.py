from google.appengine.ext import ndb
import time
import models
import datetime
import urllib
import random
import uuid

class IDTYPE():
    USER = "user"
    COUNTER = "count"
    ACCESS_SLOT = "accsl"
    ROUTE = "route"
    MESSAGE = "msg"

def getUUID(type):
    return type + str(uuid.uuid4())

class CoreModel(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True, indexed=True)
    last_modified = ndb.DateTimeProperty(auto_now=True)
    # Convenience method for checking entry existence without
    # needing the entry itself
    @classmethod
    def exists(cls, id):
        entry = cls.get_by_id(id)
        return entry is not None

    def get_id(self):
        return str(self.key.id())

    def get_created_utc(self):
        then = self.created
        return long(time.mktime(then.timetuple())*1e3 + then.microsecond/1e3)

    def get_id_str(self):
        return str(self.key.id())

#Id's generated automatically by app engine
class DefaultModel(CoreModel):
    @classmethod
    def get_by_id(cls, id):
        try:
            int(id)
            return super(DefaultModel, cls).get_by_id(int(id))
        except ValueError:
            return None

#Id's generated internally
class CustomModel(CoreModel):
    @classmethod
    def get_by_id(cls, id):
        return super(CustomModel, cls).get_by_id(id)

class User(CustomModel):
    name = ndb.StringProperty()
    email = ndb.StringProperty()
    emails = ndb.StringProperty(repeated=True)
    phoneNumbers = ndb.StringProperty(repeated=True)

class AccessSlot(CustomModel):
    routeId = ndb.StringProperty()
    active = ndb.BooleanProperty(default=True)
    start = ndb.DateTimeProperty()
    end = ndb.DateTimeProperty()
    repeatInterval = ndb.IntegerProperty() #in seconds
    cutoff = ndb.DateTimeProperty()
    currStart = ndb.DateTimeProperty()
    currEnd = ndb.DateTimeProperty()

    def check_and_update_slot(self, time_ref):
        has_changed = False
        if not self.active:
            return self.put_and_return(False, has_changed)
        curr_start = self.currStart
        curr_end = self.currEnd
        while time_ref < self.cutoff:
            if time_ref < curr_start:
                return self.put_and_return(False, has_changed)
            elif time_ref < curr_end:
                return self.put_and_return(True, has_changed)
            else:
                curr_start += datetime.timedelta(seconds=self.repeatInterval)
                curr_end += datetime.timedelta(seconds=self.repeatInterval)
                self.currStart = curr_start
                self.currEnd = curr_end
                has_changed = True

        if time_ref > self.cutoff:
            return self.put_and_return(False, has_changed)

    #update entity with new
    def put_and_return(self, val, has_changed):
        if has_changed:
            self.put()
        return val

#key id is route name
class Route(CustomModel):
    userId = ndb.StringProperty()
    emails = ndb.StringProperty(repeated=True)
    phoneNumbers = ndb.StringProperty(repeated=True)

    #convenience method for checking validity of current time
    def isNowValid(self):
        return self.isValid(datetime.datetime.utcnow())

    def isValid(self, time_ref):
        access_slots = AccessSlot.query(AccessSlot.routeId == self.get_id())
        for access_slot in access_slots:
            if access_slot.check_and_update_slot(time_ref):
                return True
        return False

    def getMembers(self):
        return models.RouteMember.query(ancestor=self.key).fetch()


#key id is route_member_name/id
class RouteMember(CustomModel):
    pass

class ModelException(BaseException):
    pass


class Naming(CustomModel):
    NUM_BINS = 100
    items = ndb.StringProperty(repeated=True)

    # separates the range into buckets
    # [  0   ][   1   ][..][  NUM_BINS - 1 ]
    # and selects a random item from the bucket determined from the random seed
    # time seed should be in deci-seconds
    def get_random_entry(self, time_seed):
        NUM_BINS = Naming.NUM_BINS
        length = len(self.items)
        items_in_bin = length / NUM_BINS
        begin_range = ((time_seed % NUM_BINS) * items_in_bin)
        end_range = begin_range + items_in_bin
        noun_index = random.randrange(begin_range, end_range)
        return self.items[noun_index]

class Message(CustomModel):
    routeName = ndb.StringProperty(indexed=True)
    source = ndb.StringProperty()
    sourceType = ndb.IntegerProperty()
    senderUserId = ndb.StringProperty()
    receiverUserId = ndb.StringProperty()
    clientUserId = ndb.StringProperty(indexed=True)
    body = ndb.StringProperty()

    def isClientMsg(self):
        return self.clientUserId == self.senderUserId

    def isOwnerMsg(self):
        return self.clientUserId == self.receiverUserId


class Test(CustomModel):
    num = ndb.IntegerProperty()