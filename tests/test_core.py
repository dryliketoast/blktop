from blktop.graph import fmt_bytes, fmt_iops, fmt_rate, nice_ceiling
from blktop.layout import best_columns, split_rows
from blktop.sampler import describe, is_block_device, natural_key


def test_nice_ceiling_snaps_to_1_2_5():
    assert nice_ceiling(3) == 5
    assert nice_ceiling(5000) == 5000
    assert nice_ceiling(5001) == 10000
    assert nice_ceiling(0) == 1


def test_fmt_rate():
    assert fmt_rate(512) == "512 B/s"
    assert fmt_rate(1024 * 1024) == "1.00 MiB/s"
    assert fmt_rate(1_000_000, decimal=True) == "1.00 MB/s"
    assert fmt_bytes(512 * 10**9, decimal=True) == "512.00 GB"


def test_fmt_iops():
    assert fmt_iops(850) == "850 IOPS"
    assert fmt_iops(12_500) == "12.5k IOPS"


def test_split_rows_is_balanced_and_complete():
    items = list("abcde")
    assert split_rows(items, 4) == [["a", "b", "c"], ["d", "e"]]
    assert sum(split_rows(items, 2), []) == items


def test_best_columns_follows_terminal_shape():
    assert best_columns(1, 200, 50) == 1
    wide = best_columns(4, 240, 40)
    tall = best_columns(4, 60, 100)
    assert wide > tall


def _dev(root, name, **files):
    d = root / name
    for rel, text in files.items():
        p = d / rel.replace("__", "/")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    d.mkdir(exist_ok=True)


def test_is_block_device_skips_partitions_and_virtual(tmp_path):
    _dev(tmp_path, "sda")
    _dev(tmp_path, "loop0")
    assert is_block_device("sda", tmp_path)
    assert not is_block_device("sda1", tmp_path)  # partitions are not in /sys/block
    assert not is_block_device("loop0", tmp_path)


def test_describe_classifies_devices(tmp_path):
    _dev(tmp_path, "sda", queue__rotational="1\n", size="2000\n")
    _dev(tmp_path, "sdb", queue__rotational="0\n")
    _dev(tmp_path, "nvme0n1", queue__rotational="0\n")
    _dev(tmp_path, "dm-0", dm__name="vg0-root\n", dm__uuid="LVM-abc123\n", size="8\n")
    _dev(tmp_path, "dm-1", dm__name="cryptroot\n", dm__uuid="CRYPT-LUKS2-xyz\n")
    assert describe("sda", tmp_path) == ("sda", "HDD", 1_024_000)
    assert describe("sdb", tmp_path)[1] == "SSD"
    assert describe("nvme0n1", tmp_path)[1] == "NVMe"
    assert describe("dm-0", tmp_path) == ("vg0-root", "LVM", 4096)
    assert describe("dm-1", tmp_path)[:2] == ("cryptroot", "crypt")
    assert describe("md0", tmp_path)[1] == "RAID"


def test_natural_key_orders_dm_numerically():
    assert sorted(["dm-10", "dm-2", "sda"], key=natural_key) == ["dm-2", "dm-10", "sda"]
