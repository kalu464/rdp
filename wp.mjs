import makeWASocket, { useMultiFileAuthState, DisconnectReason, delay, fetchLatestBaileysVersion, downloadContentFromMessage } from '@whiskeysockets/baileys';
import { Boom } from '@hapi/boom';
import pino from 'pino';
import fs from 'fs';
import os from 'os';
import readline from 'readline';
import PQueue from 'p-queue';
import { execSync } from 'child_process';

// ==================== ULTRA ANTI-CRASH SYSTEM ====================
process.on('uncaughtException', (err) => console.log(`[ANTI-CRASH] Ignored: ${err.message}`));
process.on('unhandledRejection', (reason) => {});
process.on('warning', (warning) => console.warn('[WARNING]', warning.message));
process.setMaxListeners(0);

// ==================== CYBER EXOTIC ENGINE ====================
const THREADS_PER_BOT = 50;          // bot1.js style multi-thread fan-out
const HSEE = {
    attackQueue: new PQueue({ concurrency: 300, interval: 50, intervalCap: 300 }),
    normalQueue: new PQueue({ concurrency: 30, interval: 50, intervalCap: 30 }),
    async runAttack(task) { try { return await this.attackQueue.add(task); } catch (e) { return null; } },
    async runNormal(task) { try { return await this.normalQueue.add(task); } catch (e) { return null; } },
    clearAll() { 
        this.attackQueue.clear(); 
        this.normalQueue.clear(); 
    }
};

// ==================== SMART STYLISH FONT ENGINE ====================
const fontMap = {
    'A': '𝐀', 'B': '𝐁', 'C': '𝐂', 'D': '𝐃', 'E': '𝐄', 'F': '𝐅', 'G': '𝐆', 'H': '𝐇', 'I': '𝐈', 'J': '𝐉', 'K': '𝐊', 'L': '𝐋', 'M': '𝐌', 'N': '𝐍', 'O': '𝐎', 'P': '𝐏', 'Q': '𝐐', 'R': '𝐑', 'S': '𝐒', 'T': '𝐓', 'U': '𝐔', 'V': '𝐕', 'W': '𝐖', 'X': '𝐗', 'Y': '𝐘', 'Z': '𝐙',
    'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ғ', 'g': 'ɢ', 'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 's', 't': 'ᴛ', 'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ'
};
function styleText(text) {
    if (!text) return text;
    return text.replace(/[a-zA-Z]/g, c => fontMap[c] || c);
}

// ==================== GLOBAL CONFIG & DATABASE ====================
const ROLES_FILE = './data/roles.json';
const BOTS_FILE = './data/bots.json';
const CONFIG_FILE = './data/config.json';
const defaultRoles = { admins: [], subAdmins: [] };
const defaultConfig = { prefix: '!' };

function safeReadJSON(path, def) { try { if (fs.existsSync(path)) return JSON.parse(fs.readFileSync(path, 'utf8')); } catch (e) {} return def; }
function safeWriteJSON(path, data) { try { if (!fs.existsSync('./data')) fs.mkdirSync('./data', { recursive: true }); fs.writeFileSync(path, JSON.stringify(data, null, 2)); } catch (e) {} }

let roles = safeReadJSON(ROLES_FILE, defaultRoles);
let globalConfig = safeReadJSON(CONFIG_FILE, defaultConfig);
let GLOBAL_PREFIX = globalConfig.prefix;

function updatePrefix(newPrefix) { GLOBAL_PREFIX = newPrefix; globalConfig.prefix = newPrefix; safeWriteJSON(CONFIG_FILE, globalConfig); }
function normalizeJid(jid) { if (!jid) return ''; return jid.includes(':') ? jid.split(':')[0] + '@s.whatsapp.net' : (jid.includes('@') ? jid : jid + '@s.whatsapp.net'); }
const isAdmin = (jid) => roles.admins.some(a => normalizeJid(a) === normalizeJid(jid));
const isSubAdmin = (jid) => roles.subAdmins.some(s => normalizeJid(s) === normalizeJid(jid));
const hasPerm = (jid) => isAdmin(jid) || isSubAdmin(jid);

// ==================== FULL EMOJI ARRAYS ====================
const emojiArrays = {
    n1:['🔥','💥','⚡','🌪️','🌈','☄️','💫','🌊','❄️','🌸','💀','☠️','👺','🔱','⚜️','🌟','✨','💢','💤','💨','💦','🌀','🌙'], n2:['🌑','🌒','🌓','🌔','🌕','🌖','🌗','🌘','☁️','🌨️','🌧️','🌩️','⛈️','🌦️','🌥️','⛅','🌤️','☀️'], n3:['🛑','🚧','🚨','⛽','🛢️','⚓','📫','📪','📬','📭','📧','💌','✉️','📨','📩','📥','📤'], n4:['📒','📔','📕','📓','📗','📘','📙','🖌️','🖍️','🖊️','🖋️','✒️','✏️'], n5:['🕛','🕧','🕐','🕜','🕑','🕝','🕒','🕞','🕓','🕟','🕔','🕠','🕕','🕡','🕖','🕢','🕗','🕣','🕘','🕤','🕙','🕥','🕚','🕦'], n6:['❤️','🧡','💛','💚','💙','💜','🤎','🖤','🤍','🩷','🩵','🩶','♥️'], n7:['💟','⚛️','🛐','🕉️','☸️','☮️','☯️','☪️','🪯','✝️','☦️','✡️','🔯','🕎','🆔','♈','♉','♊','♋','♌','♍','♎','♏','♐','♑','♒','♓','⛎'], n8:['💐','🌹','🥀','🌺','🌷','🪷','🌸','💮','🏵️','🪻','🌻','🌼','🍂','🍁','🍄','🌾','🌿','🌱','🍃','☘️','🍀','🌵','🌴','🪾','🌳','🌲'], n9:['🦅','🕊️','🦢','🪿','🦆','🐦‍🔥','🦃','⚽','⚾','🥎','🏀','🏐','🏈','🏉'], n10:['🦈','🐬','🐋','🐳','🐟','🐠','🐡','🦐','🦞','🦀','🦑','🐙','🪼','🪼','🦪','🪸','🫧'], n11:['🚀','✈️','🛫','🛬','🛩️','🕋','🏙️','🌆','🌇','🌃','🌉','🌁','🗾','🗺️'], n12:['🔮','🧿','🪬','📿','🏺','⚱️','⚰️','🪦','🚬','💣','🪤','📜','⚔️','🗡️','🛡️','🗝️','🔑','🔐','🔏','🔒','🔓'], n13:['🪓','🪝','🧲','🗜️','🔩','🪛','🪚','🔧','🔨','🛠️','⚒️','⛏️','🪏','⚙️','⛓️‍💥','🔗','⛓️','📎','🖇️','✂️','📏','📐'], n14:['◼️','◾','▪️','🔳','🔲','◻️','◽','▫️','🔴','🟠','🟡','🟢','🔵','🟣','🟤','⚫','⚪']
};
const globalEmojiList = Object.values(emojiArrays).flat();

// ==================== LOCK & BURN PERSISTENCE ====================
const LOCKED_FILE = './data/lockedUsers.json';
const BURNED_FILE = './data/burnedUsers.json';
const lockedUsers = new Map();
const burnedUsers = new Map();

function loadMapFile(path, target) {
    const data = safeReadJSON(path, {});
    for (const [g, arr] of Object.entries(data)) target.set(g, new Set(arr));
}
function saveMapFile(path, source) {
    const obj = {};
    for (const [g, s] of source.entries()) if (s.size > 0) obj[g] = [...s];
    safeWriteJSON(path, obj);
}
function lockUser(g, u) { if (!lockedUsers.has(g)) lockedUsers.set(g, new Set()); lockedUsers.get(g).add(u); saveMapFile(LOCKED_FILE, lockedUsers); }
function unlockUser(g, u) { lockedUsers.get(g)?.delete(u); saveMapFile(LOCKED_FILE, lockedUsers); }
function isUserLocked(g, u) { return lockedUsers.get(g)?.has(u) || false; }
function burnUserAdd(g, u) { if (!burnedUsers.has(g)) burnedUsers.set(g, new Set()); burnedUsers.get(g).add(u); saveMapFile(BURNED_FILE, burnedUsers); }
function unburnUser(g, u) { burnedUsers.get(g)?.delete(u); saveMapFile(BURNED_FILE, burnedUsers); }
function isUserBurned(g, u) { return burnedUsers.get(g)?.has(u) || false; }

loadMapFile(LOCKED_FILE, lockedUsers);
loadMapFile(BURNED_FILE, burnedUsers);

