# SCP-079-LANG - Ban or delete by detecting the language
# Copyright (C) 2019 SCP-079 <https://scp-079.org>
#
# This file is part of SCP-079-LANG.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import re
from copy import deepcopy
from string import ascii_lowercase
from typing import Match, Optional, Union

from pyrogram import CallbackQuery, Client, Filters, Message, User

from .. import glovar
from .channel import get_content, get_forward_name, get_full_name
from .etc import get_filename, get_lang, get_links, get_now, get_text, lang
from .file import save
from .group import get_description, get_group_sticker, get_pinned
from .ids import init_group_id
from .telegram import get_sticker_title

# Enable logging
logger = logging.getLogger(__name__)


def is_authorized_group(_, update: Union[CallbackQuery, Message]) -> bool:
    # Check if the message is send from the authorized group
    try:
        if isinstance(update, CallbackQuery):
            message = update.message
        else:
            message = update

        if not message.chat:
            return False

        cid = message.chat.id
        if init_group_id(cid):
            return True
    except Exception as e:
        logger.warning(f"Is authorized group error: {e}", exc_info=True)

    return False


def is_class_c(_, message: Message) -> bool:
    # Check if the message is sent from Class C personnel
    try:
        if not message.from_user:
            return False

        # Basic data
        uid = message.from_user.id
        gid = message.chat.id

        # Check permission
        if uid in glovar.admin_ids[gid] or uid in glovar.bot_ids or message.from_user.is_self:
            return True
    except Exception as e:
        logger.warning(f"Is class c error: {e}", exc_info=True)

    return False


def is_class_d(_, message: Message) -> bool:
    # Check if the message is Class D object
    try:
        if message.from_user:
            if is_class_d_user(message.from_user):
                return True

        if message.forward_from:
            fid = message.forward_from.id
            if fid in glovar.bad_ids["users"]:
                return True

        if message.forward_from_chat:
            cid = message.forward_from_chat.id
            if cid in glovar.bad_ids["channels"]:
                return True
    except Exception as e:
        logger.warning(f"Is class d error: {e}", exc_info=True)

    return False


def is_class_e(_, message: Message, test: bool = False) -> bool:
    # Check if the message is Class E object
    try:
        if message.from_user and not test:
            if is_class_e_user(message.from_user):
                return True

        if message.forward_from_chat:
            cid = message.forward_from_chat.id
            if cid in glovar.except_ids["channels"]:
                return True

        if message.game:
            short_name = message.game.short_name
            if short_name in glovar.except_ids["long"]:
                return True

        content = get_content(message)

        if not content:
            return False

        if (content in glovar.except_ids["long"]
                or content in glovar.except_ids["temp"]):
            return True
    except Exception as e:
        logger.warning(f"Is class e error: {e}", exc_info=True)

    return False


def is_declared_message(_, message: Message) -> bool:
    # Check if the message is declared by other bots
    try:
        if not message.chat:
            return False

        gid = message.chat.id
        mid = message.message_id
        return is_declared_message_id(gid, mid)
    except Exception as e:
        logger.warning(f"Is declared message error: {e}", exc_info=True)

    return False


def is_exchange_channel(_, message: Message) -> bool:
    # Check if the message is sent from the exchange channel
    try:
        if not message.chat:
            return False

        cid = message.chat.id
        if glovar.should_hide:
            return cid == glovar.hide_channel_id
        else:
            return cid == glovar.exchange_channel_id
    except Exception as e:
        logger.warning(f"Is exchange channel error: {e}", exc_info=True)

    return False


def is_from_user(_, message: Message) -> bool:
    # Check if the message is sent from a user
    try:
        if message.from_user and message.from_user.id != 777000:
            return True
    except Exception as e:
        logger.warning(f"Is from user error: {e}", exc_info=True)

    return False


