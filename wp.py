import asyncio
import json
import os
import re
import time
import random
import base64
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any
from pathlib import Path

from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, RPCError
from gtts import gTTS
from io import BytesIO

# ========== CONFIGURATION ==========
ROLES_FILE = './data/roles.json'
BOTS_FILE = './data/bots.json'
DELAYS_FILE = './data/ncDelays.json'

# ========== DEFAULT ROLES ==========
default_roles = {
    'admins': [],
    'subAdmins': {}
}

# ========== DEFAULT DELAYS ==========
default_delays = {
    # Individual NC delays (1-100)
    **{f'nc{i}': 200 for i in range(1, 101)},
    
    # Triple attack delays (1-35)
    **{f'triple{i}': 200 for i in range(1, 36)}
}

# Minimum safe delays (for warning)
MINIMUM_SAFE_DELAYS = {
    'nc_attacks': 1000,
    'messages': 1500,
    'voice': 2000,
    'group_changes': 5000,
    'triple_nc': 500
}

# ========== EMOJI ARRAYS (100 sets) ==========
emoji_arrays = {
    # FACE EMOJIS (1-10)
    'nc1': ['😀','😃','😄','😁','😆','😅','😂','🤣','😊','😇','🙂','🙃'],
    'nc2': ['😉','😌','😍','🥰','😘','😗','😙','😚','😋','😛','😝','😜'],
    'nc3': ['🤪','😎','🥸','🤓','🧐','🤯','🥳','😏','😒','😞','😔','😟'],
    'nc4': ['😕','🙁','☹️','😣','😖','😫','😩','🥺','😢','😭','😤','😠'],
    'nc5': ['😡','🤬','🤯','😳','🥵','🥶','😱','😨','😰','😥','😓','🤗'],
    'nc6': ['🤔','🫣','🤭','🤫','🤥','😶','🫥','😐','🫤','😑','😬','🫨'],
    'nc7': ['🙄','😯','😦','😧','😮','😲','🥱','😴','🤤','😪','😵','🤐'],
    'nc8': ['🥴','😷','🤒','🤕','🤢','🤮','🤧','😇','🥳','🥸','😈','👿'],
    'nc9': ['👹','👺','🤡','💩','👻','💀','☠️','👽','👾','🤖','🎃','😺'],
    'nc10': ['😸','😹','😻','😼','😽','🙀','😿','😾','👋','🤚','🖐️','✋'],
    
    # HAND GESTURES (11-20)
    'nc11': ['🖖','👌','🤌','🤏','✌️','🤞','🫰','🤟','🤘','🤙','🫵','🫲'],
    'nc12': ['🫳','👈','👉','👆','🖕','👇','☝️','👍','👎','✊','👊','🤛'],
    'nc13': ['🤜','👏','🙌','🫶','👐','🤲','🤝','🙏','✍️','💅','🤳','💪'],
    'nc14': ['🦾','🦿','🦵','🦶','👂','🦻','👃','🧠','🫀','🫁','🦷','🦴'],
    'nc15': ['👀','👁️','👅','👄','🫦','👶','🧒','👦','👧','🧑','👨','👩'],
    'nc16': ['🧔','👨‍🦰','👩‍🦰','👨‍🦱','👩‍🦱','👨‍🦳','👩‍🦳','👨‍🦲','👩‍🦲','🧑‍🦰','🧑‍🦱','🧑‍🦳'],
    'nc17': ['🧑‍🦲','👱','👱‍♀️','🧓','👴','👵','🙍','🙍‍♂️','🙍‍♀️','🙎','🙎‍♂️','🙎‍♀️'],
    'nc18': ['🙅','🙅‍♂️','🙅‍♀️','🙆','🙆‍♂️','🙆‍♀️','💁','💁‍♂️','💁‍♀️','🙋','🙋‍♂️','🙋‍♀️'],
    'nc19': ['🧏','🧏‍♂️','🧏‍♀️','🙇','🙇‍♂️','🙇‍♀️','🤦','🤦‍♂️','🤦‍♀️','🤷','🤷‍♂️','🤷‍♀️'],
    'nc20': ['👮','👮‍♂️','👮‍♀️','🕵️','🕵️‍♂️','🕵️‍♀️','💂','💂‍♂️','💂‍♀️','🥷','👷','👷‍♂️'],
    
    # PEOPLE & PROFESSIONS (21-30)
    'nc21': ['👷‍♀️','👨‍⚕️','👩‍⚕️','👨‍🎓','👩‍🎓','👨‍🏫','👩‍🏫','👨‍⚖️','👩‍⚖️','👨‍🌾','👩‍🌾','👨‍🍳'],
    'nc22': ['👩‍🍳','👨‍🔧','👩‍🔧','👨‍🏭','👩‍🏭','👨‍💼','👩‍💼','👨‍🔬','👩‍🔬','👨‍💻','👩‍💻','👨‍🎤'],
    'nc23': ['👩‍🎤','👨‍🎨','👩‍🎨','👨‍✈️','👩‍✈️','👨‍🚀','👩‍🚀','👨‍🚒','👩‍🚒','👮','🕵️','💂'],
    'nc24': ['👷','🤴','👸','👳','👳‍♂️','👳‍♀️','🧕','👲','🧔‍♀️','🤵','🤵‍♂️','🤵‍♀️'],
    'nc25': ['👰','👰‍♂️','👰‍♀️','🤰','🫃','🫄','🤱','👼','🎅','🤶','🦸','🦸‍♂️'],
    'nc26': ['🦸‍♀️','🦹','🦹‍♂️','🦹‍♀️','🧙','🧙‍♂️','🧙‍♀️','🧚','🧚‍♂️','🧚‍♀️','🧛','🧛‍♂️'],
    'nc27': ['🧛‍♀️','🧜','🧜‍♂️','🧜‍♀️','🧝','🧝‍♂️','🧝‍♀️','🧞','🧞‍♂️','🧞‍♀️','🧟','🧟‍♂️'],
    'nc28': ['🧟‍♀️','💆','💆‍♂️','💆‍♀️','💇','💇‍♂️','💇‍♀️','🚶','🚶‍♂️','🚶‍♀️','🏃','🏃‍♂️'],
    'nc29': ['🏃‍♀️','💃','🕺','🕴️','👯','👯‍♂️','👯‍♀️','🧖','🧖‍♂️','🧖‍♀️','🧗','🧗‍♂️'],
    'nc30': ['🧗‍♀️','🏇','🏂','🏌️','🏌️‍♂️','🏌️‍♀️','🏄','🏄‍♂️','🏄‍♀️','🚣','🚣‍♂️','🚣‍♀️'],
    
    # SPORTS & ACTIVITIES (31-40)
    'nc31': ['🏊','🏊‍♂️','🏊‍♀️','⛹️','⛹️‍♂️','⛹️‍♀️','🏋️','🏋️‍♂️','🏋️‍♀️','🚴','🚴‍♂️','🚴‍♀️'],
    'nc32': ['🚵','🚵‍♂️','🚵‍♀️','🤸','🤸‍♂️','🤸‍♀️','🤼','🤼‍♂️','🤼‍♀️','🤽','🤽‍♂️','🤽‍♀️'],
    'nc33': ['🤾','🤾‍♂️','🤾‍♀️','🤺','🤹','🤹‍♂️','🤹‍♀️','🧘','🧘‍♂️','🧘‍♀️','🛀','🛌'],
    'nc34': ['🧑‍🤝‍🧑','👭','👫','👬','💏','👩‍❤️‍💋‍👨','👨‍❤️‍💋‍👨','👩‍❤️‍💋‍👩','💑','👩‍❤️‍👨','👨‍❤️‍👨','👩‍❤️‍👩'],
    'nc35': ['👨‍👩‍👦','👨‍👩‍👧','👨‍👩‍👧‍👦','👨‍👩‍👦‍👦','👨‍👩‍👧‍👧','👨‍👨‍👦','👨‍👨‍👧','👨‍👨‍👧‍👦','👨‍👨‍👦‍👦','👨‍👨‍👧‍👧','👩‍👩‍👦','👩‍👩‍👧'],
    'nc36': ['👩‍👩‍👧‍👦','👩‍👩‍👦‍👦','👩‍👩‍👧‍👧','👨‍👦','👨‍👦‍👦','👨‍👧','👨‍👧‍👦','👨‍👧‍👧','👩‍👦','👩‍👦‍👦','👩‍👧','👩‍👧‍👦'],
    'nc37': ['👩‍👧‍👧','🗣️','👤','👥','🫂','👣','🐵','🐒','🦍','🦧','🐶','🐕'],
    'nc38': ['🐩','🐺','🦊','🦝','🐱','🐈','🦁','🐯','🐅','🐆','🐴','🐎'],
    'nc39': ['🦄','🦓','🦌','🐮','🐂','🐃','🐄','🐷','🐖','🐗','🐽','🐏'],
    'nc40': ['🐑','🐐','🐪','🐫','🦙','🦒','🐘','🦏','🦛','🐭','🐁','🐀'],
    
    # ANIMALS (41-50)
    'nc41': ['🐹','🐰','🐇','🐿️','🦫','🦔','🦇','🐻','🐨','🐼','🦥','🦦'],
    'nc42': ['🦨','🦘','🦡','🐾','🦃','🐔','🐓','🐣','🐤','🐥','🐦','🐧'],
    'nc43': ['🕊️','🦅','🦆','🦢','🦉','🦤','🪶','🦩','🦚','🦜','🐸','🐊'],
    'nc44': ['🐢','🦎','🐍','🐲','🐉','🦕','🦖','🐳','🐋','🐬','🦭','🐟'],
    'nc45': ['🐠','🐡','🦈','🐙','🐚','🪸','🐌','🦋','🐛','🐜','🐝','🪲'],
    'nc46': ['🐞','🦗','🕷️','🕸️','🦂','🦟','🪳','🪰','🪱','🦠','💐','🌸'],
    'nc47': ['💮','🪷','🏵️','🌹','🥀','🌺','🌻','🌼','🌷','🌱','🪴','🌲'],
    'nc48': ['🌳','🌴','🌵','🌾','🌿','☘️','🍀','🍁','🍂','🍃','🪹','🪺'],
    'nc49': ['🍄','🍇','🍈','🍉','🍊','🍋','🍌','🍍','🥭','🍎','🍏','🍐'],
    'nc50': ['🍑','🍒','🍓','🫐','🥝','🍅','🫒','🥥','🥑','🍆','🥔','🥕'],
    
    # FOOD & DRINK (51-60)
    'nc51': ['🌽','🌶️','🫑','🥒','🥬','🥦','🧄','🧅','🍄','🥜','🫘','🌰'],
    'nc52': ['🍞','🥐','🥖','🫓','🥨','🥯','🥞','🧇','🧀','🍖','🍗','🥩'],
    'nc53': ['🥓','🍔','🍟','🍕','🌭','🥪','🌮','🌯','🫔','🥙','🧆','🥚'],
    'nc54': ['🍳','🥘','🍲','🫕','🥣','🥗','🍿','🧈','🧂','🥫','🍝','🍜'],
    'nc55': ['🍠','🍢','🍣','🍤','🍥','🥮','🍡','🥟','🥠','🥡','🦪','🍦'],
    'nc56': ['🍧','🍨','🍩','🍪','🎂','🍰','🧁','🥧','🍫','🍬','🍭','🍮'],
    'nc57': ['🍯','🍼','🥛','☕','🫖','🍵','🍶','🍾','🍷','🍸','🍹','🍺'],
    'nc58': ['🍻','🥂','🥃','🥤','🧋','🧃','🧉','🧊','🥢','🍽️','🍴','🥄'],
    'nc59': ['🔪','🏺','🌍','🌎','🌏','🌐','🗺️','🗾','🧭','🏔️','⛰️','🌋'],
    'nc60': ['🗻','🏕️','🏖️','🏜️','🏝️','🏞️','🏟️','🏛️','🏗️','🧱','🪨','🪵'],
    
    # TRAVEL & PLACES (61-70)
    'nc61': ['🛖','🏘️','🏚️','🏠','🏡','🏢','🏣','🏤','🏥','🏦','🏨','🏩'],
    'nc62': ['🏪','🏫','🏬','🏭','🏯','🏰','💒','🗼','🗽','⛪','🕌','🛕'],
    'nc63': ['🕍','⛩️','🕋','⛲','⛺','🌁','🌃','🏙️','🌄','🌅','🌆','🌇'],
    'nc64': ['🌉','♨️','🎠','🎡','🎢','💈','🎪','🚂','🚃','🚄','🚅','🚆'],
    'nc65': ['🚇','🚈','🚉','🚊','🚝','🚞','🚋','🚌','🚍','🚎','🚐','🚑'],
    'nc66': ['🚒','🚓','🚔','🚕','🚖','🚗','🚘','🚙','🛻','🚚','🚛','🚜'],
    'nc67': ['🏎️','🏍️','🛵','🛺','🚲','🛴','🚏','🛣️','🛤️','🛢️','⛽','🚨'],
    'nc68': ['🚥','🚦','🛑','🚧','⚓','⛵','🛶','🚤','🛳️','⛴️','🛥️','🚢'],
    'nc69': ['✈️','🛩️','🛫','🛬','🪂','💺','🚁','🚟','🚠','🚡','🛰️','🚀'],
    'nc70': ['🛸','🪐','🌠','🌌','⛱️','🧨','🎆','🎇','🎑','✨','🎈','🎉'],
    
    # OBJECTS & SYMBOLS (71-80)
    'nc71': ['🎊','🎋','🎍','🎎','🎏','🎐','🎀','🎁','🤿','🪀','🪁','🧿'],
    'nc72': ['🎫','🎟️','🎖️','🏆','🏅','🥇','🥈','🥉','⚽','⚾','🥎','🏀'],
    'nc73': ['🏐','🏈','🏉','🎾','🥏','🎳','🏏','🏑','🏒','🥍','🏓','🏸'],
    'nc74': ['🥊','🥋','🥅','⛳','⛸️','🎣','🤿','🎽','🎿','🛷','🥌','🎯'],
    'nc75': ['🪀','🪃','🥏','🎱','🔮','🧿','🪄','🎮','🎰','🎲','🧩','🧸'],
    'nc76': ['🪅','🪆','♠️','♥️','♦️','♣️','♟️','🃏','🀄','🎴','🎭','🖼️'],
    'nc77': ['🎨','🧵','🪡','🧶','🪢','👓','🕶️','🥽','🥼','🦺','👔','👕'],
    'nc78': ['👖','🧣','🧤','🧥','🧦','👗','👘','🥻','🩱','🩲','🩳','👙'],
    'nc79': ['👚','👛','👜','👝','🎒','🩴','👞','👟','🥾','🥿','👠','👡'],
    'nc80': ['🩰','👢','👑','👒','🎩','🎓','🧢','🪖','⛑️','💄','💍','💼'],
    
    # PHONE & TECH (81-90)
    'nc81': ['📱','📲','☎️','📞','📟','📠','🔋','🔌','💻','🖥️','🖨️','⌨️'],
    'nc82': ['🖱️','🖲️','💽','💾','💿','📀','🧮','🎥','📽️','🎬','📺','📷'],
    'nc83': ['📸','📹','📼','🔍','🔎','🕯️','💡','🔦','🏮','🪔','📔','📕'],
    'nc84': ['📖','🗂️','📂','📅','📆','🗒️','📊','📈','📉','🗃️','🗄️','🗑️'],
    'nc85': ['🔒','🔓','🔏','🔐','🔑','🗝️','🔨','🪓','⛏️','⚒️','🛠️','🗡️'],
    'nc86': ['⚔️','🔫','🏹','🛡️','🔧','🔩','⚙️','🗜️','⚖️','🦯','🔗','⛓️'],
    'nc87': ['🧰','🧲','⚗️','🧪','🧫','🧬','🔬','🔭','📡','💉','🩸','💊'],
    'nc88': ['🩹','🩺','🚪','🛏️','🛋️','🪑','🚽','🚿','🛁','🧴','🧷','🧹'],
    'nc89': ['🧺','🧻','🪣','🧼','🪥','🧽','🧯','🛒','🚬','⚰️','🪦','⚱️'],
    'nc90': ['🏧','🚮','🚰','♿','🚹','🚺','🚻','🚼','🚾','🛂','🛃','🛄'],
    
    # SYMBOLS & SIGNS (91-100)
    'nc91': ['🛅','⚠️','🚸','⛔','🚫','🚳','🚭','🚯','🚱','🚷','📵','🔞'],
    'nc92': ['☢️','☣️','⬆️','↗️','➡️','↘️','⬇️','↙️','⬅️','↖️','↕️','↔️'],
    'nc93': ['↩️','↪️','⤴️','⤵️','🔃','🔄','🔙','🔚','🔛','🔜','🔝','🛐'],
    'nc94': ['⚛️','🕉️','✡️','☸️','☪️','✝️','☦️','☮️','🕎','🔯','♈','♉'],
    'nc95': ['♊','♋','♌','♍','♎','♏','♐','♑','♒','♓','⛎','🔀'],
    'nc96': ['🔁','🔂','▶️','⏩','⏭️','⏯️','◀️','⏪','⏮️','🔼','⏫','🔽'],
    'nc97': ['⏬','⏸️','⏹️','⏺️','⏏️','🎦','🔅','🔆','📶','📳','📴','♀️'],
    'nc98': ['♂️','⚧️','✖️','➕','➖','➗','♾️','‼️','⁉️','❓','❔','❕'],
    'nc99': ['❗','〰️','💱','💲','⚕️','♻️','⚜️','🔱','📛','🔰','⭕','🟠'],
    'nc100': ['🟡','🟢','🔵','🟣','🟤','⚫','⚪','🟥','🟧','🟨','🟩','🟦']
}

