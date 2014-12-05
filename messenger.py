SOURCE_TYPE_SMS = 0
SOURCE_TYPE_NATIVE = 1
SOURCE_TYPE_EMAIL = 2
SOURCE_VALUE_NATIVE = "Native"

# method to set the messenger to be in mock mode
def set_mock_mode():
    pass

def send_message(channel, channel_type, message):
    if channel_type == SOURCE_TYPE_SMS:
        pass
    elif channel_type == SOURCE_TYPE_EMAIL:
        pass
    elif channel_type == SOURCE_TYPE_NATIVE:
        pass
    else:
        raise MessageSendException()


class MessageSendException(BaseException):
    pass

class Email(object):
    HEADER_EMBED_FIELD = "On-Behalf-Of"
    pass

    #make sure to set On-Behalf-Of on outgoing message

class SMS(object):
    pass

class GCM(object):
    pass