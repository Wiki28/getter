# getter < https://t.me/kastaid >
# Copyright (C) 2022 kastaid
#
# This file is a part of < https://github.com/kastaid/getter/ >
# PLease read the GNU Affero General Public License in
# < https://github.com/kastaid/getter/blob/main/LICENSE/ >.

import asyncio
import datetime
import json
import time
from io import BytesIO
from random import randrange
from telethon.errors.rpcerrorlist import FloodWaitError
from telethon.tl import functions as fun, types as typ
from . import (
    DEVS,
    kasta_cmd,
    sendlog,
    plugins_help,
    choice,
    suppress,
    parse_pre,
    time_formatter,
    mentionuser,
    display_name,
    strip_emoji,
    humanbool,
    DEFAULT_GCAST_BLACKLIST,
    DEFAULT_GUCAST_BLACKLIST,
    get_blacklisted,
    all_gban,
    gban_list,
    is_gban,
    add_gban,
    del_gban,
    set_gban_reason,
    all_gmute,
    gmute_list,
    is_gmute,
    add_gmute,
    del_gmute,
    set_gmute_reason,
    all_gdel,
    gdel_list,
    is_gdel,
    add_gdel,
    del_gdel,
    set_gdel_reason,
    jdata,
    add_col,
    del_col,
)

gban_text = r"""
\\<b>#GBanned</b>// User {} in {}-{}={} chats!
<b>Date:</b> <code>{}</code>
<b>Taken:</b> <code>{}</code>
<b>Reported:</b> <code>{}</code>
<b>Reason:</b> {}

<i>Added to GBanned_Watch.</i>
"""
ungban_text = r"""
\\<b>#UnGBanned</b>// User {} in {}-{}={} chats!
<b>Taken:</b> <code>{}</code>

<i>Wait for 1 minutes before released.</i>
"""
gmute_text = r"""
\\<b>#GMuted</b>// User {} in {}-{}={} groups!
<b>Date:</b> <code>{}</code>
<b>Taken:</b> <code>{}</code>
<b>Reason:</b> {}

<i>Added to GMuted_Watch.</i>
"""
ungmute_text = r"""
\\<b>#UnGMuted</b>// User {} in {}-{}={} groups!
<b>Taken:</b> <code>{}</code>

<i>Wait for 1 minutes before released.</i>
"""
gdel_text = r"""
\\<b>#GDeleted</b>// User {} in chats!
<b>Date:</b> <code>{}</code>
<b>Reason:</b> {}
"""
ungdel_text = r"""
\\<b>#UnGDeleted</b>// User {} in chats!

<i>Wait for 30 seconds before released.</i>
"""
reason_text = r"""
\\<b>#{}</b>// Reason for {} updated!
<b>Previous Reason:</b> <pre>{}</pre>
<b>Latest Reason:</b> <pre>{}</pre>
"""
gkick_text = r"""
\\<b>#GKicked</b>// User {} in {}-{}={} chats!
<b>Taken:</b> <code>{}</code>
<b>Reason:</b> {}
"""
gpromote_text = r"""
\\<b>#GPromoted</b>// User {} in {}-{}={} {}!
<b>Title:</b> <code>{}</code>
<b>Taken:</b> <code>{}</code>
"""
gdemote_text = r"""
\\<b>#GDemoted</b>// User {} in {}-{}={} {}!
<b>Taken:</b> <code>{}</code>
"""
_GBAN_LOCK = asyncio.Lock()
_UNGBAN_LOCK = asyncio.Lock()
_GMUTE_LOCK = asyncio.Lock()
_UNGMUTE_LOCK = asyncio.Lock()
_GDEL_LOCK = asyncio.Lock()
_UNGDEL_LOCK = asyncio.Lock()
_GKICK_LOCK = asyncio.Lock()
_GPROMOTE_LOCK = asyncio.Lock()
_GDEMOTE_LOCK = asyncio.Lock()
_GCAST_LOCK = asyncio.Lock()
_GUCAST_LOCK = asyncio.Lock()


