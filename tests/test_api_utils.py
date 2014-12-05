import unittest
from test_utils import AppEngineTest
from utils import APIUtils, APIUtilsException

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


class TestNameConversion(AppEngineTest):
    def test_basic(self):
        name = "green%20leaf"
        self.assertEqual("green_leaf", APIUtils.route_name_to_backend_format(name))

    def test_underscore_to_name(self):
        underscore = "green_leaf"
        self.assertEqual("green%20leaf", APIUtils.name_to_external_format(underscore))

class TestSplitMessage(AppEngineTest):

    ##### Test split client message
    def test_split_client_message_valid(self):
        message_raw = "#red puddle hey man how are you"
        (route_name, message) = APIUtils.split_client_message(message_raw)
        self.assertEqual("red puddle", route_name)
        self.assertEqual("hey man how are you", message)

    def test_split_client_message_valid_case(self):
        message_raw = "#rEd PUddle hey man how are you"
        (route_name, message) = APIUtils.split_client_message(message_raw)
        self.assertEqual("red puddle", route_name)
        self.assertEqual("hey man how are you", message)

    def test_split_client_message_invalid(self):
        message_raw = "#redpuddleheymanhowareyou"
        self.assertRaises(APIUtilsException, APIUtils.split_client_message, message_raw)

    def test_split_client_message_no_identifier(self):
        message_raw = "red puddle hey man how are you"
        self.assertRaises(APIUtilsException, APIUtils.split_client_message, message_raw)

    def test_split_client_message_invalid_empty(self):
        message_raw = ""
        self.assertRaises(APIUtilsException, APIUtils.split_client_message, message_raw)

        message_raw = None
        self.assertRaises(APIUtilsException, APIUtils.split_client_message, message_raw)

    def test_split_client_message_multiple_identifiers(self):
        message_raw = "garbage###red puddle hey man how are you"
        (route_name, message) = APIUtils.split_client_message(message_raw)
        self.assertEqual("red puddle", route_name)
        self.assertEqual("hey man how are you", message)

    ##### Test split owner message
    def test_split_owner_message_valid(self):
        message_raw = "@nwendt2 yikes that sounds scary"
        (short_id, message) = APIUtils.split_owner_message(message_raw)
        self.assertEqual("nwendt2", short_id)
        self.assertEqual("yikes that sounds scary", message)

    def test_split_owner_message_valid_case(self):
        message_raw = "@NwenDT2 yikes that sounds scary"
        (short_id, message) = APIUtils.split_owner_message(message_raw)
        self.assertEqual("nwendt2", short_id)
        self.assertEqual("yikes that sounds scary", message)

    def test_split_owner_message_invalid(self):
        message_raw = "@nwendt2yikesthatsoundsscary"
        self.assertRaises(APIUtilsException, APIUtils.split_owner_message, message_raw)

    def test_split_owner_no_identifier(self):
        message_raw = "nwendt2 yikes that sounds scary"
        self.assertRaises(APIUtilsException, APIUtils.split_owner_message, message_raw)

    def test_split_owner_message_invalid_empty(self):
        message_raw = ""
        self.assertRaises(APIUtilsException, APIUtils.split_owner_message, message_raw)

        message_raw = None
        self.assertRaises(APIUtilsException, APIUtils.split_owner_message, message_raw)

    def test_split_owner_message_multiple_identifiers(self):
        message_raw = "garbage@@@@nwendt2 yikes that sounds scary"
        (route_name, message) = APIUtils.split_owner_message(message_raw)
        self.assertEqual("nwendt2", route_name)
        self.assertEqual("yikes that sounds scary", message)

        import models
        models.Message(id="aofeijf").put()


class TestGetEmailFromSender(AppEngineTest):
    def test_get_email_valid(self):
        sender_field = "Joe <joe@gmail.com>"
        sender = APIUtils.get_email_from_sender_field(sender_field)
        self.assertEqual("joe@gmail.com", sender)

    def test_get_email_valid_spaces(self):
        sender_field = " Joe  < joe@gmail.com >  "
        sender = APIUtils.get_email_from_sender_field(sender_field)
        self.assertEqual("joe@gmail.com", sender)

    def test_get_email_invalid(self):
        sender_field = " Joe < joe@gmail.com"
        self.assertRaises(APIUtilsException, APIUtils.get_email_from_sender_field, sender_field)

if __name__ == '__main__':
    unittest.main()
