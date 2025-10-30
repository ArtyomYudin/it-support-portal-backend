import asyncio
from asyncio import to_thread
from datetime import datetime, timezone
import winrm
import json
from typing import Optional
from celery import shared_task
from db.database import AsyncSessionLocal
from core.settings import settings
from core.logging_config import logger
from rabbitmq.schemas import Event
from services.dhcp_service import add_dhcp_scope, add_dhcp_scope_statistics, add_dhcp_scope_lease
from utils.celery import publish_to_exchange

RABBITMQ_URL = (
    f"amqp://{settings.RMQ_CELERY_USER}:{settings.RMQ_CELERY_PASSWORD}"
    f"@{settings.RMQ_HOST}:{settings.RMQ_PORT}/{settings.RMQ_VIRTUAL_HOST}"
)

REDIS_URL = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"

PS_SCOPE = r"""
    $ErrorActionPreference = "Stop"
    Import-Module DhcpServer

    $ServerName = "{server}"
    $scopes = Get-DhcpServerv4Scope -ComputerName $ServerName

    $result = foreach ($scope in $scopes) {{
        [PSCustomObject]@{{
            ScopeId      = $scope.ScopeId.IPAddressToString
            Name         = $scope.Name.ToString()
            SubnetMask   = $scope.SubnetMask.IPAddressToString
            StartRange   = $scope.StartRange.IPAddressToString
            EndRange     = $scope.EndRange.IPAddressToString
            State        = $scope.State.ToString()
        }}
    }}
    $result | ConvertTo-Json -Compress -Depth 3
"""

PS_SCOPE_STATS = r"""
    $ErrorActionPreference = "Stop"
    Import-Module DhcpServer
    
    $ServerName = "{server}"
    
    # Получаем все scopes и статистику
    $scopes = Get-DhcpServerv4Scope -ComputerName $ServerName
    $stats  = Get-DhcpServerv4ScopeStatistics -ComputerName $ServerName
    
    # Хэш для быстрого поиска статистики по ScopeId
    $statHash = @{{}}
    foreach ($stat in $stats) {{
        $statHash[$stat.ScopeId.IPAddressToString] = $stat
    }}
    
    # Формируем результат
    $result = foreach ($scope in $scopes) {{
        $id = $scope.ScopeId.IPAddressToString
        $stat = $statHash[$id]
        if ($stat) {{
            $total = $stat.AddressesFree + $stat.AddressesInUse
            $pct = if ($total -eq 0) {{ 0.0 }} else {{
                [math]::Round(($stat.AddressesInUse / $total) * 100, 2)
            }}
            [PSCustomObject]@{{
                ScopeId         = $id
                Name            = $scope.Name
                AddressesFree   = $stat.AddressesFree
                AddressesInUse  = $stat.AddressesInUse
                PendingOffers   = $stat.PendingOffers
                TotalAddresses  = $total
                PercentageInUse = $pct
            }}
        }}
    }}
    
    $result | ConvertTo-Json -Compress -Depth 3
"""

PS_SCOPE_LEASE = r"""
    $ErrorActionPreference = "Stop"
    Import-Module DhcpServer

    $ServerName = "{server}"
    $scopes = Get-DhcpServerv4Scope -ComputerName $ServerName

    $allLeases = foreach ($scope in $scopes) {{
        $leases = Get-DhcpServerv4Lease -ComputerName $ServerName -ScopeId $scope.ScopeId -ErrorAction SilentlyContinue
        foreach ($lease in $leases) {{
            [PSCustomObject]@{{
                ScopeId             = $scope.ScopeId.IPAddressToString
                IPAddress           = $lease.IPAddress.IPAddressToString
                ClientId            = if ($lease.ClientId) {{ $lease.ClientId }} else {{ $null }}
                HostName            = if ($lease.HostName) {{ $lease.HostName }} else {{ $null }}
                LeaseExpiryTime     = if ($lease.LeaseExpiryTime) {{ $lease.LeaseExpiryTime.ToString("yyyy-MM-ddTHH:mm:ssZ") }} else {{ $null }}
                AddressState        = $lease.AddressState.ToString()
                ClientHardwareAddress = if ($lease.ClientHardwareAddress) {{ $lease.ClientHardwareAddress }} else {{ $null }}
            }}
        }}
    }}

    $allLeases | ConvertTo-Json -Compress -Depth 3
"""

async def _publish_event(processed_servers, event, collected_at):
    if processed_servers:
        payload = {
            "event": event,
            "collected_at": collected_at,
            "servers": processed_servers,
        }
        try:
            await publish_to_exchange(payload, RABBITMQ_URL)
            logger.info(f"Published DHCP collection event for {len(processed_servers)} servers at {collected_at}")
        except Exception as e:
            logger.exception(f"Failed to publish DHCP collection event: {e}")
    else:
        logger.warning("No DHCP servers were successfully processed — skipping event publication")

