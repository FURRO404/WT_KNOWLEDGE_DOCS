# War Thunder file formats and the Dagor engine

> Initial research: wt-tools by klensy, 2014-12-21. https://github.com/klensy/wt-tools
> Contributors: Warthunder-Open-Source-Foundation (wt_blk, wt_ext_cli); Dagor-Asset-Explorer by Gredwitch; WtFileUtils by LivingTheDagor; DagorEngine by Gaijin Entertainment.

This document describes the on-disk file formats of War Thunder (WT) and the
Dagor engine. WT ships its game data in Dagor container and block formats. This
document gives the byte-level layout where the tool source code shows it, and it
names the tool that reads each format.

The facts here come from three tool code bases:

- `wt-tools` (klensy), Python. It unpacks VROMFS, DXP, DDSx, BLK, CLOG, and WRPL.
- `blk.py` and `blk_encode.py`, Python. They read and write the modern binary
  DataBlock formats (FAT and BBF3).
- `Dagor-Asset-Explorer` (Gredwitch), Python. It reads model, texture, and level
  formats (GRP, DXP2, DDSx, DBLD, DataBlock).

For related formats and APIs, see:

- [Replays (`.wrpl`)](03-replays.md)
- [The localhost:8111 telemetry API](04-localhost-8111-api.md)
- [The char server API](05-char-server-api.md)
- [Terrain and maps](07-terrain-and-maps.md)

---

## 1. VROMFS containers (`.vromfs.bin`, `.vromfs.bin_u`)

A VROMFS file is a virtual read-only file system. It holds many game files in
one archive. WT ships each data group as a `*.vromfs.bin` file. The datamine
repository stores each unpacked group in a `*.vromfs.bin_u` folder ("u" for
"unpacked"). The reference for the layout is
`wt-tools/src/wt_tools/formats/vromfs_parser.py`.

### 1.1 Header

The file starts with a 16-byte header.

```
offset  size  field           notes
0x00    4     magic           "VRFs" or "VRFx"
0x04    4     platform        "\0\0PC", "\0iOS", or "\0and"
0x08    4     original_size   uint32, size of the unpacked body
0x0c    3     packed_size     uint24, size of the packed body
0x0f    1     vromfs_type     0x40 unknown, 0x80 maybe_packed, 0xc0 zstd_packed
```

