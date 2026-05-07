import asyncio
import json
import os
import random
import re
import sys
import time
import concurrent.futures
import aiohttp
from datetime import datetime

import discord
import pytesseract
from colorama import Fore, init

# ── Cross-Platform Tesseract Setup ──────────────────────────────────────────
_TESS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tesseract")
if os.name == "nt": # Windows
    pytesseract.pytesseract.tesseract_cmd = os.path.join(_TESS_DIR, "tesseract.exe")
    os.environ["TESSDATA_PREFIX"] = _TESS_DIR
else: # Linux / Android (Termux) / VPS
    # On Linux, pytesseract looks for 'tesseract' in the system PATH automatically
    pass
# ───────────────────────────────────────────────────────────────────────────

from lib import api
from lib.ocr import *

init(convert=True)

# OCR Configurations
OCR_CFG_TEXT = r'--psm 6 --oem 3'
OCR_CFG_PRINT = r'--psm 7 -c tessedit_char_whitelist=0123456789#'

# (BUTTON_CHANNELS removed in favor of automatic detection)

# Thread Pool Executor for OCR (Increased for full-speed parallel processing)
executor = concurrent.futures.ThreadPoolExecutor(max_workers=16)

match = "(is dropping [3-4] cards!)|(I'm dropping [3-4] cards since this server is currently active!)"
v = "v2.3.2"
if "v" in v:
    beta = False
    update_url = "https://raw.githubusercontent.com/NoMeansNowastaken/KarutaSniper/master/version.txt"
else:
    beta = True
    update_url = "https://raw.githubusercontent.com/NoMeansNowastaken/KarutaSniper/beta/version.txt"

with open("config.json") as f:
    config = json.load(f)

title = os.name == 'nt'

token = config["token"]
channels = config["channels"]
guilds = config["servers"]
accuracy = float(config["accuracy"])
blaccuracy = float(config["blaccuracy"])
loghits = config["log_hits"]
logcollection = config["log_collection"]
timestamp = config["timestamp"]
update_cfg = config["update_check"]
autodrop = config["autodrop"]
debug = config["debug"]
cprint = config["check_print"]
autofarm_cfg = config["autofarm"]
tofu_enabled = config["tofu"]["enabled"]
verbose = config["very_verbose"]

# Drop priority: seconds before your own drop where foreign grabs are skipped
drop_priority_window = int(config.get("drop_priority_window", 650))
# Grab reaction delays (seconds)
grab_delay_own = float(config.get("grab_delay_own", 0.05))
grab_delay_min = float(config.get("grab_delay_min", 0.08))
grab_delay_max = float(config.get("grab_delay_max", 0.25))

if autofarm_cfg:
    resourcechannel = config["resourcechannel"]
if cprint:
    pn = int(config["print_number"])
if autodrop:
    autodropchannel = config["autodropchannel"]
    dropdelay = config["dropdelay"]
    randmin = int(config["randmin"])
    randmax = int(config["randmax"])
if tofu_enabled:
    tofu_config = config["tofu"]
    tofu_channels = tofu_config["channels"]
    shouldsummon = tofu_config["summon"]
    tcc = tofu_config["tcc"]
    if shouldsummon:
        summonchannel = tofu_config["summon_channel"]
        tofu_delay = tofu_config["dropdelay"]
        tofu_min = tofu_config["randmin"]
        tofu_max = tofu_config["randmax"]
        grandom = tofu_config["grab_random"]
    tofu_cprint = tofu_config["check_print"]