async def _to_thread(session, server, script):
    # pywinrm — синхронная библиотека, выполняем в отдельном потоке
    r = await to_thread(session.run_ps, script)

    stdout = r.std_out.decode(errors="ignore").strip()
    stderr = r.std_err.decode(errors="ignore").strip()

    if r.status_code != 0:
        logger.error(f"[{server}] PowerShell failed: {stderr}")
        return None

    if not stdout:
        logger.warning(f"[{server}] Empty PowerShell output")
        return None

    try:
        data = json.loads(stdout)
        if isinstance(data, dict):
            data = [data]
    except json.JSONDecodeError as e:
        logger.error(f"[{server}] JSON parse error: {e} — output:\n{stdout}")
        return None

    return data


async def get_dhcp_scope():
    collected_at = datetime.now(timezone.utc)  # ЕДИНЫЙ МОМЕНТ ВРЕМЕНИ
    processed_servers = []  # ← будем собирать успешно обработанные серверы

    async with AsyncSessionLocal() as db:
        for server in settings.DHCP_SERVERS:
            logger.info(f"Fetching DHCP scopes from {server}...")

            # создаём WinRM-сессию для конкретного сервера
            session = winrm.Session(
                server,
                auth=(settings.KERBEROS_USER, ""),
                transport="kerberos",
                server_cert_validation="ignore",
            )

            script = PS_SCOPE.format(server=server)

            try:
                data = await _to_thread(session, server, script)
                if data is None:  # обрабатываем ошибку
                    continue

                await add_dhcp_scope(db, data, server)
                processed_servers.append(server)  # ← только при успехе!
                logger.info(f"[{server}] {len(data)} scopes processed successfully")

            except Exception as e:
                logger.exception(f"[{server}] Failed to fetch DHCP scopes: {e}")

    # Отправка события
    await _publish_event(processed_servers, Event.EVENT_DHCP_SCOPES_COLLECTED, collected_at)

async def get_dhcp_scope_statistics():
    collected_at = datetime.now(timezone.utc)  # ЕДИНЫЙ МОМЕНТ ВРЕМЕНИ
    processed_servers = []  # ← будем собирать успешно обработанные серверы

    async with AsyncSessionLocal() as db:
        for server in settings.DHCP_SERVERS:
            logger.info(f"[{server}] Fetching DHCP scope statistics...")

            session = winrm.Session(
                server,
                auth=(settings.KERBEROS_USER, ""),
                transport="kerberos",
                server_cert_validation="ignore",
            )

            script = PS_SCOPE_STATS.format(server=server)

            try:
                data = await _to_thread(session, server, script)
                if data is None:  # обрабатываем ошибку
                    continue

                await add_dhcp_scope_statistics(db, data, server, collected_at)
                processed_servers.append(server)  # ← только при успехе!
                logger.info(f"[{server}] {len(data)} statistics records processed")

            except Exception as e:
                logger.exception(f"[{server}] Failed to fetch statistics: {e}")

    # Отправка события
    await _publish_event(processed_servers, Event.EVENT_DHCP_STATISTICS_COLLECTED, collected_at)

async def get_dhcp_scope_lease():
    collected_at = datetime.now(timezone.utc)  # ЕДИНЫЙ МОМЕНТ ВРЕМЕНИ
    processed_servers = []

    async with AsyncSessionLocal() as db:
        for server in settings.DHCP_SERVERS:
            logger.info(f"[{server}] Fetching DHCP leases...")

            session = winrm.Session(
                server,
                auth=(settings.KERBEROS_USER, ""),
                transport="kerberos",
                server_cert_validation="ignore",
            )

            script = PS_SCOPE_LEASE.format(server=server)

            try:
                data = await _to_thread(session, server, script)
                if data is None:  # обрабатываем ошибку
                    continue

                await add_dhcp_scope_lease(db, data, server, collected_at)
                logger.info(f"[{server}] {len(data)} leases processed")

            except Exception as e:
                logger.exception(f"[{server}] Failed to fetch leases: {e}")

    # Отправка события
    await _publish_event(processed_servers, Event.EVENT_DHCP_LEASES_COLLECTED, collected_at)


@shared_task(bind=True, max_retries=3)
def fetch_dhcp_scope_task(self, token: Optional[str] = None):
    try:
        asyncio.run(get_dhcp_scope())
    except Exception as exc:
        logger.error(f"Task fetch_dhcp_scope_task failed: {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)

@shared_task(bind=True, max_retries=3)
def fetch_dhcp_scope_statistics_task(self, token: Optional[str] = None):
    try:
        asyncio.run(get_dhcp_scope_statistics())
    except Exception as exc:
        logger.error(f"Task fetch_dhcp_scope_statistics_task failed: {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)

@shared_task(bind=True, max_retries=3)
def fetch_dhcp_scope_lease_task(self, token: Optional[str] = None):
    try:
        asyncio.run(get_dhcp_scope_lease())
    except Exception as exc:
        logger.error(f"Task fetch_dhcp_scope_lease_task failed: {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)



if __name__ == "__main__":
    # asyncio.run(get_dhcp_scope())
    # asyncio.run(get_dhcp_scope_statistic())
    asyncio.run(get_dhcp_scope_lease())