@kasta_cmd(
    pattern="gban(?: |$)((?s).*)",
)
@kasta_cmd(
    pattern="gban(?: |$)((?s).*)",
    sudo=True,
)
@kasta_cmd(
    pattern="ggban(?: |$)((?s).*)",
    dev=True,
)
async def _(kst):
    if kst.is_dev or kst.is_sudo:
        await asyncio.sleep(choice((4, 6, 8)))
    if not kst.is_dev and _GBAN_LOCK.locked():
        await kst.eor("`Please wait until previous •gban• finished...`", time=5, silent=True)
        return
    async with _GBAN_LOCK:
        ga = kst.client
        chat_id = kst.chat_id
        yy = await kst.eor("`GBanning...`", silent=True)
        user, reason = await ga.get_user(kst)
        if not user:
            return await yy.eor("`Reply to message or add username/id.`", time=5)
        if user.id == ga.uid:
            return await yy.eor("`Cannot gban to myself.`", time=3)
        if user.id in DEVS:
            return await yy.eor("`Forbidden to gban our awesome developers.`", time=3)
        if is_gban(user.id):
            return await yy.eor("`User is already GBanned.`", time=4)
        start_time, date = time.time(), datetime.datetime.now().timestamp()
        success, failed = 0, 0
        is_reported = False
        await ga.unblock(user.id)
        with suppress(BaseException):
            if kst.is_private:
                is_reported = await ga(
                    fun.account.ReportPeerRequest(
                        user.id,
                        reason=typ.InputReportReasonSpam(),
                        message="Sends spam messages to my account. I ask Telegram to ban such user.",
                    )
                )
            elif kst.is_group and kst.is_reply:
                is_reported = await ga(
                    fun.channels.ReportSpamRequest(
                        chat_id,
                        participant=user.id,
                        id=[kst.reply_to_msg_id],
                    )
                )
            else:
                is_reported = await ga.report_spam(user.id)
        if ga._dialogs:
            dialog = ga._dialogs
        else:
            dialog = await ga.get_dialogs()
            ga._dialogs.extend(dialog)
        for gg in dialog:
            if gg.is_group or gg.is_channel:
                try:
                    await ga.edit_permissions(gg.id, user.id, view_messages=False)
                    await asyncio.sleep(0.5)
                    success += 1
                except FloodWaitError as fw:
                    await asyncio.sleep(fw.seconds + 10)
                    try:
                        await ga.edit_permissions(gg.id, user.id, view_messages=False)
                        await asyncio.sleep(0.5)
                        success += 1
                    except BaseException:
                        failed += 1
                except BaseException:
                    failed += 1
        add_gban(user.id, date, reason)
        await ga.block(user.id)
        await ga.archive(user.id)
        taken = time_formatter((time.time() - start_time) * 1000)
        text = gban_text.format(
            mentionuser(user.id, display_name(user), width=15, html=True),
            success + failed,
            failed,
            success,
            datetime.datetime.fromtimestamp(date).strftime("%Y-%m-%d"),
            taken,
            humanbool(is_reported),
            f"<pre>{reason}</pre>" if reason else "No reason.",
        )
        await yy.eor(text, parse_mode="html")


@kasta_cmd(
    pattern="ungban(?: |$)(.*)",
)
@kasta_cmd(
    pattern="ungban(?: |$)(.*)",
    sudo=True,
)
@kasta_cmd(
    pattern="gungban(?: |$)(.*)",
    dev=True,
)
async def _(kst):
    if kst.is_dev or kst.is_sudo:
        await asyncio.sleep(choice((4, 6, 8)))
    if not kst.is_dev and _UNGBAN_LOCK.locked():
        await kst.eor("`Please wait until previous •ungban• finished...`", time=5, silent=True)
        return
    async with _UNGBAN_LOCK:
        ga = kst.client
        yy = await kst.eor("`UnGBanning...`", silent=True)
        user, _ = await ga.get_user(kst)
        if not user:
            return await yy.eor("`Reply to message or add username/id.`", time=5)
        if user.id == ga.uid:
            return await yy.eor("`Cannot ungban to myself.`", time=3)
        if not is_gban(user.id):
            await yy.eor("`User is not GBanned.`")
            yy = await yy.reply("`Force UnGBanning...`", silent=True)
        start_time, success, failed = time.time(), 0, 0
        if ga._dialogs:
            dialog = ga._dialogs
        else:
            dialog = await ga.get_dialogs()
            ga._dialogs.extend(dialog)
        for gg in dialog:
            if gg.is_group or gg.is_channel:
                try:
                    await ga.edit_permissions(gg.id, user.id)
                    await asyncio.sleep(0.5)
                    success += 1
                except FloodWaitError as fw:
                    await asyncio.sleep(fw.seconds + 10)
                    try:
                        await ga.edit_permissions(gg.id, user.id)
                        await asyncio.sleep(0.5)
                        success += 1
                    except BaseException:
                        failed += 1
                except BaseException:
                    failed += 1
        del_gban(user.id)
        await ga.unblock(user.id)
        taken = time_formatter((time.time() - start_time) * 1000)
        text = ungban_text.format(
            mentionuser(user.id, display_name(user), width=15, html=True),
            success + failed,
            failed,
            success,
            taken,
        )
        await yy.eor(text, parse_mode="html")


