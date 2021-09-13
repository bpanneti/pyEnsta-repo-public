from enum import Enum
from tool_tracking.BiasProcessing.corrector.biasCorrector import BIAS_CORRECTORS_TYPE

from tool_tracking.BiasProcessing.interface.roadLmsInterface import RoadLmsInterface
from tool_tracking.BiasProcessing.corrector.roadLms import RoadLms

from tool_tracking.BiasProcessing.interface.icpInterface import IcpInterface
from tool_tracking.BiasProcessing.corrector.icp import Icp

class ELEMENT(Enum):
    CORRECTOR = 0
    INTERFACE = 1


class Dictionary:
    @staticmethod
    def get():
        correctors = [(RoadLms, RoadLmsInterface), (Icp, IcpInterface)]
        dictionary = dict()

        types = iter(BIAS_CORRECTORS_TYPE)
        next(types)

        for kind in types:
            dictionary[kind.value] = correctors[kind.value]
        return dictionary
