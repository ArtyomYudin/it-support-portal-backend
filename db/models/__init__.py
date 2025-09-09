# Импортируем модули, а не классы
from . import employee
from . import pacs
from . import core

__all__ = ["employee", "pacs", "core"]