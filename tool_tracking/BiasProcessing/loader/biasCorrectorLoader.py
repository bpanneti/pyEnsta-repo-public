from tool_tracking.BiasProcessing.loader import roadLmsLoader as rl, icpLoader as il

class BiasCorrectorLoader():
    @staticmethod
    def load(conn, nodes, emitBiasCorrectors):
        loaders = [rl.RoadLmsLoader, il.IcpLoader]
        for loader in loaders:
            loader.load(conn, nodes, emitBiasCorrectors)