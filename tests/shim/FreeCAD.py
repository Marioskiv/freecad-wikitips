class _P:
    store = {}
    def __init__(self, path): self.path = path
    def GetBool(self, k, d=False): return self.store.get((self.path, k), d)
    def SetBool(self, k, v): self.store[(self.path, k)] = v
    def SetString(self, k, v): self.store[(self.path, k)] = v
def ParamGet(p): return _P(p)
class Console:
    @staticmethod
    def PrintMessage(m): print(m, end='')
    PrintLog = PrintError = PrintMessage
