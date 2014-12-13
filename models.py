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
    def get_by_id(cls, id, parent=None):
        try:
            int(id)
            return super(DefaultModel, cls).get_by_id(int(id), parent)
        except ValueError:
            return None

#Id's generated internally
class CustomModel(CoreModel):
    @classmethod
    def get_by_id(cls, id, parent=None):
        return super(CustomModel, cls).get_by_id(id, parent)

class User(CustomModel):
    name = ndb.StringProperty()
    email = ndb.StringProperty()
    emails = ndb.StringProperty(repeated=True)
    phoneNumbers = ndb.StringProperty(repeated=True)
    pushRegKey = ndb.StringProperty()

    def get_display_name(self):
        return self.name

    @staticmethod
    def get_display_name_from_id(user_id):
        user = models.User.get_by_id(user_id)
        if user is None:
            return None
        else:
            return user.get_display_name()

class AccessSlot(CustomModel):
    routeId = ndb.StringProperty(indexed=True)
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

#key id is route name underscore
class Route(CustomModel):
    userId = ndb.StringProperty()
    displayName = ndb.StringProperty() #first letter capitalized
    emails = ndb.StringProperty(repeated=True)
    phoneNumbers = ndb.StringProperty(repeated=True)

    #convenience method for checking validity of current time
    def is_now_valid(self):
        return self.is_valid(datetime.datetime.utcnow())

    def is_valid(self, time_ref):
        access_slots = AccessSlot.query(AccessSlot.routeId == self.get_id())
        for access_slot in access_slots:
            if access_slot.check_and_update_slot(time_ref):
                return True
        return False

    def get_members(self):
        return models.RouteMember.query(ancestor=self.key).fetch()

    @classmethod
    #override method to provide safety for get operation
    def get_by_id(cls, id, parent=None):
        safe_id = id.lower().strip()
        return super(Route, cls).get_by_id(safe_id, parent)


#key name is route_id + member_id
class RouteMember(CustomModel):
    userId = ndb.StringProperty(indexed=True)
    userDisplayName = ndb.StringProperty()
    routeId = ndb.StringProperty()
    routeDisplayId = ndb.StringProperty()
    memberId = ndb.StringProperty()

    @staticmethod
    def create_entry(route, member_id, user_id, user_name):
        route_id = route.get_id()
        display_id = str(route_id).strip()
        route_id = str(route_id).lower().strip()
        member_id = str(member_id).lower().strip()
        member = RouteMember(parent=route.key, id=route_id + member_id)
        member.routeId = route_id
        member.memberId = member_id
        member.userId = user_id
        member.userDisplayName = user_name
        member.routeDisplayId = display_id
        member.put()
        return member

    @staticmethod
    def get_entry(route, member_id):
        route_id = str(route.get_id()).lower().strip()
        member_id = str(member_id).lower().strip()
        return RouteMember.get_by_id(route_id + member_id, parent=route.key)

    @staticmethod
    def get_user_id(route, member_id):
        entry = RouteMember.get_entry(route, member_id)
        return entry.userId

    @staticmethod
    def get_user_membership(user_id):
        entries = RouteMember.query(RouteMember.userId == user_id)
        members = []
        for entry in entries:
            members.append(entry.routeDisplayId)
        return members


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
    routeId = ndb.StringProperty(indexed=True)
    source = ndb.StringProperty()
    sourceType = ndb.IntegerProperty()
    senderUserId = ndb.StringProperty()
    receiverUserId = ndb.StringProperty()
    clientUserId = ndb.StringProperty(indexed=True)
    body = ndb.StringProperty()

    def is_client_message(self):
        return self.clientUserId == self.senderUserId

    def is_owner_message(self):
        return self.clientUserId == self.receiverUserId

    @staticmethod
    def get_route_member_id(user_id, route_id):
        entry = Message.get_channel_entries(user_id, route_id).get()
        if entry is None:
            return None
        else:
            return entry.routeMemberId

    @staticmethod
    def has_used_route(user_id, route_id):
        return Message.get_channel_entries(user_id, route_id).count() != 0

    @staticmethod
    def get_channel_entries(user_id, route_id):
        return Message.query(Message.routeId == route_id)\
                         .filter(Message.senderUserId == user_id)

    @staticmethod
    def get_route_entries(route_id):
        return Message.query(Message.routeId == route_id)
