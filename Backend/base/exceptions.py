class BaseFHIRError(Exception):
    pass


class RouteNotImplemented(Exception):
    pass


class FeatureCodeIsEmpty(BaseFHIRError):
    pass


class TypeUnknown(BaseFHIRError):
    pass


class VariableNoneError(ValueError):
    pass


class ThresholdNoneError(ValueError):
    pass


class RegexUnrecognizedException(Exception):
    pass
