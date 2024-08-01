from enum import Enum


class ServiceManagerStatus(Enum):
    # the service was able to interact with external service
    # it doesn't mean a 200 response was received from the external service
    ACK = "ACK"
    # we were not able to contact the external service, likely due to
    # rate limit requirements
    BUSY = "BUSY"


class SignTaskStatus(Enum):
    # the message was signed
    SUCCESS = "SUCCESS"
    # the message is in the queue
    PENDING = "PENDING"
    # number of message sign attempts has gone over the retry limit
    FAIL = "FAIL"