def is_hide_channel(_, message: Message) -> bool:
    # Check if the message is sent from the hide channel
    try:
        if not message.chat:
            return False

        cid = message.chat.id
        if cid == glovar.hide_channel_id:
            return True
    except Exception as e:
        logger.warning(f"Is hide channel error: {e}", exc_info=True)

    return False


def is_new_group(_, message: Message) -> bool:
    # Check if the bot joined a new group
    try:
        new_users = message.new_chat_members
        if new_users:
            return any(user.is_self for user in new_users)
        elif message.group_chat_created or message.supergroup_chat_created:
            return True
    except Exception as e:
        logger.warning(f"Is new group error: {e}", exc_info=True)

    return False


def is_test_group(_, update: Union[CallbackQuery, Message]) -> bool:
    # Check if the message is sent from the test group
    try:
        if isinstance(update, CallbackQuery):
            message = update.message
        else:
            message = update

        if not message.chat:
            return False

        cid = message.chat.id
        if cid == glovar.test_group_id:
            return True
    except Exception as e:
        logger.warning(f"Is test group error: {e}", exc_info=True)

    return False


authorized_group = Filters.create(
    func=is_authorized_group,
    name="Authorized Group"
)

class_c = Filters.create(
    func=is_class_c,
    name="Class C"
)

class_d = Filters.create(
    func=is_class_d,
    name="Class D"
)

class_e = Filters.create(
    func=is_class_e,
    name="Class E"
)

declared_message = Filters.create(
    func=is_declared_message,
    name="Declared message"
)

exchange_channel = Filters.create(
    func=is_exchange_channel,
    name="Exchange Channel"
)

from_user = Filters.create(
    func=is_from_user,
    name="From User"
)

hide_channel = Filters.create(
    func=is_hide_channel,
    name="Hide Channel"
)

new_group = Filters.create(
    func=is_new_group,
    name="New Group"
)

test_group = Filters.create(
    func=is_test_group,
    name="Test Group"
)


def is_ad_text(text: str, ocr: bool, matched: str = "") -> str:
    # Check if the text is ad text
    try:
        if not text:
            return ""

        for c in ascii_lowercase:
            if c != matched and is_regex_text(f"ad{c}", text, ocr):
                return c
    except Exception as e:
        logger.warning(f"Is ad text error: {e}", exc_info=True)

    return ""


def is_ban_text(text: str, ocr: bool, message: Message = None) -> bool:
    # Check if the text is ban text
    try:
        if is_regex_text("ban", text, ocr):
            return True

        # ad + con
        ad = is_regex_text("ad", text, ocr)
        con = is_con_text(text, ocr)

        if ad and con:
            return True

        # emoji + con
        emoji = is_emoji("ad", text, message)

        if emoji and con:
            return True

        # ad_ + con
        ad = is_ad_text(text, ocr)

        if ad and con:
            return True

        # ad_ + emoji
        if ad and emoji:
            return True

        # ad_ + ad_
        if ad:
            ad = is_ad_text(text, ocr, ad)
            return bool(ad)
    except Exception as e:
        logger.warning(f"Is ban text error: {e}", exc_info=True)

    return False


def is_class_d_user(user: Union[int, User]) -> bool:
    # Check if the user is a Class D personnel
    try:
        if isinstance(user, int):
            uid = user
        else:
            uid = user.id

        if uid in glovar.bad_ids["users"]:
            return True
    except Exception as e:
        logger.warning(f"Is class d user error: {e}", exc_info=True)

    return False


def is_class_e_user(user: Union[int, User]) -> bool:
    # Check if the user is a Class E personnel
    try:
        if isinstance(user, int):
            uid = user
        else:
            uid = user.id

        if uid in glovar.bot_ids:
            return True

        group_list = list(glovar.admin_ids)
        for gid in group_list:
            if uid in glovar.admin_ids.get(gid, set()):
                return True
    except Exception as e:
        logger.warning(f"Is class e user error: {e}", exc_info=True)

    return False


