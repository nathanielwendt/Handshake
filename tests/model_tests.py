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