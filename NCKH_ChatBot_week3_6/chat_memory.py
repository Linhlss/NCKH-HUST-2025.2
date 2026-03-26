
class ChatMemory:
    def __init__(self):
        self.history = []

    def add(self, user, bot):
        self.history.append({"user": user, "bot": bot})

    def get_context(self, k=3):
        return self.history[-k:]
