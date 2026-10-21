#!/usr/bin/env python3
"""Execute the captured Linux x86-64 client's pure radar gate function.

Usage: python3 data/chaff_gate_probe.py /path/to/linux64/aces
Checks the exact binary hash before executing code at its fixed virtual address.
No game process is started. Results use zero leakage, no ambiguity and no search.
"""

import ctypes as c
import hashlib
import json
import os
from pathlib import Path
import struct
import sys

EXPECTED = "e9138baaf46bbd865382d26d941c3339a6ba1ee65a1233790f95be99c705ba4f"
path = Path(sys.argv[1])
if hashlib.sha256(path.read_bytes()).hexdigest() != EXPECTED:
    raise SystemExit("Binary differs from the audited client; re-find addresses first.")

libc = c.CDLL(None, use_errno=True)
libc.mmap.restype = c.c_void_p
libc.mmap.argtypes = [c.c_void_p, c.c_size_t, c.c_int, c.c_int, c.c_int, c.c_long]
libc.munmap.argtypes = [c.c_void_p, c.c_size_t]
fd = os.open(path, os.O_RDONLY)
size = os.fstat(fd).st_size
# PROT_READ|PROT_EXEC, MAP_PRIVATE|MAP_FIXED_NOREPLACE.
# The pure function reads constants from .rodata and writes only its output buffer.
base = libc.mmap(0x400000, size, 5, 0x100002, fd, 0)
os.close(fd)
if base != 0x400000:
    raise OSError(c.get_errno(), "Cannot map client at its ELF virtual address")

try:
    gate = c.CFUNCTYPE(c.c_uint64, c.c_void_p, c.c_void_p)(0x5F27850)
    rows = []
    for signal_width in (5, 20, 60):
        for offset in (0, 5, 10, 15, 25, 35, 45, 60):
            args = c.create_string_buffer(0x58)
            output = c.create_string_buffer(12)
            fields = {
                0: 500 + offset, 4: 500 + offset, 8: signal_width,
                0x10: -3000, 0x14: 6000, 0x18: 3000, 0x1C: 5,
                0x20: 20, 0x24: 80, 0x28: 20 / 60, 0x2C: 0,
                0x30: 500, 0x34: 0, 0x38: 80,
            }
            for address, value in fields.items():
                struct.pack_into("<f", args, address, value)
            args[0xC] = b"\x01"  # Gate present.
            args[0x50] = b"\x00"  # radarCommon.useRefWidthForTargets=false.
            valid = gate(args, output)
            main, secondary, measured = struct.unpack("<3f", output.raw)
            rows.append(dict(signal_width=signal_width, offset=offset, valid=valid,
                             main=main, secondary=secondary, measured=measured))
    print(json.dumps(dict(sha256=EXPECTED, function="0x5f27850", rows=rows), indent=2))
finally:
    libc.munmap(base, size)
