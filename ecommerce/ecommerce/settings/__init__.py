import os

ENV = os.environ.get("ENV", "prod")

match ENV:
    case "prod":
        from .prod import *
    case "local":
        from .local import *