def is_con_text(text: str, ocr: bool) -> bool:
    # Check if the text is con text
    try:
        if (is_regex_text("con", text, ocr)
                or is_regex_text("iml", text, ocr)
                or is_regex_text("pho", text, ocr)):
            return True
    except Exception as e:
        logger.warning(f"Is con text error: {e}", exc_info=True)

    return False


def is_declared_message_id(gid: int, mid: int) -> bool:
    # Check if the message's ID is declared by other bots
    try:
        if mid in glovar.declared_message_ids.get(gid, set()):
            return True
    except Exception as e:
        logger.warning(f"Is declared message id error: {e}", exc_info=True)

    return False


def is_detected_url(message: Message, test: bool = False) -> str:
    # Check if the message include detected url, return detected type
    try:
        if not test and is_class_c(None, message):
            return ""

        gid = message.chat.id
        links = get_links(message)
        for link in links:
            detected_type = glovar.contents.get(link, "")
            if detected_type and is_in_config(gid, "text", detected_type):
                return detected_type
    except Exception as e:
        logger.warning(f"Is detected url error: {e}", exc_info=True)

    return ""


def is_detected_user(message: Message) -> bool:
    # Check if the message is sent by a detected user
    try:
        if not message.from_user:
            return False

        gid = message.chat.id
        uid = message.from_user.id
        now = message.date or get_now()
        return is_detected_user_id(gid, uid, now)
    except Exception as e:
        logger.warning(f"Is detected user error: {e}", exc_info=True)

    return False


def is_detected_user_id(gid: int, uid: int, now: int) -> bool:
    # Check if the user_id is detected in the group
    try:
        user_status = glovar.user_ids.get(uid, {})

        if not user_status:
            return False

        status = user_status["detected"].get(gid, 0)
        if now - status < glovar.time_punish:
            return True
    except Exception as e:
        logger.warning(f"Is detected user id error: {e}", exc_info=True)

    return False


def is_emoji(the_type: str, text: str, message: Message = None) -> bool:
    # Check the emoji type
    try:
        if message:
            text = get_text(message, False, False)

        emoji_dict = {}
        emoji_set = {emoji for emoji in glovar.emoji_set if emoji in text and emoji not in glovar.emoji_protect}
        emoji_old_set = deepcopy(emoji_set)

        for emoji in emoji_old_set:
            if any(emoji in emoji_old and emoji != emoji_old for emoji_old in emoji_old_set):
                emoji_set.discard(emoji)

        for emoji in emoji_set:
            emoji_dict[emoji] = text.count(emoji)

        # Check ad
        if the_type == "ad":
            if any(emoji_dict[emoji] >= glovar.emoji_ad_single for emoji in emoji_dict):
                return True

            if sum(emoji_dict.values()) >= glovar.emoji_ad_total:
                return True

        # Check many
        elif the_type == "many":
            if sum(emoji_dict.values()) >= glovar.emoji_many:
                return True

        # Check wb
        elif the_type == "wb":
            if any(emoji_dict[emoji] >= glovar.emoji_wb_single for emoji in emoji_dict):
                return True

            if sum(emoji_dict.values()) >= glovar.emoji_wb_total:
                return True
    except Exception as e:
        logger.warning(f"Is emoji error: {e}", exc_info=True)

    return False


def is_high_score_user(user: User) -> float:
    # Check if the message is sent by a high score user
    try:
        if is_class_e_user(user):
            return 0.0

        uid = user.id
        user_status = glovar.user_ids.get(uid, {})

        if not user_status:
            return 0.0

        score = sum(user_status["score"].values())
        if score >= 3.0:
            return score
    except Exception as e:
        logger.warning(f"Is high score user error: {e}", exc_info=True)

    return 0.0


def is_in_config(gid: int, the_type: str, text: str = None) -> Union[bool, str]:
    # Check if the lang is in the group's config
    try:
        config = glovar.configs.get(gid, {})

        if not config:
            return False

        if not config.get(the_type):
            return False

        if isinstance(config[the_type], bool):
            return True

        if config[the_type].get("enable") and config[the_type].get("list"):
            if text is not None:
                the_lang = get_lang(text)
                if the_lang and the_lang in config[the_type]["list"]:
                    return the_lang
            else:
                return True
    except Exception as e:
        logger.warning(f"Is in config error: {e}", exc_info=True)

    return False