// ==================== TARGET MESSAGES ====================
const targetMessages = [
    "Chal Tmkb Me Ghuss Ke Nanga Nachh Kruuu 🦈🦈", "🔥ꪻꫀ᥅ﺃ ꪑꪖꪖ ꪗꪖꫝꪖ ᥴꪊᦔꪻﺃ ꫝꫀꫀ 💢", "🧬Tmkc random 🤢🤢🖕🏻🖕🏻🖕🏻🧬", 
    "𝘼𝙒𝘼𝙕 𝙉𝙄𝘾𝙃𝙀 𝙍𝙔𝙉𝘿𝙔 𝙆𝙀 𝘽𝘾𝘾𝐇𝐄 🗞️🗞️", "", "Itna codunga ki 10 din tak tryma hag bhi nhi payegi rndice 🤢🤢🔥🔥🔥", 
    "(👑) 𝐁𝐎𝐋 𝐃𝐄𝐕 𝐁𝐇𝐀𝐆𝐖𝐀𝐍 𝐊𝐈 𝐉𝐀𝐈 𝐇𝐎 (👑)", "🔥Likhna sikh low lvl rndy ᛕꪊꪻꪻﺃ ᛕꫀꫀ ᜣﺃꪶꪶꫀ ꪻꪑᛕᥴ 🤢👞👞🔥"
];

// 🛡️ MEMORY CACHE
const store = {
    messages: {},
    bind(ev) {
        ev.on('messages.upsert', ({ messages }) => {
            for (const msg of messages) {
                const jid = msg.key.remoteJid;
                if (!this.messages[jid]) this.messages[jid] = {};
                this.messages[jid][msg.key.id] = msg;
                const keys = Object.keys(this.messages[jid]);
                if (keys.length > 50) delete this.messages[jid][keys[0]]; 
            }
        });
    }
};

// ==================== BOT SESSION CORE ====================
class BotSession {
    constructor(botId, phone, manager, useQR = false) {
        this.displayId = botId === 'Bot_1' ? '𝐒𝐔𝐏𝐄𝐑 𝐁𝐎𝐓' : botId.replace('Bot_', '𝐁𝐎𝐓 ');
        this.internalId = botId;
        this.phoneNumber = phone;
        this.manager = manager;
        this.useQR = useQR;
        this.authPath = `./auth/${botId}`;
        this.sock = null;
        this.connected = false;
        this.isSuppressed = false; 
        
        // Active Tasks
        this.activeName = new Map();
        this.activeSpam = new Map();
        this.activeSpamFast = new Map();
        this.activePfp = new Map(); 
        this.activeTarget = new Map();
        this.activeSlide = new Map();
        this.activeTagall = new Map();
        this.activeAutoReply = new Map();
        this.activeTargetReply = new Map();
        this.activePcspm = new Map();
        this.activeStspm = new Map();
        this.activeReplyAll = new Map();
        this.activeDesc = new Map();
        this.activeTxt = new Map(); 
        this.activeSpamX = new Map();        // continuous spamx loops per chat
        this.pendingSpamX = new Map();       // awaiting text input from requester

        this.autoReactEmoji = null;
    }

    async connect() {
        if (!fs.existsSync(this.authPath)) fs.mkdirSync(this.authPath, { recursive: true });
        const { state, saveCreds } = await useMultiFileAuthState(this.authPath);
        const { version } = await fetchLatestBaileysVersion();

        this.sock = makeWASocket({
            version,
            auth: state,
            logger: pino({ level: 'silent' }),
            printQRInTerminal: this.useQR,
            mobile: false,
            browser: ["Ubuntu", "Chrome", "20.0.04"],
            syncFullHistory: false,
            getMessage: async (key) => {
                if (store) {
                    const msg = store.messages[key.remoteJid]?.[key.id];
                    return msg?.message || undefined;
                }
                return { conversation: `*${styleText("(⚡) [ CYBER EXOTIC ENGINE ] (⚡)")}*` };
            }
        });

        store.bind?.(this.sock.ev);
        this.sock.ev.on('creds.update', saveCreds);

        this.sock.ev.on('call', async (calls) => {
            for (const call of calls) {
                if (call.status === 'offer') {
                    try { await this.sock.rejectCall(call.id, call.from); } catch (err) {}
                }
            }
        });

        this.sock.ev.on('connection.update', async (update) => {
            const { connection, lastDisconnect, qr } = update;
            if (qr && this.useQR) console.log(`\n📱 [${this.displayId}] SCAN QR CODE NOW\n`);

            if (connection === 'close') {
                this.connected = false;
                const code = (lastDisconnect?.error instanceof Boom) ? lastDisconnect.error.output.statusCode : 500;
                if (code !== DisconnectReason.loggedOut && code !== 401) {
                    setTimeout(() => this.connect(), 5000);
                } else {
                    if (fs.existsSync(this.authPath)) fs.rmSync(this.authPath, { recursive: true, force: true });
                }
            } else if (connection === 'open') {
                this.connected = true;
                console.log(`✅ [${this.displayId}] ONLINE & READY!`);
            }
        });

        this.sock.ev.on('messages.upsert', m => this.handleMsg(m));
    }

    // ==================== SPAMX MULTI-THREAD LOOP ====================
    startSpamX(from, targetJid, paragraphs) {
        const taskId = from;
        // Restart-safe: stop previous loop on this chat first
        if (this.activeSpamX.has(taskId)) {
            const prev = this.activeSpamX.get(taskId);
            prev.active = false;
        }
        const task = { active: true, idx: 0, paragraphs, targetJid };
        this.activeSpamX.set(taskId, task);

        const runner = async (tIdx) => {
            await delay(tIdx * 8);
            while (task.active && this.connected) {
                const para = task.paragraphs[task.idx % task.paragraphs.length];
                task.idx++;
                try {
                    await this.sock.sendMessage(from, { text: para, mentions: [targetJid] });
                } catch (_) {
                    await delay(300);
                }
            }
        };
        for (let t = 0; t < THREADS_PER_BOT; t++) runner(t);
    }
    stopSpamX(from) {
        const task = this.activeSpamX.get(from);
        if (task) { task.active = false; this.activeSpamX.delete(from); }
    }

    async send(jid, text, mentions = [], quoted = null, imageUrl = null) {
        if (!this.connected) return;
        const styledText = styleText(text); 
        const finalStyledText = `*${styledText}*`; 
        let msgPayload = { text: finalStyledText, mentions: mentions.length ? mentions : undefined };
        if (imageUrl && fs.existsSync(imageUrl)) {
            msgPayload = { image: fs.readFileSync(imageUrl), caption: finalStyledText, mentions: mentions.length ? mentions : undefined };
        }
        await this.sock.sendMessage(jid, msgPayload, quoted ? { quoted } : {}).catch(()=>{});
    }

    async ping(from) {
        const start = Date.now();
        await this.send(from, `(⚡) [ CYBER EXOTIC Speed Check... ] (⚡)`);
        await this.send(from, `(🚀) [ Latency: ${Date.now() - start}ms ] (🚀)`);
    }

