
class ClientCmd :
    def __init__(self):
        self.name_ = "",

    def get_name(self):
        return self.name_

    async def perform(self, cmd, data):

        return None