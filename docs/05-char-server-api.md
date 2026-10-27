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
[09-tooling-and-repos.md](09-tooling-and-repos.md).

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
* The owned skins, decals and decorations of a player, and the skin last
  selected on each vehicle: `ano_get_bin`. See section 4.5.
* The public wishlist of a player: `ano_get_wishlist_json`, with the target id
  in the `userId` header. The answer is JSON:
  `{"userId", "units": [{"unit", "comment", "time"}]}`. [verified]
* Actions that refuse a foreign id with `ACCESS_DENIED_FOR_OTHER_PROFILES`:
  `cln_get_showcases`, `cln_get_users_terse_info`,
  `cln_get_short_user_info_jwt`, `cln_get_partner_executed_unlocks`.
  [verified]
* The price and localisation table (about 20 MB) and the entitlement prices.
* The meta block (BBF3).
* Clan info and the member roster (`cln_clan_get`). For the squadron roster
  and the SRE rating fields, see
  [10-sre-tss-info.md](10-sre-tss-info.md) section 9.
* Leaderboard pages. For the squadron leaderboard, see
  [10-sre-tss-info.md](10-sre-tss-info.md) section 9.3.
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

### 4.5 Player cosmetics and awards

Two public reads take the target id in the `userId` header and need only a
service-account JWT. Send one id header only. With both `userId` and `userid`
the server answers `BAD_USERID`. [verified]

**Awards: `ano_get_public_userstat`.** The `unlocks` dict holds every award as
`{type, stage?}`. One account held 750 entries:

    achievement 434 · challenge 156 · medal 91 · trophy_steam 69

`titles.name` lists the earned titles (a bare string when there is one), and
`title` is the title in use. `closedUnlocks` and `classinessAwards` were empty.
The profile holds no skins or decals. Unlock ids such as `ch_skins` or
`decal_applied` record an action, not an item. [verified]

**Cosmetics: `ano_get_bin`.** The answer is a FAT block of about 470 KB with
these keys:

    serverTime registerTime expiredTimeCorrection clanId clanMemberRole
    clanType clanTag clanName hangar weapons modifications crews decals
    attachables unitsExtraData resourcesInfo weaponPresets

* `resourcesInfo.core`: every owned resource, as `{exteriorInfoParams}`
  (values 1, 8 and 32 seen; meaning not known). A stock skin is
  `<unit>/<skin>`, for example `fr_leclerc_azur/esp_market`. A bare key is a
  decal or a decoration. A workshop (UGC) skin is a bare UUID of the form
  `xxxxf000-5a1e-406b-b033-52c0dfa43067`. One account held 1315 entries:
  312 skins, 900 decals, 98 decorations, 5 UUIDs. [verified]
* `hangar.<unit>.lastSkin`: the skin last selected on that unit. A change in
  the hangar shows in the next read within seconds. The `hangar` block held
  only 53 units of that account, with per-unit state (last ammo, last weapon,
  repairs, battle count). 20 of them had no `lastSkin`. Probably the field is
  left out for the standard skin. [verified; the reason is inferred]
* `decals.<unit>.<skin>` and `attachables.<unit>.<skin>`: the decal layout and
  mounted decorations per skin. These blocks hold an entry for every workshop
  skin that was opened in the hangar, owned or not. Do not use them to find
  ownership or the vehicle of a workshop skin. [verified]
* A Marketplace skin that is still a tradable item stays in the Gaijin
  inventory. It is not in `resourcesInfo`, and only the owner's own token can
  read the inventory. [inferred]

**Names.** All from the game files:

| Item | Lang key | Source |
|---|---|---|
| Stock skin | `<unit>/<skin>` | `lang/unlocks_skins.csv`, `regional_skins.csv` |
| Stock skin, no own row | the key that `skins_localization.blk` gives | `aces.vromfs.bin` `config/` |
| Stock skin, last fallback | `skin/<skin>` | `lang/unlocks_skins.csv` |
| Standard skin | `default_skin_loc` | `lang/unlocks_skins.csv` |
| Decal | `decals/<id>` | `lang/unlocks_decals.csv`, `regional_decals.csv` |
| Decoration | `attachables/<id>` | `lang/unlocks_attachables.csv` |
| Workshop skin | none | item definition name (section 4.6) |