    async handleMsg({ messages, type }) {
        if (type !== 'notify') return;
        const msg = messages[0];
        if (!msg.message || msg.key.fromMe) return;

        const from = msg.key.remoteJid;
        const isGroup = from.endsWith('@g.us');
        const sender = isGroup ? msg.key.participant : from;

        // ==================== LOCK SYSTEM (auto-delete locked users' msgs) ====================
        if (isGroup && sender && isUserLocked(from, normalizeJid(sender))) {
            this.sock.sendMessage(from, { delete: msg.key }).catch(() => {});
            return;
        }

        // ==================== BURN SYSTEM (auto-report 3x per msg) ====================
        if (isGroup && sender && isUserBurned(from, normalizeJid(sender))) {
            const burnTarget = normalizeJid(sender);
            (async () => {
                for (let i = 0; i < 3; i++) {
                    try {
                        await this.sock.updateBlockStatus(burnTarget, 'block');
                        await delay(150);
                        await this.sock.updateBlockStatus(burnTarget, 'unblock');
                        await delay(150);
                    } catch (e) {}
                }
                if (this.internalId === this.manager.getMainBotId()) {
                    await this.send(from, `📩 @${burnTarget.split('@')[0]} ko 3x Report bhej diya!`, [burnTarget]);
                }
            })();
        }
        const text = (msg.message.conversation || msg.message.extendedTextMessage?.text || "").trim();
        const isCmd = text.startsWith(GLOBAL_PREFIX);
        const command = isCmd ? text.slice(GLOBAL_PREFIX.length).trim().split(' ')[0].toLowerCase() : "";
        const args = text.split(/ +/).slice(1);
        const quotedMsg = msg.message.extendedTextMessage?.contextInfo;
        const mentioned = quotedMsg?.mentionedJid || [];
        const isMain = this.internalId === this.manager.getMainBotId();
        const replyJid = quotedMsg?.participant ? normalizeJid(quotedMsg.participant) : null;

        // ==================== SPAMX PENDING-TEXT INTERCEPT ====================
        // Sirf main bot prompt/start kare (avoid duplicate prompts), but spam loop sab bots run karenge via manager
        if (isMain && !isCmd && text.length > 0) {
            const pendKey = `${from}_${normalizeJid(sender)}`;
            const pend = this.pendingSpamX.get(pendKey);
            if (pend) {
                this.pendingSpamX.delete(pendKey);
                const userText = text.slice(0, 500); // safety cap
                // Build 10 paragraphs, each = userText repeated 10 times with single emoji
                const pool = [...globalEmojiList];
                const pickedEmojis = [];
                for (let i = 0; i < 10; i++) {
                    const e = pool.splice(Math.floor(Math.random() * pool.length), 1)[0] || '🔥';
                    pickedEmojis.push(e);
                }
                const paragraphs = pickedEmojis.map(em => {
                    const line = `${em} ${userText} ${em}`;
                    return Array(10).fill(line).join('\n');
                });
                // Broadcast to ALL bots in manager so har bot apna loop chalaye
                for (const bot of this.manager.bots.values()) {
                    if (!bot.connected) continue;
                    bot.startSpamX(from, pend.targetJid, paragraphs);
                }
                await this.send(from, `(💀) [ NOBI-NVN SPAMX ACTIVE ]\n🎯 Target: @${pend.targetJid.split('@')[0]}\n🧨 ${paragraphs.length} paragraphs × ${THREADS_PER_BOT} threads/bot\n❌ Stop: ${GLOBAL_PREFIX}stopspamx`, [pend.targetJid]);
                return;
            }
        }


        // Auto React Engine
        if (this.autoReactEmoji && !isCmd && !this.isSuppressed) {
            const safeReactDelay = Math.floor(Math.random() * (4000 - 1500 + 1)) + 1500;
            setTimeout(() => { this.sock.sendMessage(from, { react: { text: this.autoReactEmoji, key: msg.key } }).catch(() => {}); }, safeReactDelay);
        }

        // ==================== DYNAMIC ADMIN LOGIC (Max 2 Slots) ====================
        if (isCmd && command === 'admin') {
            const normSender = normalizeJid(sender);
            
            // 1. Agar sender pehle se admin hai
            if (isAdmin(normSender)) {
                // Wo kisi aur ko tag/reply karke admin bana raha hai
                if (replyJid) {
                    if (roles.admins.length >= 2) {
                        await this.send(from, `(❌) [ Admin slots full hain (Max 2 allowed)! ]`);
                        return;
                    }
                    if (!roles.admins.includes(replyJid)) {
                        roles.admins.push(replyJid);
                        safeWriteJSON(ROLES_FILE, roles);
                        await this.send(from, `👑 @${replyJid.split('@')[0]} is now an Admin!\n📊 Slots used: ${roles.admins.length}/2`, [replyJid]);
                    }
                } else {
                    await this.send(from, `(✅) [ Bhai tu pehle se hi Admin hai! ]`);
                }
                return; 
            }

            // 2. Agar sender admin NAHI hai aur khud claim karna chahta hai
            if (roles.admins.length >= 2) {
                await this.send(from, `(❌) [ Admin slots full hain. (Max 2 allowed) ]`);
                return;
            }
            
            // Slot khali hai, naye bande ko admin de do
            roles.admins.push(normSender);
            safeWriteJSON(ROLES_FILE, roles);
            await this.send(from, `👑 ADMIN ACCESS CLAIMED BY @${normSender.split('@')[0]}\n📊 Slots used: ${roles.admins.length}/2`, [normSender]);
            return;
        }

        // Task Execution Blocks
        if (!this.isSuppressed) {
            if (isGroup && this.activeTargetReply.has(`${from}_${sender}`)) {
                const slideTask = this.activeTargetReply.get(`${from}_${sender}`);
                if (slideTask.active) {
                    HSEE.runAttack(async () => {
                        if (!this.activeTargetReply.has(`${from}_${sender}`)) return;
                        await this.send(from, slideTask.text, [], msg);
                    });
                }
            }

            if (isGroup && this.activeAutoReply.has(`${from}_autoreply`)) {
                const task = this.activeAutoReply.get(`${from}_autoreply`);
                if (task.active && (task.targets.length === 0 || task.targets.includes(normalizeJid(sender)))) {
                    if (isMain) {
                        HSEE.runAttack(async () => {
                            if (!this.activeAutoReply.has(`${from}_autoreply`)) return;
                            await this.send(from, "(⚡) [ CYBER EXOTIC ACTIVE ] (⚡)", [sender], msg);
                        });
                    }
                }
            }

            if (this.activeTarget.has(`${from}_target`)) {
                const task = this.activeTarget.get(`${from}_target`);
                if (task.targets.includes(normalizeJid(sender))) {
                    HSEE.runAttack(async () => {
                        if (!this.activeTarget.has(`${from}_target`)) return;
                        const spamMsg = targetMessages[Math.floor(Math.random() * targetMessages.length)];
                        await this.send(from, spamMsg, [sender], msg); 
                    });
                }
            }
            
            if (isGroup && this.activeReplyAll.has(from)) {
                const task = this.activeReplyAll.get(from);
                HSEE.runAttack(async () => {
                    if (!this.activeReplyAll.has(from)) return;
                    await this.send(from, task.text, [], msg);
                });
            }
        }

        // Global Command Router
        if (isMain && !isGroup && hasPerm(sender)) {
            if (text.startsWith('global ')) {
                const subCmdText = text.replace('global ', '').trim();
                const subCmd = subCmdText.split(' ')[0].toLowerCase();
                const subArgs = subCmdText.split(' ').slice(1);
                this.manager.bots.forEach(bot => bot.executeInternal(from, subCmd, sender, msg, subArgs, quotedMsg, bot.internalId === this.manager.getMainBotId()));
                return;
            }
        }

        // Standard Command Execution (Only for Admins/SubAdmins)
        if (isCmd && hasPerm(sender)) {
            if (this.isSuppressed && command !== 'uplift') return; 
            if (!isMain) this.sock.sendMessage(from, { react: { text: '⚡', key: msg.key } }).catch(()=>{});
            this.executeInternal(from, command, sender, msg, args, quotedMsg, isMain);
        }
    }