def is_limited_user(gid: int, user: User, now: int, short: bool = True) -> bool:
    # Check the user is limited
    try:
        if is_class_e_user(user):
            return False

        if glovar.configs[gid].get("new"):
            if is_new_user(user, now, gid):
                return True

        uid = user.id

        if not glovar.user_ids.get(uid, {}):
            return False

        if not glovar.user_ids[uid].get("join", {}):
            return False

        if is_high_score_user(user) >= 1.8:
            return True

        join = glovar.user_ids[uid]["join"].get(gid, 0)
        if short and now - join < glovar.time_short:
            return True

        track = [gid for gid in glovar.user_ids[uid]["join"]
                 if now - glovar.user_ids[uid]["join"][gid] < glovar.time_track]

        if len(track) >= glovar.limit_track:
            return True
    except Exception as e:
        logger.warning(f"Is limited user error: {e}", exc_info=True)

    return False


def is_new_user(user: User, now: int, gid: int = 0, joined: bool = False) -> bool:
    # Check if the message is sent from a new joined member
    try:
        if is_class_e_user(user):
            return False

        uid = user.id

        if not glovar.user_ids.get(uid, {}):
            return False

        if not glovar.user_ids[uid].get("join", {}):
            return False

        if joined:
            return True

        if gid:
            join = glovar.user_ids[uid]["join"].get(gid, 0)
            if now - join < glovar.time_new:
                return True
        else:
            for gid in list(glovar.user_ids[uid]["join"]):
                join = glovar.user_ids[uid]["join"].get(gid, 0)
                if now - join < glovar.time_new:
                    return True
    except Exception as e:
        logger.warning(f"Is new user error: {e}", exc_info=True)

    return False


def is_nm_text(text: str) -> bool:
    # Check if the text is nm text
    try:
        if (is_regex_text("nm", text)
                or is_regex_text("bio", text)
                or is_ban_text(text, False)):
            return True
    except Exception as e:
        logger.warning(f"Is nm text error: {e}", exc_info=True)

    return False


