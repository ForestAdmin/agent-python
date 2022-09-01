from forestadmin.agent_toolkit.options import Options


class BaseResource:
    def __init__(self, options: Options):
        self.option = options
