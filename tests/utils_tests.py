import unittest
from test_utils import AppEngineTest
from utils import APIUtils, UtilsException, MessageUtils, NamingGenerator
from test_utils import ConsistencyTest
import datetime
import models

class TestNamingGenerator(ConsistencyTest):
    def setUp(self):
        super(TestNamingGenerator, self).setUp()
        self.now = datetime.datetime.utcnow()
        AppEngineTest.set_up_naming()

    def test_basic_route_id(self):
        route_name = NamingGenerator.get_route_id()
        self.assertIsNotNone(route_name)

    def test_load_route_id(self):
        routes = []
        for i in range(1000):
            route_id = NamingGenerator.get_route_id()
            routes.append(route_id)
        self.assertEqual(len(routes), len(set(routes)))

    #Test that many entries that are likely colliding with the same entries still get unique route names
    #Comment out @ndb.transactional decorator on the create_route function in NamingGenerator
    #and this test will fail most times
    def test_contention_route_id(self):
        #Set up naming again, customized to only have 220 entries to create many collisions in naming
        AppEngineTest.set_up_naming(220)
        def get_route(results, index):
            route_name = NamingGenerator.get_route_id()
            self.assertIsNotNone(route_name)
            results[index] = route_name

        results = [None] * 200
        count = 0
        for i in range(1,41):
            threads = [None]
            from threading import Thread
            for j in range(1,6):
                t = Thread(target=get_route, args=(results, count ))
                threads.append(t)
                count += 1
                t.start()

            for j in range(1,6):
                threads[j].join()

        self.assertEqual(len(results), len(set(results)))

    def test_basic_member(self):
        route_id = NamingGenerator.get_route_id()
        route = models.Route.get_by_id(route_id)
        member_name = NamingGenerator.get_route_member_name(route)
        self.assertIsNotNone(member_name)

    def test_load_member(self):
        route_id = NamingGenerator.get_route_id()
        route = models.Route.get_by_id(route_id)
        members = []
        for i in range(500):
            member_name = NamingGenerator.get_route_member_name(route)
            members.append(member_name)
        self.assertEqual(len(members), len(set(members)))
        self.assertEqual(len(members), len(route.getMembers()))

    #control the number of animals available and make sure the enumeration works
    def test_loop_member(self):
        models.Naming.NUM_BINS = 2
        AppEngineTest.set_up_naming(10)

        animals = models.Naming.get_by_id(NamingGenerator.ANIM_KEY)
        last_animal = animals.items[len(animals.items) - 1]

        route_id = NamingGenerator.get_route_id()
        route = models.Route.get_by_id(route_id)

        member_name = None
        for i in range(40):
            member_name = NamingGenerator.get_route_member_name(route)
        self.assertEqual(member_name, last_animal + "3")

    def test_contention_member(self):
        #Set up naming again, customized to only have 220 entries to create many collisions in naming
        AppEngineTest.set_up_naming(220)

        route_id = NamingGenerator.get_route_id()
        route = models.Route.get_by_id(route_id)

        def get_route_member_name(results, index, route):
            member_name = NamingGenerator.get_route_member_name(route)
            self.assertIsNotNone(member_name)
            results[index] = member_name

        results = [None] * 200
        count = 0
        for i in range(1,41):
            threads = [None]
            from threading import Thread
            for j in range(1,6):
                t = Thread(target=get_route_member_name, args=(results, count, route))
                threads.append(t)
                count += 1
                t.start()

            for j in range(1,6):
                threads[j].join()

        self.assertEqual(len(results), len(set(results)))
        self.assertEqual(len(results), len(route.getMembers()))