`skins_localization.blk` maps pairs such as `germ_leopard_2a6/lederbraun` to
`skin/ger_camo_lederbraun` (10153 pairs). These rules named all 312 skins and
all but one of 900 decals of the account above. [verified]

**Stock and special decals.** Most owned decals are stock: every player can get
them. A decal or decoration is stock when its definition
(`char.vromfs.bin` `config/decals.blk` or `attachable.blk`, plus
`regional.vromfs.bin` `config/decals_ext.blk`) has `costGold > 0`, or when its
`unlock` (a string or a list) names an entry in `config/unlocks.blk`
`unlockable[]` whose `mode.type` is a play-progress counter:

    missionsWonScore missionsPlayedScore missionsWon killedPlayersScore
    killedGroundScore burnedUnitsScore totalMissionScore awardDamage
    amountDamagesZone char_aircrafts_in_era char_login_time_range

`char_login_time_range` grants the 160 `common/numbers` decals at login. The
other decals (`costGold -1` and no progress unlock) come from events, packs,
tournaments, partners or the Marketplace. Of one account's 900 decals, 607 were
stock. Of its 98 decorations, 24 were stock. `unlocks.blk` `default.unlock` (51
ids) holds no decals. [verified]

**Vehicle of a workshop skin.** `aces.vromfs.bin` `config/skins_market.blk` is
keyed by unit. Each block (a list when the unit has several) has a
`marketplaceItemdefId`. The client reads this file to list Marketplace skins
per vehicle. Join it with the item definition that has the UUID as its
`resource` (section 4.6). This mapped all 5 owned workshop skins of the account
above. A few itemdefs are listed for more than one unit. [verified]

### 4.6 Marketplace and inventory reads

These services are not the `char` server, but they take the same JWT.

**Item definitions.** `POST https://inventory-proxy-01.gaijin.net/char` with
the headers `action: GetItemDefsClient`, `token: <JWT>`, `appid: 1067` and a
JSON body `{"itemdefids": "<id>,<id>", "language": "english"}`. The ids are a
comma string. A JSON array gives `!ERROR:INVENTORY_INVALID_PARAMETERS`. The
answer is `response.itemdef_json`, about 2.7 MB with 2470 definitions, and it
seems to hold the whole client catalog whatever ids are sent. [verified]
Fields used:

    itemdefid  name  marketable  market_hash_name  tags  icon_url
    meta = resourceType:t="skin"; resource:t="<uuid or resource id>"

**Market search.** `POST https://market-proxy.gaijin.net/web` as a form:

    action=cln_market_search  token=<JWT>  skip  count (100 works)
    text  language=en_US  options=any_sell_orders  appid_filter=1067

Without `token` the answer is `TOKEN_REQUIRED`. Each asset has `hash_name`,
`name`, `price`, `depth` and `tags` (`type:skin|decal|attachable|chest|key|…`).
The full War Thunder listing was 2829 items over 29 pages. [verified]

**Hash name forms.**

    ugcitem_<itemdefid>        workshop skins
    id<itemdefid>_<resource>   decals and decorations, e.g. id300016_direct_hit_decal
    <display name>             older items and vehicles

The resource id in the second form is the same id as in `resourcesInfo.core`.
Stock, pack, event and esports skins are not Marketplace items. Of one
account's 1315 resources, 16 had a listing. [verified]

**Listing page.** `https://trade.gaijin.net/market/1067/<hash_name>`, from the
site's route `market/:app_id/:item_hash_name`. `/?a=<app>&n=<hash>` redirects
there. [verified from the site bundle]

