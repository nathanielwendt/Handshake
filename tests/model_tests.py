import models
from test_utils import AppEngineTest
import datetime
from models import getUUID, IDTYPE

class TestAccessSlot(AppEngineTest):
    def setUp(self):
        super(TestAccessSlot, self).setUp()

        self.now = datetime.datetime.now()
        self.slot_id = getUUID(IDTYPE.ACCESS_SLOT)
        data = {
            "id": self.slot_id,
            "routeId": "route001",
            "active": True,
            "start": self.now,
            "end": self.now + datetime.timedelta(hours=2),
            "repeatInterval": 60 * 60 * 24,
            "cutoff": self.now + datetime.timedelta(days=3),
            "currStart": self.now,
            "currEnd": self.now + datetime.timedelta(hours=2)
        }
        self.access_slot = models.AccessSlot(**data)
        self.access_slot.put()

    def test_basic_checks(self):
        t1 = self.now + datetime.timedelta(hours=1)
        t2 = self.now + datetime.timedelta(hours=3)
        t3 = self.now + datetime.timedelta(days=1, hours=1)
        t4 = self.now + datetime.timedelta(days=1, hours=3)
        t5 = self.now + datetime.timedelta(days=3, hours=1)
        self.assertTrue(self.access_slot.check_and_update_slot(t1))
        self.assertFalse(self.access_slot.check_and_update_slot(t2))
        self.assertTrue(self.access_slot.check_and_update_slot(t3))
        self.assertFalse(self.access_slot.check_and_update_slot(t4))
        self.assertFalse(self.access_slot.check_and_update_slot(t5))

    #test that the slot updates its own currStart and currEnd based on
    #most recent queries
    def test_update(self):
        t1 = self.now + datetime.timedelta(days=1, hours=1)
        self.assertTrue(self.access_slot.check_and_update_slot(t1))

        slot = models.AccessSlot.get_by_id(self.slot_id)
        self.assertNotEqual(self.now, slot.currStart)
        self.assertEqual(self.now, slot.start)


class TestRouteMember(AppEngineTest):
    def setUp(self):
        super(TestRouteMember, self).setUp()
        models.User(id="user001", name="Darwin Plum").put()

        self.route = models.Route(id="BlueBonnet")
        self.route.put()

    def test_create_and_get_entry(self):
        models.RouteMember.create_entry(self.route, "fox2", "user001", "Darwin Plum")
        entry = models.RouteMember.get_entry(self.route, "fox2")
        self.assertIsNotNone(entry)
        self.assertEqual("BlueBonnet", entry.routeDisplayId) #preserve original case
        self.assertEqual("Darwin Plum", entry.userDisplayName)

    def test_get_user_id(self):
        models.RouteMember.create_entry(self.route, "fox2", "user001", "Darwin Plum")
        user_id = models.RouteMember.get_user_id(self.route, "fox2")
        self.assertEqual("user001", user_id)

    def test_get_user_membership(self):
        members = models.RouteMember.get_user_membership("user001")
        self.assertEquals([], members)

        blue_bonnet = models.Route(id="BlueBonnet")
        blue_bonnet.put()
        sly_dog = models.Route(id="SlyDog")
        sly_dog.put()
        slippery_vertigo = models.Route(id="SlipperyVertigo")
        slippery_vertigo.put()
        green_lawn = models.Route(id="GreenLawn")
        green_lawn.put()

        models.RouteMember.create_entry(blue_bonnet, "fox1", "user001", "Darwin Plum")
        models.RouteMember.create_entry(sly_dog, "cat", "user001", "Darwin Plum")
        models.RouteMember.create_entry(slippery_vertigo, "anteater", "user001", "Darwin Plum")
        models.RouteMember.create_entry(blue_bonnet, "fox2", "user002", "Dave Franco")
        models.RouteMember.create_entry(green_lawn, "fox1", "user003", "Jimmy Buff")

        members = models.RouteMember.get_user_membership("user001")
        self.assertEqual({"BlueBonnet","SlyDog","SlipperyVertigo"}, set(members))

        members = models.RouteMember.get_user_membership("user002")
        self.assertEqual({"BlueBonnet"}, set(members))

        members = models.RouteMember.get_user_membership("user003")
        self.assertEqual({"GreenLawn"}, set(members))