@kasta_cmd(
    pattern="gmute(?: |$)((?s).*)",
)
@kasta_cmd(
    pattern="gmute(?: |$)((?s).*)",
    sudo=True,
)
@kasta_cmd(
    pattern="ggmute(?: |$)((?s).*)",
    dev=True,
)
async def _(kst):
    if kst.is_dev or kst.is_sudo:
        await asyncio.sleep(choice((4, 6, 8)))
    if not kst.is_dev and _GMUTE_LOCK.locked():
        await kst.eor("`Please wait until previous •gmute• finished...`", time=5, silent=True)
        return
    async with _GMUTE_LOCK:
        ga = kst.client
        yy = await kst.eor("`Gmuting...`", silent=True)
        user, reason = await ga.get_user(kst)
        if not user:
            return await yy.eor("`Reply to message or add username/id.`", time=5)
        if user.id == ga.uid:
            return await yy.eor("`Cannot gmute to myself.`", time=3)
        if user.id in DEVS:
            return await yy.eor("`Forbidden to gmute our awesome developers.`", time=3)
        if is_gmute(user.id):
            return await yy.eor("`User is already GMuted.`", time=4)
        start_time, date = time.time(), datetime.datetime.now().timestamp()
        success, failed = 0, 0
        if ga._dialogs:
            dialog = ga._dialogs
        else:
            dialog = await ga.get_dialogs()
            ga._dialogs.extend(dialog)
        for gg in dialog:
            if gg.is_group:
                try:
                    await ga.edit_permissions(gg.id, user.id, send_messages=False)
                    await asyncio.sleep(0.5)
                    success += 1
                except FloodWaitError as fw:
                    await asyncio.sleep(fw.seconds + 10)
                    try:
                        await ga.edit_permissions(gg.id, user.id, send_messages=False)
                        await asyncio.sleep(0.5)
                        success += 1
                    except BaseException:
                        failed += 1
                except BaseException:
                    failed += 1
        add_gmute(user.id, date, reason)
        taken = time_formatter((time.time() - start_time) * 1000)
        text = gmute_text.format(
            mentionuser(user.id, display_name(user), width=15, html=True),
            success + failed,
            failed,
            success,
            datetime.datetime.fromtimestamp(date).strftime("%Y-%m-%d"),
            taken,
            f"<pre>{reason}</pre>" if reason else "No reason.",
        )
        await yy.eor(text, parse_mode="html")


@kasta_cmd(
    pattern="ungmute(?: |$)(.*)",
)
@kasta_cmd(
    pattern="ungmute(?: |$)(.*)",
    sudo=True,
)
@kasta_cmd(
    pattern="gungmute(?: |$)(.*)",
    dev=True,
)
async def _(kst):
    if kst.is_dev or kst.is_sudo:
        await asyncio.sleep(choice((4, 6, 8)))
    if not kst.is_dev and _UNGMUTE_LOCK.locked():
        await kst.eor("`Please wait until previous •ungmute• finished...`", time=5, silent=True)
        return
    async with _UNGMUTE_LOCK:
        ga = kst.client
        yy = await kst.eor("`UnGmuting...`", silent=True)
        user, _ = await ga.get_user(kst)
        if not user:
            return await yy.eor("`Reply to message or add username/id.`", time=5)
        if user.id == ga.uid:
            return await yy.eor("`Cannot ungmute to myself.`", time=3)
        if not is_gmute(user.id):
            await yy.eor("`User is not GMuted.`")
            yy = await yy.reply("`Force UnGmuting...`", silent=True)
        start_time, success, failed = time.time(), 0, 0
        if ga._dialogs:
            dialog = ga._dialogs
        else:
            dialog = await ga.get_dialogs()
            ga._dialogs.extend(dialog)
        for gg in dialog:
            if gg.is_group:
                try:
                    await ga.edit_permissions(gg.id, user.id, send_messages=True)
                    await asyncio.sleep(0.5)
                    success += 1
                except FloodWaitError as fw:
                    await asyncio.sleep(fw.seconds + 10)
                    try:
                        await ga.edit_permissions(gg.id, user.id, send_messages=True)
                        await asyncio.sleep(0.5)
                        success += 1
                    except BaseException:
                        failed += 1
                except BaseException:
                    failed += 1
        del_gmute(user.id)
        taken = time_formatter((time.time() - start_time) * 1000)
        text = ungmute_text.format(
            mentionuser(user.id, display_name(user), width=15, html=True),
            success + failed,
            failed,
            success,
            taken,
        )
        await yy.eor(text, parse_mode="html")


@kasta_cmd(
    pattern="gdel(?: |$)((?s).*)",
)
@kasta_cmd(
    pattern="gdel(?: |$)((?s).*)",
    sudo=True,
)
@kasta_cmd(
    pattern="ggdel(?: |$)((?s).*)",
    dev=True,
)
async def _(kst):
    if kst.is_dev or kst.is_sudo:
        await asyncio.sleep(choice((4, 6, 8)))
    if not kst.is_dev and _GDEL_LOCK.locked():
        await kst.eor("`Please wait until previous •gdel• finished...`", time=5, silent=True)
        return
    async with _GDEL_LOCK:
        ga = kst.client
        yy = await kst.eor("`GDeleting...`", silent=True)
        user, reason = await ga.get_user(kst)
        if not user:
            return await yy.eor("`Reply to message or add username/id.`", time=5)
        if user.id == ga.uid:
            return await yy.eor("`Cannot gdel to myself.`", time=3)
        if user.id in DEVS:
            return await yy.eor("`Forbidden to gdel our awesome developers.`", time=3)
        if is_gdel(user.id):
            return await yy.eor("`User is already GDeleted.`", time=4)
        date = datetime.datetime.now().timestamp()
        add_gdel(user.id, date, reason)
        text = gdel_text.format(
            mentionuser(user.id, display_name(user), width=15, html=True),
            datetime.datetime.fromtimestamp(date).strftime("%Y-%m-%d"),
            f"<pre>{reason}</pre>" if reason else "No reason.",
        )
        await yy.eor(text, parse_mode="html")