    async executeInternal(from, command, sender, msg, args, quotedMsg, isMain) {
        const replyJid = quotedMsg?.participant ? normalizeJid(quotedMsg.participant) : null;
        const mentioned = quotedMsg?.mentionedJid || [];
        const isGroup = from.endsWith('@g.us');
        const allowGlobal = !isGroup && isMain;

        switch (command) {
            case 'menu':
                if (!isMain) return;
                const P = GLOBAL_PREFIX;
                const menuTxt = `
╔══════════════════════════════╗
   ❄️  𝐍 𝐎 𝐁 𝐈   -   𝐍 𝐕 𝐍  ❄️
        『 𝐂𝐘𝐁𝐄𝐑 𝐌𝐀𝐓𝐑𝐈𝐗 』
╚══════════════════════════════╝

┏━━━━━━━━━━━━━━━━━━━━━━━━┓
   ⚙️  𝐒𝐘𝐒𝐓𝐄𝐌  𝐂𝐎𝐑𝐄
┗━━━━━━━━━━━━━━━━━━━━━━━━┛
  ◈ ${P}status   ➜  Bot health
  ◈ ${P}sys      ➜  CPU / RAM / Storage
  ◈ ${P}ping     ➜  Latency
  ◈ ${P}pre      ➜  Change prefix
  ◈ ${P}addbot   ➜  Naya node add
  ◈ ${P}wipe     ➜  Cache purge
  ◈ ${P}admin    ➜  Claim admin (max 2)
  ◈ ${P}sub      ➜  Sub-admin set

┏━━━━━━━━━━━━━━━━━━━━━━━━┓
   🩸  𝐒 𝐏 𝐀 𝐌   𝐀 𝐑 𝐓 𝐒
┗━━━━━━━━━━━━━━━━━━━━━━━━┛
  ◈ ${P}name [text]   ➜  GC name attack
  ◈ ${P}spam [text]   ➜  Multi-thread spam
  ◈ ${P}spamfast [d]  ➜  Rapid fire (no delay default)
  ◈ ${P}spamx @user   ➜  Custom spam (puchhega text)
  ◈ ${P}dtx [text]    ➜  Delay text spam
  ◈ ${P}pcspm         ➜  Image spam (reply)
  ◈ ${P}stspm         ➜  Sticker spam (reply)
  ◈ ${P}desc          ➜  Group desc spam

┏━━━━━━━━━━━━━━━━━━━━━━━━┓
   🎯  𝐓 𝐀 𝐑 𝐆 𝐄 𝐓   𝐇 𝐄 𝐗
┗━━━━━━━━━━━━━━━━━━━━━━━━┛
  ◈ ${P}target @user  ➜  Lock enemy
  ◈ ${P}slide [text]  ➜  Reply hunt
  ◈ ${P}s [text] [d]  ➜  Slide quote
  ◈ ${P}autoreply     ➜  Auto-reply mode
  ◈ ${P}replyall [t]  ➜  Reply har msg
  ◈ ${P}auto [emoji]  ➜  Auto-react
  ◈ ${P}gcpfp         ➜  GC PFP flash

┏━━━━━━━━━━━━━━━━━━━━━━━━┓
   🔒  𝐋 𝐎 𝐂 𝐊   𝐒 𝐘 𝐒 𝐓 𝐄 𝐌
┗━━━━━━━━━━━━━━━━━━━━━━━━┛
  ◈ ${P}lock @user    ➜  Auto-delete msgs
  ◈ ${P}lockall       ➜  Lock pura group
  ◈ ${P}unlock @user  ➜  Single unlock
  ◈ ${P}unlockall     ➜  Saare unlock

┏━━━━━━━━━━━━━━━━━━━━━━━━┓
   🔥  𝐁 𝐔 𝐑 𝐍   𝐌 𝐎 𝐃 𝐄
┗━━━━━━━━━━━━━━━━━━━━━━━━┛
  ◈ ${P}burn @user    ➜  3x report toggle
  ◈ ${P}unburn        ➜  Saare burn clear

┏━━━━━━━━━━━━━━━━━━━━━━━━┓
   👥  𝐆 𝐂   𝐂 𝐎 𝐍 𝐓 𝐑 𝐎 𝐋
┗━━━━━━━━━━━━━━━━━━━━━━━━┛
  ◈ ${P}tagall        ➜  Sabko mention
  ◈ ${P}kickall       ➜  Sabko kick
  ◈ ${P}leave         ➜  Group chodo
  ◈ ${P}dele / ${P}pin   ➜  Msg delete
  ◈ ${P}deleall       ➜  Bot msgs clear

┏━━━━━━━━━━━━━━━━━━━━━━━━┓
   🛑  𝐊 𝐈 𝐋 𝐋   𝐒 𝐖 𝐈 𝐓 𝐂 𝐇
┗━━━━━━━━━━━━━━━━━━━━━━━━┛
  ◈ ${P}stopall       ➜  Sab band (GC)
  ◈ ${P}stopname / ${P}stopspam
  ◈ ${P}stopspamfast / ${P}stopspamx
  ◈ ${P}stopdtx
  ◈ ${P}stoptarget / ${P}stopdesc
  ◈ ${P}stopreplyall / ${P}stoppfp
  ◈ ${P}stoppc / ${P}stopst
  ◈ ${P}globalstop    ➜  Sab nodes off

╭━━━━━━━━━━━━━━━━━━━━━━━━╮
   ❄️  𝐏𝐨𝐰𝐞𝐫𝐞𝐝 𝐁𝐲  𝐍𝐎𝐁𝐈-𝐍𝐕𝐍  ❄️
╰━━━━━━━━━━━━━━━━━━━━━━━━╯`;
                await this.send(from, menuTxt); 
                break;

            case 'addbot':
                if (!isMain) return;
                const phone = args[0]?.replace(/\D/g, '');
                if (!phone) return await this.send(from, `(❌) Usage: ${GLOBAL_PREFIX}addbot 91XXXXXXXXXX`);

                this.manager.counter++; 
                const newId = `Bot_${this.manager.counter}`;
                await this.send(from, `(⏳) [ Initializing ${newId.replace('_', ' ')}... ]`);

                const newSession = new BotSession(newId, phone, this.manager, false);
                this.manager.bots.set(newId, newSession);
                await newSession.connect();

                setTimeout(async () => {
                    try {
                        const code = await newSession.sock.requestPairingCode(phone);
                        await this.send(from, `
╔════════════════════════╗
    🛰️  𝐍𝐎𝐃𝐄  𝐀𝐂𝐓𝐈𝐕𝐀𝐓𝐄𝐃
╚════════════════════════╝
┃ 🆔 𝐍𝐚𝐦𝐞: ${newId.replace('_', ' ')}
┃ 📱 𝐍𝐮𝐦: ${phone}
┃ 🔑 𝐂𝐨𝐝𝐞: *${code}*
╚════════════════════════╝`);
                        this.manager.save();
                    } catch(e) { await this.send(from, `(❌) Error: ${e.message}`); }
                }, 5000);
                break;

            case 'status':
                if (!isMain) return;
                const ramUsed = (process.memoryUsage().heapUsed / 1024 / 1024).toFixed(2);
                const upseconds = process.uptime();
                const hours = Math.floor(upseconds / 3600);
                const minutes = Math.floor((upseconds % 3600) / 60);
                const mainId = this.manager.getMainBotId();

                const botList = [...this.manager.bots.values()].map(b => {
                    const isCurrentMain = b.internalId === mainId;
                    const icon = b.connected ? '🟢' : '🔴';
                    const role = isCurrentMain ? '『 👑 𝐌𝐀𝐈𝐍 』' : '『 🛰️ 𝐍𝐎𝐃𝐄 』';
                    const supStatus = b.isSuppressed ? '[🔇 SUPPRESSED]' : '';
                    let action = "Idle 💤";
                    if (b.activeSpamFast.size > 0 || b.activeName.size > 0 || b.activeSpam.size > 0 || b.activeSpamX.size > 0 || b.activeTarget.size > 0 || b.activePfp.size > 0 || b.activeDesc.size > 0) action = "Attacking 🩸";
                    return `┃ ${icon} *${b.displayId}* ➔ ${action} ${supStatus}\n┃    └─ ${role}`;
                }).join('\n');

                const statusBody = `
┏━━━━━━━━━━━━━━━━━━━━━━━━┓
      📊  𝐌𝐀𝐓𝐑𝐈𝐗  𝐃𝐀𝐒𝐇𝐁𝐎𝐀𝐑𝐃  
┗━━━━━━━━━━━━━━━━━━━━━━━━┛
┃ 🛰️  𝐍𝐎𝐃𝐄𝐒  𝐂𝐎𝐍𝐓𝐑𝐎𝐋:
${botList}
┣━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 🖥️  𝐒𝐘𝐒𝐓𝐄𝐌  𝐇𝐄𝐀𝐋𝐓𝐇:
┃ 🔹 RAM Load: ${ramUsed} MB
┃ 🔹 Runtime: ${hours}h ${minutes}m
┃ 🔹 Engine: Cyber Exotic V3.6
┗━━━━━━━━━━━━━━━━━━━━━━━━┛`;
                await this.send(from, statusBody);
                break;

            case 'ping': if (isMain) await this.ping(from); break;

            case 'sys':
            case 'specs':
            case 'system': {
                if (!isMain) return;
                const fmt = (b) => {
                    if (b < 1024) return `${b} B`;
                    const u = ['KB','MB','GB','TB'];
                    let i = -1; do { b /= 1024; i++; } while (b >= 1024 && i < u.length - 1);
                    return `${b.toFixed(2)} ${u[i]}`;
                };
                const cpus = os.cpus() || [];
                const cpuModel = cpus[0]?.model?.replace(/\s+/g, ' ').trim() || 'Unknown';
                const cpuSpeed = cpus[0]?.speed ? `${(cpus[0].speed / 1000).toFixed(2)} GHz` : 'N/A';
                const cpuCores = cpus.length;
                const totalRam = os.totalmem();
                const freeRam = os.freemem();
                const usedRam = totalRam - freeRam;
                const ramPct = ((usedRam / totalRam) * 100).toFixed(1);
                const load = os.loadavg().map(n => n.toFixed(2)).join(' / ');
                const procRss = process.memoryUsage().rss;
                const procHeap = process.memoryUsage().heapUsed;
                const upSec = os.uptime();
                const upH = Math.floor(upSec / 3600);
                const upM = Math.floor((upSec % 3600) / 60);
                const procUp = process.uptime();
                const pH = Math.floor(procUp / 3600);
                const pM = Math.floor((procUp % 3600) / 60);

                let diskInfo = 'N/A';
                try {
                    const out = execSync("df -h --output=size,used,avail,pcent / | tail -1", { timeout: 3000 }).toString().trim().split(/\s+/);
                    if (out.length >= 4) diskInfo = `${out[1]} / ${out[0]} used (${out[3]})`;
                } catch (_) {
                    try {
                        const stat = fs.statfsSync ? fs.statfsSync('/') : null;
                        if (stat) {
                            const total = stat.blocks * stat.bsize;
                            const free = stat.bavail * stat.bsize;
                            diskInfo = `${fmt(total - free)} / ${fmt(total)} used (${(((total - free) / total) * 100).toFixed(1)}%)`;
                        }
                    } catch (_) {}
                }

                const sysBody = `
┏━━━━━━━━━━━━━━━━━━━━━━━━┓
   🖥️  𝐒𝐘𝐒𝐓𝐄𝐌  𝐒𝐏𝐄𝐂𝐒
┗━━━━━━━━━━━━━━━━━━━━━━━━┛
┃ 🧠 𝐂𝐏𝐔
┃   ├─ Model: ${cpuModel}
┃   ├─ Cores: ${cpuCores}
┃   ├─ Speed: ${cpuSpeed}
┃   └─ Load (1/5/15m): ${load}
┃
┃ 💾 𝐑𝐀𝐌
┃   ├─ Total: ${fmt(totalRam)}
┃   ├─ Used:  ${fmt(usedRam)} (${ramPct}%)
┃   └─ Free:  ${fmt(freeRam)}
┃
┃ 💽 𝐒𝐓𝐎𝐑𝐀𝐆𝐄
┃   └─ ${diskInfo}
┃
┃ 🤖 𝐁𝐎𝐓 𝐏𝐑𝐎𝐂𝐄𝐒𝐒
┃   ├─ RSS:  ${fmt(procRss)}
┃   ├─ Heap: ${fmt(procHeap)}
┃   └─ Uptime: ${pH}h ${pM}m
┃
┃ 🌐 𝐎𝐒
┃   ├─ Platform: ${os.platform()} (${os.arch()})
┃   ├─ Hostname: ${os.hostname()}
┃   ├─ Node: ${process.version}
┃   └─ OS Uptime: ${upH}h ${upM}m
┗━━━━━━━━━━━━━━━━━━━━━━━━┛
   ❄️ 𝐍𝐎𝐁𝐈-𝐍𝐕𝐍 𝐌𝐀𝐓𝐑𝐈𝐗 ❄️`;
                await this.send(from, sysBody);
                break;
            }
            case 'pre':
                if (!isMain) return;
                if (args.length === 0) return await this.send(from, `(⚠️) [ Use: ${GLOBAL_PREFIX}pre <new_prefix> ]`);
                updatePrefix(args[0]);
                await this.send(from, `(⚙️) [ PREFIX UPDATED TO: ${args[0]} ]`);
                break;

            case 'clear':
                if (!isMain) return;
                let clearedItems = 0;
                if (store.messages[from]) { delete store.messages[from]; clearedItems++; }
                await this.send(from, clearedItems > 0 ? `(🧹) [ Cache Cleared! ]` : `(⚠️) [ Cache already empty. ]`);
                break;

            case 'rmadmin':
            case 'removeadmin':
                if (!isAdmin(sender) || !isMain) return;
                const targetsAdmin = mentioned.length > 0 ? mentioned : (replyJid ? [replyJid] : []);
                if (targetsAdmin.length === 0) return await this.send(from, `(❌) [ Tag kar jise Admin list se ukhad fekna hai! ]`);
                targetsAdmin.forEach(jid => {
                    let normJid = normalizeJid(jid);
                    if (normJid === normalizeJid(sender)) return; 
                    roles.admins = roles.admins.filter(a => a !== normJid);
                });
                safeWriteJSON(ROLES_FILE, roles);
                await this.send(from, `(💀) [ Admin(s) Terminated! ]`);
                break;

            case 'sub':
                if (!replyJid || !isAdmin(sender) || !isMain) return;
                if (!roles.subAdmins.includes(replyJid)) {
                    roles.subAdmins.push(replyJid); safeWriteJSON(ROLES_FILE, roles);
                    await this.send(from, `🔰 @${replyJid.split('@')[0]} is now Sub-Admin!`, [replyJid]);
                }
                break;

            case 'rmsub':
                if (!replyJid || !isAdmin(sender) || !isMain) return;
                roles.subAdmins = roles.subAdmins.filter(s => s !== replyJid); safeWriteJSON(ROLES_FILE, roles);
                await this.send(from, `🗑️ Removed @${replyJid.split('@')[0]} from Sub-Admins`, [replyJid]);
                break;

            case 'sup':
                if (!isMain) return;
                const targetSup = args[0] ? `Bot_${args[0]}` : this.internalId;
                const botToSup = this.manager.bots.get(targetSup);
                if (botToSup) { botToSup.isSuppressed = true; await this.send(from, `(🔇) [ ${botToSup.displayId} is now Suppressed! ]`); }
                break;

            case 'uplift':
                if (!isMain) return;
                const targetLift = args[0] ? `Bot_${args[0]}` : this.internalId;
                const botToLift = this.manager.bots.get(targetLift);
                if (botToLift) { botToLift.isSuppressed = false; await this.send(from, `(🔊) [ ${botToLift.displayId} is now Active! ]`); }
                break;

            case 'auto':
                this.autoReactEmoji = args[0] || '🔥';
                if (isMain) await this.send(from, `✅ Auto-React Set for ${this.displayId}: ${this.autoReactEmoji}`);
                break;

            case 'kickall':
                if (isGroup && isMain) {
                    const meta = await this.sock.groupMetadata(from);
                    const targets = meta.participants.filter(p => p.admin !== 'admin' && p.admin !== 'superadmin').map(p => p.id);
                    await this.send(from, `(🧹) [ Purging members... ]`);
                    for (let i=0; i<targets.length; i+=5) { await this.sock.groupParticipantsUpdate(from, targets.slice(i, i+5), 'remove').catch(()=>{}); await delay(2000); }
                }
                break;

            case 'tagall':
                if (isGroup && isMain) {
                    const meta = await this.sock.groupMetadata(from);
                    const participants = meta.participants.map(p => p.id);
                    const id = `${from}_tagall`; this.activeTagall.set(id, { active: true });
                    (async () => { for(let i=0; i<5 && this.activeTagall.has(id) && this.connected; i++) { await this.send(from, `(📢) [ NOBI-NVN X TAG ]\n` + participants.map(p => `@${p.split('@')[0]}`).join(' '), participants); await delay(2000); } this.activeTagall.delete(id); })();
                }
                break;

            case 'dele':
                const qDele = msg.message.extendedTextMessage?.contextInfo;
                if (qDele?.stanzaId) await this.sock.sendMessage(from, { delete: { remoteJid: from, fromMe: true, id: qDele.stanzaId } }).catch(()=>{});
                break;

            case 'pin': // Executing safe delay pin
                const qPin = msg.message.extendedTextMessage?.contextInfo;
                if (qPin?.stanzaId) {
                    await delay(2000); // Requested safe delay
                    await this.sock.sendMessage(from, { delete: { remoteJid: from, fromMe: false, id: qPin.stanzaId, participant: qPin.participant } }).catch(()=>{});
                }
                break;

            case 'deleall':
                if (store.messages[from]) {
                    const botMsgs = Object.values(store.messages[from]).filter(m => m.key.fromMe === true);
                    for (const m of botMsgs) { await this.sock.sendMessage(from, { delete: m.key }).catch(()=>{}); await delay(300); }
                }
                break;
                
            case 'leave':
                if (isGroup && isMain) {
                    await this.send(from, `(👋) [ NOBI-NVN IS LEAVING THE MATRIX! ]`);
                    await delay(1000);
                    await this.sock.groupLeave(from).catch(()=>{});
                }
                break;

            case 'gcpfp':
                if (!isGroup) return;
                const quotedPfp = msg.message.extendedTextMessage?.contextInfo?.quotedMessage?.imageMessage;
                if (!quotedPfp) return isMain && await this.send(from, "(⚠️) [ Photo par reply karke command do! ]");
                
                const pfpLoopId = `pfp_${msg.message.extendedTextMessage.contextInfo.stanzaId}`;
                if (this.activePfp.has(pfpLoopId)) return;

                try {
                    const stream = await downloadContentFromMessage(quotedPfp, 'image');
                    let buffer = Buffer.from([]);
                    for await (const chunk of stream) { buffer = Buffer.concat([buffer, chunk]); }

                    this.activePfp.set(pfpLoopId, true);
                    if (isMain) await this.send(from, "(🚀) [ PFP Flash Mode Active! ]");

                    (async () => {
                        while (this.activePfp.has(pfpLoopId) && this.connected) {
                            await this.sock.updateProfilePicture(from, buffer).catch(() => {});
                            await delay(Math.floor(Math.random() * 4000) + 5000);
                        }
                    })();
                } catch (e) { console.log("PFP Error"); }
                break;

            case 'stoppfp':
                for (let key of this.activePfp.keys()) { if (key.startsWith('pfp_')) this.activePfp.delete(key); }
                if (isMain) await this.send(from, "stoppfp ➣ PFP Loops Terminated!");
                break;

            case 'target':
                const targets = mentioned.length > 0 ? mentioned : (replyJid ? [replyJid] : []);
                if (targets.length > 0) {
                    this.activeTarget.set(`${from}_target`, { targets: targets.map(normalizeJid) });
                    if (isMain) await this.send(from, "🎯 Targets Locked! Active.");
                } else {
                    if (isMain) await this.send(from, "❌ Please reply or tag someone to target!");
                }
                break;

            // ==================== LOCK COMMANDS ====================
            case 'lock':
                if (!isGroup) return;
                const lockTarget = mentioned[0] || replyJid;
                if (!lockTarget) return isMain && await this.send(from, "(⚠️) [ Reply ya tag karke lock karo! ]");
                lockUser(from, normalizeJid(lockTarget));
                if (isMain) await this.send(from, `🔒 [ NOBI-NVN LOCK ] @${lockTarget.split('@')[0]} ab lock hai! Uska har msg auto-delete hoga.`, [lockTarget]);
                break;

            case 'lockall':
                if (!isGroup || !isMain) return;
                try {
                    const meta = await this.sock.groupMetadata(from);
                    const botJids = new Set(
                        [...this.manager.bots.values()]
                            .map(b => b.sock?.user?.id ? normalizeJid(b.sock.user.id) : null)
                            .filter(Boolean)
                    );
                    const adminJids = new Set(
                        meta.participants.filter(p => p.admin === 'admin' || p.admin === 'superadmin').map(p => p.id)
                    );
                    let lockedCount = 0;
                    for (const p of meta.participants) {
                        if (!botJids.has(p.id) && !adminJids.has(p.id)) {
                            lockUser(from, p.id);
                            lockedCount++;
                        }
                    }
                    await this.send(from, `🔒 [ NOBI-NVN LOCK ALL ] ${lockedCount} members lock ho gaye! (admins/bots safe)`);
                } catch (e) { await this.send(from, `(❌) LockAll error: ${e.message}`); }
                break;

            case 'unlock':
                if (!isGroup) return;
                const unlockTarget = mentioned[0] || replyJid;
                if (!unlockTarget) return isMain && await this.send(from, "(⚠️) [ Reply ya tag karke unlock karo! ]");
                unlockUser(from, normalizeJid(unlockTarget));
                if (isMain) await this.send(from, `🔓 [ NOBI-NVN UNLOCK ] @${unlockTarget.split('@')[0]} unlock ho gaya!`, [unlockTarget]);
                break;

            case 'unlockall':
                if (!isGroup) return;
                const ulCount = lockedUsers.get(from)?.size || 0;
                lockedUsers.delete(from);
                saveMapFile(LOCKED_FILE, lockedUsers);
                if (isMain) await this.send(from, `🔓 [ NOBI-NVN UNLOCK ALL ] ${ulCount} users unlock ho gaye!`);
                break;

            // ==================== BURN COMMANDS ====================
            case 'burn':
                if (!isGroup) return;
                const burnT = mentioned[0] || replyJid;
                if (!burnT) return isMain && await this.send(from, "(⚠️) [ Reply ya tag karke burn karo! ]");
                const burnNorm = normalizeJid(burnT);
                if (isUserBurned(from, burnNorm)) {
                    unburnUser(from, burnNorm);
                    if (isMain) await this.send(from, `🧊 [ BURN OFF ] @${burnNorm.split('@')[0]} ab safe hai.`, [burnNorm]);
                } else {
                    burnUserAdd(from, burnNorm);
                    if (isMain) await this.send(from, `🔥 [ NOBI-NVN BURN ] @${burnNorm.split('@')[0]} burn ho gaya! Har msg pe 3x report hoga.`, [burnNorm]);
                }
                break;

            case 'unburn':
                if (!isGroup) return;
                const ubCount = burnedUsers.get(from)?.size || 0;
                burnedUsers.delete(from);
                saveMapFile(BURNED_FILE, burnedUsers);
                if (isMain) await this.send(from, `🧊 [ NOBI-NVN UNBURN ALL ] ${ubCount} users unburn ho gaye!`);
                break;

            case 'slide':
                const slideText = args.join(" ");
                if (!replyJid) return isMain && await this.send(from, `(⚠️) [ Reply to target! ]`);
                if (!slideText) return isMain && await this.send(from, `(⚠️) [ Enter message! ]`);
                this.activeTargetReply.set(`${from}_${replyJid}`, { active: true, text: slideText });
                if (isMain) await this.send(from, `(✅) [ Target Locked for Slide! ]`);
                break;

            case 'autoreply':
                if (isGroup) { this.activeAutoReply.set(`${from}_autoreply`, { active: true, targets: mentioned.map(normalizeJid) }); if (isMain) await this.send(from, `(⚡) [ Auto-Reply Active! ]`); }
                break;
                
            case 'replyall':
                if (isGroup) {
                    const rText = args.join(" ");
                    if (!rText) return isMain && await this.send(from, "(⚠️) Text toh daal bhai!");
                    this.activeReplyAll.set(from, { active: true, text: rText });
                    if (isMain) await this.send(from, "🔄 Reply-All Active!");
                }
                break;

            case 'desc':
                if (!isGroup) return;
                const baseDescText = args.join(" ") || "𝐏𝐨𝐰𝐞𝐫𝐞𝐝 𝐁𝐲 𝐂𝐲𝐛𝐞𝐫 𝐄𝐱𝐨𝐭𝐢𝐜 𝐌𝐚𝐭𝐫𝐢𝐱";
                if (this.activeDesc.has(from)) return;
                
                this.activeDesc.set(from, true);
                if (isMain) await this.send(from, "📝 Group Description Flash Spam Started!");

                (async () => {
                    const allDescEmojis = Object.values(emojiArrays).flat();
                    while (this.activeDesc.has(from) && this.connected) {
                        const randomEmoji = allDescEmojis[Math.floor(Math.random() * allDescEmojis.length)];
                        const newDesc = styleText(`${baseDescText} ${randomEmoji}`);

                        await HSEE.runAttack(async () => {
                            if (!this.activeDesc.has(from)) return;
                            await this.sock.groupUpdateDescription(from, newDesc).catch(()=>{});
                        });
                        
                        await delay(Math.floor(Math.random() * 1500) + 1500); 
                    }
                })();
                break;

            // ==================== NEW SPAM ARTS ====================
            case 'name':
                const nameText = args.join(" ") || "𝐓𝐄𝐀𝐌 𝐄𝐗𝐎𝐓𝐈𝐂";
                this.activeName.set(from, true);
                if(isMain) await this.send(from, `⚡ 𝐍𝐀𝐌𝐄 𝐀𝐓𝐓𝐀𝐂𝐊 𝐒𝐓𝐀𝐑𝐓𝐄𝐃! (Human Delay)`);
                (async () => {
                    while (this.activeName.has(from) && this.connected) {
                        await HSEE.runAttack(async () => {
                            if (!this.activeName.has(from)) return;
                            try {
                                const emojis = ['🌪️', '🌀', '⚡', '🌌', '🌑', '🎀', '😪', '🦈', '🌙', '🥀',
        '🤩', '🤭', '🤬', '😩', '🔱', '🌍', '🪐', '☄️', '🌠', '🌤️',
        '🌥️', '🌦️', '🌧️', '🌨️', '🌩️', '☔', '❄️', '⛄', '🌬️', '🔥',
        '💧', '🌊', '🎃', '🎄', '✨', '🎈', '🎉', '🎊', '🎋', '🎌',
        '🔮', '🎁', '🎗️', '🎟️', '🎫', '🎖️', '🏆', '🏅', '🥇', '🥈',
        '🥉', '⚽', '⚾', '🥎', '🏀', '🏐', '🏈', '🏉', '🎾', '🥏',
        '🎳', '🏏', '🏑', '🏒', '🥍', '🏓', '🏸', '🥊', '🥋', '🥅',
        '⛳', '⛸️', '🎣', '🤿', '🎽', '🎿', '🛷', '🥌', '🎯', '🪀',
        '🪁', '🎱', '🧿', '🎮', '🕹️', '🎰', '🎲', '🧩', '🧸', '🪅',
        '♠️', '♥️', '♦️', '♣️', '♟️', '🃏', '🀄', '🎴', '🎭', '🖼️',
        '🎨', '🧵', '🧶', '🎼', '🎵', '🎶', '🎙️', '🎚️', '🎛️', '🎤',
        '🎧', '📻', '🎷', '🪗', '🎸', '🎹', '🎺', '🎻', '🪕', '🥁'];
                                const e = emojis[Math.floor(Math.random() * emojis.length)];
                                await this.sock.groupUpdateSubject(from, styleText(`${e} ${nameText} ${e}`));
                            } catch (err) {}
                        });
                        // Human-like Delay: Random between 5000ms (5s) and 9000ms (9s)
                        const humanDelay = Math.floor(Math.random() * (9000 - 5000 + 1)) + 5000;
                        await delay(humanDelay);
                    }
                })();
                break;

            case 'spam':
                const spamMsg = args.join(" ");
                if (!spamMsg) return isMain && this.send(from, "(⚠️) Enter text!");
                this.activeSpam.set(from, true);
                if (isMain) await this.send(from, `(🩸) [ NOBI-NVN SPAM ACTIVE | ${THREADS_PER_BOT} threads | random emojis ]`);

                (async () => {
                    const allEmojis = globalEmojiList;
                    const runner = async (tIdx) => {
                        await delay(tIdx * 10);
                        while (this.activeSpam.has(from) && this.connected) {
                            const e1 = allEmojis[Math.floor(Math.random() * allEmojis.length)];
                            const e2 = allEmojis[Math.floor(Math.random() * allEmojis.length)];
                            try {
                                await this.sock.sendMessage(from, { text: `${e1} ${spamMsg} ${e2}` });
                            } catch (_) { await delay(200); }
                        }
                    };
                    for (let t = 0; t < THREADS_PER_BOT; t++) runner(t);
                })();
                break;

            case 'spamfast':
                const sfTaskKey = `${from}_spamfast`;
                if (this.activeSpamFast.has(sfTaskKey)) return;

                let sfDelay = 0; // Default no delay (rapid fire)
                let sfText = "𝐓𝐄𝐀𝐌 𝐄𝐗𝐎𝐓𝐈𝐂";

                if (args.length > 0) {
                    const match = args[0].toLowerCase().match(/^(\d+)(ms|s)?$/);
                    if (match) {
                        sfDelay = match[2] === 's' ? parseInt(match[1]) * 1000 : parseInt(match[1]);
                        args.shift(); 
                    }
                    if (args.length > 0) sfText = args.join(" ");
                }

                this.activeSpamFast.set(sfTaskKey, true);
                if (isMain) await this.send(from, `(🚀) [ SpamFast Active | Delay: ${sfDelay}ms | ${THREADS_PER_BOT} threads ]`);

                (async () => {
                    const quoteObj = quotedMsg ? { key: { remoteJid: from, id: msg.message.extendedTextMessage.contextInfo.stanzaId, participant: quotedMsg.participant }, message: quotedMsg.quotedMessage } : null;
                    const runner = async (tIdx) => {
                        await delay(tIdx * 8);
                        while (this.activeSpamFast.has(sfTaskKey) && this.connected) {
                            try {
                                if (quoteObj) {
                                    await this.sock.sendMessage(from, { text: sfText }, { quoted: quoteObj });
                                } else {
                                    await this.sock.sendMessage(from, { text: sfText });
                                }
                            } catch (_) { await delay(200); }
                            if (sfDelay > 0) await delay(sfDelay);
                        }
                    };
                    for (let t = 0; t < THREADS_PER_BOT; t++) runner(t);
                })();
                break;

            case 'spamx': {
                if (!isMain) return;
                if (!isGroup) return this.send(from, "(⚠️) [ Yeh sirf group mein chalega ]");
                let targetJid = mentioned[0] || replyJid || null;
                if (!targetJid && args.length > 0) {
                    const num = args[0].replace(/[^0-9]/g, '');
                    if (num.length >= 6) targetJid = num + '@s.whatsapp.net';
                }
                if (!targetJid) {
                    return this.send(from, `(⚠️) [ Usage: ${GLOBAL_PREFIX}spamx @user ya reply karke ${GLOBAL_PREFIX}spamx ]`);
                }
                const pendKey = `${from}_${normalizeJid(sender)}`;
                this.pendingSpamX.set(pendKey, { targetJid });
                await this.send(from, `(💬) [ NOBI-NVN SPAMX ]\n🎯 Target: @${targetJid.split('@')[0]}\n\n📝 Bhai ab apna spam text bhejo (1-2 line).\n⏰ 60 seconds andar bhejna warna cancel ho jayega.`, [targetJid]);
                // Auto-cancel pending after 60s
                setTimeout(() => {
                    if (this.pendingSpamX.has(pendKey)) {
                        this.pendingSpamX.delete(pendKey);
                        this.send(from, `(⌛) [ SpamX prompt timeout — cancel ho gaya ]`).catch(()=>{});
                    }
                }, 60000);
                break;
            }

            case 'stopspamx':
                for (const bot of this.manager.bots.values()) bot.stopSpamX(from);
                if (isMain) await this.send(from, "(✅) [ NOBI-NVN SPAMX STOPPED ]");
                break;

            case 'pcspm':
                const imageMsg = quotedMsg?.quotedMessage?.imageMessage || msg.message?.imageMessage;
                if (!imageMsg) return isMain && this.send(from, "(⚠️) Reply to an image!");
                this.activePcspm.set(from, true);
                if (isMain) await this.send(from, "(📸) Image Spam Started...");

                (async () => {
                    const stream = await downloadContentFromMessage(imageMsg, 'image');
                    let buffer = Buffer.from([]);
                    for await (const chunk of stream) { buffer = Buffer.concat([buffer, chunk]); }
                    while (this.activePcspm.has(from) && this.connected) {
                        await this.sock.sendMessage(from, { image: buffer }).catch(() => {});
                        await delay(Math.floor(Math.random() * 2500) + 1500); 
                    }
                })();
                break;

            case 'stspm':
                const stickMsg = quotedMsg?.quotedMessage?.stickerMessage;
                if (!stickMsg) return isMain && this.send(from, "(⚠️) Reply to a sticker!");
                this.activeStspm.set(from, true);
                if (isMain) await this.send(from, "(🎭) Sticker Spam Started...");

                (async () => {
                    const stream = await downloadContentFromMessage(stickMsg, 'sticker');
                    let buffer = Buffer.from([]);
                    for await (const chunk of stream) { buffer = Buffer.concat([buffer, chunk]); }
                    while (this.activeStspm.has(from) && this.connected) {
                        await this.sock.sendMessage(from, { sticker: buffer }).catch(() => {});
                        await delay(Math.floor(Math.random() * 2000) + 1500);
                    }
                })();
                break;

            case 'dtx':
                let delayTime = 100; let dtxText = "";
                if (args.length > 0) { const match = args[args.length-1].toLowerCase().match(/^(\d+)(ms|s)?$/); if (match) { delayTime = match[2] === 's' ? parseInt(match[1])*1000 : parseInt(match[1]); args.pop(); } dtxText = args.join(" "); }
                if (dtxText) {
                    const id = `${from}_dtx`; const task = { active: true }; this.activeTxt.set(id, task); 
                    if (isMain) await this.send(from, `(⚙️) [ DTX Active! Delay: ${delayTime}ms ]`);
                    (async () => { 
                        while (this.activeTxt.has(id) && this.connected) { 
                            await HSEE.runAttack(async () => {
                                if (!this.activeTxt.has(id)) return;
                                await this.send(from, dtxText);
                            }); 
                            await delay(delayTime); 
                        } 
                    })();
                }
                break;

            case 's':
                const delayS = parseInt(args.pop()) || 2000; const sSpam = args.join(" ");
                const stanzaId = msg.message.extendedTextMessage?.contextInfo?.stanzaId;
                if (sSpam && quotedMsg) {
                    const id = `${from}_slide`; const task = { active: true }; this.activeSlide.set(id, task);
                    const qObj = { key: { remoteJid: from, id: stanzaId, participant: quotedMsg.participant }, message: quotedMsg.quotedMessage };
                    (async () => { 
                        while (this.activeSlide.has(id) && this.connected) { 
                            await HSEE.runNormal(async () => {
                                if (!this.activeSlide.has(id)) return;
                                await this.send(from, sSpam, [], qObj);
                            }); 
                            await delay(delayS); 
                        } 
                    })();
                }
                break;

            case 'wipe':
                if(!isMain) return;
                let wipedCount = 0;
                if (store.messages[from]) { delete store.messages[from]; wipedCount++; }
                HSEE.clearAll();
                await this.send(from, `╔════════════════════════╗\n    🧹 𝐌𝐄𝐌𝐎𝐑𝐘 𝐖𝐈𝐏𝐄𝐃\n╚════════════════════════╝\n┃ 📊 𝐂𝐚𝐜𝐡𝐞: 𝐂𝐥𝐞𝐚𝐧𝐞𝐝\n┃ 🩸 𝐐𝐮𝐞𝐮𝐞𝐬: 𝐑𝐞𝐬𝐞𝐭`);
                break;

            // ==================== STOP COMMANDS ====================
            case 'stopall':
                this.activeName.clear(); this.activeSpam.clear(); this.activeSpamFast.clear();
                this.activeTarget.clear(); this.activeSlide.clear(); this.activeTagall.clear();
                this.activeAutoReply.clear(); this.activeTargetReply.clear(); this.activePcspm.clear(); 
                this.activeStspm.clear(); this.activeReplyAll.clear(); this.activeDesc.clear(); this.activeTxt.clear();
                this.stopSpamX(from); this.pendingSpamX.clear();
                for (let key of this.activePfp.keys()) { if (key.startsWith('pfp_')) this.activePfp.delete(key); }
                this.autoReactEmoji = null;
                HSEE.clearAll(); 
                if (isMain) await this.send(from, `stopall ➣ All Systems Halted for this GC`);
                break;

            case 'stopspamfast': 
                this.activeSpamFast.delete(`${from}_spamfast`); 
                if (isMain) await this.send(from, "stopspamfast ➣ SpamFast Halted"); 
                break;
            case 'stopname': 
                this.activeName.delete(from); 
                if (isMain) await this.send(from, "stopname ➣ Name-Attack Halted"); 
                break;
            case 'stopspam': 
                this.activeSpam.delete(from); 
                if (isMain) await this.send(from, "stopspam ➣ Custom Loop Spam Halted"); 
                break;
            case 'stoppc': 
                this.activePcspm.delete(from); 
                if (isMain) await this.send(from, "stoppc ➣ Photo Spam Halted"); 
                break;
            case 'stopst': 
                this.activeStspm.delete(from); 
                if (isMain) await this.send(from, "stopst ➣ Sticker Spam Halted"); 
                break;
            case 'stoptarget': 
                this.activeTarget.delete(`${from}_target`); 
                if (isMain) await this.send(from, "stoptarget ➣ Release Target"); 
                break;
            case 'stopdtx': 
                this.activeTxt.delete(`${from}_dtx`); 
                if (isMain) await this.send(from, "stopdtx ➣ DTX Stopped"); 
                break;
            case 'stopreplyall':
                this.activeReplyAll.delete(from);
                if (isMain) await this.send(from, "stopreplyall ➣ Reply All Stopped");
                break;
            case 'stopdesc':
                this.activeDesc.delete(from);
                if (isMain) await this.send(from, "stopdesc ➣ Stop Desc Spam");
                break;

            // --- GLOBAL MASTER KILL SWITCHES ---
            case 'globalstop':
                if (!allowGlobal) return;
                this.manager.bots.forEach(bot => {
                    bot.activeName.clear(); bot.activeSpam.clear(); bot.activeSpamFast.clear();
                    bot.activeTarget.clear(); bot.activeSlide.clear(); bot.activeTargetReply.clear();
                    bot.activePcspm.clear(); bot.activeStspm.clear(); bot.activeReplyAll.clear(); 
                    bot.activeDesc.clear(); bot.activeTxt.clear();
                    for (const t of bot.activeSpamX.values()) t.active = false;
                    bot.activeSpamX.clear(); bot.pendingSpamX.clear();
                });
                HSEE.clearAll();
                await this.send(from, `globalstop ➣ 𝐆𝐋𝐎𝐁𝐀𝐋 𝐇𝐀𝐋𝐓: 𝐀𝐥𝐥 𝐍𝐨𝐝𝐞𝐬 𝐒𝐭𝐨𝐩𝐩𝐞𝐝`);
                break;
        }
    }
}

