from lib.twilio.rest import TwilioRestClient
import urllib, urllib2

SOURCE_TYPE_SMS = 0
SOURCE_TYPE_NATIVE = 1
SOURCE_TYPE_EMAIL = 2
SOURCE_VALUE_NATIVE = "Native"


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
    TWILIO_NUM = "13603835654"

    @staticmethod
    def send(number, message):
        account = "ACe0577efeaa81892073804b438bd0887d"
        token = "4d61f59af147ca5ccf562e08f72e3696"
        client = TwilioRestClient(account, token)

        message = client.messages.create(to=number, from_=SMS.TWILIO_NUM,
                                         body=message)

class GCM(object):
    PUSH_URL = 'https://android.googleapis.com/gcm/send'
    GOOGLE_API_KEY = 'AIzaSyBzq9JM80Oa7lfPcq2AVp3eFY94CVTjb-Y'

    @staticmethod
    def send(reg_key, message):
        values = {
            'registration_id': reg_key,
            'data': message
        }

        body = urllib.urlencode(values)
        request = urllib2.Request(GCM.PUSH_URL, body)
        request.add_header('Authorization', 'key=' + GCM.GOOGLE_API_KEY)
        response = urllib2.urlopen(request)


class MessageException(BaseException):
    pass