# ========== FONT STYLES ==========
font_styles = {
    # DOUBLE STRIKE/BOLD FONTS
    'double': {
        'name': "Double Strike",
        'chars': {
            'A': '𝔸', 'B': '𝔹', 'C': 'ℂ', 'D': '𝔻', 'E': '𝔼', 'F': '𝔽', 'G': '𝔾',
            'H': 'ℍ', 'I': '𝕀', 'J': '𝕁', 'K': '𝕂', 'L': '𝕃', 'M': '𝕄', 'N': 'ℕ',
            'O': '𝕆', 'P': 'ℙ', 'Q': 'ℚ', 'R': 'ℝ', 'S': '𝕊', 'T': '𝕋', 'U': '𝕌',
            'V': '𝕍', 'W': '𝕎', 'X': '𝕏', 'Y': '𝕐', 'Z': 'ℤ',
            'a': '𝕒', 'b': '𝕓', 'c': '𝕔', 'd': '𝕕', 'e': '𝕖', 'f': '𝕗', 'g': '𝕘',
            'h': '𝕙', 'i': '𝕚', 'j': '𝕛', 'k': '𝕜', 'l': '𝕝', 'm': '𝕞', 'n': '𝕟',
            'o': '𝕠', 'p': '𝕡', 'q': '𝕢', 'r': '𝕣', 's': '𝕤', 't': '𝕥', 'u': '𝕦',
            'v': '𝕧', 'w': '𝕨', 'x': '𝕩', 'y': '𝕪', 'z': '𝕫',
            '0': '𝟘', '1': '𝟙', '2': '𝟚', '3': '𝟛', '4': '𝟜', '5': '𝟝', '6': '𝟞',
            '7': '𝟟', '8': '𝟠', '9': '𝟡'
        }
    },
    
    # MONOSPACE/BLOCK FONTS
    'mono': {
        'name': "Monospace",
        'chars': {
            'A': '𝙰', 'B': '𝙱', 'C': '𝙲', 'D': '𝙳', 'E': '𝙴', 'F': '𝙵', 'G': '𝙶',
            'H': '𝙷', 'I': '𝙸', 'J': '𝙹', 'K': '𝙺', 'L': '𝙻', 'M': '𝙼', 'N': '𝙽',
            'O': '𝙾', 'P': '𝙿', 'Q': '𝚀', 'R': '𝚁', 'S': '𝚂', 'T': '𝚃', 'U': '𝚄',
            'V': '𝚅', 'W': '𝚆', 'X': '𝚇', 'Y': '𝚈', 'Z': '𝚉',
            'a': '𝚊', 'b': '𝚋', 'c': '𝚌', 'd': '𝚍', 'e': '𝚎', 'f': '𝚏', 'g': '𝚐',
            'h': '𝚑', 'i': '𝚒', 'j': '𝚓', 'k': '𝚔', 'l': '𝚕', 'm': '𝚖', 'n': '𝚗',
            'o': '𝚘', 'p': '𝚙', 'q': '𝚚', 'r': '𝚛', 's': '𝚜', 't': '𝚝', 'u': '𝚞',
            'v': '𝚟', 'w': '𝚠', 'x': '𝚡', 'y': '𝚢', 'z': '𝚣',
            '0': '𝟶', '1': '𝟷', '2': '𝟸', '3': '𝟹', '4': '𝟺', '5': '𝟻', '6': '𝟼',
            '7': '𝟽', '8': '𝟾', '9': '𝟿'
        }
    },
    
    # SCRIPT/CURSIVE FONTS
    'script': {
        'name': "Script",
        'chars': {
            'A': '𝒜', 'B': '𝐵', 'C': '𝒞', 'D': '𝒟', 'E': '𝐸', 'F': '𝐹', 'G': '𝒢',
            'H': '𝐻', 'I': '𝐼', 'J': '𝒥', 'K': '𝒦', 'L': '𝐿', 'M': '𝑀', 'N': '𝒩',
            'O': '𝒪', 'P': '𝒫', 'Q': '𝒬', 'R': '𝑅', 'S': '𝒮', 'T': '𝒯', 'U': '𝒰',
            'V': '𝒱', 'W': '𝒲', 'X': '𝒳', 'Y': '𝒴', 'Z': '𝒵',
            'a': '𝒶', 'b': '𝒷', 'c': '𝒸', 'd': '𝒹', 'e': '𝑒', 'f': '𝒻', 'g': 'ℊ',
            'h': '𝒽', 'i': '𝒾', 'j': '𝒿', 'k': '𝓀', 'l': '𝓁', 'm': '𝓂', 'n': '𝓃',
            'o': '𝑜', 'p': '𝓅', 'q': '𝓆', 'r': '𝓇', 's': '𝓈', 't': '𝓉', 'u': '𝓊',
            'v': '𝓋', 'w': '𝓌', 'x': '𝓍', 'y': '𝓎', 'z': '𝓏'
        }
    },
    
    # BOLD SCRIPT FONTS
    'boldscript': {
        'name': "Bold Script",
        'chars': {
            'A': '𝓐', 'B': '𝓑', 'C': '𝓒', 'D': '𝓓', 'E': '𝓔', 'F': '𝓕', 'G': '𝓖',
            'H': '𝓗', 'I': '𝓘', 'J': '𝓙', 'K': '𝓚', 'L': '𝓛', 'M': '𝓜', 'N': '𝓝',
            'O': '𝓞', 'P': '𝓟', 'Q': '𝓠', 'R': '𝓡', 'S': '𝓢', 'T': '𝓣', 'U': '𝓤',
            'V': '𝓥', 'W': '𝓦', 'X': '𝓧', 'Y': '𝓨', 'Z': '𝓩',
            'a': '𝓪', 'b': '𝓫', 'c': '𝓬', 'd': '𝓭', 'e': '𝓮', 'f': '𝓯', 'g': '𝓰',
            'h': '𝓱', 'i': '𝓲', 'j': '𝓳', 'k': '𝓴', 'l': '𝓵', 'm': '𝓶', 'n': '𝓷',
            'o': '𝓸', 'p': '𝓹', 'q': '𝓺', 'r': '𝓻', 's': '𝓼', 't': '𝓽', 'u': '𝓾',
            'v': '𝓿', 'w': '𝔀', 'x': '𝔁', 'y': '𝔂', 'z': '𝔃'
        }
    },
    
    # GOTHIC/BLACKLETTER FONTS
    'gothic': {
        'name': "Gothic",
        'chars': {
            'A': '𝔄', 'B': '𝔅', 'C': 'ℭ', 'D': '𝔇', 'E': '𝔈', 'F': '𝔉', 'G': '𝔊',
            'H': 'ℌ', 'I': 'ℑ', 'J': '𝔍', 'K': '𝔎', 'L': '𝔏', 'M': '𝔐', 'N': '𝔑',
            'O': '𝔒', 'P': '𝔓', 'Q': '𝔔', 'R': 'ℜ', 'S': '𝔖', 'T': '𝔗', 'U': '𝔘',
            'V': '𝔙', 'W': '𝔚', 'X': '𝔛', 'Y': '𝔜', 'Z': 'ℨ',
            'a': '𝔞', 'b': '𝔟', 'c': '𝔠', 'd': '𝔡', 'e': '𝔢', 'f': '𝔣', 'g': '𝔤',
            'h': '𝔥', 'i': '𝔦', 'j': '𝔧', 'k': '𝔨', 'l': '𝔩', 'm': '𝔪', 'n': '𝔫',
            'o': '𝔬', 'p': '𝔭', 'q': '𝔮', 'r': '𝔯', 's': '𝔰', 't': '𝔱', 'u': '𝔲',
            'v': '𝔳', 'w': '𝔴', 'x': '𝔵', 'y': '𝔶', 'z': '𝔷'
        }
    },
    
    # BOLD GOTHIC FONTS
    'boldgothic': {
        'name': "Bold Gothic",
        'chars': {
            'A': '𝕬', 'B': '𝕭', 'C': '𝕮', 'D': '𝕯', 'E': '𝕰', 'F': '𝕱', 'G': '𝕲',
            'H': '𝕳', 'I': '𝕴', 'J': '𝕵', 'K': '𝕶', 'L': '𝕷', 'M': '𝕸', 'N': '𝕹',
            'O': '𝕺', 'P': '𝕻', 'Q': '𝕼', 'R': '𝕽', 'S': '𝕾', 'T': '𝕿', 'U': '𝖀',
            'V': '𝖁', 'W': '𝖂', 'X': '𝖃', 'Y': '𝖄', 'Z': '𝖅',
            'a': '𝖆', 'b': '𝖇', 'c': '𝖈', 'd': '𝖉', 'e': '𝖊', 'f': '𝖋', 'g': '𝖌',
            'h': '𝖍', 'i': '𝖎', 'j': '𝖏', 'k': '𝖐', 'l': '𝖑', 'm': '𝖒', 'n': '𝖓',
            'o': '𝖔', 'p': '𝖕', 'q': '𝖖', 'r': '𝖗', 's': '𝖘', 't': '𝖙', 'u': '𝖚',
            'v': '𝖛', 'w': '𝖜', 'x': '𝖝', 'y': '𝖞', 'z': '𝖟'
        }
    },
    
    # SQUARE/FULLWIDTH FONTS
    'square': {
        'name': "Square",
        'chars': {
            'A': 'Ａ', 'B': 'Ｂ', 'C': 'Ｃ', 'D': 'Ｄ', 'E': 'Ｅ', 'F': 'Ｆ', 'G': 'Ｇ',
            'H': 'Ｈ', 'I': 'Ｉ', 'J': 'Ｊ', 'K': 'Ｋ', 'L': 'Ｌ', 'M': 'Ｍ', 'N': 'Ｎ',
            'O': 'Ｏ', 'P': 'Ｐ', 'Q': 'Ｑ', 'R': 'Ｒ', 'S': 'Ｓ', 'T': 'Ｔ', 'U': 'Ｕ',
            'V': 'Ｖ', 'W': 'Ｗ', 'X': 'Ｘ', 'Y': 'Ｙ', 'Z': 'Ｚ',
            'a': 'ａ', 'b': 'ｂ', 'c': 'ｃ', 'd': 'ｄ', 'e': 'ｅ', 'f': 'ｆ', 'g': 'ｇ',
            'h': 'ｈ', 'i': 'ｉ', 'j': 'ｊ', 'k': 'ｋ', 'l': 'ｌ', 'm': 'ｍ', 'n': 'ｎ',
            'o': 'ｏ', 'p': 'ｐ', 'q': 'ｑ', 'r': 'ｒ', 's': 'ｓ', 't': 'ｔ', 'u': 'ｕ',
            'v': 'ｖ', 'w': 'ｗ', 'x': 'ｘ', 'y': 'ｙ', 'z': 'ｚ',
            '0': '０', '1': '１', '2': '２', '3': '３', '4': '４', '5': '５', '6': '６',
            '7': '７', '8': '８', '9': '９'
        }
    },
    
    # CIRCLED FONTS
    'circled': {
        'name': "Circled",
        'chars': {
            'A': 'Ⓐ', 'B': 'Ⓑ', 'C': 'Ⓒ', 'D': 'Ⓓ', 'E': 'Ⓔ', 'F': 'Ⓕ', 'G': 'Ⓖ',
            'H': 'Ⓗ', 'I': 'Ⓘ', 'J': 'Ⓙ', 'K': 'Ⓚ', 'L': 'Ⓛ', 'M': 'Ⓜ', 'N': 'Ⓝ',
            'O': 'Ⓞ', 'P': 'Ⓟ', 'Q': 'Ⓠ', 'R': 'Ⓡ', 'S': 'Ⓢ', 'T': 'Ⓣ', 'U': 'Ⓤ',
            'V': 'Ⓥ', 'W': 'Ⓦ', 'X': 'Ⓧ', 'Y': 'Ⓨ', 'Z': 'Ⓩ',
            'a': 'ⓐ', 'b': 'ⓑ', 'c': 'ⓒ', 'd': 'ⓓ', 'e': 'ⓔ', 'f': 'ⓕ', 'g': 'ⓖ',
            'h': 'ⓗ', 'i': 'ⓘ', 'j': 'ⓙ', 'k': 'ⓚ', 'l': 'ⓛ', 'm': 'ⓜ', 'n': 'ⓝ',
            'o': 'ⓞ', 'p': 'ⓟ', 'q': 'ⓠ', 'r': 'ⓡ', 's': 'ⓢ', 't': 'ⓣ', 'u': 'ⓤ',
            'v': 'ⓥ', 'w': 'ⓦ', 'x': 'ⓧ', 'y': 'ⓨ', 'z': 'ⓩ',
            '0': '⓪', '1': '①', '2': '②', '3': '③', '4': '④', '5': '⑤', '6': '⑥',
            '7': '⑦', '8': '⑧', '9': '⑨'
        }
    }
}