class TestContractConforms(AppEngineTest):
    def setUp(self):
        super(TestContractConforms, self).setUp()
        self.expect_failed = 0
        self.expect_passed = 0

    def verify_true(self, val, message):
        if val:
            self.expect_passed += 1
        else:
            self.expect_failed += 1

    def expect_result(self, failed=None, passed=None):
        if passed is not None:
            self.assertEqual(passed, self.expect_passed)
        if failed is not None:
            self.assertEqual(failed, self.expect_failed)

    def test_required_valid_list_simple(self):
        contract = {
            "a": ["+"]
        }
        data = {
            "a": [10]
        }
        APIUtils.check_contract_conforms(contract, data, self.verify_true)
        self.expect_result(failed=0, passed=2) #1 for each entry, 1 for the list itself

    def test_required_valid_list_multiple(self):
        contract = {
            "a": ["+"]
        }
        data = {
            "a": [10,20,30]
        }
        APIUtils.check_contract_conforms(contract, data, self.verify_true)
        self.expect_result(failed=0, passed=4) #3 for each entry, 1 for the list itself

    def test_required_empty_list_simple(self):
        contract = {
            "a": ["+"]
        }
        data = {
            "a": []
        }
        APIUtils.check_contract_conforms(contract, data, self.verify_true)
        self.expect_result(failed=1, passed=0)

    def test_required_partial_missing_list(self):
        contract = {
            "a": ["+"]
        }
        data = {
            "a": [10,None,30]
        }
        APIUtils.check_contract_conforms(contract, data, self.verify_true)
        self.expect_result(failed=1, passed=3) #3 for each entry, 1 for the list itself

    def test_required_empty_list_complex(self):
        contract = {
            "a": [{
                "x": "+"
            }]
        }
        data = {
            "a": []
        }
        APIUtils.check_contract_conforms(contract, data, self.verify_true)
        self.expect_result(failed=1, passed=0)

    def test_required_none_value(self):
        contract = {
            "a": "+"
        }
        data = {
            "a": None
        }
        APIUtils.check_contract_conforms(contract, data, self.verify_true)
        self.expect_result(failed=1, passed=0)

    def test_required_none_value_str(self):
        contract = {
            "a": "+"
        }
        data = {
            "a": 'None'
        }
        APIUtils.check_contract_conforms(contract, data, self.verify_true)
        self.expect_result(failed=1, passed=0)

    def test_optional(self):
        contract = {
            "a": "*"
        }
        data = {
            "a": None
        }
        APIUtils.check_contract_conforms(contract, data, self.verify_true)
        self.expect_result(failed=0, passed=0)

    def test_nested_perfect(self):
        contract = {
            "a": "+",
            "b": {
                "x": "+",
                "y": "+"
            }
        }
        data = {
            "a": 11,
            "b": {
                "x": 10,
                "y": 12
            }
        }
        APIUtils.check_contract_conforms(contract, data, self.verify_true)
        self.expect_result(failed=0, passed=3)

    def test_nested_partial_fail(self):
        contract = {
            "a": "+",
            "b": {
                "x": "+",
                "y": "+"
            }
        }
        data = {
            "a": 11,
            "b": {
                #"x": 10,
                "y": 12
            }
        }
        APIUtils.check_contract_conforms(contract, data, self.verify_true)
        self.expect_result(failed=1, passed=2)

    def test_nested_list_perfect(self):
        contract = {
            "a": "+",
            "b": [{
                "x": "+",
                "y": "+"
            }]
        }
        data = {
            "a": 11,
            "b": [
                {
                    "x": 10,
                    "y": 12
                },
                {
                    "x": 20,
                    "y": 22,
                },
                {
                    "x": 40,
                    "y": 42,
                }
            ]
        }
        APIUtils.check_contract_conforms(contract, data, self.verify_true)
        self.expect_result(failed=0, passed=8) #7 for all the elements and 1 check for empty list

    def test_nested_list_partial_fails(self):
        contract = {
            "a": "+",
            "b": [{
                "x": "+",
                "y": "+"
            }]
        }

        data = {
            "a": 11,
            "b": [
                {
                    "x": 10,
                    "y": 12
                },
                {
                    #"x": 20,
                    "y": 22,
                },
                {
                    #"x": 40,
                    #"y": 42,
                }
            ]
        }
        APIUtils.check_contract_conforms(contract, data, self.verify_true)
        self.expect_result(failed=3, passed=5)

    def test_exact_value_match(self):
        contract = {
            "a": "exactVal"
        }
        data = {
            "a": "exactVal"
        }
        APIUtils.check_contract_conforms(contract, data, self.verify_true)
        self.expect_result(failed=0, passed=1)

    def test_exact_value_no_match(self):
        contract = {
            "a": "exactVal"
        }
        data = {
            "a": "NOTexactVal"
        }
        APIUtils.check_contract_conforms(contract, data, self.verify_true)
        self.expect_result(failed=1, passed=0)


