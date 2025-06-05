import discord
import os
import datetime
import json
import asyncio

# SANITIZE FOLDER NAMES
def sanitize_name(name: str) -> str:

    """
    Discord channel names are limited to lowercase, alphanumeric + hyphens/underscores,
    but guild names can contain spaces or emojis, this replaces spaces with underscores
    and strips out any os‐path‐separator characters.
    """

    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    out = name.replace(' ', '_')
    for ch in invalid_chars:
        out = out.replace(ch, '')
    return out

# MAIN BOT CLASS
class AyeBotBackup(discord.Client):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # TEMPORARY - EVERY GUILD THE BOT IS IN GETS BACKED UP, NO MANUAL CONTROL YET :(
 
    async def on_ready(self):
        print(f"🟢 Logged in as {self.user} ({self.user.id}).")

        await asyncio.sleep(2) # SMALL DELAY BEFORE OUTPUT SPAM FOR PERSONAL PREFERENCE :3
        await self.start_backup()

    # LOOP THROUGH EVERY GUILD AND EVERY TEXT CHANNEL
    async def start_backup(self):

        """
        Data currently fetched:
        - Author ID
        - Author Username
        - Author Discriminator (Used by bots)
        - Message ID
        - Message Timestamp
        - Message Content
        - Attached CDN files
        - Reactions
        - Edited boolean

        Data to be fetched hopefully soon:
        - Deleted boolean
        """

        base_backup_folder = os.path.join(os.getcwd(), "backup")

        for guild in self.guilds:

            # CREATE A FOLDER FOR THIS GUILD
            guild_folder_name = f"{sanitize_name(guild.name)}_{guild.id}"
            guild_folder_path = os.path.join(base_backup_folder, guild_folder_name)
            os.makedirs(guild_folder_path, exist_ok=True)
            print(f"🔵 Backing up guild: {guild.name} ({guild.id}) → {guild_folder_path}.")

            # SET UP EMPTY DICT FOR BACKUP INFO
            info_file_path = os.path.join(guild_folder_path, "backup_info.json")
            backup_info: dict[int, int] = {}

            # ATTEMPT TO EXTRACT BACKUP INFO FROM JSON
            if os.path.isfile(info_file_path):
                try:
                    with open(info_file_path, 'r', encoding="utf-8") as f:\
                        raw = json.load(f)
                    
                    # CONVERT JSON KEYS (STRINGS) TO INTEGERS
                    for cid_str, ts in raw.items():
                        try:
                            cid = int(cid_str)
                            backup_info[cid] = int(ts)
                        except ValueError:
                            continue
                
                # IF FILE IS MALFORMED OR UNREADABLE, START FROM BEGINNING
                except (json.JSONDecodeError, OSError):
                    print(f"🟡 Warning: Info file ({info_file_path}) is unreadable or incorrectly formatted, starting backup from zero.")

            # ITERATE THROUGH EVERY TEXT CHANNEL IN THE GUILD
            for channel in guild.text_channels:

                # ONLY BACK UP CHANNELS THE BOT CAN READ
                if not channel.permissions_for(guild.me).read_message_history:
                    print(f"    🟡 Warning: Skipping {channel.name} ({channel.id}) – no Read Message History permission.")
                    continue

                # CREATE CHANNEL FOLDER AND ATTACHMENTS SUBFOLDER
                channel_folder_name = f"{sanitize_name(channel.name)}_{channel.id}"
                channel_folder_path = os.path.join(guild_folder_path, channel_folder_name)

                attachments_folder = os.path.join(channel_folder_path, "attachments")
                os.makedirs(attachments_folder, exist_ok=True)

                # OPEN A JSONL FILE TO WRITE EVERY MESSAGE AS ONE JSON OBJECT PER LINE
                messages_file_path = os.path.join(channel_folder_path, "messages.jsonl")
                print(f"    🔵 Backing up channel: {channel.name} ({channel.id}) → {channel_folder_path}.")

                # DETERMINE WHERE TO START (FULL OR INCREMENTAL)
                existing_ms = backup_info.get(channel.id, 0)
                if existing_ms > 0:
                    
                    # CONVERT STORED UNIX-MS INTO UTC DATETIME
                    after_dt = datetime.datetime.fromtimestamp(existing_ms / 1000.0, tz=datetime.timezone.utc)
                    print(f"        🔵 Resuming from {after_dt.isoformat()} (ms = {existing_ms}).")
                else:
                    after_dt = None # FETCH FROM VERY BEGINNING

                newest_ms = existing_ms # WILL BE UPDATED AS NEW MESSAGES ARE PROCESSED

                # OPEN messages.jsonl IN APPPEND MODE IF IT ALREADY EXISTS, OTHERWISE WRITE MODE
                mode = 'a' if os.path.isfile(messages_file_path) else 'w'
                with open(messages_file_path, mode, encoding="utf-8") as msg_file:

                    # FETCH EVERY MESSAGE (oldest_firt=True TO PRESERVE CHRONOLOGICAL ORDER)
                    async for msg in channel.history(
                        limit=None,
                        oldest_first=True,
                        after=after_dt # IF APPENDING, OLD MESSAGES ARE NOT REPROCESSED
                    ):

                        # BUILD A LIST OF ATTACHMENTS AND DOWNLOAD EACH ONE
                        attachments_info = []
                        for attachment in msg.attachments:

                            # PREFIX LOCAL FILENAME WITH attachment.id TO AVOID COLLISIONS
                            local_filename = f"{attachment.id}_{sanitize_name(attachment.filename)}"
                            local_path = os.path.join(attachments_folder, local_filename)

                            # SAVE THE ATTACHMENT LOCALLY
                            try:
                                await attachment.save(local_path)
                                print(f"        🟢 Saved attachment {attachment.filename} → {local_path}.")
                            except Exception as e:
                                print(f"        🟡 Warning: Failed to download {attachment.url}: {e}.")
                                local_path = None

                            attachments_info.append({
                                "id": attachment.id,
                                "filename": attachment.filename,
                                "url": attachment.url, # ORIGINAL CDN LINK
                                "local_path": local_path, # LOCAL FILE LINK
                            })

                        # BUILD A LIST OF REACTIONS AND WHO REACTED
                        reactions_info = []

                        for reaction in msg.reactions:
                            try:
                                # reaction.users() RETURNS AN AsyncIterator OF ALL USERS WHO CLICKED THIS REACTION
                                users_list = [user async for user in reaction.users(limit=None)]
                            except Exception as e:
                                # IN CASE OF A PERMISSION/RATE-LIMIT ERROR, RECORD AN EMPTY LIST
                                print(f"        🟡 Warning: Could not fetch users for reaction {reaction.emoji} on message {msg.id}: {e}")
                                users_list = []

                            # TURN EACH USER INTO A SMALL DICT
                            reactors = [
                                {
                                    "id": user.id,
                                    "name": user.name,
                                    "discriminator": user.discriminator
                                }
                                for user in users_list
                            ]

                            reactions_info.append({
                                "emoji": str(reaction.emoji),
                                "count": reaction.count,
                                "users": reactors
                            })

                        # DETERMINE IF MESSAGE WAS EVER EDITED
                        edited_flag = msg.edited_at is not None

                        # BUILD JSON-SERIALIZABLE MESSAGE DICT
                        message_data = {
                            "id": msg.id,
                            "author": {
                                "name": msg.author.name,
                                "discriminator": msg.author.discriminator,
                                "id": msg.author.id
                            },
                            "timestamp": msg.created_at.isoformat(),
                            "content": msg.content,
                            "attachments": attachments_info,
                            "edited": edited_flag,
                            "reactions": reactions_info
                        }

                        # WRITE IT AS ONE JSON-ENCODED LINE
                        msg_file.write(json.dumps(message_data, ensure_ascii=False))
                        msg_file.write("\n")

                        # UPDATE NEWEST TIMESTAMP (IN MS)
                        ms = int(msg.created_at.timestamp() * 1000)
                        if ms > newest_ms:
                            newest_ms = ms

                # UPDATE IN-MEMORY DICT WITH NEWEST TIMESTAMP
                backup_info[channel.id] = newest_ms

                print(f"    🟢 Finished backing up channel: {channel.name} ({channel.id}).")

            # CONVERT dict[int, int] TO dict[str, int] FOR VALID JSON
            to_dump = { str(cid): ts for cid, ts in backup_info.items() }

            # DUMP TIMESTAMP TO JSON FILE
            with open(info_file_path, 'w', encoding="utf-8") as f:
                json.dump(to_dump, f, indent=2)

            print(f"    🟢 Updated timestamps → {info_file_path}.")
            print(f"🟢 Finished backing up guild: {guild.name} ({guild.id}).")

        print("🟢 Backup complete for all guilds.")

# ENTRYPOINT
if __name__ == "__main__":

    # INPUT YOUR OWN TOKEN IF YOU WISH TO USE THIS TOOL
    TOKEN = ""

    # intents.guilds AND intents.messages ARE ENABLED BY DEFAULT IN Intents.default()
    intents = discord.Intents.default()
    intents.message_content = True
    client = AyeBotBackup(intents=intents)
    client.run(TOKEN)
