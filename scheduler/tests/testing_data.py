class Message:
    def __init__(self, key, value):
        self.key = key
        self.value = value


right_message = Message(
    key="test_id_1",
    value={
        "url": "test_url",
        "body": {"args": "test_args"},
        "tenant": "test_tenant",
        "response_topic": "test_response_topic",
    },
)

wrong_message = Message(
    key="test_id_2",
    value={
        "ref": "test_ref",
        "body": {"args": "test_args"},
        "response_topic": "test_response_topic",
    },
)
