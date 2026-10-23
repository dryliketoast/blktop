"""Per-device I/O throughput sampling built on psutil, with sysfs for device details."""

import re
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

import psutil

HISTORY = 1000
SYS_BLOCK = Path("/sys/block")
HIDDEN = ("loop", "ram")  # never interesting for throughput
NOT_DEFAULT = ("zram", "dm-")  # listed, but not ticked until asked for (dm sits on top of disks already shown)


@dataclass
class Device:
    name: str  # kernel name, e.g. nvme0n1 or dm-0
    label: str  # display name, e.g. vg0-root for a dm device
    kind: str  # NVMe, SSD, HDD, LVM, crypt, RAID, ...
    size: int  # bytes, 0 when unknown
    read: deque[float] = field(default_factory=lambda: deque(maxlen=HISTORY))
    write: deque[float] = field(default_factory=lambda: deque(maxlen=HISTORY))
    read_total: int = 0
    write_total: int = 0
    iops: float = 0.0
    busy: float = 0.0  # percent of the interval the device had I/O in flight
    _prev: tuple[int, int, int, int] | None = None


def natural_key(name: str) -> list[int | str]:
    """Sort dm-2 before dm-10."""
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", name)]


def _sys(root: Path, name: str, *parts: str) -> str | None:
    try:
        return root.joinpath(name, *parts).read_text().strip()
    except OSError:
        return None


def is_block_device(name: str, root: Path = SYS_BLOCK) -> bool:
    """Whole devices only: /sys/block lists disks, dm and md, but not partitions."""
    if name.startswith(HIDDEN):
        return False
    return not root.is_dir() or (root / name).is_dir()


def describe(name: str, root: Path = SYS_BLOCK) -> tuple[str, str, int]:
    """(display label, kind, size in bytes) for a block device."""
    label = name
    if name.startswith("dm-"):
        label = _sys(root, name, "dm", "name") or name
        uuid = _sys(root, name, "dm", "uuid") or ""
        prefix = uuid.split("-", 1)[0]
        kind = {"LVM": "LVM", "CRYPT": "crypt", "mpath": "multipath"}.get(prefix, "dm")
    elif name.startswith("md"):
        kind = "RAID"
    elif name.startswith("nvme"):
        kind = "NVMe"
    elif name.startswith("zram"):
        kind = "zram"
    else:
        kind = "HDD" if _sys(root, name, "queue", "rotational") == "1" else "SSD"
    sectors = _sys(root, name, "size")
    size = int(sectors) * 512 if sectors and sectors.isdigit() else 0
    return label, kind, size


class Sampler:
    def __init__(self) -> None:
        self.devices: dict[str, Device] = {}
        self._last: float | None = None

    def names(self) -> list[str]:
        return sorted(self.devices, key=natural_key)

    def sample(self) -> None:
        now = time.monotonic()
        dt = None if self._last is None else max(now - self._last, 1e-3)
        self._last = now
        counters = {
            n: c for n, c in (psutil.disk_io_counters(perdisk=True) or {}).items() if is_block_device(n)
        }

        for name in set(self.devices) - set(counters):
            del self.devices[name]
        for name, c in counters.items():
            dev = self.devices.get(name)
            if dev is None:
                dev = self.devices[name] = Device(name, *describe(name))
            busy_ms = getattr(c, "busy_time", 0)
            cur = (c.read_bytes, c.write_bytes, c.read_count + c.write_count, busy_ms)
            r_rate = w_rate = 0.0
            dev.iops = dev.busy = 0.0
            if dt and dev._prev:
                # a counter reset (device re-added) shows as a negative delta
                r_rate = max(0, cur[0] - dev._prev[0]) / dt
                w_rate = max(0, cur[1] - dev._prev[1]) / dt
                dev.iops = max(0, cur[2] - dev._prev[2]) / dt
                dev.busy = min(100.0, max(0, cur[3] - dev._prev[3]) / (dt * 10))
            dev._prev = cur
            dev.read.append(r_rate)
            dev.write.append(w_rate)
            dev.read_total, dev.write_total = c.read_bytes, c.write_bytes
