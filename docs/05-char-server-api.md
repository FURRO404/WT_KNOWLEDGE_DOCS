# War Thunder `char` server API and JWT auth

> Initial research: llamaz (https://github.com/llama-for3ver), Lux, and axiangcoding (https://github.com/axiangcoding).
> Contributors: DagorEngine by Gaijin Entertainment (the BLK wire format). https://github.com/GaijinEntertainment/DagorEngine

This document describes the War Thunder online `char` server API and its JWT
authentication. The source is empirical research against the live server on a
throwaway account, plus the datamine (v2.57.x) and the retail `aces` binary.

The `char` server holds the account profile, the economy, and the clan data.
The endpoint is a per-region host, for example
`https://char-lw-nl-005-2.warthunder.com`. The client selects a host from a
"circuit blk" that it pulls from `public-configs.warthunder.com`.

For the DataBlock (BLK) binary format, see
[02-file-formats.md](02-file-formats.md). This document names the two BLK
variants (FAT `0x01` and BBF3) but does not re-explain the format.

For the repositories and tools, see also
[10-tooling-and-repos.md](10-tooling-and-repos.md).

---

## 1. Authentication

### 1.1 The JWT

The `char` server authenticates each request with a JWT (JSON Web Token). The
Gaijin auth server issues the JWT when the player logs in.

The JWT is an RS256 token of about 1 KB. Its life is 30 days.

### 1.2 JWT claims

The JWT has three segments. The payload segment holds:

    app_perm   = the War Thunder application id
    prj        = warthunder
    uid        = <account uid>
    nick       = <account nick>
    exp, iat   = numeric times. exp - iat = 720 hours (30 days).
    perm       = ["login.can", "private_data.token_env.production"]
    tags/tgs   = "diffcurr,email_verified,lang_en,player_wt,sso,
                  sso_allowed_post,..."
    lng, cntry = language, country
    fac, loc, slt = opaque values
    iss, kid   = issuer and key id

The payload is base64url text, so a reader can decode it to get `uid` and
`exp` without the key. The client does not verify the RS256 signature. The
`char` server is the party that verifies the signature.

### 1.3 Refresh

The refresh is proactive: a client renews the token before `exp`. The `char`
API also returns a JSON error with `TOKEN_EXPIRED` or `INVALID_TOKEN` when it
rejects the token, which a client can treat as a signal to log in again.

### 1.4 How the client presents the JWT

The client sends the JWT in the `token` HTTP header on every `char` request
(read and write). The `token` header is the only credential. There is no
request signature.

---

## 2. Read path: `GET /json`

* Endpoint: `https://char-<region>.warthunder.com/json`
* Method: `GET`.
* The action name and every parameter are HTTP headers.
* The JWT is the `token` header.

Example:

    GET /json HTTP/1.1
    action: <action name>
    token: <JWT>
    <param header>: <value>

### 2.1 Success response

The success response is a binary DataBlock. Two formats occur. See
[02-file-formats.md](02-file-formats.md) for the format details.

* FAT, first byte `0x01`. Most read answers use this format. The `/char`
  write-success profile blob also uses this format.
* BBF3, first five bytes `00 42 42 46 03` (`\0BBF\3`). The older format. Some
  read answers still use it.

The decoder picks the format from the leading bytes, so the caller needs no
change.

### 2.2 Failure response

The failure response is a small JSON body:

    {"result":{"success":false,"error":"..."}}

A JSON body from a read is always an error. A success is always binary.

### 2.3 Read error codes

    LANGUAGE_REQUIRE            missing lang header
    CLAN_IS_NOT_EXISTS          unknown clan
    NO_DATA_RECEIVED            missing required data
    NAME_EXPECTED               action needs a name
    PLATFORM_EXPECTED           action needs the platform headers
    BAD_ACTION                  the action name is in the binary but this
                                cluster rejects it
    FULL_DOWNLOAD_DENIED        the full profile blob is not downloadable
    UNKNOWN_USERID              needs a valid target uid
    UNKNOWN_STORAGE_TYPE        unknown storage type for a stored blob
    INVALID_VALUE               bad leaderboard params
    INVALID_PARAMS_NO_CACHE_ID  a request without its cache id
    INVALID_SHARD_ID_PROVIDED   a request with a bad shard id

---

## 3. Write path: `POST /char`

* Endpoint: `https://char-<region>.warthunder.com/char`
* Method: `POST`.
* The action and the auth go in headers.
* The parameters go in the request body as a binary DataBlock (FAT type
  `0x01`). Send the body uncompressed. Do not send the `compr` header.

Example:

    POST /char HTTP/1.1
    action: <action name>
    token: <JWT>
    uidHint: 100000001
    Content-Type: application/octet-stream
    gameVersion: 2.57.1.91
    platform: PC
    platform_id: 9
    transactid: 7216550319341266796
    rpver: 0    rsati: 0@00    rpsui: 0
    <body = FAT 0x01 block of the action parameters>

### 3.1 Headers

The retail client sends this header set (from its own logs):

    action  gameVersion  comprTypes  internalIp  platform  platform_id
    uidHint  token  rpver  rsati  rpsui  transactid
    Content-Type: application/octet-stream  compr  Expect:

Header notes:

    token       the JWT. The only credential.
    uidHint     the client's local session uid. It is not derived from the
                token and not checked against it client-side.
    gameVersion the server validates it. A stale build gets
                !ERROR:INVALID_VERSION. Send the current datamine version, for
                example 2.57.1.91.
    transactid  a 63-bit CSPRNG value. Reused across retries as an idempotency
                key.
    rpver, rsati, rpsui   session counters. Default values are tolerated.

### 3.2 Compression

Do not send the `compr` header for the body unless you reproduce the client's
exact compression framing. With `compr` present the server tries to decompress
the body and returns `INCORRECT_DATA_RECEIVED<N>`. Plain bodies are accepted.

The retail client asks for a compressed answer with
`chardcompressedanswer: on`. The first answer body byte is then the codec
(`b` = bzip2). A client that does not ask for compression gets the plain blob.

### 3.3 Success response

The success response is the account profile blob as a FAT block (first byte
`0x01`). One recorded success is 378 599 bytes with 22 379 leaf values. See
section 4 for what the blob holds.

A body that the decoder cannot read does not mean that the write failed. In
one recorded case the success body did not decode, but the `userlogs` entry
showed that the server applied the write.

### 3.4 Failure response

The failure response is a `!ERROR:<CODE>` text body, for example:

    !ERROR:INVALID_GOODS_COST
    !ERROR:RESOURCE_ALREADY_EXIST
    !ERROR:UNLOCK_NOT_FOUND

### 3.5 JSON body variant (`EATT_JSON_REQUEST`)

Some `char` actions use `char_send_custom_action(action, EATT_JSON_REQUEST,
blk, text, -1)` instead of `char_send_blk`. The framing is the same request
with the body replaced:

* The body is the text payload (JSON, or a blk in text form).
* The params blk rides as headers.
* `Content-Type` stays `application/octet-stream`. The server picks the body
  format from the action, not from the content type.

For an inventory action, the `char` server forwards the body to the
inventory service. An error then comes back as a `!ERROR:<CODE>` text body
that carries that service's own JSON envelope:

    !ERROR:<CODE>:{"response":{"success":false,"error":"<CODE>"}}

---

## 4. What the server supplies to the client

The client shows account data that the `char` server supplies. The client does
not own this data. The server is authoritative, and each write answers with a
new profile blob.

### 4.1 The profile blob

The write-success profile blob (section 3.3) is the account state. It holds:

    resourcesInfo   owned resources, each with spendGold
    goldBalance     the gold balance
    attachables     per-vehicle mounted decorations
    warBonds        warbond state
    trophies        trophy state
    userlogs        account event log (buy events are type 47)

### 4.2 Read data

The read path supplies the data for other screens of the client:

* The public profile of a player: nick, clan, exp, an `unlocks` dict, and
  stats.
* The price and localisation table (about 20 MB) and the entitlement prices.
* The meta block (BBF3).
* Clan info and the member roster.
* Leaderboard pages. A squadron leaderboard page holds 200 rows at most.
* News.

### 4.3 Server-side rules for writes

* The server re-prices each buy. It does not trust a cost that the client
  sends.
* A save to the account's own namespace (for example, mounted decorations)
  writes the mounted list only. It cannot add a resource that the account does
  not own.
* The server gates operator tasks by role.

### 4.4 Error code taxonomy

Write and economy codes:

    INVALID_GOODS_COST · RESOURCE_ALREADY_EXIST · NOT_ENOUGH_GOLD ·
    UNLOCK_NOT_FOUND · INVALID_UNLOCK_NAME · BAD_INPUT_NAME · OFFER_NOT_FOUND ·
    WARBOND_AWARD_INFO_NOT_FOUND_IN_CONFIG · TROPHY_CANT_BE_BOUGHT ·
    WARBOND_NOT_ENOUGH_SHOP_LEVEL · ALREADY_UNLOCKED · UNLOCK_NOT_ALLOWED ·
    UNLOCK_NAME_EXPECTED

Framing and transport codes:

    INVALID_VERSION · INCORRECT_DATA_RECEIVED<N> · INVALID_JSON_RECEIVED ·
    REQUEST_GRANT_REWARDS_FAILED · INVALID_REQUEST · INVALID_VALUE ·
    NAME_EXPECTED · NO_DATA_RECEIVED · PLATFORM_EXPECTED · LANGUAGE_REQUIRE ·
    BAD_ACTION · UNKNOWN_STORAGE_TYPE · UNKNOWN_USERID

Inventory codes:

    INVENTORY_INVALID_OUTPUTITEMDEFID · INVENTORY_TRANSACTID_EXPECTED ·
    INVENTORY_INVALID_MATERIAL · FEATURE_IS_NOT_PRESENT:<feature>

Auth codes (from the JSON error body):

    TOKEN_EXPIRED · INVALID_TOKEN
