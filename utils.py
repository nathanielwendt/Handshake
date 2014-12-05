import datetime
import urllib
import re

class APIUtils(object):
    @staticmethod
    def get_email_from_sender_field(sender_field):
        match = re.search(r'(\<){1}(.)*?(\>){1}', sender_field)
        if match:
            sender = match.group(0)
            return sender[1: len(sender) - 1].strip() #trim < >
        else:
            raise APIUtilsException("could not find email from field")

    @staticmethod
    def get_default_success_response():
        return {"status": "success"}

    @staticmethod
    def datetime_to_epoch(dt):
        epoch = datetime.datetime.utcfromtimestamp(0)
        delta = dt - epoch
        return delta.total_seconds()

    @staticmethod
    def epoch_to_datetime(seconds):
        return datetime.datetime.fromtimestamp(seconds)

    CLIENT_MESSAGE_IDENTIFIER = "#"
    OWNER_MESSAGE_IDENTIFIER = "@"

    @staticmethod
    # expects a message formatted as:
    # format:      #routeName the rest of the body here
    # example:      #leaf green hey man how is it going
    # @returns a tuple formatted as (route_name, message_stripped)
    # @throws exception if message is not formatted properly
    def split_client_message(message):
        if message == "" or message is None:
            raise APIUtilsException("split message: empty or none input")

        regex = r'(' + APIUtils.CLIENT_MESSAGE_IDENTIFIER + '){1}([\w-])+(\s){1}([\w-])+'
        route_name_reg = re.search(regex, message)

        if route_name_reg:
            route_name_raw = route_name_reg.group(0)
            reg_match_begin = message.find(route_name_raw) #if multiple chars before @ symbol, need additional offset
            message = message[reg_match_begin + len(route_name_raw) + 1:]
            route_name = route_name_raw[route_name_raw.find(APIUtils.CLIENT_MESSAGE_IDENTIFIER) + 1:].lower()
            return route_name, message
        else:
            raise APIUtilsException("split message: could not find route name")

    @staticmethod
    def split_owner_message(message):
        if message == "" or message is None:
            raise APIUtilsException("split message: empty or none input")

        regex = r'(' + APIUtils.OWNER_MESSAGE_IDENTIFIER + '){1}([\w-])+(\s){1}'
        route_name_reg = re.search(regex, message)

        if route_name_reg:
            route_name_raw = route_name_reg.group(0)
            reg_match_begin = message.find(route_name_raw) #if multiple chars before @ symbol, need additional offset
            message = message[reg_match_begin + len(route_name_raw):]
            client_id = route_name_raw.strip()[1:].lower()
            return client_id, message
        else:
            raise APIUtilsException("split message: could not find client short id")


    def is_client_message(self, message):
        return message.find(APIUtils.CLIENT_MESSAGE_IDENTIFIER) == 0

    def is_owner_message(self, message):
        return message.find(APIUtils.OWNER_MESSAGE_IDENTIFIER) == 0


    @staticmethod
    def check_contract_conforms(contract, data, verify_true_action):
        for c_key, c_value in contract.items():
            # recursively follow subdirectories, contract follows down a level as well
            if isinstance(c_value, dict):
                try:
                    APIUtils.check_contract_conforms(c_value, data[c_key], verify_true_action)
                except KeyError:
                    APIUtils.check_partial_for_requires(c_value, verify_true_action)
            else:
                if c_value == "*" and isinstance(c_value, basestring):
                    pass
                elif isinstance(c_value, list):
                    sub_contract = c_value[0]
                    data_value = data[c_key]
                    verify_empty_list_cond = data_value != '[]' and data_value != []
                    verify_true_action(verify_empty_list_cond, c_key + " is an empty list and it is required")

                    if isinstance(sub_contract, dict):
                        for item in data_value:
                            APIUtils.check_contract_conforms(sub_contract, item, verify_true_action)
                    else:
                        for item in data_value:
                            APIUtils.check_contract_conforms({c_key: sub_contract}, {c_key: item}, verify_true_action)
                elif c_value == "!" and isinstance(c_value, basestring):
                    try:
                        val = data[c_key]
                        verify_true_action(False, "value was included when contract excluded it")
                    except KeyError:
                        continue
                elif c_value == "+" and isinstance(c_value, basestring):
                    try:
                        data_value = data[c_key]
                        verify_none_list_cond = data_value != 'None' and data_value != None
                        verify_true_action(verify_none_list_cond, c_key + " (or a list item with " + c_key + ") is None and it is required")
                    except KeyError:
                        verify_true_action(False, "contract key '" + c_key + "' was not found")
                else:
                    verify_true_action(c_value == data[c_key], "key: '" + c_key + "' should be exactly >> " + c_value + " but is instead >> " + data[c_key])

    @staticmethod
    def check_partial_for_requires(partial, verify_true_action):
        for key, value in partial.items():
            if isinstance(value, dict):
                APIUtils.check_partial_for_requires(value, verify_true_action)
            elif isinstance(value, list):
                for list_item in value:
                    APIUtils.check_partial_for_requires(list_item, verify_true_action)
            else:
                verify_true_action(value == "*", "If data doesn't have a key for this nested element, "
                                             "all fields must be wildcard allowed")


class APIUtilsException(BaseException):
    pass