Note on `vromfs_type`. `wt-tools` reads the raw high byte (`0x40` / `0x80` /
`0xc0`). `wt_blk` reads the same field as the top 6 bits of a `uint32` and
right-shifts by 2, so it names the values `0x10` / `0x20` / `0x30`. The two
tools describe the same bits. `wt_blk` names them `ZSTD_OBFS_NOCHECK` (`0x40`
raw, no digest), `PLAIN` (`0x80` raw), and `ZSTD_OBFS` (`0xc0` raw). `PLAIN`
and `ZSTD_OBFS` carry a trailing 16-byte MD5 over the unpacked payload;
`ZSTD_OBFS_NOCHECK` carries none. Source:
[wt_blk](https://github.com/Warthunder-Open-Source-Foundation/wt_blk).

If the magic is `VRFx`, an 8-byte extension header follows the main header.

```
offset  size  field     notes
0x10    2     size      uint16
0x12    2     flags     uint16
0x14    4     version   uint32, e.g. 0x0207003A == 2.7.0.58
```

The version marks the format age. The unpacker calls the file a "new version"
when `version >= 34013242` (2.7.0.58). New versions use the zstd BLK packing that
Section 2.5 describes.

### 1.2 Body compression

The parser picks the body format from `vromfs_type` and `packed_size`:

- `zstd_packed` (`0xc0`): the body is one zstd stream.
- `not_packed` (`0x80` and `packed_size == 0`): the body is raw.
- `zlib_packed` (`0x80` and `packed_size > 0`): the body is a zlib stream (old
  files).

The zstd and zlib bodies both decompress to the same "not packed" layout that
Section 1.3 describes.

The zstd body is obfuscated at its head and tail. There is one 16-byte XOR key.
The parser applies the key at the head and the same key reversed at the tail:

- Bytes `[0 .. 16)` XOR the key `AA55AA55 F00FF00F AA55AA55 12481248`.
- For a body of 32 bytes or more, a 16-byte block near the tail XOR the reversed
  key `12481248 AA55AA55 F00FF00F AA55AA55`. The tail block starts at
  `(len & 0x03FFFFFC) - 16`.
- A body of 16 to 31 bytes XOR the head block only. A body under 16 bytes is
  unchanged.

The middle bytes stay as they are. Source: `wt_blk`
(`src/vromf/de_obfuscation.rs`), which cites Gaijin's
`dag_zstdObfuscate.h`.

### 1.3 Not-packed body layout (the file table)

The decompressed body starts with a small header, then two tables. All offsets
in the body are relative to the start of the body (`data_start_offset`).

```
offset  size  field                 notes
+0x00   4     filename_table_offset uint32
+0x04   4     files_count           uint32
+0x08   8     (skipped)
+0x10   4     filedata_table_offset uint32
```

The filename table holds the path of each file. The parser seeks to
`filename_table_offset`, reads the first filename offset, seeks there, then reads
`files_count` NUL-terminated UTF-8 strings. A name that starts with the bytes
`FF 3F nm 00` maps to the special name `nm` (the name map, see Section 2.4).

The file-data table holds one 16-byte record per file:

```
offset  size  field             notes
+0x00   4     file_data_offset  uint32, relative to body start
+0x04   4     file_data_size    uint32
+0x08   8     unknown
```

Each record points to the raw bytes of one file. The bytes may be a further
packed BLK (see Section 2.5).

### 1.4 How to unpack

Use `vromfs_unpacker` from `wt-tools`:

```
vromfs_unpacker.exe some.vromfs.bin
```

This writes the files to a `some.vromfs.bin_u` folder. Options:

- `-O`, `--output`: set the output path.
- `--metadata`: print a JSON map of `{filename: md5_hash}` instead of unpacking.
- `--input_filelist`: pass a JSON array of paths to unpack a subset, e.g.
  `["buildtstamp", "gamedata/units/tankmodels/fr_b1_ter.blk"]`.

The Python entry point is `wt-tools/src/wt_tools/vromfs_unpacker.py`.

### 1.5 The datamine file set

The `War-Thunder-Datamine` repository (by gszabi99) holds the unpacked VROMFS
groups. Each top-level folder is one unpacked container. The `version` file in
the repository root gives the game build (2.58.0.24 at the time of this
document). The groups are:

| Folder                    | Content                                                |
|---------------------------|--------------------------------------------------------|
| `aces.vromfs.bin_u`       | main game data: `gamedata`, `config`, `levels`, `templates`, `gamelibs`, `danetlibs`, `assetsimport` |
| `char.vromfs.bin_u`       | `config` (economy and unit config as `.blkx`): `shop`, `rank`, `modifications`, `items`, `crew_skills`, and more |
| `game.vromfs.bin_u`       | game scripts and settings                              |
| `gui.vromfs.bin_u`        | UI layout and script                                   |
| `lang.vromfs.bin_u`       | localization (`lang` folder)                           |
| `regional.vromfs.bin_u`, `regional-lang.vromfs.bin_u` | region-specific data and text |
| `mis.vromfs.bin_u`        | missions                                               |
| `tex.vromfs.bin_u`, `atlases.vromfs.bin_u`, `images.vromfs.bin_u` | textures and UI images |
| `webUi.vromfs.bin_u`      | web UI                                                 |
| `wwdata.vromfs.bin_u`     | world war data                                         |

The datamine stores BLK files as decoded `.blkx` (JSON). See Section 2 for the
BLK formats.

---

## 2. Dagor BLK / DataBlock binary format

A DataBlock (`.blk`) is a tree of named blocks. Each block holds typed
parameters and child blocks. WT uses several binary encodings of this tree and
one text encoding. The tool source shows the layout of each encoding.

The engine assigns each parameter type a numeric id. Two tool code bases use
slightly different names for the same ids. The table below joins them. The id is
the `DataBlock::ParamType`.

| id   | engine type | wtunlock name | wt-tools name | size in value slot |
|------|-------------|---------------|---------------|--------------------|
| 0x01 | string      | STRING        | str           | 4 (offset or name id) |
| 0x02 | int         | INT           | int           | 4                  |
| 0x03 | real        | FLOAT         | float         | 4                  |
| 0x04 | Point2      | FLOAT2        | vec2f         | 8 (out of line)    |
| 0x05 | Point3      | FLOAT3        | vec3f         | 12 (out of line)   |
| 0x06 | Point4      | FLOAT4        | vec4f         | 16 (out of line)   |
| 0x07 | IPoint2     | INT2          | vec2i         | 8 (out of line)    |
| 0x08 | IPoint3     | INT3          | vec3i         | 12 (out of line)   |
| 0x09 | bool        | BOOL          | bool          | value in header    |
| 0x0a | E3DCOLOR    | COLOR         | color         | 4 (RGBA bytes)     |
| 0x0b | TMatrix     | FLOAT12       | m4x3f         | 48 (out of line)   |
| 0x0c | int64       | LONG          | time / i64    | 8 (out of line)    |
| 0x0d | IPoint4     | INT4          | (n/a)         | 16 (out of line)   |

Note: `wt-tools` maps id 0x0c to `time` (two uint32) in the old BBF format. The
modern engine uses id 0x0c for int64. The two tools read different format
generations, so the names differ.

### 2.1 The leading byte: format flavours

The modern binary DataBlock starts with one byte that names the flavour.
`blk.py` (class `FileType`, from FlareFlo's parser)
maps this byte:

```
0x00  BBF             (old, see Section 2.6)
0x01  FAT             name map is built in
0x02  FAT_ZSTD        FAT, body is zstd
0x03  SLIM            name map is external
0x04  SLIM_ZSTD       SLIM, body is zstd
0x05  SLIM_ZSTD_DICT  SLIM, body is zstd with a shared dictionary
```

A FAT block carries its own name map. A SLIM block does not; the reader must
pass an external name map (see Section 2.4). The `_ZSTD` flavours zstd-compress
everything after the leading byte. The `_DICT` flavour needs a shared zstd
dictionary to decompress.

### 2.2 FAT layout (leading byte 0x01)

The FAT reader is `BlkDecoder` in `blk.py`. The writer is `encode_fat` and
`encode_fat_tree` in `blk_encode.py`. The layout after the leading byte is:

```
1 byte    format id (0x01 for plain FAT)
uleb128   names_in_name_map   number of names
uleb128   name_map_size       byte length of the name blob (includes trailing NUL)
bytes     name blob           names, NUL-separated, UTF-8
uleb128   num_of_blocks
uleb128   num_of_params
uleb128   params_data_size
bytes     params_data         out-of-line param payloads (strings, vectors, ...)
N * 8     param chunks        one 8-byte chunk per param
M         block descriptors   one descriptor per block (uleb128 fields)
```

All counts and offsets use unsigned LEB128 (`decode_uleb128`).

The name blob is one byte string of all names joined by NUL. The reader splits
on NUL and checks that the count matches `names_in_name_map`. Name id 0 is the
root placeholder; the encoder writes `__root__` there.

Each param chunk is 8 bytes:

```
offset  size  field       notes
+0x00   3     name_id     3-byte little-endian index into the name map
+0x03   1     type_id     the ParamType id (see the table above)
+0x04   4     value       inline value or an offset into params_data
```

The 4-byte value slot holds the value for a small inline type (int, float, bool,
color). For a larger type (string, vector, matrix, int64), the slot holds an
offset into `params_data`, and the real bytes live there.

For a string (`type_id == 0x01`), the high bit of the 4-byte value has a special
meaning. If bit 31 is set, the low 31 bits are a name-map index (the string is a
name). If bit 31 is clear, the low 31 bits are an offset into `params_data` to a
NUL-terminated UTF-8 string. See `BLKTypes.fromRawParamInfo`.

Each block descriptor gives the shape of one block. The fields are:

```
uleb128   name_id         0 for the root; otherwise (direct name id) + 1
uleb128   params_count    number of params that belong to this block
uleb128   blocks_count    number of child blocks
uleb128   first_block_id  present only if blocks_count > 0
```

The blocks are stored flat and breadth-first. A block's params take a contiguous
slice of the flat chunk array, in block order. A block's children take the range
`first_block_id .. first_block_id + blocks_count` of the flat block array. The
reader (`BlkDecoder._link`) walks this range to rebuild the tree.

Note the name-id convention: a param chunk's name id indexes the name list
directly (`names[nid]`), but a block descriptor's name id is the direct id plus
one, because the reader does `names[block_id - 1]` and reserves id 0 for the
root. `blk_encode.py` documents this offset-by-one and confirms it by a
round-trip test.

The `encode_fat`/`BlkDecoder` round-trip works in this environment. A flat block
`{'name': 'x', 'cost': 3}` encodes and decodes back to
`{'root': {'name': 'x', 'cost': 3}}`.

The char server answers requests in FAT, and it accepts FAT request bodies. See
[the char server API](05-char-server-api.md).

### 2.3 SLIM layout (leading bytes 0x03, 0x04, 0x05)

A SLIM block has the same body as FAT, but it has no built-in name blob. The
reader reads `names_in_name_map` (the count), then skips straight to the block
data and uses an external name map that the caller supplies. WT stores the shared
name map as a separate `nm` file inside the VROMFS (see Section 2.4).

The 0x04 and 0x05 flavours zstd-compress the body. The 0x05 flavour needs a
shared zstd dictionary (see Section 2.5). `BlkDecoder` decompresses the body with
`zstandard.ZstdDecompressor(zstd_dict)` before it reads the layout.

### 2.4 The shared name map (`nm` file)

WT deduplicates the many repeated block and parameter names across the whole
VROMFS. It stores every name once in a single name-map file. The VROMFS parser
finds this file under the special name `nm` (the last entry, with the raw name
bytes `FF 3F nm 00`). The SLIM blocks then reference names by index into this
shared map.

`vromfs_unpacker.py` detects the name map: it is here when the last file in the
table is named `nm`. To unpack it, the tool skips the first 40 bytes, then zstd-
decompresses the rest.

The first 40 bytes are now known. `wt_blk` (`src/blk/name_map.rs`) and
`WtFileUtils` both read them as two digests:

```
[0x00 .. 0x08)   names digest   (8 bytes)
[0x08 .. 0x28)   dict digest    (32 bytes, a SHA-256)
[0x28 .. ]       zstd stream    (decode WITHOUT a dictionary)
```

The decompressed body is `uleb128 names_count`, `uleb128 names_data_size`, then
the NUL-separated names. The dict digest names the shared `.dict` file: the
file name is the hex of that 32-byte digest. Source:
[wt_blk](https://github.com/Warthunder-Open-Source-Foundation/wt_blk).

### 2.5 Per-file BLK packing inside VROMFS (new versions)

In a new-version VROMFS, each stored `.blk` file starts with one packing-type
byte. `vromfs_unpacker.py` reads this byte and picks the unpack path:

```
byte  meaning
0x01  not zstd packed, small BLK with an inner dict; write bytes[1:]
0x02  seen in code, not handled (prints a warning)
0x03  not zstd packed, small BLK; write bytes[1:]
0x04  zstd packed, no dict, with a name map; decompress bytes[1:]
0x05  zstd packed with the shared dict; decompress bytes[1:]
else  raw text BLK; write bytes as is
```

The shared zstd dictionary comes from the first file in the VROMFS when that
file has the extension `.dict`. `vromfs_unpacker.py` builds a
`ZstdCompressionDict` from that file's bytes and uses it for every 0x05 file. It
uses `format=zstandard.FORMAT_ZSTD1`.

### 2.6 The old BBF format (leading bytes `\0BBF`, and the `\0BBz` zlib wrapper)

An older binary DataBlock starts with the 4-byte magic `\0BBF`. `wt-tools`
`blk_unpack.py` reads this format, and it reads a zlib-wrapped variant with the
magic `\0BBz`.

For `\0BBz`, the header is:

```
offset  size  field           notes
0x00    4     magic           "\0BBz"
0x04    4     unpacked_size   uint32
0x08    4     packed_size     uint32
0x0c    ...   zlib stream     packed_size bytes, zlib compressed
```

The tool zlib-decompresses `data[0x0c : 0x0c + packed_size]` to get the `\0BBF`
block. (The code notes it loses 256 trailing bytes it can not yet use.)

The `\0BBF` block then carries a version word at offset 0x04:

- version 2 (game 1.45 and lower), read by `_unpack_v2`.
- version 3 (game 1.47 and up), read by `_unpack_v3`.

Both versions store a list of key-name strings, then an optional sub-units name
block (the string values), then the block/param data. The key names hash to an
8-bit id. The hash is:

```
key_hash = 5
for each char c:  key_hash = (33 * key_hash + ord(c)) & 0xff
```

On a hash collision, the tool adds 0x100 to the id until the id is free. A param
record uses `struct HxB` at its start: a uint16 id, a skip byte, then a type
byte. Read `get_block_value` in `blk_unpack.py` for the exact value size of each
type.

### 2.7 The modern BBF3 format (leading bytes `\0BBF`, version 3)

`blk.py` (class `Bbf3Decoder`) reads a newer BBF3
block. This is a port of the engine reader
`prog/engine/ioSys/dataBlock/blk_readBBF3.cpp`. The char method
`cln_get_meta_blk` answers in this format. The layout is:

```
offset  size  field    notes
0x00    4     magic    00 'B' 'B' 'F'
0x04    4     version  low 16 bits must be 3
0x08    4     size     number of bytes that follow
...           name map        hash-bucketed, see below
...           string table
...           root block, then sub-blocks, recursively
```

The name map is stored in hash-bucket order, not id order. The reader rebuilds a
name's old id from its hash:

- Read a 16-bit `buckets_word`. The top 2 bits are the storage type. The low 14
  bits are the bucket count (a power of two).
- Read the name count (`count_compact`: 1, 2, or 4 bytes by storage type).
- For each name, read a variable-length length prefix (`decode_len`), then the
  UTF-8 bytes.
- Compute `bucket = string_hash(name) % bucket_count`, where `string_hash` is
  djb2 (`h = h*33 + byte`, start 5381, mask 0xFFFFFFFF).
- The old id is `seen_in_bucket * bucket_count + bucket`, where `seen_in_bucket`
  counts prior names in the same bucket.
- Align the read on a 4-byte boundary at the end.

The string table stores all string values in one page. A 32-bit header holds the
storage type (top 2 bits) and the total byte size (low 30 bits). A per-string
variable-length prefix gives each string's length.

Each block stores `params_num` (uint16), then `blocks_num` (uint16). Then it
stores the param descriptors, then the param values, then the child blocks. A
param descriptor is a uint32: the low 24 bits are the name's old id, bits 24..30
are the param type, and bit 31 is the bool value flag. A bool carries its value
in the descriptor, so the value pass skips it. A child-block record is a 4-byte
old id, then the child block. Read `Bbf3Decoder._read_block` and `_read_value`
for the exact per-type reads.

### 2.8 Text BLK (`.blk` as plain text)

A `.blk` file can also be plain text. The text form is a nested block syntax:

```
block_name {
  param:type = value;
  child {
    other:t = "string";
  }
}
```

`wt-tools` `blk_unpack.py` falls back to a text parse when the binary parse
fails. It uses the LALR grammar in
`wt-tools/src/wt_tools/formats/blk.lark` (via the `lark` library). If the text
parses, the tool copies it as is.

The `strict_blk` output type writes the in-game text form, with short type names
(`t`, `i`, `r`, `p2`, `p3`, `p4`, `ip2`, `ip3`, `b`, `c`, `m`, `i64`). See
`type_list_strict_blk` and `print_strict_blk`.

### 2.9 How to unpack and pack BLK

Use `blk_unpack` from `wt-tools`:

```
blk_unpack.exe some.blk                       # -> some.blkx as JSON
blk_unpack.exe --format=strict_blk some.blk   # -> in-game text form
blk_unpack.exe folder_name                    # unpack every .blk in the folder
```

Output formats: `json` (default), `json_min`, `strict_blk`, `json_2`. The
`--sort` flag sorts keys in JSON output, which helps a diff.

To shrink a mission BLK under the 512 KB editor limit, use `blk_minify`:

```
blk_minify.exe --strip_all some_mission.blk some_mission_minified.blk
```

To read or write the modern FAT/SLIM/BBF3 formats in Python, use
`blk.py` (`BlkDecoder(body).to_dict()`) and
`blk_encode.py` (`encode_fat`, `encode_fat_tree`).

---

## 3. Other asset formats

### 3.1 DXP2 texture packs (`*.dxp.bin`)

A DXP2 file packs many DDSx textures with their descriptors. The reader is
`wt-tools/src/wt_tools/dxp_unpack.py` and
`Dagor-Asset-Explorer/src/dae/parse/...`. The header:

```
offset  size  field         notes
0x00    4     magic         "DxP2"
0x08    2     total_files   uint16
0x10    4     -> block: file-data offsets
0x20    4     -> block: 0x20-byte DDS header per file
0x30    4     -> block: per-file (offset, size) pairs
0x48    ...   file names    NUL-terminated, one per file
```

The unpacker reads the file names, the 0x20-byte DDSx header of each texture, and
the (offset, size) of each texture body. It writes each texture as
`name.ddsx` (the 0x20 header, then the body). Command:

```
dxp_unpack.exe some.dxp.bin      # -> some.dxp.bin_u/ with .ddsx files
```

### 3.2 DDSx textures (`*.ddsx`)

A DDSx is a compressed DDS texture with a Dagor header. The reader is
`wt-tools/src/wt_tools/formats/ddsx_parser.py`. The 32-byte header:

```
offset  size  field         notes
0x00    4     label         "DDSx"
0x04    4     d3dFormat     the DXGI/D3D format code
0x08    4     flags         see the flag list below
0x0c    2     w
0x0e    2     h
0x10    1     levels        mip count
0x11    1     hqPartLevels
0x12    2     depth
0x14    2     bitsPerPixel
0x16    1     lQmip/mQmip   two nibbles
0x17    1     dxtShift/uQmip  two nibbles
0x18    4     memSz         unpacked size
0x1c    4     packedSz      packed size (0 means not packed)
```

The body follows the header. If `packedSz != 0`, the body is `packedSz` packed
bytes; else it is `memSz` raw bytes. The compression comes from the `flags`
field. The relevant flags:

```
FLG_ZLIB   = 0x80000000
FLG_7ZIP   = 0x40000000
FLG_OODLE  = 0x60000000
FLG_ZSTD   = 0x20000000
FLG_COMPR_MASK = 0xe0000000
```

Oodle is not Windows-only. Two decoders exist:

- `wt-tools` `ddsx_unpack` calls the game's `oo2core_6_win64.dll`, so that one
  tool path runs on Windows.
- `ooz` is an open standalone Kraken/Leviathan decoder. It needs no Oodle DLL.
  It decodes Oodle on Linux with the `ooz_linux` build for terrain, props, and
  textures. See [07-terrain-and-maps.md](07-terrain-and-maps.md) for the
  `ooz_linux` framing.

Command (`wt-tools`, Windows path):

```
ddsx_unpack.exe some.ddsx        # -> some.dds
ddsx_unpack.exe some_folder      # unpack a folder of .ddsx to .dds
```

### 3.3 The generic Dagor compressed block

Model and level data use a small compressed-block wrapper. The reader is
`Dagor-Asset-Explorer/src/dae/util/decompression.py` (class `CompressedData`).
The block is:

```
3 bytes   compressed size (uint24, little-endian)
1 byte    method
N bytes   compressed data
```

The method byte selects the codec:

```
0x20  LZMA
0x40  zstd
0x60  zlib
0x80  Oodle (Kraken/Leviathan)
```

An Oodle block prefixes its data with a 4-byte uncompressed size. DAE calls the
game's own `daKernel-dev.dll` for Oodle and zstd (ordinals 572/574 for Oodle,
954/962 for zstd), and it uses `pylzma` and `zlib` for the others. DAE uses the
game DLL, but Oodle decode does not need it. On Linux the `ooz` decoder reads
the same Oodle stream with no DLL. See
[07-terrain-and-maps.md](07-terrain-and-maps.md).

### 3.4 Game resource packs (GRP2, `*.grp`) and descriptors

A GRP holds the real resource data for models and other assets. The reader is
`Dagor-Asset-Explorer/src/dae/parse/gameres.py` (class `GameResourcePack`). A
GRP starts with the magic `GRP2`. It stores a name map, a table of real-resource
entries, and a second resource-data table. Each entry has a class id, an offset,
and a real-resource id. The class id selects the resource kind (RendInst,
DynModel, GeomNodeTree, CollisionGeom, FX, AnimChar, PhysObj, LandClass, and
more, per the DAE readme glossary).

A `GameResDesc` file (`riDesc.bin` or `dynModelDesc.bin`) gives the material and
texture names for the models. Its layout is a compressed DataBlock: a leading
byte `2`, a 3-byte size, then a zstd stream that decompresses to a binary
DataBlock (see Section 2). WT stores these files in `content/base/res`.

### 3.5 The DBLD binary level dump (`*.bin`, DBLD)

A packed level is a DBLD file. The file starts with the 8-byte magic
`DBLD3x64`: the fourcc `DBLD` plus the version word `3x64`. The engine reads
them as `_MAKE4C('DBLD')` and `DBLD_Version` (`prog/engine/scene/loadLevel.cpp`
in DagorEngine). The `Dagor-Asset-Explorer` reader is `dbld.py`. The file is a
stream of tagged blocks. The tag is a 4-byte code. The tags include:

```
TAG_RQRL 0x4c527152  RendInst list
TAG_DXP2 0x32507844  texture pack (see 3.1)
TAG_TEX  0x58455400  textures
TAG_LMAP 0x70616d6c  land blend texture
TAG_HM2  0x324d4800  heightmaps
TAG_LMP2 0x32704d4c  land texture
TAG_RIGZ 0x7a474952  RendInstGen (map prop layout)
TAG_SCN  0x4e435300  scene
TAG_FRT  0x54524600  static collision
TAG_OBJ  0x6a624f00  objects
TAG_END  0x444e4500  end
```

The `HM2`, `LMAP`, and `RIGZ` tags matter for terrain and prop work. See
[Terrain and maps](07-terrain-and-maps.md) for how to decode the heightmap and
the prop layout.

### 3.6 CLOG encrypted logs (`*.clog`)

A `.clog` is an XOR-encrypted log file. The reader is
`wt-tools/src/wt_tools/clog_unpack.py`. The tool XORs the file bytes with a
repeating key. The key file holds hex byte values separated by whitespace.
Command:

```
clog_unpack.exe -i some_log.clog -k keyfile.bin -o out_log.log
```

### 3.7 Replays (`*.wrpl`)

A replay is a WRPL container. It holds a settings BLK, a zlib-packed replay
stream, and a result BLK. The parser is
`wt-tools/src/wt_tools/formats/wrpl_parser.py`. The file magic is
`E5 AC 00 10`, then a 2-byte version. The parser seeks to a version-dependent
offset (0x440, 0x444, or 0x450) to reach the first inner `\0BBF` block. For the
full replay format and the fields, see [Replays](03-replays.md).

### 3.8 Fonts and other files

The VROMFS groups also hold fonts, UI images, atlases, and text. The
`vromfs_unpacker` extracts these as raw files. The tool does no further decode of
a font file; it writes the bytes as they are in the container.

### 3.9 The WOSF Rust toolchain

The War Thunder Open Source Foundation (WOSF) maintains a Rust toolchain. It is
the fast, current way to unpack these formats. Repos:

- [wt_ext_cli](https://github.com/Warthunder-Open-Source-Foundation/wt_ext_cli) —
  the command-line front end.
- [wt_blk](https://github.com/Warthunder-Open-Source-Foundation/wt_blk) — the
  format library (VROMFS, BLK, DXP/GRP). It has Python and WASM bindings.
- [wt_datamine_extractor](https://github.com/Warthunder-Open-Source-Foundation/wt_datamine_extractor) —
  turns unpacked blkx/csv into structured game data (shells, missiles, bombs).
- [wt_csv](https://github.com/Warthunder-Open-Source-Foundation/wt_csv) — a
  parser for the game's `;`-delimited quoted `.csv` files (the `lang` tables).
- [wt_version](https://github.com/Warthunder-Open-Source-Foundation/wt_version) —
  parses the 4-part game version.
- [wt_dm_api](https://github.com/Warthunder-Open-Source-Foundation/wt_dm_api) —
  an HTTP server that fetches vromfs and serves any BLK as raw, text, or JSON.
  Here `dm` means datamine, not damage model.

`wt_ext_cli` subcommands (from `src/cli/`):

```
wt_ext_cli unpack_vromf   -i <file|dir> -o <out> --format [Json|BlkText|BlkCompact|Raw]
wt_ext_cli unpack_raw_blk -i <dir> -o <out> --nm <name map> --dict <zstd dict> --format Json
wt_ext_cli repack_vromf   -i <dir|file> -o <out> --header [vrfs|vrfx] --packing [plain|zstd_obfs|zstd_obfs_nocheck]
wt_ext_cli vromf_version  -i <file|dir> -f [json|plain]
wt_ext_cli unpack_dxp_and_grp -i <dir> -o <out>
```

`unpack_vromf` writes the name map as `nm.txt` at the content root by default
(`--no_dump_nm` disables). `unpack_raw_blk` takes the external `--nm` and
`--dict` by hand for SLIM files.

Note: `wt_blk` does not implement the legacy BBF path. It marks `BBF = 0x00`
"unsupported, a legacy format from before 2019". For BBF and BBF3, use the
`wt-tools` and Python BLK readers named above.

[WtFileUtils](https://github.com/LivingTheDagor/WtFileUtils) (Python) is a
second reference reader for VROMFS and BLK. It confirms the FAT and SLIM
flavours, the VROMFS header, the XOR obfuscation, and the `nm` two-digest
header. Its own README says it is slow and points to `wt_ext_cli` for real work.

---

## 4. Tooling summary

| Format                    | Tool / repo                    | Command or entry point |
|---------------------------|--------------------------------|------------------------|
| VROMFS + BLK (fast, current) | wt_ext_cli (WOSF), Rust     | `wt_ext_cli unpack_vromf -i file.vromfs.bin -o out` |
| VROMFS `.vromfs.bin`      | wt-tools                       | `vromfs_unpacker.exe file.vromfs.bin` |
| BLK (old BBF/BBz)         | wt-tools                       | `blk_unpack.exe file.blk` |
| BLK (FAT/SLIM/BBF3)       | `blk.py` (Python)              | `BlkDecoder(body).to_dict()` |
| BLK write (FAT)           | `blk_encode.py` (Python)       | `encode_fat`, `encode_fat_tree` |
| BLK text grammar          | wt-tools `formats/blk.lark`    | used by `blk_unpack` fallback |
| BLK minify                | wt-tools                       | `blk_minify.exe in.blk out.blk` |
| DXP2 `.dxp.bin`           | wt-tools / DAE                 | `dxp_unpack.exe file.dxp.bin` |
| DDSx `.ddsx`              | wt-tools / DAE                 | `ddsx_unpack.exe file.ddsx` (wt-tools uses the oo2core DLL for Oodle; `ooz_linux` decodes Oodle on Linux) |
| CLOG `.clog`              | wt-tools                       | `clog_unpack.exe -i in.clog -k key.bin -o out.log` |
| WRPL `.wrpl`              | wt-tools                       | `wrpl_parser.py` (see [Replays](03-replays.md)) |
| GRP2, DBLD, models        | Dagor-Asset-Explorer           | GUI, drag and drop |
| Compressed block (Oodle/zstd/lzma/zlib) | DAE `decompression.py` | `CompressedData(file).decompress()` |

---

## Repository status

- **wt-tools** (klensy) — Python. Unpacks VROMFS, DXP2, DDSx, BLK (old BBF and
  BBz), CLOG, and WRPL, and minifies BLK. The master branch moves slowly (new
  work goes to `dev`), but the format logic is current. It is the base that
  other tools fork.
- **BLK reader/writer** (blk parts) — Python. `blk.py` reads FAT, SLIM, and
  BBF3. `blk_encode.py` writes FAT blocks for char-server requests. The BBF3
  reader is a direct port of the engine's `blk_readBBF3.cpp`. Current and
  working.
- **Dagor-Asset-Explorer** (Gredwitch) — Python plus PyQt5. Reads Dagor models
  (RendInst, DynModel), GRP2 packs, DXP2, DDSx, DataBlock, and DBLD levels, and
  exports models to OBJ, DMF, and Source. Full export needs Windows and the game
  DLLs.
- **WOSF Rust toolchain** — `wt_ext_cli` and `wt_blk`, Apache-2.0. The fast,
  current unpacker for VROMFS and BLK. It uses zstd only; it has no Oodle and no
  BBF. See section 3.9 for the repos and commands.
- **WtFileUtils** (LivingTheDagor) — Python, MIT. A second reference reader for
  VROMFS and BLK. It cross-checks the format facts in this section.
