#!/usr/bin/env python3
"""Probe scalar tracking, non-rotating shell drag and signature profile evaluation.

Usage: python3 data/chaff_tracking_probe.py /path/to/linux64/aces
Runs only the named functions in a private ELF mapping. The scalar-filter probe
stubs the angular helper to success; drag probes have zero external force and a
fixed sea-level atmosphere. No executable file or running game is modified.
"""
import ctypes as c
import hashlib
import json
from pathlib import Path
import struct
import sys

EXPECTED = "e9138baaf46bbd865382d26d941c3339a6ba1ee65a1233790f95be99c705ba4f"
blob = Path(sys.argv[1]).read_bytes()
if hashlib.sha256(blob).hexdigest() != EXPECTED:
    raise SystemExit("Client differs from the audited binary; re-find addresses first.")
libc = c.CDLL(None, use_errno=True)
libc.mmap.restype = c.c_void_p
libc.mmap.argtypes = [c.c_void_p, c.c_size_t, c.c_int, c.c_int, c.c_int, c.c_long]
libc.munmap.argtypes = [c.c_void_p, c.c_size_t]
start, end = 0x400000, 0xB600000
base = libc.mmap(start, end - start, 7, 0x100022, -1, 0)
if base != start:
    raise OSError(c.get_errno(), "Cannot map the audited ELF at its virtual address")

def put(buf, address, value):
    struct.pack_into("<f", buf, address, value)

def get(buf, address):
    return struct.unpack_from("<f", buf, address)[0]

def constant_float(address, value):
    c.memmove(address, b"\xb8" + struct.pack("<f", value) + b"\x66\x0f\x6e\xc0\xc3", 10)

try:
    phoff = struct.unpack_from("<Q", blob, 32)[0]
    stride, count = struct.unpack_from("<HH", blob, 54)
    for i in range(count):
        kind, _, offset, address, _, size, _, _ = struct.unpack_from("<II6Q", blob, phoff + i * stride)
        if kind == 1:
            c.memmove(address, blob[offset:offset + size], size)
    libm = c.CDLL("libm.so.6")
    for address, name in ((0x40BC40, "powf"), (0x40BC50, "expf"), (0x40B560, "sincosf")):
        target = c.cast(getattr(libm, name), c.c_void_p).value
        c.memmove(address, b"\xff\x25\0\0\0\0" + struct.pack("<Q", target), 14)
    # Isolate scalar range/Doppler calculations from the separate angular filter.
    c.memmove(0x5F22B20, b"\xb8\x01\0\0\0\xc3", 6)
    update = c.CFUNCTYPE(c.c_uint64, c.c_void_p, c.c_void_p, c.c_void_p, c.c_int,
                        c.c_void_p, c.c_void_p, c.c_float, c.c_float, c.c_float, c.c_float)(0x5F53F90)
    rows = []
    for dt in (0.005, 0.01, 1 / 48, 0.1):
        for alpha, beta, limited in ((0.8, 0.05, False), (0.25, 0.03, True)):
            cfg, state, aux = c.create_string_buffer(0x500), c.create_string_buffer(0x60), c.create_string_buffer(0x40)
            struct.pack_into("<Q", state, 0x58, c.addressof(cfg))
            fields = {0x16C: 300, 0x174: 150000, 0x178: 300, 0x17C: 300,
                      0x190: -3000, 0x198: 3000, 0x19C: 20, 0x1A0: 20,
                      0x3A8: alpha, 0x3AC: beta, 0x3B0: 2147440000, 0x3B4: 2147440000,
                      0x3B8: 2147440000, 0x3BC: alpha, 0x3C0: beta,
                      0x3C4: 100 if limited else 2147440000,
                      0x3C8: 250 if limited else 2147440000, 0x3CC: 1 if limited else 2147440000}
            for address, value in fields.items():
                put(cfg, address, value)
            cfg[0x168], cfg[0x18C] = b"\1", b"\1"
            put(state, 0x28, 10000)
            put(state, 0x2C, -500)
            put(state, 0x34, 500)
            valid = update(state, aux, aux, 0, aux, aux, 2, 10000 - 500 * dt + 10, 510, dt)
            rows.append(dict(dt=dt, alpha=alpha, beta=beta, limited=limited, valid=valid,
                             range=get(state, 0x28), range_rate=get(state, 0x2C),
                             doppler=get(state, 0x34), doppler_rate=get(state, 0x38)))
    constant_float(0x5CCD160, 1.225)
    constant_float(0x5CCD100, 340)
    # config/gameparams.blk shellBallisticsParams.maxAcceleration = 6000 m/s^2.
    c.c_double.from_address(0xAFB8E28).value = 6000 ** 2
    init_cfg = c.CFUNCTYPE(None, c.c_void_p)(0x85DCC30)
    init_state = c.CFUNCTYPE(None, c.c_void_p)(0x85DE150)
    step = c.CFUNCTYPE(None, c.c_void_p, c.c_void_p, c.c_void_p, c.c_float, c.c_float)(0x85DE310)
    drag = []
    for velocity in ((280, 0, 0), (0, 0, 280), (0, 280, 0), (10, 10, 10)):
        cfg, state, forces = c.create_string_buffer(0x80), c.create_string_buffer(0x80), c.create_string_buffer(0x80)
        init_cfg(cfg)
        init_state(state)
        for address, value in {0: 0.026, 4: 0.01, 0x24: 3.141592653589793 * 0.026 ** 2 / 4,
                               0x34: 100, 0x40: 0}.items():
            put(cfg, address, value)
        put(forces, 0x68, 1e20)
        for address, value in zip((0x1C, 0x20, 0x24), velocity):
            put(state, address, value)
        step(forces, cfg, state, 0.001, 0.001)
        drag.append(dict(initial=velocity, dt=0.001,
                         position=[get(state, x) for x in (0, 4, 8)],
                         velocity=[get(state, x) for x in (0x1C, 0x20, 0x24)]))
    profile = c.CFUNCTYPE(c.c_float, c.c_void_p, c.c_float)(0x5FEFF00)
    breakpoints = (c.c_float * 4)(0.05, 0.1, 12, 15)
    ages = (0, 0.05, 0.075, 0.1, 1, 12, 13.5, 15)
    print(json.dumps(dict(sha256=EXPECTED, tracking=rows, drag=drag,
                         profile=[dict(age=t, value=profile(breakpoints, t)) for t in ages]), indent=2))
finally:
    libc.munmap(base, end - start)