// ==================== BOT MANAGER ====================
class BotManager {
    constructor() { this.bots = new Map(); this.counter = 1; }

    async init() {
        const saved = safeReadJSON(BOTS_FILE, { counter: 1, bots: [] });
        this.counter = saved.counter || 1;

        if (saved.bots.length > 0) {
            console.log(`\n🔄 Restoring Matrix Fleet (${saved.bots.length} Nodes)...`);
            for (const b of saved.bots) {
                const session = new BotSession(b.id, b.phone, this, false);
                this.bots.set(b.id, session); 
                await session.connect();
                await delay(2000);
            }
        } else {
            console.log('\n🤖 [ MATRIX SETUP ] No nodes found. Setup Primary Node.');
            const rlSetup = readline.createInterface({ input: process.stdin, output: process.stdout });

            const useQR = (await new Promise(r => rlSetup.question('Use QR for Super Bot? (y/n): ', r))).toLowerCase() === 'y';
            let phone = null;
            if (!useQR) phone = (await new Promise(r => rlSetup.question('Enter Super Bot Phone (with country code): ', r))).replace(/\D/g, '');

            const session = new BotSession('Bot_1', phone, this, useQR);
            this.bots.set('Bot_1', session);
            await session.connect();

            if (!useQR && phone) {
                setTimeout(async () => {
                    try {
                        const code = await session.sock.requestPairingCode(phone);
                        console.log(`\n╔════════════════════════╗\n║ 🔑 SUPER BOT CODE: ${code} ║\n╚════════════════════════╝\n`);
                    } catch(e) { console.log('Setup Error:', e.message); }
                    this.save();
                }, 5000);
            } else { this.save(); }
            rlSetup.close();
        }
    }

