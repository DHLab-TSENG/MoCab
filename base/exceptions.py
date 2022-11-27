class BaseFHIRError(Exception):
    pass


class FeatureCodeIsEmpty(BaseFHIRError):
    pass


class TypeUnknown(BaseFHIRError):
    pass