@kasta_cmd(
    pattern="ungdel(?: |$)(.*)",
)
@kasta_cmd(
    pattern="ungdel(?: |$)(.*)",
    sudo=True,
)
@kasta_cmd(
    pattern="gungdel(?: |$)(.*)",
    dev=True,
)
async def _(kst):
    if kst.is_dev or kst.is_sudo:
        await asyncio.sleep(choice((4, 6, 8)))
    if not kst.is_dev and _UNGDEL_LOCK.locked():
        await kst.eor("`Please wait until previous •ungdel• finished...`", time=5, silent=True)
        return
    async with _UNGDEL_LOCK:
        ga = kst.client
        yy = await kst.eor("`UnGDeleting...`", silent=True)
        user, _ = await ga.get_user(kst)
        if not user:
            return await yy.eor("`Reply to message or add username/id.`", time=5)
        if user.id == ga.uid:
            return await yy.eor("`Cannot ungdel to myself.`", time=3)
        if not is_gdel(user.id):
            await yy.eor("`User is not GDeleted.`")
            yy = await yy.reply("`Force UnGDeleting...`", silent=True)
        del_gdel(user.id)
        text = ungdel_text.format(
            mentionuser(user.id, display_name(user), width=15, html=True),
        )
        await yy.eor(text, parse_mode="html")


@kasta_cmd(
    pattern="set(gban|gmute|gdel)(?: |$)((?s).*)",
)
async def _(kst):
    ga = kst.client
    yy = await kst.eor("`Processing...`")
    cmd = kst.pattern_match.group(1)
    user, reason = await ga.get_user(kst, 2)
    if not user:
        return await yy.eor("`Reply to message or add username/id.`", time=5)
    if user.id == ga.uid:
        return await yy.eor(f"`Cannot set {cmd} reason to myself.`", time=3)
    if user.id in DEVS:
        return await yy.eor("`Forbidden to set {cmd} reason for our awesome developers.`", time=3)
    if cmd == "gban":
        mode = "GBanned"
        is_banned = is_gban(user.id)
        if not is_banned:
            return await yy.eor(f"`User is not {mode}.`", time=4)
        if is_banned.reason == reason:
            return await yy.eor(f"`{mode} reason already set.`", time=4)
        prev_reason = set_gban_reason(user.id, reason)
    elif cmd == "gmute":
        mode = "GMuted"
        is_muted = is_gmute(user.id)
        if not is_muted:
            return await yy.eor(f"`User is not {mode}.`", time=4)
        if is_muted.reason == reason:
            return await yy.eor(f"`{mode} reason already set.`", time=4)
        prev_reason = set_gmute_reason(user.id, reason)
    else:
        mode = "GDeleted"
        is_deleted = is_gdel(user.id)
        if not is_deleted:
            return await yy.eor(f"`User is not {mode}.`", time=4)
        if is_deleted.reason == reason:
            return await yy.eor(f"`{mode} reason already set.`", time=4)
        prev_reason = set_gdel_reason(user.id, reason)
    text = reason_text.format(
        mode,
        mentionuser(user.id, display_name(user), width=15, html=True),
        prev_reason,
        reason,
    )
    await yy.eor(text, parse_mode="html")


@kasta_cmd(
    pattern="is(gban|gmute|gdel)(?: |$)(.*)",
)
async def _(kst):
    ga = kst.client
    yy = await kst.eor("`Processing...`")
    cmd = kst.pattern_match.group(1)
    user, _ = await ga.get_user(kst, 2)
    if not user:
        return await yy.eor("`Reply to message or add username/id.`", time=5)
    if cmd == "gban":
        mode = "GBanned"
        check = is_gban(user.id)
    elif cmd == "gmute":
        mode = "GMuted"
        check = is_gmute(user.id)
    else:
        mode = "GDeleted"
        check = is_gdel(user.id)
    if check:
        text = f"<b><u>Is {mode} User</u></b>\n"
        text += f"User ID: {check.user_id}\n"
        text += "Date: {}\n".format(datetime.datetime.fromtimestamp(check.date).strftime("%Y-%m-%d"))
        text += "Reason: {}".format(check.reason or "No reason.")
        return await yy.eor(text, parse_mode="html")
    text = f"`User is not {mode}.`"
    await yy.eor(text, time=5)


