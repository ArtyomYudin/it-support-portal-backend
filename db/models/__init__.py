# Импортируем модули, а не классы
from . import employee
from . import pacs
from . import core
from . import vpn

__all__ = ["employee", "pacs", "core", "vpn"]