def is_not_allowed(client: Client, message: Message, text: str = None) -> str:
    # Check if the message is not allowed in the group
    try:
        if not message.chat:
            return ""

        # Basic data
        gid = message.chat.id

        # Regular message
        if not text:
            # Check detected records

            # If the user is being punished
            if is_detected_user(message):
                return "true true"

            # If the message has been detected
            content = get_content(message)
            if content:
                detection = glovar.contents.get(content, "")
                if detection and is_in_config(gid, "text", detection):
                    return detection

            # Url
            detected_url = is_detected_url(message)
            if detected_url:
                return detected_url

            # Start detect

            # Check name

            if is_in_config(gid, "name"):

                # Check the forward from name:
                forward_name = get_forward_name(message)
                if forward_name and forward_name not in glovar.except_ids["long"]:
                    the_lang = is_in_config(gid, "name", forward_name)
                    if the_lang:
                        return f"name {the_lang}"

                # Check the user's name
                name = get_full_name(message.from_user)
                if name and name not in glovar.except_ids["long"]:
                    the_lang = is_in_config(gid, "name", name)
                    if the_lang:
                        return f"name {the_lang}"

            # Check text

            # Bypass
            message_content = get_content(message)
            message_text = get_text(message)
            description = get_description(client, gid)
            if (description and message_text) and message_text in description:
                return ""

            pinned_message = get_pinned(client, gid)
            pinned_content = get_content(pinned_message)
            if (pinned_content and message_content) and message_content in pinned_content:
                return ""

            pinned_text = get_text(pinned_message)
            if (pinned_text and message_text) and message_text in pinned_text:
                return ""

            # Languages
            if is_in_config(gid, "text"):
                # Plain text
                the_lang = is_in_config(gid, "text", message_text)
                if the_lang:
                    return f"text {the_lang}"

                # Filename
                file_name = get_filename(message)
                the_lang = is_in_config(gid, "text", file_name)
                if the_lang:
                    return f"text {the_lang}"

                # Game
                if message.game:
                    game_title = message.game.title
                    the_lang = is_in_config(gid, "text", game_title)
                    if the_lang:
                        return f"text {the_lang}"

                # Via Bot
                if message.via_bot:
                    name = get_full_name(message.via_bot)
                    if name not in glovar.except_ids["long"]:
                        the_lang = is_in_config(gid, "text", name)
                        if the_lang:
                            return f"text {the_lang} {name}"

            # Special Chinese Characters
            if is_in_config(gid, "spc"):
                if is_regex_text("spc", message_text):
                    return f"text {lang('spc')}"

            # Special English Characters
            if is_in_config(gid, "spe"):
                if is_regex_text("spe", message_text):
                    return f"text {lang('spe')}"

            # Check Sticker
            if is_in_config(gid, "sticker"):
                # Bypass
                group_sticker = get_group_sticker(client, gid)
                if message.sticker:
                    sticker_name = message.sticker.set_name
                    if sticker_name and sticker_name == group_sticker:
                        return ""
                else:
                    sticker_name = ""

                if sticker_name:
                    sticker_title = get_sticker_title(client, sticker_name)
                    if sticker_title not in glovar.except_ids["long"]:
                        the_lang = is_in_config(gid, "sticker", sticker_title)
                        if the_lang:
                            return f"text {the_lang} {sticker_title}"

        # Preview message
        else:
            the_lang = is_in_config(gid, "text", text)
            if the_lang:
                return f"text {the_lang}"
    except Exception as e:
        logger.warning(f"Is not allowed error: {e}", exc_info=True)

    return ""


def is_regex_text(word_type: str, text: str, ocr: bool = False, again: bool = False) -> Optional[Match]:
    # Check if the text hit the regex rules
    result = None
    try:
        if text:
            if not again:
                text = re.sub(r"\s{2,}", " ", text)
            elif " " in text:
                text = re.sub(r"\s", "", text)
            else:
                return None
        else:
            return None

        with glovar.locks["regex"]:
            words = list(eval(f"glovar.{word_type}_words"))

        for word in words:
            if ocr and "(?# nocr)" in word:
                continue

            result = re.search(word, text, re.I | re.S | re.M)

            # Count and return
            if result:
                count = eval(f"glovar.{word_type}_words").get(word, 0)
                count += 1
                eval(f"glovar.{word_type}_words")[word] = count
                save(f"{word_type}_words")
                return result

        # Try again
        return is_regex_text(word_type, text, ocr, True)
    except Exception as e:
        logger.warning(f"Is regex text error: {e}", exc_info=True)

    return result


def is_watch_user(user: User, the_type: str, now: int) -> bool:
    # Check if the message is sent by a watch user
    try:
        if is_class_e_user(user):
            return False

        uid = user.id
        until = glovar.watch_ids[the_type].get(uid, 0)
        if now < until:
            return True
    except Exception as e:
        logger.warning(f"Is watch user error: {e}", exc_info=True)

    return False


def is_wb_text(text: str, ocr: bool) -> bool:
    # Check if the text is wb text
    try:
        if (is_regex_text("wb", text, ocr)
                or is_regex_text("ad", text, ocr)
                or is_regex_text("iml", text, ocr)
                or is_regex_text("pho", text, ocr)
                or is_regex_text("sho", text, ocr)
                or is_regex_text("spc", text, ocr)):
            return True

        for c in ascii_lowercase:
            if c not in {"i"} and is_regex_text(f"ad{c}", text, ocr):
                return True
    except Exception as e:
        logger.warning(f"Is wb text error: {e}", exc_info=True)

    return False
