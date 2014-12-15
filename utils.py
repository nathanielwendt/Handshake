import re
from lib import cloudstorage
import uuid
import datetime
import time
import models
from google.appengine.ext import ndb
import random
import messenger
from email.parser import HeaderParser

class UtilsException(Exception):
    def __init__(self, message):
        self.message = message

class MessageUtils(object):
    CLIENT_MESSAGE_IDENTIFIER = "#"
    OWNER_MESSAGE_IDENTIFIER = "@"

    @staticmethod
    def get_email_from_sender_field(sender_field):
        match = re.search(r'(\<){1}(.)*?(\>){1}', sender_field)
        if match:
            sender = match.group(0)
            return sender[1: len(sender) - 1].strip() #trim < >
        else:
            raise UtilsException("could not find email from field")

    @staticmethod
    # expects a message formatted as:
    # format:      #routeName the rest of the body here
    # example:      #leaf green hey man how is it going
    # @returns a tuple formatted as (route_name, message_stripped)
    # @throws exception if message is not formatted properly
    def split_client_message(message):
        if message == "" or message is None:
            raise UtilsException("split message: empty or none input")

        regex = r'(' + MessageUtils.CLIENT_MESSAGE_IDENTIFIER + '){1}([\w-])+(\s){1}'
        route_name_reg = re.search(regex, message)

        if route_name_reg:
            route_name_raw = route_name_reg.group(0).strip()
            reg_match_begin = message.find(route_name_raw) #if multiple chars before @ symbol, need additional offset
            message = message[reg_match_begin + len(route_name_raw) + 1:].strip()
            route_name = route_name_raw[route_name_raw.find(MessageUtils.CLIENT_MESSAGE_IDENTIFIER) + 1:].lower()
            return route_name, message
        else:
            raise UtilsException("split message: could not find route name")

    @staticmethod
    def split_owner_message(message):
        if message == "" or message is None:
            raise UtilsException("split message: empty or none input")

        identifier_index = message.find(MessageUtils.OWNER_MESSAGE_IDENTIFIER)
        if identifier_index <= 1:
            raise UtilsException("split message: malformed message")

        member = message[:identifier_index].strip().lower()
        remainder = message[identifier_index + 1:]
        first_space = remainder.find(" ")
        if first_space == -1:
            raise UtilsException("split message: malformed message")

        route = remainder[:first_space].strip().lower()
        message = remainder[first_space + 1:].strip()
        return member, route, message

    @staticmethod
    def is_client_message(message):
        return message.find(MessageUtils.CLIENT_MESSAGE_IDENTIFIER) == 0

    @staticmethod
    def is_owner_message(message):
        return message.find(MessageUtils.OWNER_MESSAGE_IDENTIFIER) > 0

    @staticmethod
    def strip_country_code_from_number(number):
        plus_index = number.find("+")
        if plus_index > -1:
            return number[plus_index + 2:]
        else:
            return number

    @staticmethod
    def get_header_from_message(message):
        parser = HeaderParser()
        headers = parser.parsestr(message.as_string())
        return headers.get(messenger.Email.HEADER_EMBED_FIELD)

    @staticmethod
    def split_owner_subject(message_subject):
        portions = message_subject.split(":")
        member, route_id, message = MessageUtils.split_owner_message(portions[2])
        return member, route_id

    @staticmethod
    def strip_html(content):
        tag = False
        quote = False
        out = ""

        for c in content:
                if c == '<' and not quote:
                    tag = True
                elif c == '>' and not quote:
                    tag = False
                elif (c == '"' or c == "'") and tag:
                    quote = not quote
                elif not tag:
                    out = out + c

        return out

class BaseUtils(object):
    @staticmethod
    def datetime_to_epoch(dt):
        epoch = datetime.datetime.utcfromtimestamp(0)
        delta = dt - epoch
        return delta.total_seconds()

    @staticmethod
    def epoch_to_datetime(seconds):
        return datetime.datetime.fromtimestamp(seconds)