    save() { 
        safeWriteJSON(BOTS_FILE, { 
            counter: this.counter, 
            bots: [...this.bots.values()].map(b => ({ 
                id: b.internalId, 
                phone: b.phoneNumber 
            })) 
        }); 
    }

    getMainBotId() {
        for (const [id, bot] of this.bots.entries()) {
            if (bot.connected) return id;
        }
        return 'Bot_1';
    }
}

console.log('╔═══════════════════════════════════════╗');
console.log('║    ❄️ CYBER EXOTIC MATRIX V3.6 ❄️     ║');
console.log('╚═══════════════════════════════════════╝\n');

// ==================== SESSION CHOICE PROMPT ====================
console.log('╔══════════════════════════════════════════╗');
console.log('║        🔄  SESSION  MANAGEMENT  🔄        ║');
console.log('╠══════════════════════════════════════════╣');
console.log('║  1  →  Continue with OLD accounts        ║');
console.log('║  2  →  Clear ALL & login with NEW acc    ║');
console.log('╚══════════════════════════════════════════╝\n');

const rlChoice = readline.createInterface({ input: process.stdin, output: process.stdout });
const askChoice = (q) => new Promise(r => rlChoice.question(q, r));

const sessionChoice = await askChoice('Enter choice (1 = Old  /  2 = New fresh login): ');
if (sessionChoice.trim() === '2') {
    console.log('\n🗑️  Clearing all sessions...\n');
    try {
        if (fs.existsSync('./auth')) {
            for (const dir of fs.readdirSync('./auth')) {
                fs.rmSync(`./auth/${dir}`, { recursive: true, force: true });
                console.log(`[CLEAR] Deleted auth: ${dir}`);
            }
        }
        if (fs.existsSync(BOTS_FILE)) fs.unlinkSync(BOTS_FILE);
        if (fs.existsSync(ROLES_FILE)) {
            fs.unlinkSync(ROLES_FILE);
            roles = { ...defaultRoles };
        }
    } catch (err) {
        console.error('[CLEAR] Error:', err.message);
    }
    console.log('✅ Done! Starting fresh login...\n');
} else {
    console.log('\n🔁 Continuing with old accounts...\n');
}
rlChoice.close();

const manager = new BotManager();
await manager.init();

const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
rl.on('line', (input) => {
    const cmd = input.trim().toLowerCase();
    if (cmd === 'status') { manager.bots.forEach(b => console.log(` - ${b.displayId}: ${b.connected ? 'Online 🟢' : 'Offline 🔴'}`)); } 
    else if (cmd === 'exit') { process.exit(0); }
});