@kasta_cmd(
    pattern="list(gban|gmute|gdel)(?: |$)(.*)",
)
async def _(kst):
    cmd = kst.pattern_match.group(1)
    is_json = kst.pattern_match.group(2).strip().lower() == "json"
    if is_json:
        if cmd == "gban":
            lists = gban_list()
        elif cmd == "gmute":
            lists = gmute_list()
        else:
            lists = gdel_list()
        await kst.eor(json.dumps(lists, indent=2, default=str), parse_mode=parse_pre)
        return
    if cmd == "gban":
        mode = "GBanned"
        users = all_gban()
    elif cmd == "gmute":
        mode = "GMuted"
        users = all_gmute()
    else:
        mode = "GDeleted"
        users = all_gdel()
    total = len(users)
    if total > 0:
        text = f"<b><u>{total} {mode} Users</u></b>\n"
        for x in users:
            text += f"User ID: {x.user_id}\n"
            text += "Date: {}\n".format(datetime.datetime.fromtimestamp(x.date).strftime("%Y-%m-%d"))
            text += "Reason: {}\n\n".format(x.reason or "No reason.")
        return await kst.eor(text, parse_mode="html")
    text = f"`You got no {mode} users!`"
    await kst.eor(text, time=5)


@kasta_cmd(
    pattern="gkick(?: |$)((?s).*)",
)
@kasta_cmd(
    pattern="gkick(?: |$)((?s).*)",
    sudo=True,
)
@kasta_cmd(
    pattern="ggkick(?: |$)((?s).*)",
    dev=True,
)
async def _(kst):
    if kst.is_dev or kst.is_sudo:
        await asyncio.sleep(choice((4, 6, 8)))
    if not kst.is_dev and _GKICK_LOCK.locked():
        await kst.eor("`Please wait until previous •gkick• finished...`", time=5, silent=True)
        return
    async with _GKICK_LOCK:
        ga = kst.client
        yy = await kst.eor("`GKicking...`", silent=True)
        user, reason = await ga.get_user(kst)
        if not user:
            return await yy.eor("`Reply to message or add username/id.`", time=5)
        if user.id == ga.uid:
            return await yy.eor("`Cannot gkick to myself.`", time=3)
        if user.id in DEVS:
            return await yy.eor("`Forbidden to gkick our awesome developers.`", time=3)
        start_time, success, failed = time.time(), 0, 0
        if ga._dialogs:
            dialog = ga._dialogs
        else:
            dialog = await ga.get_dialogs()
            ga._dialogs.extend(dialog)
        for gg in dialog:
            if gg.is_group or gg.is_channel:
                try:
                    await ga.kick_participant(gg.id, user.id)
                    await asyncio.sleep(0.5)
                    success += 1
                except FloodWaitError as fw:
                    await asyncio.sleep(fw.seconds + 10)
                    try:
                        await ga.kick_participant(gg.id, user.id)
                        await asyncio.sleep(0.5)
                        success += 1
                    except BaseException:
                        failed += 1
                except BaseException:
                    failed += 1
        taken = time_formatter((time.time() - start_time) * 1000)
        text = gkick_text.format(
            mentionuser(user.id, display_name(user), width=15, html=True),
            success + failed,
            failed,
            success,
            taken,
            f"<pre>{reason}</pre>" if reason else "No reason.",
        )
        await yy.eor(text, parse_mode="html")


@kasta_cmd(
    pattern="gpromote(?: |$)(.*)",
)
@kasta_cmd(
    pattern="ggpromote(?: |$)(.*)",
    dev=True,
)
async def _(kst):
    if kst.is_dev:
        await asyncio.sleep(choice((4, 6, 8)))
    if not kst.is_dev and _GPROMOTE_LOCK.locked():
        await kst.eor("`Please wait until previous •gpromote• finished...`", time=5, silent=True)
        return
    async with _GPROMOTE_LOCK:
        ga = kst.client
        yy = await kst.eor("`GPromoting...`", silent=True)
        user, args = await ga.get_user(kst)
        if not user:
            return await yy.eor("`Reply to message or add username/id.`", time=5)
        if user.id == ga.uid:
            return await yy.eor("`Cannot gpromote to myself.`", time=3)
        opts = args.split(" ")
        to = opts[0].lower() if opts[0].lower() in ("group", "channel") else ""
        title = " ".join(strip_emoji(" ".join(opts[1:] if to else opts)).split()).strip()
        if len(title) > 16:
            title = title[:16]
        start_time, success, failed = time.time(), 0, 0
        async for gg in ga.iter_dialogs():
            if (
                "group" in to
                and gg.is_group
                or "group" not in to
                and "channel" in to
                and gg.is_channel
                or "group" not in to
                and "channel" not in to
                and (gg.is_group or gg.is_channel)
            ):
                try:
                    await ga.edit_admin(
                        gg.id,
                        user.id,
                        change_info=False,
                        delete_messages=True,
                        post_messages=True,
                        edit_messages=True,
                        ban_users=True,
                        invite_users=True,
                        pin_messages=False,
                        add_admins=False,
                        manage_call=True,
                        anonymous=False,
                        title=title,
                    )
                    await asyncio.sleep(0.5)
                    success += 1
                except BaseException:
                    failed += 1
        taken = time_formatter((time.time() - start_time) * 1000)
        text = gpromote_text.format(
            mentionuser(user.id, display_name(user), width=15, html=True),
            success + failed,
            failed,
            success,
            to or "all chats",
            title,
            taken,
        )
        await yy.eor(text, parse_mode="html")


