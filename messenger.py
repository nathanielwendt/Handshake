SOURCE_TYPE_SMS = 0
SOURCE_TYPE_NATIVE = 1
SOURCE_TYPE_EMAIL = 2
SOURCE_VALUE_NATIVE = "Native"

# method to set the messenger to be in mock mode
def set_mock_mode():


def send_message(channel, channel_type, message):
    if channel_type == SOURCE_TYPE_SMS:
        SMS.send(channel, message)
    elif channel_type == SOURCE_TYPE_EMAIL:
        Email.send(channel, message)
    elif channel_type == SOURCE_TYPE_NATIVE:
        GCM.send(channel, message)
    else:
        raise MessageException("Message channel type could not be determined")



class Email(object):
    HEADER_EMBED_FIELD = "On-Behalf-Of"

    @staticmethod
    def send(email, message):
        pass

    #make sure to set On-Behalf-Of on outgoing message

class SMS(object):
    @staticmethod
    def send(number, message):
        pass

class GCM(object):
    @staticmethod
    def send(reg_key, message):
        pass


class MessageException(BaseException):
    pass