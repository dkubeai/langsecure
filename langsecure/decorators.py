from . import factory

def implements(fqcn: str):
    def decorator(cls):
        factory.register(fqcn, cls)
        return cls
    return decorator