@kasta_cmd(
    pattern="gdemote(?: |$)(.*)",
)
@kasta_cmd(
    pattern="ggdemote(?: |$)(.*)",
    dev=True,
)
async def _(kst):
    if kst.is_dev:
        await asyncio.sleep(choice((4, 6, 8)))
    if not kst.is_dev and _GDEMOTE_LOCK.locked():
        await kst.eor("`Please wait until previous •gdemote• finished...`", time=5, silent=True)
        return
    async with _GDEMOTE_LOCK:
        ga = kst.client
        yy = await kst.eor("`GDemoting...`", silent=True)
        user, args = await ga.get_user(kst)
        if not user:
            return await yy.eor("`Reply to message or add username/id.`", time=5)
        if user.id == ga.uid:
            return await yy.eor("`Cannot gdemote to myself.`", time=3)
        opts = args.split(" ")
        to = opts[0].lower() if opts[0].lower() in ("group", "channel") else ""
        start_time, success, failed = time.time(), 0, 0
        async for gg in ga.iter_dialogs():
            if (
                "group" in to
                and gg.is_group
                or "group" not in to
                and "channel" in to
                and gg.is_channel
                or "group" not in to
                and "channel" not in to
                and (gg.is_group or gg.is_channel)
            ):
                try:
                    await ga.edit_admin(
                        gg.id,
                        user.id,
                        change_info=False,
                        post_messages=False,
                        edit_messages=False,
                        delete_messages=False,
                        ban_users=False,
                        invite_users=False,
                        pin_messages=False,
                        add_admins=False,
                        manage_call=False,
                        anonymous=False,
                    )
                    await asyncio.sleep(0.5)
                    success += 1
                except BaseException:
                    failed += 1
        taken = time_formatter((time.time() - start_time) * 1000)
        text = gdemote_text.format(
            mentionuser(user.id, display_name(user), width=15, html=True),
            success + failed,
            failed,
            success,
            to or "all chats",
            taken,
        )
        await yy.eor(text, parse_mode="html")


@kasta_cmd(
    pattern="g(admin|)cast(?: |$)((?s).*)",
)
@kasta_cmd(
    pattern="gg(admin|)cast(?: |$)((?s).*)",
    dev=True,
)
async def _(kst):
    if kst.is_dev:
        await asyncio.sleep(choice((4, 6, 8)))
    if not kst.is_dev and _GCAST_LOCK.locked():
        await kst.eor("`Please wait until previous •gcast• finished...`", time=5, silent=True)
        return
    async with _GCAST_LOCK:
        ga = kst.client
        group = kst.pattern_match.group
        is_admin = group(1).strip() == "admin"
        match = group(2)
        if match:
            message = match
        elif kst.is_reply:
            message = await kst.get_reply_message()
        else:
            return await kst.eor("`Give some text to Gcast or reply message.`", time=5, silent=True)
        yy = await kst.eor(
            "⚡ __**Broadcasting to {}...**__".format(
                "groups as admin" if is_admin else "all groups",
            ),
            silent=True,
        )
        start_time, success, failed, error = time.time(), 0, 0, ""
        GCAST_BLACKLIST = await get_blacklisted(
            url="https://raw.githubusercontent.com/kastaid/resources/main/gcastblacklist.py",
            attempts=6,
            fallbacks=DEFAULT_GCAST_BLACKLIST,
        )
        gblack = {*GCAST_BLACKLIST, *jdata.gblacklist}
        if ga._dialogs:
            dialog = ga._dialogs
        else:
            dialog = await ga.get_dialogs()
            ga._dialogs.extend(dialog)
        for gg in dialog:
            if gg.is_group:
                chat_id = gg.entity.id
                if int("-100" + str(chat_id)) not in gblack and (
                    not is_admin or (gg.entity.admin_rights or gg.entity.creator)
                ):
                    try:
                        await ga.send_message(
                            chat_id,
                            message=message,
                            link_preview=False,
                        )
                        await asyncio.sleep(randrange(2, 5))
                        success += 1
                    except FloodWaitError as fw:
                        await asyncio.sleep(fw.seconds + 10)
                        try:
                            await ga.send_message(
                                chat_id,
                                message=message,
                                link_preview=False,
                            )
                            await asyncio.sleep(randrange(2, 5))
                            success += 1
                        except Exception as err2:
                            error += "• " + str(err2) + "\n"
                            failed += 1
                    except Exception as err1:
                        error += "• " + str(err1) + "\n"
                        failed += 1
        taken = time_formatter((time.time() - start_time) * 1000)
        text = r"\\**#Gcast**// {} in {}-{}={} {}.".format(
            taken,
            success + failed,
            failed,
            success,
            "groups as admin" if is_admin else "groups",
        )
        if error and not kst.is_dev:
            with suppress(BaseException), BytesIO(str.encode(error)) as file:
                file.name = "gcast_error.log"
                await sendlog(
                    r"\\**#Gcast**// Error Logs",
                    file=file,
                    force_document=True,
                    allow_cache=False,
                    silent=True,
                )
        await yy.eor(text)


