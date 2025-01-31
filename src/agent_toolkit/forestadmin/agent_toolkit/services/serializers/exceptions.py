class JsonApiException(Exception):
    pass


class JsonApiSerializerException(JsonApiException):
    pass


class JsonApiDeserializerException(JsonApiException):
    pass