class Main(discord.Client):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.charblacklist = None
        self.aniblacklist = None
        self.animes = None
        self.chars = None
        self.ready = False
        self.timer = 0
        self.url = None
        self.missed = 0
        self.collected = 0
        self.buttons = None
        self.tofutimer = 0
        self.next_drop_at = 0.0   # unix timestamp of next scheduled autodrop
        self.session = None       # created in setup_hook once event loop is running
        if tofu_enabled:
            self.tofureact = False
            self.tofuurl = None
            self.tcc = tcc

    async def setup_hook(self):
        """Called by discord.py before connecting - event loop is running here."""
        self.session = aiohttp.ClientSession()

    async def timecheck(self):
        """Background task to decrement timers every second."""
        while True:
            await asyncio.sleep(1)
            if self.timer > 0: self.timer -= 1
            if self.tofutimer > 0: self.tofutimer -= 1

    async def close(self):
        await self.session.close()
        await super().close()

    def _is_own_drop(self, message) -> bool:
        """Returns True if the drop was triggered by the bot account itself."""
        # Mentions (both regular and nickname formats)
        if f"<@{self.user.id}>" in message.content or f"<@!{self.user.id}>" in message.content:
            return True
        # Check if it's a reply to our kd/d command
        if message.reference and message.reference.cached_message:
            if message.reference.cached_message.author.id == self.user.id:
                content = message.reference.cached_message.content.lower()
                if content.startswith("kd") or content.startswith("d") or content.startswith("k d"):
                    return True
        return False

    def _should_skip_grab(self, is_own_drop: bool) -> bool:
        # NEVER skip our own drop
        if is_own_drop:
            return False
            
        # USER REQUEST: Remove grab restriction waiting for self drop.
        # The bot will now grab foreign drops normally and autodrop will wait for the cooldown.
        return False

    async def on_ready(self):
        os.system("cls" if os.name == "nt" else "clear")
        await asyncio.sleep(0.5)
        thing = Fore.LIGHTMAGENTA_EX + r"""
 ____  __.                    __             _________      .__                     
|    |/ _|____ _______ __ ___/  |______     /   _____/ ____ |__|_____   ___________ 
|      < \__  \\_  __ \  |  \   __\__  \    \_____  \ /    \|  \____ \_/ __ \_  __ \
|    |  \ / __ \|  | \/  |  /|  |  / __ \_  /        \   |  \  |  |_> >  ___/|  | \/
|____|__ (____  /__|  |____/ |__| (____  / /_______  /___|  /__|   __/ \___  >__|   
        \/    \/                       \/          \/     \/   |__|        \/       
"""
        if sys.gettrace() is None:
            try:
                cols = os.get_terminal_size().columns
            except OSError:
                cols = 80
            for line in thing.split("\n"):
                print(line.center(cols))
            print(Fore.LIGHTMAGENTA_EX + "─" * cols)
        
        tprint(f"{Fore.BLUE}Logged in as {Fore.RED}{self.user.name}#{self.user.discriminator} {Fore.GREEN}({self.user.id}){Fore.RESET} ")
        
        async with self.session.get(update_url) as resp:
            latest_ver = (await resp.text()).strip()
        if latest_ver != v:
            tprint(f"{Fore.RED}You are on version {v}, while the latest version is {latest_ver}")
        
        dprint(f"discord.py-self version {discord.__version__}")
        try:
            dprint(f"Tesseract version {pytesseract.get_tesseract_version()}")
        except (Exception, BaseException):
            dprint("Tesseract version check failed (using older/custom version)")
        if beta:
            tprint(f"{Fore.RED}[!] You are on the beta branch, please report all actual issues to the github repo")
        
        await self.update_files()
        asyncio.create_task(self.timecheck())
        
        # Sync cooldowns on startup instead of wasting a drop
        tprint(f"{Fore.CYAN}Initial Startup Sync: Requesting cooldowns...{Fore.RESET}")
        asyncio.create_task(self.sync_cooldowns_trigger(startup=True))
        
        dprint(f"Tofu Status: {tofu_enabled}")
        
        for guild_id in guilds:
            guild = self.get_guild(guild_id)
            if guild:
                try:
                    await guild.subscribe(typing=True, activities=False, threads=False, member_updates=False)
                except Exception:
                    tprint(f"{Fore.RED}Error when subscribing to server {guild_id}")
            else:
                tprint(f"{Fore.RED}Error: Server {guild_id} not found")

        asyncio.create_task(self.cooldown())
        asyncio.create_task(self.filewatch("keywords\\animes.txt"))
        asyncio.create_task(self.filewatch("keywords\\characters.txt"))
        asyncio.create_task(self.filewatch("keywords\\aniblacklist.txt"))
        asyncio.create_task(self.configwatch("config.json"))
        asyncio.create_task(self.filewatch("keywords\\charblacklist.txt"))
        
        if autodrop:
            asyncio.create_task(self.autodrop())
        if tofu_enabled and shouldsummon:
            asyncio.create_task(self.summon())
        if autofarm_cfg:
            asyncio.create_task(self.run_autofarm())
            
        self.ready = True

    async def on_message(self, message):
        cid = message.channel.id
        
        # Tofu Bot Monitoring
        if self.ready and tofu_enabled and message.author.id == 792827809797898240:
            if cid not in tofu_channels:
                return
            
            tofu_drop_match = re.search(r"(<@(\d*)> is summoning 2 cards!)|(Server activity has summoned)", message.content)
            if tofu_drop_match and self.tofutimer == 0:
                is_own_summon = tofu_drop_match.group(2) == str(self.user.id)
                await self._process_tofu_drop(message, is_own_summon)
            elif re.search(f"<@{str(self.user.id)}> grabbed a \\*\\*Fusion", message.content):
                self.tofutimer += 540
                self.missed -= 1
                self.collected += 1
                tprint(f"{Fore.BLUE}[Tofu - {message.channel.name}] Obtained Fusion Token{Fore.RESET}")
                if logcollection:
                    with open("log.txt", "a") as ff:
                        ff.write(f"{current_time()} - Fusion Token - {self.tofuurl}\n" if timestamp else f"Fusion Token - {self.tofuurl}\n")
            elif re.search(f"<@{str(self.user.id)}> (grabbed .* |fought off .* )", message.content):
                a = re.search(f"<@{str(self.user.id)}> .*:(.*):.*#(.*)` \u00b7 (.*) \u00b7 \\*\\*(.*)\\*\\*", message.content)
                if a:
                    self.tofutimer += 540
                    self.missed -= 1
                    self.collected += 1
                    tprint(f"{Fore.BLUE}[Tofu - {message.channel.name}] Obtained Card: {Fore.LIGHTMAGENTA_EX}{a.group(4)} from {a.group(3)} | Print #{a.group(2)}{Fore.RESET}")
                    if logcollection:
                        with open("log.txt", "a") as ff:
                            ff.write(f"{current_time()} - Tofu Card: {a.group(4)} from {a.group(3)} - {self.tofuurl}\n" if timestamp else f"Tofu Card: {a.group(4)} from {a.group(3)}- {self.tofuurl}\n")
                    
                    # Trigger unified success actions with character name
                    asyncio.create_task(self.on_grab_success(a.group(4)))
            return

        # General Guards
        if not self.ready or cid not in channels:
            return

        # Karuta Bot Monitoring
        if message.author.id == 646937666251915264:
            # Sync from kcd embed
            if message.embeds and any(e.author.name == "View Cooldowns" for e in message.embeds):
                # Verify this is a response to OUR command
                is_our_kcd = False
                if message.reference and message.reference.cached_message:
                    if message.reference.cached_message.author.id == self.user.id:
                        is_our_kcd = True
                
                # Fallback: check if our ID is in the description (handles both <@ID> and <@!ID>)
                desc = message.embeds[0].description or ""
                if str(self.user.id) in desc:
                    is_our_kcd = True
                
                if is_our_kcd:
                    await self._parse_kcd(message)
                return

            # Sync from "you must wait" messages
            if "you must wait" in message.content.lower():
                # Strictly ensure it's addressed to us
                is_for_us = False
                if f"<@{self.user.id}>" in message.content or f"<@!{self.user.id}>" in message.content:
                    is_for_us = True
                
                if is_for_us:
                    # Use the new robust parser for the text between backticks
                    inner_match = re.search(r"`(.*)`", message.content)
                    if inner_match:
                        ts = inner_match.group(1).lower()
                        wait_seconds = 0
                        h = re.search(r"(\d+)\s*h", ts)
                        if h: wait_seconds += int(h.group(1)) * 3600
                        m = re.search(r"(\d+)\s*m", ts)
                        if m: wait_seconds += int(m.group(1)) * 60
                        s = re.search(r"(\d+)\s*s", ts)
                        if s: wait_seconds += int(s.group(1))
                        
                        # Remove safety buffer as requested
                        wait_seconds += 0
                        
                        if "grabbing" in message.content.lower():
                            self.timer = wait_seconds
                            dprint(f"Synced Grab Cooldown from message: {self.timer}s")
                        elif "dropping" in message.content.lower():
                            self.next_drop_at = time.time() + wait_seconds
                            dprint(f"Synced Drop Cooldown from message: {wait_seconds}s")
                return

            if re.search("A wishlisted card is dropping!", message.content):
                dprint("Wishlisted card detected")

            own_drop = self._is_own_drop(message)
            
            # Quick permission check to avoid 403s
            perms = message.channel.permissions_for(message.guild.me)
            if not perms.send_messages: return

            if (self.timer == 0 or own_drop) and re.search(match, message.content):
                async with self.session.get(message.attachments[0].url) as resp:
                    if resp.status == 200:
                        image_bytes = await resp.read()
                        await self._process_karuta_drop(image_bytes, message, own_drop)
            
            elif re.search(f"<@{str(self.user.id)}> (took the \\*\\*.*\\*\\* card `.*`!|fought off .* and took the \\*\\*.*\\*\\* card `.*`!)", message.content):
                a = re.search(f"<@{str(self.user.id)}>.*took the \\*\\*(.*)\\*\\* card `(.*)`!", message.content)
                if a:
                    self.timer += 540
                    self.missed -= 1
                    self.collected += 1
                    tprint(f"{Fore.BLUE}[{message.channel.name}] Obtained Card: {Fore.LIGHTMAGENTA_EX}{a.group(1)}{Fore.RESET}")
                    if logcollection:
                        with open("log.txt", "a") as ff:
                            ff.write(f"{current_time()} - Card: {a.group(1)} - {self.url}\n" if timestamp else f"Card: {a.group(1)} - {self.url}\n")
                    
                    # Trigger unified success actions with character name
                    asyncio.create_task(self.on_grab_success(a.group(1)))
            
            elif message.content.startswith(f"<@{str(self.user.id)}>, your **Evasion"):
                dprint("Evasion blessing detected resetting grab cd")
                self.timer = 0
            
            elif message.content.startswith(f"<@{str(self.user.id)}>, your **Generosity"):
                dprint("Generosity blessing detected resetting drop cd")

    async def _process_karuta_drop(self, image_bytes, message, own_drop):
        try:
            if self._should_skip_grab(own_drop):
                return
    
            loop = asyncio.get_event_loop()
            card_count = get_card_count(image_bytes)
    
            # Launch ALL OCR tasks simultaneously in thread pool
            all_tasks = []
            for i in range(card_count):
                all_tasks.append(loop.run_in_executor(executor, pytesseract.image_to_string, karuta_get_char_top(image_bytes, i), "eng", OCR_CFG_TEXT))
                all_tasks.append(loop.run_in_executor(executor, pytesseract.image_to_string, karuta_get_char_bottom(image_bytes, i), "eng", OCR_CFG_TEXT))
                if cprint or own_drop:
                    all_tasks.append(loop.run_in_executor(executor, pytesseract.image_to_string, karuta_get_print(image_bytes, i), "eng", OCR_CFG_PRINT))
    
            results = await asyncio.gather(*all_tasks)
    
            stride = 3 if (cprint or own_drop) else 2
            
            self.url = message.attachments[0].url
            cid = message.channel.id
            emoji_map = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
    
            # Collect all prints first to allow fallback to lowest print
            printlist = []
            if cprint or own_drop:
                for i in range(card_count):
                    try:
                        prin = int(re.sub(r"\D", "", results[i * stride + 2]))
                        printlist.append(prin)
                    except:
                        printlist.append(9999999)

            best_score = -1 # -1: No hit, 0: Lowest Print, 1: Anime Hit, 2: Character Hit
            best_idx = 0
            best_reason = "Fallback"
            
            for i in range(card_count):
                base = i * stride
                character = results[base].strip().replace("\n", " ")
                anime = results[base + 1].strip().replace("\n", " ")
                prin = printlist[i] if (cprint or own_drop) else 9999999
    
                # Scoring: Character (2) > Anime (1) > Print/Fallback (0)
                score = -1
                hit_reason = ""
                
                if api.isSomething(character, self.chars, accuracy) and not api.isSomething(character, self.charblacklist, accuracy):
                    score = 2
                    hit_reason = f"Character: {character}"
                elif api.isSomething(anime, self.animes, accuracy) and not api.isSomething(anime, self.aniblacklist, blaccuracy):
                    if score < 1:
                        score = 1
                        hit_reason = f"Anime: {anime}"
                elif (cprint or own_drop) and prin <= pn:
                    if score < 0:
                        score = 0
                        hit_reason = f"Print # {prin}"

                # Update best card if this one is better or if it's our own drop and this print is lower
                if own_drop:
                    # On own drops, if scores are equal (e.g. both are score 0), pick the lower print
                    if score > best_score:
                        best_score = score
                        best_idx = i
                        best_reason = hit_reason
                    elif score == best_score and score <= 0: # Comparing prints for non-whitelist hits
                        if printlist[i] < printlist[best_idx]:
                            best_idx = i
                            best_reason = f"Lower Print # {printlist[i]}"
                else:
                    # On foreign drops, first hit of highest possible score wins
                    if score > best_score:
                        best_score = score
                        best_idx = i
                        best_reason = hit_reason
                        if score == 2: break # Instant win on character hit for foreign drops

            # Final check: if it was a hit OR if it's our own drop
            if best_score >= 0 or own_drop:
                if not own_drop and best_score < 0: return # Foreign drop with no hit
                
                if self._should_skip_grab(own_drop): return
                
                if best_score >= 0:
                    tprint(f"{Fore.GREEN}[{message.channel.name}] HIT: {best_reason}{Fore.RESET}")
                else:
                    best_idx = printlist.index(min(printlist))
                    tprint(f"{Fore.LIGHTMAGENTA_EX}[{message.channel.name}] Own drop — grabbing lowest print card (#{printlist[best_idx]}){Fore.RESET}")

                click_delay = grab_delay_own if own_drop else random.uniform(grab_delay_min, grab_delay_max)
                if message.components:
                    deadline = loop.time() + 4.0
                    while True:
                        if message.components and not message.components[0].children[0].disabled:
                            await asyncio.sleep(click_delay)
                            try:
                                await message.components[0].children[best_idx].click()
                            except: pass
                            await self.afterclick(message.channel)
                            return
                        if loop.time() > deadline: return
                        await asyncio.sleep(0.01)
                else:
                    perms = message.channel.permissions_for(message.guild.me)
                    if perms.add_reactions:
                        await asyncio.sleep(click_delay)
                        try:
                            await message.add_reaction(emoji_map[best_idx])
                        except: pass
                        self.timer += 60
                        self.missed += 1
                    return
    
        except Exception as e:
            dprint(f"Error in Karuta Drop Processing: {e}")
            if own_drop:
                tprint(f"{Fore.LIGHTMAGENTA_EX}[{message.channel.name}] Processing error, but it's your drop — emergency grabbing card 1{Fore.RESET}")
                try:
                    if message.components:
                        await message.components[0].children[0].click()
                    else:
                        await message.add_reaction("1️⃣")
                    await self.afterclick(message.channel)
                except: pass

    async def _process_tofu_drop(self, message, is_own_summon):
        async with self.session.get(message.attachments[0].url) as resp:
            if resp.status != 200:
                return
            image_bytes = await resp.read()

        cid = message.channel.id
        loop = asyncio.get_event_loop()
        emoji_map = ["1️⃣", "2️⃣"]

        all_tasks = []
        for i in range(2):
            all_tasks.append(loop.run_in_executor(executor, pytesseract.image_to_string, tofu_get_char_top(image_bytes, i), "eng", self.tcc))
            all_tasks.append(loop.run_in_executor(executor, pytesseract.image_to_string, tofu_get_char_bottom(image_bytes, i), "eng", self.tcc))
            if tofu_cprint:
                all_tasks.append(loop.run_in_executor(executor, pytesseract.image_to_string, tofu_get_print(image_bytes, i), "eng", OCR_CFG_PRINT))

        results = await asyncio.gather(*all_tasks)

        stride = 3 if tofu_cprint else 2
        charlist, anilist, printlist = [], [], []
        for i in range(2):
            base = i * stride
            charlist.append(results[base].strip().replace("\n", " "))
            anilist.append(results[base + 1].strip().replace("\n", " "))
            if tofu_cprint:
                try:
                    printlist.append(int(re.sub(r"\D", "", results[base + 2])))
                except ValueError:
                    printlist.append(9999999)

        vprint(f"Tofu Anilist: {anilist}")
        vprint(f"Tofu Charlist: {charlist}")

        hit_found = False
        for i in range(2):
            character = charlist[i]
            anime = anilist[i]
            prin = printlist[i] if tofu_cprint else 9999999

            hit, hit_reason = False, ""
            if api.isSomething(character, self.chars, accuracy) and not api.isSomething(character, self.charblacklist, accuracy) and not api.isSomething(anime, self.aniblacklist, blaccuracy):
                hit, hit_reason = True, f"[Tofu] Character: {character} from {anime}"
            elif api.isSomething(anime, self.animes, accuracy) and not api.isSomething(character, self.charblacklist, accuracy) and not api.isSomething(anime, self.aniblacklist, blaccuracy):
                hit, hit_reason = True, f"[Tofu] Anime: {anime} | {character}"
            elif tofu_cprint and prin <= pn and not api.isSomething(anime, self.aniblacklist, blaccuracy) and not api.isSomething(character, self.charblacklist, accuracy):
                hit, hit_reason = True, f"[Tofu] Print # {prin}"

            if hit:
                tprint(f"{Fore.GREEN}[Tofu - {message.channel.name}] Found {hit_reason}{Fore.RESET}")
                self.tofuurl = message.attachments[0].url
                if loghits:
                    with open("log.txt", "a") as ff:
                        ff.write(f"{current_time()} - {hit_reason} - {self.tofuurl}\n" if timestamp else f"{hit_reason} - {self.tofuurl}\n")
                click_delay = grab_delay_own if is_own_summon else random.uniform(grab_delay_min, grab_delay_max)
                await asyncio.sleep(click_delay)
                if isbutton(cid):
                    await message.components[0].children[i].click()
                    await self.tofuafterclick()
                else:
                    await message.add_reaction(emoji_map[i])
                    self.tofutimer += 60
                    self.missed += 1
                hit_found = True
                break

        if not hit_found and is_own_summon and grandom and not self.tofureact:
            self.tofureact = True
            tprint(f"{Fore.LIGHTMAGENTA_EX}[Tofu - {message.channel.name}] No cards found, defaulting to random")
            await asyncio.sleep(grab_delay_own)
            if isbutton(cid):
                await message.components[0].children[random.randint(0, 1)].click()
                await self.tofuafterclick()
            else:
                await message.add_reaction("❓")
                self.tofutimer += 60
                self.missed += 1

    async def run_autofarm(self):
        channel = self.get_channel(resourcechannel)
        if not channel:
            tprint(f"{Fore.RED}Autofarm - Error: Resource channel {resourcechannel} not found. Disabling autofarm.{Fore.RESET}")
            return
        
        # Wait a bit on startup to allow kcd sync to finish first
        await asyncio.sleep(random.uniform(10.0, 20.0))
        
        while True:
            async with channel.typing():
                await asyncio.sleep(random.uniform(0.2, 1))
            await channel.send("kw")
            try:
                reply = await self.wait_for("message", check=lambda m: m.author.id == 646937666251915264 and m.channel.id == resourcechannel, timeout=30)
                if "you do not have" in reply.content:
                    tprint("Autofarm - You dont have a permit")
                    await asyncio.sleep(3600)
                else:
                    h_match = re.search(r"(\d+) hours?", reply.content)
                    m_match = re.search(r"(\d+) minutes?", reply.content)
                    if h_match:
                        hours = int(h_match.group(1))
                        tprint(f"Autofarm - Waiting for {hours} hours to work again")
                        await asyncio.sleep(hours * 3600 + 5)
                    elif m_match:
                        minutes = int(m_match.group(1))
                        tprint(f"Autofarm - Waiting for {minutes} minutes to work again")
                        await asyncio.sleep(minutes * 60 + 5)
                    else:
                        tprint("Autofarm - Processing...")
                        await self.autofindresource()
                        await reply.components[0].children[1].click()
                        tprint("Autofarm - Worked successfully!")
                        await asyncio.sleep(12 * 3600 + 5)
            except asyncio.TimeoutError:
                dprint("Autofarm timed out waiting for response")
                await asyncio.sleep(60)

    async def autofindresource(self):
        channel = self.get_channel(resourcechannel)
        
        # Fast but Safe: Small jitter and typing
        async with channel.typing():
            await asyncio.sleep(random.uniform(0.5, 1.1))
        await channel.send("kn")
        
        try:
            # Wait for specific worker bot response
            reply = await self.wait_for("message", 
                check=lambda m: m.author.id == 1271850048707231744 and m.channel.id == resourcechannel,
                timeout=15)
            
            # Copy content exactly
            command_to_send = reply.content
            
            # Jittered delay for typing the command
            await asyncio.sleep(random.uniform(0.8, 1.6))
            async with channel.typing():
                await asyncio.sleep(random.uniform(0.6, 1.2))
            await channel.send(command_to_send)
            
            # Final pause before kw
            await asyncio.sleep(random.uniform(1.2, 2.2))
            await channel.send("kw")
            
        except asyncio.TimeoutError:
            dprint("Autofarm - Worker bot didn't respond to kn")

    async def autodrop(self):
        # Initial drop schedule (only if not already set by on_ready)
        if self.next_drop_at == 0.0:
            self.next_drop_at = time.time() + dropdelay + random.randint(randmin, randmax)
        
        while True:
            await asyncio.sleep(1)
            now = time.time()
            
            # If a drop is scheduled and it's time to fire
            if self.next_drop_at > 0 and now >= self.next_drop_at:
                # Extra check: if we are currently on grab cooldown, wait for it
                if self.timer > 0:
                    self.next_drop_at = now + self.timer + 2 # wait for grab cd + buffer
                    continue

                # Pick a random channel from the list for this drop
                channel_id = random.choice(autodropchannel) if isinstance(autodropchannel, list) else autodropchannel
                channel = self.get_channel(channel_id)
                
                if not channel:
                    tprint(f"{Fore.RED}Error: Could not find autodrop channel {channel_id}")
                    self.next_drop_at = now + 60
                    continue

                self.next_drop_at = 0.0 # processing drop
                async with channel.typing():
                    await asyncio.sleep(random.uniform(0.5, 1.5))
                await channel.send("kd")
                tprint(f"{Fore.LIGHTWHITE_EX}Auto Dropped Cards in {channel.name}")
                
                # Schedule next drop
                self.next_drop_at = time.time() + dropdelay + random.randint(randmin, randmax)

    async def summon(self):
        channel = self.get_channel(summonchannel)
        while True:
            await asyncio.sleep(tofu_delay + random.randint(tofu_min, tofu_max))
            if self.tofutimer != 0:
                await asyncio.sleep(self.tofutimer)
            async with channel.typing():
                await asyncio.sleep(random.uniform(0.2, 1))
            await channel.send("ts")
            tprint(f"{Fore.LIGHTWHITE_EX}Summoned Cards")

    def _get_activity_channel(self):
        """Returns the designated channel for secondary commands like kv/kcd."""
        target_id = 1238089297639505955
        return self.get_channel(target_id)

    async def afterclick(self, channel):
        dprint(f"Clicked on Button")
        self.timer += 60
        self.missed += 1
        
        # Sync cooldowns after every attempt to get accurate timing
        asyncio.create_task(self.sync_cooldowns_trigger())

    async def sync_cooldowns_trigger(self, startup=False):
        # Use a designated activity channel
        channel = self._get_activity_channel()
        if not channel: return
        
        # Use a faster delay for startup to ensure we sync before the first drop
        delay_range = (2.0, 4.0) if startup else (5.0, 8.0)
        
        async with channel.typing():
            await asyncio.sleep(random.uniform(*delay_range))
        await channel.send("kcd")

    async def _parse_kcd(self, message):
        """Parses the kcd embed from Karuta to sync timers."""
        if not message.embeds: return
        embed = message.embeds[0].to_dict()
        desc = embed.get("description", "")
        if "Showing cooldowns for" not in desc or f"<@{self.user.id}>" not in desc: return

        # Helper to parse "X hours Y minutes Z seconds" into seconds
        def parse_time_str(time_str):
            time_str = time_str.lower()
            if "currently available" in time_str:
                return 0
            
            total_seconds = 0
            # Look for hours
            h = re.search(r"(\d+)\s*h", time_str)
            if h: total_seconds += int(h.group(1)) * 3600
            # Look for minutes
            m = re.search(r"(\d+)\s*m", time_str)
            if m: total_seconds += int(m.group(1)) * 60
            # Look for seconds
            s = re.search(r"(\d+)\s*s", time_str)
            if s: total_seconds += int(s.group(1))
            
            return total_seconds if total_seconds > 0 else 0

        # Extract Grab line
        grab_match = re.search(r"\*\*Grab\*\* is (.*)", desc)
        if grab_match:
            new_timer = parse_time_str(grab_match.group(1))
            if new_timer > self.timer: # Only update if it's longer
                self.timer = new_timer
                dprint(f"Synced Grab Cooldown: {self.timer}s")

        # Extract Drop line
        drop_match = re.search(r"\*\*Drop\*\* is (.*)", desc)
        if drop_match:
            drop_wait = parse_time_str(drop_match.group(1))
            if drop_wait > 0:
                self.next_drop_at = time.time() + drop_wait
                dprint(f"Synced Drop Cooldown: {drop_wait}s")
            else:
                # If drop is available, ensure autodrop isn't blocked by priority window
                self.next_drop_at = 0.0

    async def on_grab_success(self, character_name):
        """Unified handler for successful card acquisition."""
        # Use a designated activity channel instead of the grab channel
        channel = self._get_activity_channel()
        if not channel: return
        
        # Check if the character is in our whitelist
        is_whitelisted = False
        if character_name:
            # Use api.isSomething for a robust match check
            if api.isSomething(character_name, self.chars, accuracy):
                is_whitelisted = True

        # Safer delays to avoid Discord 429 rate limits
        await asyncio.sleep(random.uniform(3.0, 5.0))
        await channel.send("kv")
        
        await asyncio.sleep(random.uniform(4.0, 7.0))
        # Use kt imp for whitelisted, kt b for others
        cmd = "kt imp" if is_whitelisted else "kt b"
        await channel.send(cmd)

    async def tofuafterclick(self):
        dprint(f"Clicked on Button")
        self.tofutimer += 60
        self.missed += 1
        self.tofureact = False

    async def cooldown(self):
        while True:
            await asyncio.sleep(1)
            if self.timer > 0:
                self.timer -= 1
            if self.tofutimer > 0:
                self.tofutimer -= 1
            
            if title:
                status = f"Karuta Sniper {v} - Collected {self.collected} - Missed {self.missed}"
                if self.timer > 0: status += f" - Cooldown: {self.timer}s"
                if self.tofutimer > 0: status += f" - Tofu CD: {self.tofutimer}s"
                if self.timer == 0 and self.tofutimer == 0: status += " - Ready"
                os.system(f"title {status}")

    async def update_files(self):
        with open("keywords\\characters.txt") as ff: self.chars = ff.read().splitlines()
        with open("keywords\\animes.txt") as ff: self.animes = ff.read().splitlines()
        with open("keywords\\aniblacklist.txt") as ff: self.aniblacklist = ff.read().splitlines()
        with open("keywords\\charblacklist.txt") as ff: self.charblacklist = ff.read().splitlines()
        tprint(f"{Fore.MAGENTA}Loaded {len(self.animes)} animes, {len(self.aniblacklist)} blacklisted animes, {len(self.chars)} characters, {len(self.charblacklist)} blacklisted characters")

    async def filewatch(self, path):
        bruh = api.FileWatch(path)
        while True:
            await asyncio.sleep(2)
            if bruh.watch():
                await self.update_files()

    async def configwatch(self, path):
        bruh = api.FileWatch(path)
        while True:
            await asyncio.sleep(1)
            if bruh.watch():
                with open("config.json") as ff:
                    config = json.load(ff)
                    global accuracy, drop_priority_window, grab_delay_own, grab_delay_min, grab_delay_max, autodropchannel
                    accuracy = float(config["accuracy"])
                    drop_priority_window = int(config.get("drop_priority_window", 650))
                    grab_delay_own = float(config.get("grab_delay_own", 0.05))
                    grab_delay_min = float(config.get("grab_delay_min", 0.2))
                    grab_delay_max = float(config.get("grab_delay_max", 0.5))
                    autodropchannel = config.get("autodropchannel", autodropchannel)
                    if tofu_enabled: self.tcc = config["tofu"]["tcc"]
                    dprint(f"Updated config from {path}")