# ========== TRIPLE ATTACK DEFINITIONS ==========
triple_nc_combos = {
    # Format: triple_name: [nc1, nc2, nc3] - Each runs as separate attack
    'triple1': ['nc1', 'nc2', 'nc3'],
    'triple2': ['nc4', 'nc5', 'nc6'],
    'triple3': ['nc7', 'nc8', 'nc9'],
    'triple4': ['nc10', 'nc11', 'nc12'],
    'triple5': ['nc13', 'nc14', 'nc15'],
    'triple6': ['nc16', 'nc17', 'nc18'],
    'triple7': ['nc19', 'nc20', 'nc21'],
    'triple8': ['nc22', 'nc23', 'nc24'],
    'triple9': ['nc25', 'nc26', 'nc27'],
    'triple10': ['nc28', 'nc29', 'nc30'],
    
    # PHONE KEYBOARD TRIPLE ATTACKS
    'triple11': ['nc81', 'nc82', 'nc83'],
    'triple12': ['nc84', 'nc85', 'nc86'],
    'triple13': ['nc87', 'nc88', 'nc89'],
    'triple14': ['nc90', 'nc91', 'nc92'],
    'triple15': ['nc93', 'nc94', 'nc95'],
    
    # FACE ATTACKS
    'triple16': ['nc1', 'nc4', 'nc7'],
    'triple17': ['nc2', 'nc5', 'nc8'],
    'triple18': ['nc3', 'nc6', 'nc9'],
    
    # HAND ATTACKS
    'triple19': ['nc11', 'nc12', 'nc13'],
    
    # FOOD ATTACKS
    'triple20': ['nc50', 'nc51', 'nc52'],
    'triple21': ['nc53', 'nc54', 'nc55'],
    'triple22': ['nc56', 'nc57', 'nc58'],
    
    # TRAVEL ATTACKS
    'triple23': ['nc64', 'nc65', 'nc66'],
    'triple24': ['nc67', 'nc68', 'nc69'],
    
    # SPORTS ATTACKS
    'triple25': ['nc72', 'nc73', 'nc74'],
    
    # CLOTHING ATTACKS
    'triple26': ['nc77', 'nc78', 'nc79'],
    
    # SYMBOL ATTACKS
    'triple27': ['nc93', 'nc97', 'nc99'],
    'triple28': ['nc94', 'nc95', 'nc96'],
    'triple29': ['nc98', 'nc99', 'nc100'],
    
    # MIXED ATTACKS
    'triple30': ['nc31', 'nc41', 'nc71'],
    'triple31': ['nc20', 'nc40', 'nc60'],
    'triple32': ['nc35', 'nc45', 'nc55'],
    'triple33': ['nc25', 'nc35', 'nc45'],
    'triple34': ['nc15', 'nc25', 'nc35'],
    'triple35': ['nc5', 'nc15', 'nc25']
}

# ========== THUNDER MENU ==========
THUNDER_MENU = """
╔══════════════════════════════════════════════╗
║         ⚡⚡⚡ ROCKY WP GOD v3.0 ⚡⚡⚡         ║
║       ⚡ TRIPLE NC ATTACK SYSTEM ⚡          ║
╠══════════════════════════════════════════════╣
║  👑 ADMIN COMMANDS                           ║
╠══════════════════════════════════════════════╣
║  +admin      → Become admin (DM)             ║
║  -admin      → Remove yourself               ║
║  +sub        → Make sub-admin (reply)        ║
║  -sub        → Remove sub-admin              ║
╠══════════════════════════════════════════════╣
║  🤖 BOT MANAGEMENT                           ║
╠══════════════════════════════════════════════╣
║  +add [num]  → Add new bot                   ║
║  +bots       → List all bots                 ║
║  +ping       → Check bot latency             ║
╠══════════════════════════════════════════════╣
║  ⚡ TEXT + EMOJI ATTACKS (NEW!) ⚡           ║
╠══════════════════════════════════════════════╣
║  +tne [font] [nc#] [text] [delay]           ║
║  Fonts: double, mono, script, boldscript    ║
║          gothic, boldgothic, square, circled║
║  Example: +tne double nc1 RAID 1000         ║
║  Example: +tne script nc50 HELLO 1500       ║
║  +fonts       → Show available fonts        ║
║  -tne         → Stop text+emoji attacks     ║
╠══════════════════════════════════════════════╣
║  ⚡ TRIPLE NC ATTACKS (35 Types) ⚡          ║
╠══════════════════════════════════════════════╣
║  +triple1 [text]  → Starts: nc1 + nc2 + nc3  ║
║  +triple2 [text]  → Starts: nc4 + nc5 + nc6  ║
║  +triple3 [text]  → Starts: nc7 + nc8 + nc9  ║
║  +triple4 [text]  → Starts: nc10+nc11+nc12   ║
║  +triple5 [text]  → Starts: nc13+nc14+nc15   ║
║  ... up to +triple35                        ║
╠══════════════════════════════════════════════╣
║  DELAY CONTROLS                             ║
╠══════════════════════════════════════════════╣
║  +delaytriple[1-35] [ms] → Set triple delay ║
║  +delaync[1-100] [ms]    → Set NC delay     ║
║  +delays                → Show all delays   ║
╠══════════════════════════════════════════════╣
║  ⚡ INDIVIDUAL NC ATTACKS (100 Types) ⚡    ║
╠══════════════════════════════════════════════╣
║  +nc1 to +nc100 [text] → Single NC attacks  ║
║  -nc                   → Stop NC attacks    ║
╠══════════════════════════════════════════════╣
║  💬 MESSAGE ATTACKS                        ║
╠══════════════════════════════════════════════╣
║  +s [text] [delay]  → Slide attack         ║
║  -s                 → Stop slides          ║
║  +txt [text] [delay]→ Text spam            ║
║  -txt               → Stop text            ║
╠══════════════════════════════════════════════╣
║  🎤 TTS VOICE ATTACKS                      ║
╠══════════════════════════════════════════════╣
║  +tts [text]        → Send voice           ║
║  +ttsatk [text] [delay] → Voice spam       ║
║  -ttsatk            → Stop voice           ║
╠══════════════════════════════════════════════╣
║  📸 PICTURE ATTACKS                        ║
╠══════════════════════════════════════════════╣
║  +pic [delay]       → Pic spam             ║
║                      (reply to pic)         ║
║  -pic               → Stop pic             ║
╠══════════════════════════════════════════════╣
║  🛑 STOP ALL                               ║
╠══════════════════════════════════════════════╣
║  -all        → Stop all attacks            ║
╠══════════════════════════════════════════════╣
║  📋 INFO                                   ║
╠══════════════════════════════════════════════╣
║  +menu       → Show this menu              ║
║  +status     → Active attacks              ║
║  +delays     → Show current delays         ║
║  +triples    → List triple combos          ║
║  +fonts      → Show all font styles        ║
╠══════════════════════════════════════════════╣
║       ⚡ ULTIMATE POWER ⚡                   ║
╚══════════════════════════════════════════════╝
"""

