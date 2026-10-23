# blktop

btop-style block device I/O throughput monitor with a tiling TUI. Sibling of
`nictop`, for HDD, SSD, NVMe, LVM, LUKS and md RAID devices instead of network
interfaces. Python project managed with [uv](https://docs.astral.sh/uv/).

## Setup

    uv sync

## Run

    uv run blktop
    uv run blktop --theme nord --interval 0.5
    uv run blktop --list-themes

Each tile shows one device: read throughput (▼) graphed above, write
throughput (▲) mirrored below, with the current rate, peak, graph scale, IOPS
and percent busy. The title shows the device kind (HDD/SSD/NVMe/LVM/crypt/RAID)
and size. Device-mapper devices are labelled with their mapper name
(e.g. `vg0-root (dm-0)`). Partitions, loop and ram devices are hidden.

## Keys

| Key | Action |
| --- | --- |
| `space` / `enter` | tick or untick the focused device (`tab` focuses the list) |
| `a` / `n` | select all / none |
| `t` / `T` | next / previous theme (or `ctrl+p` for the theme picker) |
| `b` | toggle binary (MiB/s) / decimal (MB/s) units |
| `s` | show or hide the device list |
| `q` | quit |

Selected tiles fill the whole area and re-flow when the terminal is resized.
Theme, selection and units are remembered in `~/.config/blktop/config.json`.

LVM and LUKS (`dm-*`) devices sit on top of physical disks, so their traffic also
shows up on the disk(s) underneath. Only the physical disks are ticked on first
run; tick the volumes you want to watch in the device list.

## Tests

    uv run pytest

## Standalone binary

    ./scripts/build.sh        # -> dist/blktop

Single file, no Python needed on the target. PyInstaller binaries are tied to the
OS, CPU architecture and glibc they were built on, so build on the oldest distro
you want to support (and once per architecture).