def current_time():
    return datetime.now().strftime("%H:%M:%S")


def isbutton(data):
    return data in BUTTON_CHANNELS


def tprint(message):
    if timestamp:
        print(f"{Fore.LIGHTBLUE_EX}{current_time()} | {Fore.RESET}{message}")
    else:
        print(message)


def dprint(message):
    if debug:
        tprint(f"{Fore.LIGHTRED_EX}Debug{Fore.BLUE} - {message}")


def vprint(message):
    if verbose:
        tprint(f"{Fore.CYAN}{message}{Fore.WHITE}")


# update_check is now handled inline in on_ready


if __name__ == "__main__":
    if token == "":
        inp = input(f"{Fore.RED}No token found, would you like to find tokens from your pc? (y/n): {Fore.RESET}")
        if inp == "y":
            token = api.get_tokens(False)
            if token:
                token = token[0].split(": ")[1]
            else:
                print("No tokens found.")
                sys.exit()

    client = Main(guild_subscriptions=False)
    tprint(f"{Fore.GREEN}Starting Bot{Fore.RESET}")
    try:
        client.run(token)
    except KeyboardInterrupt:
        tprint(f"{Fore.RED}Ctrl-C detected\nExiting...{Fore.RESET}")
        asyncio.run(client.close())
        sys.exit()