class NamingGenerator(object):
    NOUN_KEY = "nouns"
    ADJ_KEY = "adjectives"
    ANIM_KEY = "animals"
    TWILIO_KEY = "twilio"
    FILES = {
        "adjectives": "adjectives.txt",
        "animals": "animals.txt",
        "nouns": "nouns.txt"
    }
    PATH_BASE = "/handshake-app.appspot.com/"

    @staticmethod
    #retrieves a route name that is guaranteed to be unique
    #will continue trying routes until it finds a unique entry
    #the route entry will be created with the route name used as an id and placeholder
    #to 'save' the spot of the route entry for the assigned name
    def get_route_id():
        adjectives = models.Naming.get_by_id(NamingGenerator.ADJ_KEY)
        nouns = models.Naming.get_by_id(NamingGenerator.NOUN_KEY)

        while True:
            time_seed = int(time.time() * 100) #time in deci-seconds
            adjective = adjectives.get_random_entry(time_seed)
            noun = nouns.get_random_entry(time_seed)
            cand_route_name = (adjective + noun).lower().strip()
            cand_route_display_name = (adjective + noun).strip()
            try:
                NamingGenerator.create_route(cand_route_name, cand_route_display_name)
                return cand_route_name
            except UtilsException:
                continue


    @staticmethod
    @ndb.transactional(retries=10)
    #creates a dummy route entry to reserve the name (subsequent requests will see that it now exists)
    #if the route already exists, throws an exception
    def create_route(cand_route_name, cand_route_display_name):
        route = models.Route.get_by_id(cand_route_name)
        if route is None:
            models.Route(id=cand_route_name, displayName=cand_route_display_name).put()
        else:
            raise UtilsException("route exists for that name")

    @staticmethod
    def generate_route_member(route_entity, user_id):
        animals = models.Naming.get_by_id(NamingGenerator.ANIM_KEY)
        animals_length = len(animals.items)

        user_name = models.User.get_display_name_from_id(user_id)
        if user_name is None:
            raise UtilsException("could not find user associated with user id")

        @ndb.transactional(retries=10)
        def get_next():
            created_animals = models.RouteMember.query(ancestor=route_entity.key).fetch()
            created_animals_length = len(created_animals)

            multiple = created_animals_length / animals_length
            index = (created_animals_length % animals_length + 1) - 1

            if multiple == 0:
                append_item = ''
            else:
                append_item = str(multiple)

            member_id = animals.items[index] + append_item
            member = models.RouteMember.create_entry(route_entity, member_id, user_id, user_name)
            return member

        return get_next()

    @staticmethod
    # Populates the Naming model with an entry for each item in FILES
    # Does not check if the file size is too large to itemize into the datastore entry
    # so it is assumed that check is made in creating the input files
    def initialize_ds_names(local_dir=None, size_limit=None):
        for name,file in NamingGenerator.FILES.iteritems():
            valid_items = []
            delim = ""

            if local_dir is None:
                gcs_file = cloudstorage.open(filename=NamingGenerator.PATH_BASE + file, mode='r')
            else:
                gcs_file = open(local_dir + file, mode='r')
            for line in gcs_file:
                line = line.strip()
                if not line or\
                        len(line.split(" ")) > 1 or\
                        line.find("-") > 0 or\
                        len(line) > 8:
                    continue

                valid_items.append(line.capitalize())

            entry = models.Naming(id=name)
            random.shuffle(valid_items)
            if size_limit is None:
                entry.items = valid_items
            else:
                entry.items = valid_items[0:size_limit]
            entry.put()


class APIUtils(object):
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
                    #check for empty list, or empty list str representation (from json), or check for wildcard as second
                    #argument on list indicating that an empty list is ok
                    verify_empty_list_cond = data_value != '[]' and data_value != [] or c_value[1] == "*"
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