@kasta_cmd(
    pattern="gucast(?: |$)((?s).*)",
)
@kasta_cmd(
    pattern="ggucast(?: |$)((?s).*)",
    dev=True,
)
async def _(kst):
    if kst.is_dev:
        await asyncio.sleep(choice((4, 6, 8)))
    if not kst.is_dev and _GUCAST_LOCK.locked():
        await kst.eor("`Please wait until previous •gucast• finished...`", time=5, silent=True)
        return
    async with _GUCAST_LOCK:
        ga = kst.client
        match = kst.pattern_match.group(1)
        if match:
            message = match
        elif kst.is_reply:
            message = await kst.get_reply_message()
        else:
            return await kst.eor("`Give some text to Gucast or reply message.`", time=5, silent=True)
        yy = await kst.eor(
            "⚡ __**Broadcasting to all pm users...**__",
            silent=True,
        )
        start_time, success, failed = time.time(), 0, 0
        GUCAST_BLACKLIST = await get_blacklisted(
            url="https://raw.githubusercontent.com/kastaid/resources/main/gucastblacklist.py",
            attempts=6,
            fallbacks=DEFAULT_GUCAST_BLACKLIST,
        )
        gblack = {*DEVS, *GUCAST_BLACKLIST, *jdata.gblacklist}
        if ga._dialogs:
            dialog = ga._dialogs
        else:
            dialog = await ga.get_dialogs()
            ga._dialogs.extend(dialog)
        for gg in dialog:
            if gg.is_user and not gg.entity.bot:
                chat_id = gg.id
                if chat_id not in gblack:
                    try:
                        await ga.send_message(
                            chat_id,
                            message=message,
                            link_preview=False,
                        )
                        await asyncio.sleep(randrange(2, 5))
                        success += 1
                    except FloodWaitError as fw:
                        await asyncio.sleep(fw.seconds + 10)
                        try:
                            await ga.send_message(
                                chat_id,
                                message=message,
                                link_preview=False,
                            )
                            await asyncio.sleep(randrange(2, 5))
                            success += 1
                        except BaseException:
                            failed += 1
                    except BaseException:
                        failed += 1
        taken = time_formatter((time.time() - start_time) * 1000)
        text = r"\\**#Gucast**// {} in {}-{}={} users.".format(
            taken,
            success + failed,
            failed,
            success,
        )
        await yy.eor(text)


@kasta_cmd(
    pattern="gblack(?: |$)(.*)",
)
async def _(kst):
    await gblacklisted(kst, "add")


@kasta_cmd(
    pattern="rmgblack(?: |$)(.*)",
)
async def _(kst):
    await gblacklisted(kst, "remove")


async def gblacklisted(kst, mode):
    ga = kst.client
    yy = await kst.eor("`Processing...`")
    where = await ga.get_text(kst)
    if where:
        try:
            chat_id = await ga.get_id(where)
        except Exception as err:
            return await yy.eor(str(err), parse_mode=parse_pre)
    else:
        chat_id = kst.chat_id
    GCAST_BLACKLIST = await get_blacklisted(
        url="https://raw.githubusercontent.com/kastaid/resources/main/gcastblacklist.py",
        attempts=6,
        fallbacks=DEFAULT_GCAST_BLACKLIST,
    )
    GUCAST_BLACKLIST = await get_blacklisted(
        url="https://raw.githubusercontent.com/kastaid/resources/main/gucastblacklist.py",
        attempts=6,
        fallbacks=DEFAULT_GUCAST_BLACKLIST,
    )
    system_gblack = {*GCAST_BLACKLIST, *DEVS, *GUCAST_BLACKLIST}
    gblack = jdata.gblack()
    if mode == "add":
        if chat_id in system_gblack:
            return await yy.eor("`Chat is already built-in gblacklist.`", time=4)
        if chat_id in jdata.gblacklist:
            return await yy.eor("`Chat is already gblacklist.`", time=4)
        try:
            title = display_name(await ga.get_entity(chat_id))
        except BaseException:
            title = "None"
        chatdata = {
            "title": title,
            "date": datetime.datetime.now().timestamp(),
        }
        gblack[str(chat_id)] = chatdata
        add_col("gblack", gblack)
        forwhat = "Added"
    elif mode == "remove":
        if chat_id in system_gblack:
            return await yy.eor("`Cannot remove built-in gblacklist.`", time=4)
        if chat_id not in jdata.gblacklist:
            return await yy.eor("`Chat is not gblacklist.`", time=4)
        del gblack[str(chat_id)]
        add_col("gblack", gblack)
        forwhat = "Removed"
    await yy.eor(f"<b><u>Global Broadcasts Blacklist</u></b>\n{forwhat} [<code>{chat_id}</code>]", parse_mode="html")


