# getter < https://t.me/kastaid >
# Copyright (C) 2022-present kastaid
#
# This file is a part of < https://github.com/kastaid/getter/ >
# PLease read the GNU Affero General Public License in
# < https://github.com/kastaid/getter/blob/main/LICENSE/ >.

from . import (
    kasta_cmd,
    plugins_help,
    formatx_send,
    deep_get,
    Fetch,
    FUN_APIS,
)


@kasta_cmd(
    pattern="get(cat|dog|food|neko|waifu|neko18|waifu18|blowjob|cringe|cry|dance|happy|fact|quote)$",
)
async def _(kst):
    cmd = kst.pattern_match.group(1)
    yy = await kst.eor("`Processing...`")
    api = FUN_APIS[cmd]
    url = api.get("url")
    res = await Fetch(url, re_json=True)
    if not res:
        return await yy.eod("`Try again now!`")
    try:
        if isinstance(res, list):
            res = next((_ for _ in res), {})
        out = deep_get(res, api.get("value"))
        if api.get("type") == "text":
            source = api.get("source")
            if source:
                out += "\n~ {}".format(res.get(source))
            await yy.eor(out)
        else:
            await yy.eor(
                file=out,
                force_document=False,
            )
    except Exception as err:
        await yy.eor(formatx_send(err), parse_mode="html")


plugins_help["random"] = {
    "{i}getcat": "Random cat image.",
    "{i}getdog": "Random dog image.",
    "{i}getfood": "Random food image.",
    "{i}getneko": "Random neko image.",
    "{i}getwaifu": "Random waifu image.",
    "{i}getneko18": "Random neko nsfw image.",
    "{i}getwaifu18": "Random waifu nsfw image.",
    "{i}getblowjob": "Random blowjob nsfw image.",
    "{i}getcringe": "Random anime cringe gif.",
    "{i}getcry": "Random anime cry gif.",
    "{i}getdance": "Random anime dance gif.",
    "{i}gethappy": "Random anime happy gif.",
    "{i}getfact": "Random fun facts.",
    "{i}getquote": "Random quotes.",
}