class TestSplitMessage(AppEngineTest):
    ##### Test split client message
    def test_split_client_message_valid(self):
        message_raw = "#RedPuddle hey man how are you"
        (route_name, message) = MessageUtils.split_client_message(message_raw)
        self.assertEqual("redpuddle", route_name)
        self.assertEqual("hey man how are you", message)

    def test_split_client_message_valid_case(self):
        message_raw = "#rEdPUddle hey man how are you"
        (route_name, message) = MessageUtils.split_client_message(message_raw)
        self.assertEqual("redpuddle", route_name)
        self.assertEqual("hey man how are you", message)

    def test_split_client_message_invalid(self):
        message_raw = "#redpuddleheymanhowareyou"
        self.assertRaises(UtilsException, MessageUtils.split_client_message, message_raw)

    def test_split_client_message_no_identifier(self):
        message_raw = "red puddle hey man how are you"
        self.assertRaises(UtilsException, MessageUtils.split_client_message, message_raw)

    def test_split_client_message_invalid_empty(self):
        message_raw = ""
        self.assertRaises(UtilsException, MessageUtils.split_client_message, message_raw)

        message_raw = None
        self.assertRaises(UtilsException, MessageUtils.split_client_message, message_raw)

    def test_split_client_message_multiple_identifiers(self):
        message_raw = "garbage###RedPuddle hey man how are you"
        (route_name, message) = MessageUtils.split_client_message(message_raw)
        self.assertEqual("redpuddle", route_name)
        self.assertEqual("hey man how are you", message)

    def test_split_client_message_extra_space(self):
        message_raw = "#RedPuddle    hey man how are you"
        (route_name, message) = MessageUtils.split_client_message(message_raw)
        self.assertEqual("redpuddle", route_name)
        self.assertEqual("hey man how are you", message)

    ##### Test split owner message
    def test_split_owner_message_valid(self):
        message_raw = "cat@TangyBubble yikes that sounds scary"
        (member, route, message) = MessageUtils.split_owner_message(message_raw)
        self.assertEqual("cat", member)
        self.assertEqual("tangybubble", route)
        self.assertEqual("yikes that sounds scary", message)

    #should only preserve case sensitivity in message
    def test_split_owner_message_valid_case(self):
        message_raw = "Cat@tangybUbble yikes That soundS SCary"
        (member, route, message) = MessageUtils.split_owner_message(message_raw)
        self.assertEqual("cat", member)
        self.assertEqual("tangybubble", route)
        self.assertEqual("yikes That soundS SCary", message)

    def test_split_owner_message_invalid_no_space(self):
        message_raw = "cat@TangyBubbleyikesthatsoundsscary"
        self.assertRaises(UtilsException, MessageUtils.split_owner_message, message_raw)

    def test_split_owner_message_invalid_no_member(self):
        message_raw = "@TangyBubble yikesthatsoundsscary"
        self.assertRaises(UtilsException, MessageUtils.split_owner_message, message_raw)

    def test_split_owner_message_invalid_empty(self):
        message_raw = ""
        self.assertRaises(UtilsException, MessageUtils.split_owner_message, message_raw)

    def test_split_owner_message_multiple_ats(self):
        message_raw = "cat@TangyBubble @yikes El3k g"
        (member, route, message) = MessageUtils.split_owner_message(message_raw)
        self.assertEqual("cat", member)
        self.assertEqual("tangybubble", route)
        self.assertEqual("@yikes El3k g", message)

class TestEmailUtils(AppEngineTest):
    def test_get_email_valid(self):
        sender_field = "Joe <joe@gmail.com>"
        sender = MessageUtils.get_email_from_sender_field(sender_field)
        self.assertEqual("joe@gmail.com", sender)

    def test_get_email_valid_spaces(self):
        sender_field = " Joe  < joe@gmail.com >  "
        sender = MessageUtils.get_email_from_sender_field(sender_field)
        self.assertEqual("joe@gmail.com", sender)

    def test_get_email_invalid(self):
        sender_field = " Joe < joe@gmail.com"
        self.assertRaises(UtilsException, MessageUtils.get_email_from_sender_field, sender_field)

if __name__ == '__main__':
    unittest.main()