@kasta_cmd(
    pattern="listgblack$",
)
async def _(kst):
    gblacklist = jdata.gblacklist
    total = len(gblacklist)
    if total > 0:
        text = f"<b><u>{total} GBlacklist Chats</u></b>\n"
        gblack = jdata.gblack()
        for x in gblacklist:
            chat_id = str(x)
            text += "Chat Title: {}\n".format(gblack[chat_id]["title"])
            text += f"Chat ID: {x}\n"
            text += "Date: {}\n\n".format(datetime.datetime.fromtimestamp(gblack[chat_id]["date"]).strftime("%Y-%m-%d"))
        return await kst.eor(text, parse_mode="html")
    text = "`You got no gblacklist chats!`"
    await kst.eor(text, time=5)


@kasta_cmd(
    pattern="rmallgblack$",
)
async def _(kst):
    if not jdata.gblacklist:
        return await kst.eor("`You got no gblacklist chats!`", time=3)
    del_col("gblack")
    await kst.eor("`Successfully to remove all gblacklist chats!`")


plugins_help["globaltools"] = {
    "{i}gban [reply]/[in_private]/[username/mention/id] [reason]": "Globally Banned user in groups/channels permanently, possible also blocked, archived and report them as spam. Watcher per-id is cached in 1 minutes.",
    "{i}ungban [reply]/[in_private]/[username/mention/id]": "Release user from gbanwatch also force unban globally.",
    "{i}gmute [reply]/[in_private]/[username/mention/id] [reason]": "Globally Muted user in groups permanently. Watcher per-id is cached in 1 minutes.",
    "{i}ungmute [reply]/[in_private]/[username/mention/id]": "Release user from gmutewatch also force unmute globally.",
    "{i}gdel [reply]/[in_private]/[username/mention/id] [reason]": "Globally Delete user messages in chats every send. Watcher per-id is cached in 30 seconds.",
    "{i}ungdel [reply]/[in_private]/[username/mention/id]": "Release user from gdel.",
    "{i}setgban [reply]/[in_private]/[username/mention/id] [reason]": "Update gban reason.",
    "{i}setgmute [reply]/[in_private]/[username/mention/id] [reason]": "Update gmute reason.",
    "{i}setgdel [reply]/[in_private]/[username/mention/id] [reason]": "Update gdel reason.",
    "{i}isgban [reply]/[in_private]/[username/mention/id]": "Check if user is GBanned.",
    "{i}isgmute [reply]/[in_private]/[username/mention/id]": "Check if user is GMuted.",
    "{i}isgdel [reply]/[in_private]/[username/mention/id]": "Check if user is GDeleted.",
    "{i}listgban [json]": "List all GBanned users.",
    "{i}listgmute [json]": "List all GMuted users.",
    "{i}listgdel [json]": "List all GDeleted users.",
    "{i}gkick [reply]/[in_private]/[username/mention/id] [reason]": "Globally Kick user in groups/channels temporarily.",
    "{i}gpromote [reply]/[in_private]/[username/mention/id] [channel/group] [title]": "Globally Promote user where you are admin. Choose type of chats to promote user by add 'channel' or 'group' or 'all' (default: all). The title must be less than 16 characters and emoji are not allowed, or use the default localized title.",
    "{i}gdemote [reply]/[in_private]/[username/mention/id] [channel/group/all]": "Globally Demote user where you are admin.",
    "{i}gcast [text]/[reply]": "Send broadcast messages to all groups.",
    "{i}gadmincast [text]/[reply]": "Same as above, but only in where you are admin.",
    "{i}gucast [text]/[reply]": "Send broadcast messages to all pm users.",
    "{i}gblack [current/chat_id/username]": "Add chat to gblacklist and ignores global broadcast. Both for gcast and gucast!",
    "{i}rmgblack [current/chat_id/username]": "Remove the chat from gblacklist.",
    "{i}listgblack": "List all gblacklist chats.",
    "{i}rmallgblack": """Remove all gblacklist chats.

**DWYOR ~ Do With Your Own Risk**""",
}