# ========== HELPER FUNCTIONS ==========

def load_roles() -> dict:
    """Load roles from file"""
    try:
        if os.path.exists(ROLES_FILE):
            with open(ROLES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f'[ROLES] Error loading roles: {e}')
    return default_roles.copy()

def save_roles(roles: dict):
    """Save roles to file"""
    try:
        os.makedirs('./data', exist_ok=True)
        with open(ROLES_FILE, 'w', encoding='utf-8') as f:
            json.dump(roles, f, indent=2)
    except Exception as e:
        print(f'[ROLES] Error saving roles: {e}')

def load_delays() -> dict:
    """Load delays from file"""
    try:
        if os.path.exists(DELAYS_FILE):
            with open(DELAYS_FILE, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                delays = default_delays.copy()
                delays.update(loaded)
                
                # Check for dangerously low delays
                for key, value in delays.items():
                    if key.startswith('triple') and value < MINIMUM_SAFE_DELAYS['triple_nc']:
                        print(f'⚠️ WARNING: {key} delay is set to {value}ms (RISKY - Minimum recommended: {MINIMUM_SAFE_DELAYS["triple_nc"]}ms)')
                    elif key.startswith('nc') and value < MINIMUM_SAFE_DELAYS['nc_attacks']:
                        print(f'⚠️ WARNING: {key} delay is set to {value}ms (RISKY - Minimum recommended: {MINIMUM_SAFE_DELAYS["nc_attacks"]}ms)')
                
                return delays
    except Exception as e:
        print(f'[DELAYS] Error loading delays: {e}')
    return default_delays.copy()

def save_delays(delays: dict):
    """Save delays to file"""
    try:
        os.makedirs('./data', exist_ok=True)
        with open(DELAYS_FILE, 'w', encoding='utf-8') as f:
            json.dump(delays, f, indent=2)
    except Exception as e:
        print(f'[DELAYS] Error saving delays: {e}')

def convert_to_font(text: str, font_name: str) -> str:
    """Convert text to a specific font style"""
    font = font_styles.get(font_name)
    if not font:
        return text
    
    result = []
    for char in text:
        if char in font['chars']:
            result.append(font['chars'][char])
        else:
            result.append(char)
    return ''.join(result)

def generate_tts(text: str, lang: str = 'en') -> BytesIO:
    """Generate TTS audio"""
    tts = gTTS(text=text, lang=lang, slow=False)
    audio_buffer = BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)
    return audio_buffer

# ========== GLOBAL VARIABLES ==========
roles = load_roles()
nc_delays = load_delays()

def is_admin(jid: str) -> bool:
    """Check if user is admin"""
    return jid in roles['admins']

def is_sub_admin(jid: str, group_jid: str) -> bool:
    """Check if user is sub-admin for a group"""
    return jid in roles['subAdmins'].get(group_jid, [])

def has_permission(jid: str, group_jid: str) -> bool:
    """Check if user has admin or sub-admin permission"""
    return is_admin(jid) or is_sub_admin(jid, group_jid)

def add_admin(jid: str) -> bool:
    """Add admin"""
    if jid not in roles['admins']:
        roles['admins'].append(jid)
        save_roles(roles)
        return True
    return False

def remove_admin(jid: str) -> bool:
    """Remove admin"""
    if jid in roles['admins']:
        roles['admins'].remove(jid)
        save_roles(roles)
        return True
    return False

def add_sub_admin(jid: str, group_jid: str) -> bool:
    """Add sub-admin"""
    if group_jid not in roles['subAdmins']:
        roles['subAdmins'][group_jid] = []
    if jid not in roles['subAdmins'][group_jid]:
        roles['subAdmins'][group_jid].append(jid)
        save_roles(roles)
        return True
    return False

def remove_sub_admin(jid: str, group_jid: str) -> bool:
    """Remove sub-admin"""
    if group_jid in roles['subAdmins'] and jid in roles['subAdmins'][group_jid]:
        roles['subAdmins'][group_jid].remove(jid)
        if not roles['subAdmins'][group_jid]:
            del roles['subAdmins'][group_jid]
        save_roles(roles)
        return True
    return False

# ========== BOT SESSION CLASS ==========

