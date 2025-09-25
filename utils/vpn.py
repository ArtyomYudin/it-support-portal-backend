import re


# Паттерны для событий входа и выхода Cisco ASA AnyConnect VPN
PATTERN_ADD = r'%ASA-7-746012: user-identity: Add IP-User mapping (\S+) - LOCAL\\\\([^@\s]+)(?:@[^\s]*)? Succeeded - VPN user'
PATTERN_DEL = r'%ASA-7-746013: user-identity: Delete IP-User mapping (\S+) - LOCAL\\\\([^@\s]+)(?:@[^\s]*)? Succeeded - VPN user'

def parse_event(event_str: str):
    """Возвращает тип события, internal_ip, username или None, если не удалось распарсить."""
    if not event_str:
        return None

    match_add = re.search(PATTERN_ADD, event_str)
    if match_add:
        internal_ip = match_add.group(1)
        username = match_add.group(2)
        return "login", internal_ip, username

    match_del = re.search(PATTERN_DEL, event_str)
    if match_del:
        internal_ip = match_del.group(1)
        username = match_del.group(2)
        return "logout", internal_ip, username

    return None