class BotSession:
    """Individual bot session"""
    
    def __init__(self, bot_id: str, phone_number: str, bot_manager: 'BotManager', requesting_jid: str = None):
        self.bot_id = bot_id
        self.phone_number = phone_number
        self.bot_manager = bot_manager
        self.requesting_jid = requesting_jid
        self.client: Optional[Client] = None
        self.connected = False
        self.bot_number = None
        
        # Active attacks storage
        self.active_name_changes: Dict[str, asyncio.Task] = {}  # Individual NC attacks
        self.active_triple_nc: Dict[str, dict] = {}  # Triple attacks
        self.active_slides: Dict[str, dict] = {}  # Slide attacks
        self.active_txt_senders: Dict[str, asyncio.Task] = {}  # Text spam
        self.active_tts_senders: Dict[str, asyncio.Task] = {}  # TTS spam
        self.active_pic_senders: Dict[str, asyncio.Task] = {}  # Picture spam
        self.active_text_emoji_attacks: Dict[str, dict] = {}  # Text+emoji attacks
        
        # Track last replied message for slide attacks
        self.last_replied_msg: Dict[str, Any] = {}
        
        # Flag for attack tasks
        self.stop_flags: Dict[str, bool] = {}
    
    async def start(self):
        """Start the bot client"""
        try:
            # Create session directory
            session_path = f'./sessions/{self.bot_id}'
            os.makedirs(session_path, exist_ok=True)
            
            # Create client
            self.client = Client(
                name=f'session_{self.bot_id}',
                workdir=session_path,
                api_id=123456,  # Replace with your API ID
                api_hash='your_api_hash',  # Replace with your API hash
                phone_number=self.phone_number if self.phone_number else None,
                in_memory=False
            )
            
            @self.client.on_message(filters.text | filters.sticker | filters.photo | filters.voice | filters.video)
            async def handle_message(client: Client, message: Message):
                await self.handle_message(message)
            
            await self.client.start()
            self.connected = True
            self.bot_number = (await self.client.get_me()).id
            print(f'[{self.bot_id}] ✅ CONNECTED! Number: {self.bot_number}')
            
            # If requesting JID exists, send confirmation
            if self.requesting_jid:
                await self.send_message(
                    self.requesting_jid,
                    f'🤖 *{self.bot_id} CONNECTED!* 🤖\n\n✅ Bot is online and ready!\n📱 Number: +{self.phone_number}'
                )
                
        except Exception as e:
            print(f'[{self.bot_id}] Connection error: {e}')
            self.connected = False
    
    async def stop(self):
        """Stop the bot client"""
        self.connected = False
        if self.client:
            await self.client.stop()
    
    async def handle_message(self, message: Message):
        """Handle incoming messages"""
        try:
            if not message.text:
                return
            if message.from_user and message.from_user.is_self:
                return
            
            # Get message details
            from_jid = str(message.chat.id)
            is_group = message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]
            sender = str(message.from_user.id)
            
            # Add @s.whatsapp.net format for consistency
            if not sender.endswith('@s.whatsapp.net'):
                sender = f'{sender}@s.whatsapp.net'
            
            text = message.text.strip()
            original_text = text
            text_lower = text.lower()
            
            # Debug log
            print(f'[{self.bot_id}] MSG from {sender}: {text}')
            
            # Check permissions
            sender_is_admin = is_admin(sender)
            sender_is_sub_admin = is_group and is_sub_admin(sender, from_jid)
            sender_has_permission = sender_is_admin or sender_is_sub_admin
            
            # ADMIN COMMANDS (DM only)
            if not is_group and text_lower == '+admin':
                if len(roles['admins']) == 0:
                    add_admin(sender)
                    await self.send_message(from_jid, f'⚡ *THUNDER {self.bot_id}* ⚡\n\n✅ You are now the ADMIN!\n\nSend *+menu* to see commands')
                    print(f'[{self.bot_id}] New admin: {sender}')
                elif sender_is_admin:
                    await self.send_message(from_jid, f'⚠️ You are already the admin! - {self.bot_id}')
                else:
                    await self.send_message(from_jid, f'❌ Admin already exists! Only one admin allowed. - {self.bot_id}')
                return
            
            if not is_group and text_lower == '-admin':
                if sender_is_admin:
                    remove_admin(sender)
                    await self.send_message(from_jid, f'✅ You are no longer an admin! - {self.bot_id}')
                    print(f'[{self.bot_id}] Removed admin: {sender}')
                else:
                    await self.send_message(from_jid, f'⚠️ You are not an admin! - {self.bot_id}')
                return
            
            # SUB-ADMIN COMMANDS (Group only)
            if is_group and text_lower == '+sub' and sender_is_admin:
                if not message.reply_to_message:
                    await self.send_message(from_jid, f'❌ Reply to someone to make them sub-admin! - {self.bot_id}')
                    return
                
                target = message.reply_to_message.from_user
                if target.is_self:
                    await self.send_message(from_jid, f'❌ Cannot make bot sub-admin! - {self.bot_id}')
                    return
                
                target_jid = f'{target.id}@s.whatsapp.net'
                if add_sub_admin(target_jid, from_jid):
                    await self.send_message(
                        from_jid,
                        f'✅ @{target_jid.split("@")[0]} is now a SUB-ADMIN! - {self.bot_id}',
                        parse_mode=enums.ParseMode.HTML
                    )
                else:
                    await self.send_message(from_jid, f'⚠️ Already a sub-admin! - {self.bot_id}')
                return
            
            if is_group and text_lower == '-sub' and sender_is_admin:
                if not message.reply_to_message:
                    await self.send_message(from_jid, f'❌ Reply to someone to remove them as sub-admin! - {self.bot_id}')
                    return
                
                target = message.reply_to_message.from_user
                target_jid = f'{target.id}@s.whatsapp.net'
                if remove_sub_admin(target_jid, from_jid):
                    await self.send_message(
                        from_jid,
                        f'✅ @{target_jid.split("@")[0]} is no longer a sub-admin! - {self.bot_id}',
                        parse_mode=enums.ParseMode.HTML
                    )
                else:
                    await self.send_message(from_jid, f'⚠️ Not a sub-admin! - {self.bot_id}')
                return
            
            # BOT MANAGEMENT COMMANDS
            if text_lower.startswith('+add ') and sender_has_permission:
                number = re.sub(r'[^0-9]', '', text[5:].strip())
                if len(number) < 10:
                    await self.send_message(from_jid, f'❌ Invalid phone number! - {self.bot_id}\n\nUsage: +add [number]\nExample: +add 1234567890')
                    return
                
                result = await self.bot_manager.add_bot(number, from_jid)
                await self.send_message(from_jid, result)
                return
            
            if text_lower == '+bots' and sender_has_permission:
                bots = self.bot_manager.command_bus.get_all_bots()
                msg = f'🤖 *ACTIVE BOTS ({self.bot_id})* 🤖\n\n'
                msg += f'Total Bots: {len(bots)}\n\n'
                
                for bot in bots:
                    status = '✅ Online' if bot.connected else '⚠️ Offline'
                    msg += f'{bot.bot_id}: {status}\n'
                    if bot.bot_number:
                        msg += f'  📱 {bot.bot_number}\n'
                
                await self.send_message(from_jid, msg)
                return
            
            if text_lower == '+ping' and sender_has_permission:
                start_time = time.time()
                await self.send_message(from_jid, '🏓 Pinging...')
                latency = int((time.time() - start_time) * 1000)
                await self.send_message(from_jid, f'⚡ *THUNDER PING* ⚡\n\n🏓 Latency: {latency}ms\n🤖 Bot: {self.bot_id}')
                return
            
            # DELAYS COMMAND
            if text_lower == '+delays' and sender_has_permission:
                delay_msg = f'⚡ *THUNDER DELAYS ({self.bot_id})* ⚡\n\n'
                
                # Show Triple Attack delays
                delay_msg += '*TRIPLE ATTACK DELAYS:*\n'
                delay_msg += '━━━━━━━━━━━━━━━━━━━━━\n'
                
                for i in range(1, 36):
                    triple_key = f'triple{i}'
                    delay_value = nc_delays.get(triple_key, 200)
                    combo_names = triple_nc_combos.get(triple_key, ['nc1', 'nc2', 'nc3'])
                    
                    delay_msg += f'{triple_key}: {", ".join(combo_names)} → {delay_value}ms'
                    
                    if delay_value < MINIMUM_SAFE_DELAYS['triple_nc']:
                        delay_msg += ' ⚠️ RISKY!\n'
                    else:
                        delay_msg += ' ✅\n'
                    
                    if i % 5 == 0:
                        delay_msg += '\n'
                
                delay_msg += '\n*INDIVIDUAL NC DELAYS (Sample):*\n'
                delay_msg += '━━━━━━━━━━━━━━━━━━━━━\n'
                
                for i in range(1, 11):
                    nc_key = f'nc{i}'
                    delay_value = nc_delays.get(nc_key, 200)
                    first_emoji = emoji_arrays.get(nc_key, ['❓'])[0]
                    
                    delay_msg += f'{nc_key}: {first_emoji} → {delay_value}ms'
                    
                    if delay_value < MINIMUM_SAFE_DELAYS['nc_attacks']:
                        delay_msg += ' ⚠️\n'
                    else:
                        delay_msg += ' ✅\n'
                
                delay_msg += '... +nc11 to +nc100 available\n\n'
                delay_msg += f'⚠️ MINIMUM SAFE DELAYS:\n'
                delay_msg += f'• Triple Attacks: {MINIMUM_SAFE_DELAYS["triple_nc"]}ms\n'
                delay_msg += f'• Individual NC: {MINIMUM_SAFE_DELAYS["nc_attacks"]}ms\n'
                delay_msg += f'• Messages: {MINIMUM_SAFE_DELAYS["messages"]}ms\n\n'
                delay_msg += 'Use +delaync[1-100] [ms] or +delaytriple[1-35] [ms]'
                
                await self.send_message(from_jid, delay_msg)
                return
            
            # TRIPLES COMMAND
            if text_lower == '+triples' and sender_has_permission:
                triples_msg = f'⚡ *TRIPLE NC ATTACKS ({self.bot_id})* ⚡\n\n'
                triples_msg += f'Total Triple Attacks: 35\n'
                triples_msg += f'Format: +triple[1-35] [text]\n\n'
                
                for i in range(1, 36):
                    triple_key = f'triple{i}'
                    combo_names = triple_nc_combos.get(triple_key, ['nc1', 'nc2', 'nc3'])
                    first_emoji = emoji_arrays.get(combo_names[0], ['❓'])[0]
                    second_emoji = emoji_arrays.get(combo_names[1], ['❓'])[0]
                    third_emoji = emoji_arrays.get(combo_names[2], ['❓'])[0]
                    
                    triples_msg += f'{triple_key}: {first_emoji} {second_emoji} {third_emoji}'
                    
                    # Add description for some attacks
                    if i == 11:
                        triples_msg += ' (Phone Attacks 1)'
                    elif i == 12:
                        triples_msg += ' (Phone Attacks 2)'
                    elif i == 13:
                        triples_msg += ' (Phone Attacks 3)'
                    elif i == 14:
                        triples_msg += ' (Phone Attacks 4)'
                    elif i == 15:
                        triples_msg += ' (Phone Attacks 5)'
                    
                    triples_msg += '\n'
                    
                    if i % 7 == 0:
                        triples_msg += '\n'
                
                triples_msg += '\nExample: +triple1 RAID → Starts nc1, nc2, and nc3 simultaneously'
                await self.send_message(from_jid, triples_msg)
                return
            
            # FONTS COMMAND
            if text_lower == '+fonts' and sender_has_permission:
                font_msg = f'🎨 *AVAILABLE FONT STYLES* 🎨\n\n'
                for i, (font_name, font_info) in enumerate(font_styles.items()):
                    sample_text = convert_to_font('Thunder', font_name)
                    font_msg += f'{font_name}: {font_info["name"]}\nSample: {sample_text}\n'
                    if (i + 1) % 2 == 0:
                        font_msg += '\n'
                font_msg += '\nUsage: +tne [font] [nc#] [text] [delay]\nExample: +tne double nc1 RAID 1000'
                await self.send_message(from_jid, font_msg)
                return
            
            if text_lower == '+menu' and sender_has_permission:
                await self.send_message(from_jid, f'{THUNDER_MENU}\n\n📍 Responding from: {self.bot_id}')
                return
            
            # STATUS COMMAND
            if text_lower == '+status' and sender_has_permission:
                all_bots = self.bot_manager.command_bus.get_all_bots()
                total_name = sum(len(bot.active_name_changes) for bot in all_bots)
                total_triple = sum(len(bot.active_triple_nc) for bot in all_bots)
                total_slide = sum(len(bot.active_slides) for bot in all_bots)
                total_txt = sum(len(bot.active_txt_senders) for bot in all_bots)
                total_tts = sum(len(bot.active_tts_senders) for bot in all_bots)
                total_pic = sum(len(bot.active_pic_senders) for bot in all_bots)
                total_tne = sum(len(bot.active_text_emoji_attacks) for bot in all_bots)
                
                local_name = len([k for k in self.active_name_changes.keys() if k.startswith(from_jid)])
                local_triple = len([k for k in self.active_triple_nc.keys() if k.startswith(from_jid)])
                local_slide = len([k for k in self.active_slides.keys() if k.startswith(from_jid)])
                local_txt = len([k for k in self.active_txt_senders.keys() if k.startswith(from_jid)])
                local_tts = len([k for k in self.active_tts_senders.keys() if k.startswith(from_jid)])
                local_pic = len([k for k in self.active_pic_senders.keys() if k.startswith(from_jid)])
                local_tne = len([k for k in self.active_text_emoji_attacks.keys() if k.startswith(from_jid)])
                
                status_msg = f"""
⚡ *{self.bot_id} THUNDER STATUS* ⚡
━━━━━━━━━━━━━━━━━━━━━
📊 *THIS CHAT ({self.bot_id})*
━━━━━━━━━━━━━━━━━━━━━
⚔️ Individual NC: {local_name}
🎭 Triple Attacks: {local_triple}
🎨 Text+Emoji: {local_tne}
🎯 Slide Attacks: {local_slide}
💀 Text Attacks: {local_txt}
🎤 TTS Attacks: {local_tts}
📸 Pic Attacks: {local_pic}
━━━━━━━━━━━━━━━━━━━━━
🌐 *ALL BOTS GLOBAL*
━━━━━━━━━━━━━━━━━━━━━
⚔️ Individual NC: {total_name}
🎭 Triple Attacks: {total_triple}
🎨 Text+Emoji: {total_tne}
🎯 Slide Attacks: {total_slide}
💀 Text Attacks: {total_txt}
🎤 TTS Attacks: {total_tts}
📸 Pic Attacks: {total_pic}
━━━━━━━━━━━━━━━━━━━━━
🤖 Active Bots: {len([b for b in all_bots if b.connected])}/{len(all_bots)}
━━━━━━━━━━━━━━━━━━━━━"""
                
                await self.send_message(from_jid, status_msg)
                return
            
            # STOP ALL COMMAND
            if text_lower == '-all' and sender_has_permission:
                await self.bot_manager.command_bus.broadcast_command('stop_all', {'from': from_jid}, self.bot_id)
                return
            
            # TEXT+EMOJI ATTACK COMMAND
            if text_lower.startswith('+tne ') and sender_has_permission:
                args = original_text[5:].strip().split()
                if len(args) < 4:
                    await self.send_message(from_jid, f'❌ Usage: +tne [font] [nc#] [text] [delay] - {self.bot_id}\nExample: +tne double nc1 RAID 1000\nUse +fonts to see available fonts')
                    return
                
                font_style = args[0].lower()
                nc_key = args[1].lower()
                tne_delay = int(args[-1])
                tne_text = ' '.join(args[2:-1])
                
                if font_style not in font_styles:
                    await self.send_message(from_jid, f'❌ Invalid font style! Use +fonts to see available styles - {self.bot_id}')
                    return
                
                if nc_key not in emoji_arrays:
                    await self.send_message(from_jid, f'❌ Invalid NC number! Use nc1 to nc100 - {self.bot_id}')
                    return
                
                if tne_delay < 100:
                    await self.send_message(from_jid, f'❌ Delay must be >= 100ms - {self.bot_id}')
                    return
                
                if not is_group:
                    await self.send_message(from_jid, f'❌ Use this in a group! - {self.bot_id}')
                    return
                
                await self.bot_manager.command_bus.broadcast_command(
                    'start_tne',
                    {'from': from_jid, 'tne_text': tne_text, 'tne_delay': tne_delay, 'font_style': font_style, 'nc_key': nc_key},
                    self.bot_id
                )
                return
            
            if text_lower == '-tne' and sender_has_permission:
                if not is_group:
                    await self.send_message(from_jid, f'❌ Use this in a group! - {self.bot_id}')
                    return
                
                await self.bot_manager.command_bus.broadcast_command('stop_tne', {'from': from_jid}, self.bot_id)
                return
            
            # TRIPLE ATTACK DELAY SETTING
            for i in range(1, 36):
                triple_key = f'triple{i}'
                if text_lower.startswith(f'+delay{triple_key} '):
                    try:
                        delay_value = int(text.split()[1])
                        if delay_value < 50:
                            await self.send_message(from_jid, f'❌ Delay must be >= 50ms - {self.bot_id}')
                            return
                        
                        nc_delays[triple_key] = delay_value
                        save_delays(nc_delays)
                        
                        combo_names = triple_nc_combos.get(triple_key, ['nc1', 'nc2', 'nc3'])
                        
                        warning = ''
                        if delay_value < MINIMUM_SAFE_DELAYS['triple_nc']:
                            warning = f'\n\n⚠️ WARNING: {delay_value}ms is VERY RISKY for triple attacks!\nRecommended minimum: {MINIMUM_SAFE_DELAYS["triple_nc"]}ms'
                        
                        await self.send_message(from_jid, f'⚡ *THUNDER {self.bot_id}* ⚡\n\n✅ {triple_key.upper()} delay set to {delay_value}ms\nRuns: {", ".join(combo_names)} simultaneously{warning}')
                        return
                    except (ValueError, IndexError):
                        pass
            
            # INDIVIDUAL NC DELAY SETTING
            for i in range(1, 101):
                nc_key = f'nc{i}'
                if text_lower.startswith(f'+delay{nc_key} '):
                    try:
                        delay_value = int(text.split()[1])
                        if delay_value < 50:
                            await self.send_message(from_jid, f'❌ Delay must be >= 50ms - {self.bot_id}')
                            return
                        
                        nc_delays[nc_key] = delay_value
                        save_delays(nc_delays)
                        
                        warning = ''
                        if delay_value < MINIMUM_SAFE_DELAYS['nc_attacks']:
                            warning = f'\n\n⚠️ WARNING: {delay_value}ms is VERY RISKY!\nRecommended minimum: {MINIMUM_SAFE_DELAYS["nc_attacks"]}ms'
                        
                        await self.send_message(from_jid, f'⚡ *THUNDER {self.bot_id}* ⚡\n\n✅ {nc_key.upper()} delay set to {delay_value}ms{warning}')
                        return
                    except (ValueError, IndexError):
                        pass
            
            # TRIPLE ATTACK COMMANDS
            for i in range(1, 36):
                triple_key = f'triple{i}'
                if text_lower.startswith(f'+{triple_key} '):
                    name_text = text[len(triple_key)+2:].strip()
                    if not name_text:
                        await self.send_message(from_jid, f'❌ Usage: +{triple_key} [text] - {self.bot_id}\nExample: +{triple_key} RAID')
                        return
                    
                    if not is_group:
                        await self.send_message(from_jid, f'❌ Use this in a group! - {self.bot_id}')
                        return
                    
                    await self.bot_manager.command_bus.broadcast_command(
                        'start_triple_nc',
                        {'from': from_jid, 'name_text': name_text, 'triple_key': triple_key},
                        self.bot_id
                    )
                    return
            
            # INDIVIDUAL NC ATTACK COMMANDS
            for i in range(1, 101):
                nc_key = f'nc{i}'
                if text_lower.startswith(f'+{nc_key} '):
                    name_text = text[len(nc_key)+2:].strip()
                    if not name_text:
                        await self.send_message(from_jid, f'❌ Usage: +{nc_key} [text] - {self.bot_id}\nExample: +{nc_key} RAID')
                        return
                    
                    if not is_group:
                        await self.send_message(from_jid, f'❌ Use this in a group! - {self.bot_id}')
                        return
                    
                    await self.bot_manager.command_bus.broadcast_command(
                        'start_nc',
                        {'from': from_jid, 'name_text': name_text, 'nc_key': nc_key},
                        self.bot_id
                    )
                    return
            
            if text_lower == '-nc' and sender_has_permission:
                if not is_group:
                    await self.send_message(from_jid, f'❌ Use this in a group! - {self.bot_id}')
                    return
                
                await self.bot_manager.command_bus.broadcast_command('stop_nc', {'from': from_jid}, self.bot_id)
                await self.bot_manager.command_bus.broadcast_command('stop_triple_nc', {'from': from_jid}, self.bot_id)
                return
            
            # SLIDE ATTACK
            if text_lower.startswith('+s ') and sender_has_permission:
                if not message.reply_to_message:
                    await self.send_message(from_jid, f'❌ Reply to target\'s message! - {self.bot_id}\nUsage: +s [text] [delay]')
                    return
                
                args = text[3:].strip().split()
                if len(args) < 2:
                    await self.send_message(from_jid, f'❌ Usage: +s [text] [delay] - {self.bot_id}\nExample: +s Hello 1000')
                    return
                
                slide_delay = int(args[-1])
                slide_text = ' '.join(args[:-1])
                
                if slide_delay < 100:
                    await self.send_message(from_jid, f'❌ Delay must be >= 100ms - {self.bot_id}')
                    return
                
                target = message.reply_to_message.from_user
                target_jid = f'{target.id}@s.whatsapp.net'
                
                await self.bot_manager.command_bus.broadcast_command(
                    'start_slide',
                    {'from': from_jid, 'slide_text': slide_text, 'slide_delay': slide_delay, 'target_jid': target_jid},
                    self.bot_id
                )
                return
            
            if text_lower == '-s' and sender_has_permission:
                await self.bot_manager.command_bus.broadcast_command('stop_slide', {'from': from_jid}, self.bot_id)
                return
            
            # TEXT SPAM
            if text_lower.startswith('+txt ') and sender_has_permission:
                args = text[5:].strip().split()
                if len(args) < 2:
                    await self.send_message(from_jid, f'❌ Usage: +txt [text] [delay] - {self.bot_id}\nExample: +txt Hello 1000')
                    return
                
                txt_delay = int(args[-1])
                txt_text = ' '.join(args[:-1])
                
                if txt_delay < 100:
                    await self.send_message(from_jid, f'❌ Delay must be >= 100ms - {self.bot_id}')
                    return
                
                await self.bot_manager.command_bus.broadcast_command(
                    'start_txt',
                    {'from': from_jid, 'txt_text': txt_text, 'txt_delay': txt_delay},
                    self.bot_id
                )
                return
            
            if text_lower == '-txt' and sender_has_permission:
                await self.bot_manager.command_bus.broadcast_command('stop_txt', {'from': from_jid}, self.bot_id)
                return
            
            # TTS ATTACKS
            if text_lower.startswith('+tts ') and sender_has_permission:
                tts_text = text[5:].strip()
                if not tts_text:
                    await self.send_message(from_jid, f'❌ Usage: +tts [text] - {self.bot_id}\nExample: +tts Hello everyone')
                    return
                
                try:
                    audio_buffer = generate_tts(tts_text)
                    await self.client.send_voice(from_jid, audio_buffer)
                except Exception as e:
                    print(f'[{self.bot_id}] TTS error: {e}')
                    await self.send_message(from_jid, f'❌ TTS error - {self.bot_id}')
                return
            
            if text_lower.startswith('+ttsatk ') and sender_has_permission:
                args = text[8:].strip().split()
                if len(args) < 2:
                    await self.send_message(from_jid, f'❌ Usage: +ttsatk [text] [delay] - {self.bot_id}\nExample: +ttsatk Hello 2000')
                    return
                
                tts_delay = int(args[-1])
                tts_text = ' '.join(args[:-1])
                
                if tts_delay < 1000:
                    await self.send_message(from_jid, f'❌ Delay must be >= 1000ms (1s) - {self.bot_id}')
                    return
                
                await self.bot_manager.command_bus.broadcast_command(
                    'start_tts',
                    {'from': from_jid, 'tts_text': tts_text, 'tts_delay': tts_delay},
                    self.bot_id
                )
                return
            
            if text_lower == '-ttsatk' and sender_has_permission:
                await self.bot_manager.command_bus.broadcast_command('stop_tts', {'from': from_jid}, self.bot_id)
                return
            
            # PICTURE ATTACKS
            if text_lower.startswith('+pic ') and sender_has_permission:
                if not message.reply_to_message or not message.reply_to_message.photo:
                    await self.send_message(from_jid, f'❌ Reply to an image! - {self.bot_id}\nUsage: +pic [delay]')
                    return
                
                pic_delay = int(text[5:].strip())
                if pic_delay < 100:
                    await self.send_message(from_jid, f'❌ Delay must be >= 100ms - {self.bot_id}')
                    return
                
                try:
                    # Download the image
                    photo = message.reply_to_message.photo
                    file_path = await self.client.download_media(photo)
                    
                    if file_path:
                        with open(file_path, 'rb') as f:
                            image_buffer = base64.b64encode(f.read()).decode('utf-8')
                        
                        await self.bot_manager.command_bus.broadcast_command(
                            'start_pic',
                            {'from': from_jid, 'pic_delay': pic_delay, 'image_buffer': image_buffer},
                            self.bot_id
                        )
                        
                        # Clean up
                        os.remove(file_path)
                except Exception as e:
                    print(f'[{self.bot_id}] Error downloading image: {e}')
                    await self.send_message(from_jid, f'❌ Error downloading image - {self.bot_id}')
                return
            
            if text_lower == '-pic' and sender_has_permission:
                await self.bot_manager.command_bus.broadcast_command('stop_pic', {'from': from_jid}, self.bot_id)
                return
                
        except Exception as e:
            print(f'[{self.bot_id}] ERROR: {e}')
    
    async def execute_command(self, command_type: str, data: dict, send_confirmation: bool = True):
        """Execute a command (attack)"""
        try:
            # INDIVIDUAL NC ATTACK
            if command_type == 'start_nc':
                from_jid = data['from']
                name_text = data['name_text']
                nc_key = data['nc_key']
                emojis = emoji_arrays.get(nc_key, ['❓'])
                name_delay = nc_delays.get(nc_key, 200)
                
                # Create multiple threads for this attack
                for i in range(5):
                    task_id = f'{from_jid}_{nc_key}_{i}'
                    
                    if task_id in self.active_name_changes:
                        self.stop_flags[task_id] = True
                        await asyncio.sleep(0.1)
                    
                    self.stop_flags[task_id] = False
                    
                    async def run_nc(thread_id: str, emoji_idx_start: int):
                        emoji_index = emoji_idx_start
                        await asyncio.sleep(emoji_idx_start * 0.2)
                        
                        while not self.stop_flags.get(thread_id, False):
                            try:
                                emoji = emojis[emoji_index % len(emojis)]
                                new_name = f'{name_text} {emoji}'
                                
                                # Update group subject (name)
                                await self.client.set_chat_title(from_jid, new_name)
                                
                                emoji_index += 1
                                await asyncio.sleep(name_delay / 1000)
                            except FloodWait as e:
                                await asyncio.sleep(e.value)
                            except Exception:
                                await asyncio.sleep(name_delay / 1000)
                        
                        # Clean up
                        if thread_id in self.active_name_changes:
                            del self.active_name_changes[thread_id]
                    
                    task = asyncio.create_task(run_nc(task_id, i * (len(emojis) // 5)))
                    self.active_name_changes[task_id] = task
                
                if send_confirmation:
                    warning = ''
                    if name_delay < MINIMUM_SAFE_DELAYS['nc_attacks']:
                        warning = f'\n\n⚠️ WARNING: {name_delay}ms is VERY RISKY!\nRisk of WhatsApp ban is HIGH!'
                    
                    await self.send_message(from_jid, f'⚡ *THUNDER {nc_key.upper()} STARTED* ⚡\n\n💥 {name_text}\n⏱️ Delay: {name_delay}ms{warning}\n🤖 Bot: {self.bot_id}')
            
            # TRIPLE NC ATTACK
            elif command_type == 'start_triple_nc':
                from_jid = data['from']
                name_text = data['name_text']
                triple_key = data['triple_key']
                combo_names = triple_nc_combos.get(triple_key, ['nc1', 'nc2', 'nc3'])
                triple_delay = nc_delays.get(triple_key, 200)
                
                # Store this triple attack
                triple_task_id = f'{from_jid}_{triple_key}'
                triple_task = {'active': True, 'nc_keys': combo_names}
                self.active_triple_nc[triple_task_id] = triple_task
                
                print(f'[{self.bot_id}] Starting TRIPLE ATTACK: {", ".join(combo_names)} with delay {triple_delay}ms')
                
                # Start each NC in the combo as SEPARATE attacks
                for nc_key in combo_names:
                    emojis = emoji_arrays.get(nc_key, ['❓'])
                    individual_delay = nc_delays.get(nc_key, 200)
                    
                    for i in range(3):
                        thread_id = f'{from_jid}_{triple_key}_{nc_key}_{i}'
                        
                        if thread_id in self.active_name_changes:
                            self.stop_flags[thread_id] = True
                            await asyncio.sleep(0.1)
                        
                        self.stop_flags[thread_id] = False
                        
                        async def run_triple_nc(thread_id: str, emoji_idx_start: int, active_flag: dict):
                            emoji_index = emoji_idx_start
                            await asyncio.sleep(emoji_idx_start * 0.1)
                            
                            while not self.stop_flags.get(thread_id, False) and active_flag.get('active', False):
                                try:
                                    emoji = emojis[emoji_index % len(emojis)]
                                    new_name = f'{name_text} {emoji}'
                                    
                                    await self.client.set_chat_title(from_jid, new_name)
                                    
                                    emoji_index += 1
                                    await asyncio.sleep(individual_delay / 1000)
                                except FloodWait as e:
                                    await asyncio.sleep(e.value)
                                except Exception:
                                    await asyncio.sleep(individual_delay / 1000)
                            
                            # Clean up
                            if thread_id in self.active_name_changes:
                                del self.active_name_changes[thread_id]
                        
                        task = asyncio.create_task(run_triple_nc(thread_id, i, triple_task))
                        self.active_name_changes[thread_id] = task
                
                if send_confirmation:
                    first_emoji = emoji_arrays.get(combo_names[0], ['❓'])[0]
                    second_emoji = emoji_arrays.get(combo_names[1], ['❓'])[0]
                    third_emoji = emoji_arrays.get(combo_names[2], ['❓'])[0]
                    
                    warning = ''
                    if triple_delay < MINIMUM_SAFE_DELAYS['triple_nc']:
                        warning = f'\n\n⚠️ WARNING: {triple_delay}ms is VERY RISKY for triple attacks!\nRisk of WhatsApp ban is EXTREMELY HIGH!'
                    
                    await self.send_message(from_jid, f'⚡ *THUNDER {triple_key.upper()} STARTED* ⚡\n\n💥 {name_text}\n🎭 Running 3 NCs: {", ".join(combo_names)}\n⚡ Each: {first_emoji} {second_emoji} {third_emoji}\n⏱️ Delay: {triple_delay}ms{warning}\n🤖 Bot: {self.bot_id}')
            
            # TEXT+EMOJI ATTACK
            elif command_type == 'start_tne':
                from_jid = data['from']
                tne_text = data['tne_text']
                tne_delay = data['tne_delay']
                font_style = data['font_style']
                nc_key = data['nc_key']
                emojis = emoji_arrays.get(nc_key, ['❓'])
                font_name = font_styles.get(font_style, {}).get('name', 'Normal')
                
                task_id = f'{from_jid}_tne_{font_style}_{nc_key}'
                
                if task_id in self.active_text_emoji_attacks:
                    self.active_text_emoji_attacks[task_id]['active'] = False
                    await asyncio.sleep(0.2)
                
                tne_task = {
                    'active': True,
                    'font_style': font_style,
                    'nc_key': nc_key,
                    'emoji_index': 0
                }
                self.active_text_emoji_attacks[task_id] = tne_task
                
                async def run_tne():
                    while tne_task['active']:
                        try:
                            emoji = emojis[tne_task['emoji_index'] % len(emojis)]
                            converted_text = convert_to_font(tne_text, font_style)
                            final_text = f'{converted_text} {emoji}'
                            
                            await self.client.set_chat_title(from_jid, final_text)
                            
                            tne_task['emoji_index'] += 1
                            await asyncio.sleep(tne_delay / 1000)
                        except FloodWait as e:
                            await asyncio.sleep(e.value)
                        except Exception as e:
                            print(f'[{self.bot_id}] TNE Error: {e}')
                            await asyncio.sleep(tne_delay / 1000)
                
                asyncio.create_task(run_tne())
                
                if send_confirmation:
                    sample_emoji = emojis[0] if emojis else '❓'
                    converted_sample = convert_to_font(tne_text, font_style)
                    sample_final = f'{converted_sample} {sample_emoji}'
                    
                    warning = ''
                    if tne_delay < MINIMUM_SAFE_DELAYS['nc_attacks']:
                        warning = f'\n\n⚠️ WARNING: {tne_delay}ms is VERY RISKY!\nRisk of WhatsApp ban is HIGH!'
                    
                    await self.send_message(from_jid, f'🎨 *TEXT+EMOJI ATTACK STARTED* 🎨\n\nFont: {font_name}\nEmoji Set: {nc_key}\nText: {tne_text}\nConverted: {converted_sample}\nFinal: {sample_final}\n⏱️ Delay: {tne_delay}ms{warning}\n🤖 Bot: {self.bot_id}')
            
            # STOP INDIVIDUAL NC
            elif command_type == 'stop_nc':
                from_jid = data['from']
                stopped = 0
                
                for task_id in list(self.active_name_changes.keys()):
                    if task_id.startswith(from_jid) and '_triple_' not in task_id:
                        self.stop_flags[task_id] = True
                        stopped += 1
                
                if stopped > 0 and send_confirmation:
                    await self.send_message(from_jid, f'⚡ *THUNDER NC STOPPED* ⚡\n\n✅ Stopped {stopped} individual NC threads - {self.bot_id}')
            
            # STOP TRIPLE NC
            elif command_type == 'stop_triple_nc':
                from_jid = data['from']
                stopped_combos = 0
                
                for task_id in list(self.active_triple_nc.keys()):
                    if task_id.startswith(from_jid):
                        self.active_triple_nc[task_id]['active'] = False
                        
                        # Find and stop all associated NC threads
                        for name_task_id in list(self.active_name_changes.keys()):
                            if name_task_id.startswith(from_jid) and task_id.split('_')[1] in name_task_id:
                                self.stop_flags[name_task_id] = True
                        
                        del self.active_triple_nc[task_id]
                        stopped_combos += 1
                
                if stopped_combos > 0 and send_confirmation:
                    await self.send_message(from_jid, f'⚡ *TRIPLE ATTACKS STOPPED* ⚡\n\n✅ Stopped {stopped_combos} triple attack(s) - {self.bot_id}')
            
            # STOP TEXT+EMOJI ATTACKS
            elif command_type == 'stop_tne':
                from_jid = data['from']
                stopped = 0
                
                for task_id in list(self.active_text_emoji_attacks.keys()):
                    if task_id.startswith(from_jid):
                        self.active_text_emoji_attacks[task_id]['active'] = False
                        del self.active_text_emoji_attacks[task_id]
                        stopped += 1
                
                if stopped > 0 and send_confirmation:
                    await self.send_message(from_jid, f'🎨 *TEXT+EMOJI ATTACKS STOPPED* 🎨\n\n✅ Stopped {stopped} text+emoji attack(s) - {self.bot_id}')
            
            # SLIDE ATTACK
            elif command_type == 'start_slide':
                from_jid = data['from']
                slide_text = data['slide_text']
                slide_delay = data['slide_delay']
                target_jid = data['target_jid']
                
                task_id = f'{from_jid}_slide_{target_jid}'
                
                if task_id in self.active_slides:
                    self.active_slides[task_id]['active'] = False
                    await asyncio.sleep(0.2)
                
                slide_task = {
                    'active': True,
                    'target_jid': target_jid,
                    'text': slide_text,
                    'group_jid': from_jid,
                    'last_replied_id': None
                }
                self.active_slides[task_id] = slide_task
                
                async def run_slide():
                    while slide_task['active']:
                        try:
                            # For slide attack, we need to reply to the target's last message
                            # In Pyrogram, we can get the last message from the target
                            async for msg in self.client.get_chat_history(from_jid, limit=10):
                                if str(msg.from_user.id) + '@s.whatsapp.net' == target_jid:
                                    await msg.reply(slide_text)
                                    break
                        except Exception as e:
                            print(f'[{self.bot_id}] SLIDE Error: {e}')
                        await asyncio.sleep(slide_delay / 1000)
                
                asyncio.create_task(run_slide())
                
                if send_confirmation:
                    warning = ''
                    if slide_delay < MINIMUM_SAFE_DELAYS['messages']:
                        warning = f'\n\n⚠️ WARNING: {slide_delay}ms is VERY RISKY!\nRisk of WhatsApp ban is HIGH!'
                    
                    await self.send_message(from_jid, f'⚡ *THUNDER SLIDE STARTED* ⚡\n\n💬 {slide_text}\n⏱️ Delay: {slide_delay}ms{warning}\n🤖 Bot: {self.bot_id}')
            
            elif command_type == 'stop_slide':
                from_jid = data['from']
                stopped = 0
                
                for task_id in list(self.active_slides.keys()):
                    if task_id.startswith(from_jid):
                        self.active_slides[task_id]['active'] = False
                        del self.active_slides[task_id]
                        stopped += 1
                
                if stopped > 0 and send_confirmation:
                    await self.send_message(from_jid, f'⚡ *THUNDER SLIDE STOPPED* ⚡\n\n✅ {stopped} attack(s) - {self.bot_id}')
            
            # TEXT SPAM
            elif command_type == 'start_txt':
                from_jid = data['from']
                txt_text = data['txt_text']
                txt_delay = data['txt_delay']
                
                task_id = f'{from_jid}_txt'
                
                if task_id in self.active_txt_senders:
                    self.stop_flags[task_id] = True
                    await asyncio.sleep(0.2)
                
                self.stop_flags[task_id] = False
                
                async def run_txt():
                    while not self.stop_flags.get(task_id, False):
                        try:
                            await self.client.send_message(from_jid, txt_text)
                        except Exception as e:
                            print(f'[{self.bot_id}] TXT Error: {e}')
                        await asyncio.sleep(txt_delay / 1000)
                    
                    # Clean up
                    if task_id in self.active_txt_senders:
                        del self.active_txt_senders[task_id]
                
                task = asyncio.create_task(run_txt())
                self.active_txt_senders[task_id] = task
                
                if send_confirmation:
                    warning = ''
                    if txt_delay < MINIMUM_SAFE_DELAYS['messages']:
                        warning = f'\n\n⚠️ WARNING: {txt_delay}ms is VERY RISKY!\nRisk of WhatsApp ban is HIGH!'
                    
                    await self.send_message(from_jid, f'⚡ *THUNDER TEXT ATTACK* ⚡\n\n💬 {txt_text}\n⏱️ Delay: {txt_delay}ms{warning}\n🤖 Bot: {self.bot_id}')
            
            elif command_type == 'stop_txt':
                from_jid = data['from']
                task_id = f'{from_jid}_txt'
                
                if task_id in self.active_txt_senders:
                    self.stop_flags[task_id] = True
                    if send_confirmation:
                        await self.send_message(from_jid, f'✅ Text attack stopped - {self.bot_id}')
            
            # TTS ATTACK
            elif command_type == 'start_tts':
                from_jid = data['from']
                tts_text = data['tts_text']
                tts_delay = data['tts_delay']
                
                task_id = f'{from_jid}_tts'
                
                if task_id in self.active_tts_senders:
                    self.stop_flags[task_id] = True
                    await asyncio.sleep(0.2)
                
                self.stop_flags[task_id] = False
                
                async def run_tts():
                    while not self.stop_flags.get(task_id, False):
                        try:
                            audio_buffer = generate_tts(tts_text)
                            await self.client.send_voice(from_jid, audio_buffer)
                        except Exception as e:
                            print(f'[{self.bot_id}] TTS Error: {e}')
                        await asyncio.sleep(tts_delay / 1000)
                    
                    # Clean up
                    if task_id in self.active_tts_senders:
                        del self.active_tts_senders[task_id]
                
                task = asyncio.create_task(run_tts())
                self.active_tts_senders[task_id] = task
                
                if send_confirmation:
                    warning = ''
                    if tts_delay < MINIMUM_SAFE_DELAYS['voice']:
                        warning = f'\n\n⚠️ WARNING: {tts_delay}ms is VERY RISKY!\nRisk of WhatsApp ban is HIGH!'
                    
                    await self.send_message(from_jid, f'⚡ *THUNDER TTS ATTACK* ⚡\n\n🎤 {tts_text}\n⏱️ Delay: {tts_delay}ms{warning}\n🤖 Bot: {self.bot_id}')
            
            elif command_type == 'stop_tts':
                from_jid = data['from']
                task_id = f'{from_jid}_tts'
                
                if task_id in self.active_tts_senders:
                    self.stop_flags[task_id] = True
                    if send_confirmation:
                        await self.send_message(from_jid, f'✅ TTS attack stopped - {self.bot_id}')
            
            # PICTURE ATTACK
            elif command_type == 'start_pic':
                from_jid = data['from']
                pic_delay = data['pic_delay']
                image_buffer = data['image_buffer']
                
                task_id = f'{from_jid}_pic'
                
                if task_id in self.active_pic_senders:
                    self.stop_flags[task_id] = True
                    await asyncio.sleep(0.2)
                
                self.stop_flags[task_id] = False
                
                async def run_pic():
                    while not self.stop_flags.get(task_id, False):
                        try:
                            # Decode base64 image
                            image_data = base64.b64decode(image_buffer)
                            # Save to temp file
                            temp_path = f'temp_{task_id}.jpg'
                            with open(temp_path, 'wb') as f:
                                f.write(image_data)
                            await self.client.send_photo(from_jid, temp_path)
                            os.remove(temp_path)
                        except Exception as e:
                            print(f'[{self.bot_id}] PIC Error: {e}')
                        await asyncio.sleep(pic_delay / 1000)
                    
                    # Clean up
                    if task_id in self.active_pic_senders:
                        del self.active_pic_senders[task_id]
                
                task = asyncio.create_task(run_pic())
                self.active_pic_senders[task_id] = task
                
                if send_confirmation:
                    warning = ''
                    if pic_delay < MINIMUM_SAFE_DELAYS['messages']:
                        warning = f'\n\n⚠️ WARNING: {pic_delay}ms is VERY RISKY!\nRisk of WhatsApp ban is HIGH!'
                    
                    await self.send_message(from_jid, f'⚡ *THUNDER PIC ATTACK* ⚡\n\n📸 Picture spam started\n⏱️ Delay: {pic_delay}ms{warning}\n🤖 Bot: {self.bot_id}')
            
            elif command_type == 'stop_pic':
                from_jid = data['from']
                task_id = f'{from_jid}_pic'
                
                if task_id in self.active_pic_senders:
                    self.stop_flags[task_id] = True
                    if send_confirmation:
                        await self.send_message(from_jid, f'✅ Pic attack stopped - {self.bot_id}')
            
            # STOP ALL
            elif command_type == 'stop_all':
                from_jid = data['from']
                stopped = 0
                
                # Stop individual NC
                for task_id in list(self.active_name_changes.keys()):
                    if task_id.startswith(from_jid):
                        self.stop_flags[task_id] = True
                        stopped += 1
                
                # Stop triple attacks
                for task_id in list(self.active_triple_nc.keys()):
                    if task_id.startswith(from_jid):
                        self.active_triple_nc[task_id]['active'] = False
                        del self.active_triple_nc[task_id]
                        stopped += 1
                
                # Stop text+emoji attacks
                for task_id in list(self.active_text_emoji_attacks.keys()):
                    if task_id.startswith(from_jid):
                        self.active_text_emoji_attacks[task_id]['active'] = False
                        del self.active_text_emoji_attacks[task_id]
                        stopped += 1
                
                # Stop slides
                for task_id in list(self.active_slides.keys()):
                    if task_id.startswith(from_jid):
                        self.active_slides[task_id]['active'] = False
                        del self.active_slides[task_id]
                        stopped += 1
                
                # Stop text
                txt_task_id = f'{from_jid}_txt'
                if txt_task_id in self.active_txt_senders:
                    self.stop_flags[txt_task_id] = True
                    stopped += 1
                
                # Stop TTS
                tts_task_id = f'{from_jid}_tts'
                if tts_task_id in self.active_tts_senders:
                    self.stop_flags[tts_task_id] = True
                    stopped += 1
                
                # Stop pics
                pic_task_id = f'{from_jid}_pic'
                if pic_task_id in self.active_pic_senders:
                    self.stop_flags[pic_task_id] = True
                    stopped += 1
                
                if stopped > 0 and send_confirmation:
                    await self.send_message(from_jid, f'🛑 *THUNDER {self.bot_id}* 🛑\n\n✅ Stopped {stopped} attack(s)!')
                
        except Exception as e:
            print(f'[{self.bot_id}] executeCommand error: {e}')
    
    async def send_message(self, jid: str, text: str, parse_mode: str = None):
        """Send a message"""
        if not self.client or not self.connected:
            return
        try:
            await self.client.send_message(jid, text, parse_mode=parse_mode)
        except Exception as e:
            print(f'[{self.bot_id}] Send message error: {e}')

# ========== COMMAND BUS CLASS ==========

class CommandBus:
    """Distributes commands to all bots"""
    
    def __init__(self):
        self.bot_sessions: Dict[str, BotSession] = {}
    
    def register_bot(self, bot_id: str, session: BotSession):
        """Register a bot session"""
        self.bot_sessions[bot_id] = session
    
    def unregister_bot(self, bot_id: str):
        """Unregister a bot session"""
        if bot_id in self.bot_sessions:
            del self.bot_sessions[bot_id]
    
    async def broadcast_command(self, command_type: str, data: dict, origin_bot_id: str, send_confirmation: bool = True):
        """Broadcast command to all bots"""
        for bot_id, bot in self.bot_sessions.items():
            try:
                is_origin = bot_id == origin_bot_id
                await bot.execute_command(command_type, data, is_origin and send_confirmation)
            except Exception as e:
                print(f'[{bot_id}] Command execution error: {e}')
    
    def get_all_bots(self) -> List[BotSession]:
        """Get all bot sessions"""
        return list(self.bot_sessions.values())
    
    def get_connected_bots(self) -> List[BotSession]:
        """Get connected bots"""
        return [b for b in self.bot_sessions.values() if b.connected]
    
    def get_leader_bot(self) -> Optional[BotSession]:
        """Get the first connected bot"""
        connected = self.get_connected_bots()
        return connected[0] if connected else None

# ========== BOT MANAGER CLASS ==========

class BotManager:
    """Manages multiple bot sessions"""
    
    def __init__(self):
        self.bots: Dict[str, BotSession] = {}
        self.command_bus = CommandBus()
        self.bot_counter = 0
        self.loaded_data = self.load_bots()
    
    def load_bots(self) -> dict:
        """Load saved bots"""
        try:
            if os.path.exists(BOTS_FILE):
                with open(BOTS_FILE, 'r', encoding='utf-8') as f:
                    saved_bots = json.load(f)
                    self.bot_counter = saved_bots.get('counter', 0)
                    print(f'[MANAGER] Found {len(saved_bots.get("bots", []))} saved bot(s)')
                    return saved_bots
        except Exception as e:
            print(f'[MANAGER] No saved bots found, starting fresh: {e}')
        return {'counter': 0, 'bots': []}
    
    def save_bots(self):
        """Save bots to file"""
        try:
            os.makedirs('./data', exist_ok=True)
            data = {
                'counter': self.bot_counter,
                'bots': [
                    {'id': bot_id, 'phone_number': bot.phone_number, 'connected': bot.connected}
                    for bot_id, bot in self.bots.items()
                ]
            }
            with open(BOTS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f'[MANAGER] Error saving bots: {e}')
    
    async def restore_saved_bots(self):
        """Restore saved bot sessions"""
        if self.loaded_data.get('bots'):
            print(f'[MANAGER] Restoring {len(self.loaded_data["bots"])} bot session(s)...')
            
            for bot_data in self.loaded_data['bots']:
                phone_number = bot_data.get('phone_number')
                
                session = BotSession(bot_data['id'], phone_number, self, None)
                self.bots[bot_data['id']] = session
                self.command_bus.register_bot(bot_data['id'], session)
                
                print(f'[MANAGER] Reconnecting {bot_data["id"]}...')
                await session.start()
                await asyncio.sleep(2)
            
            self.save_bots()
        else:
            print('[MANAGER] No saved sessions. Use +add command to add bots.\n')
    
    async def add_bot(self, phone_number: str, requesting_jid: str = None) -> str:
        """Add a new bot"""
        self.bot_counter += 1
        bot_id = f'BOT{self.bot_counter}'
        
        session = BotSession(bot_id, phone_number, self, requesting_jid)
        self.bots[bot_id] = session
        self.command_bus.register_bot(bot_id, session)
        
        await session.start()
        self.save_bots()
        
        return f'🤖 *{bot_id} CREATED!* 🤖\n\n✅ Bot session created\n📱 Number: {phone_number}\n\n⏳ Waiting for connection...'
    
    def remove_bot(self, bot_id: str):
        """Remove a bot"""
        if bot_id in self.bots:
            self.command_bus.unregister_bot(bot_id)
            del self.bots[bot_id]
            self.save_bots()
            print(f'[MANAGER] Removed {bot_id}')

# ========== MAIN FUNCTION ==========

async def main():
    """Main entry point"""
    # Print startup message
    print('╔══════════════════════════════════════════════╗')
    print('║   ⚡ THUNDER MULTI-BOT SYSTEM v3.0 ⚡         ║')
    print('║     ⚡ TRIPLE NC + TEXT+EMOJI SYSTEM ⚡       ║')
    print('╚══════════════════════════════════════════════╝\n')
    print('📱 COMPLETE PHONE KEYBOARD EMOJIS INCLUDED!')
    print('🎨 8 FONT STYLES FOR TEXT+EMOJI ATTACKS')
    print('🎭 35 TRIPLE ATTACKS AVAILABLE')
    print('⚡ 100 INDIVIDUAL NC TYPES')
    print('\n🎨 NEW TEXT+EMOJI FEATURE:')
    print('• Combine any text with any emoji set')
    print('• Apply 8 different font styles')
    print('• Command: +tne [font] [nc#] [text] [delay]')
    print('• Example: +tne double nc1 RAID 1000')
    print('• Fonts: double, mono, script, boldscript')
    print('          gothic, boldgothic, square, circled')
    print('\n⚠️  WARNING: Default delays are set to 200ms')
    print('⚠️  This is VERY RISKY and may cause WhatsApp bans!')
    print('⚠️  Use +delaytriple[1-35] [ms] to set safer delays (500ms+)')
    print('⚠️  Use +delaync[1-100] [ms] for individual delays (1000ms+)\n')
    
    # Create bot manager and restore saved bots
    bot_manager = BotManager()
    await bot_manager.restore_saved_bots()
    
    print('\n✅ Thunder Bot System Ready!')
    print('📌 Send +admin in DM to become admin')
    print('📌 Send +fonts to see all font styles')
    print('📌 Send +tne double nc1 RAID 1000 to test new feature')
    print('📌 Send +triples to see all 35 triple attacks')
    print('📌 Send +menu to see all commands')
    print('📱 Phone keyboard emojis: nc81-nc100')
    print('🎨 Text+Emoji: Combine any text with any emoji set!')
    print('⚡ Triple attacks: Runs 3 different NCs simultaneously!')
    print('⚠️  WARNING: Use at your own risk!\n')
    
    # Keep the program running
    try:
        while True:
            await asyncio.sleep(3600)  # Keep alive
    except KeyboardInterrupt:
        print('\n[MAIN] Shutting down...')
        for bot in bot_manager.bots.values():
            await bot.stop()
        print('[MAIN] Goodbye!')

if __name__ == '__main__':
    asyncio.run(main())
