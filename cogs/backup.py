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
        print(f"🟢 Logged in as {self.user} ({self.user.id})")

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

        Data to be fetched hopefully soon:
        - Reactions
        - Edited boolean
        """

        base_backup_folder = os.path.join(os.getcwd(), "backup")

        for guild in self.guilds:

            # CREATE A FOLDER FOR THIS GUILD
            guild_folder_name = f"{sanitize_name(guild.name)}_{guild.id}"
            guild_folder_path = os.path.join(base_backup_folder, guild_folder_name)
            os.makedirs(guild_folder_path, exist_ok=True)
            print(f"🔵 Backing up guild: {guild.name} ({guild.id}) → {guild_folder_path}")

            # ITERATE THROUGH EVERY TEXT CHANNEL IN THE GUILD
            for channel in guild.text_channels:
              
                # ONLY BACK UP CHANNELS THE BOT CAN READ
                if not channel.permissions_for(guild.me).read_message_history:
                    print(f"    🟡 Skipping {channel.name} ({channel.id}) – no Read Message History permission")
                    continue

                # CREATE CHANNEL FOLDER AND ATTACHMENTS SUBFOLDER
                channel_folder_name = f"{sanitize_name(channel.name)}_{channel.id}"
                channel_folder_path = os.path.join(guild_folder_path, channel_folder_name)

                attachments_folder = os.path.join(channel_folder_path, "attachments")
                os.makedirs(attachments_folder, exist_ok=True)

                # OPEN A JSONL FILE TO WRITE EVERY MESSAGE AS ONE JSON OBJECT PER LINE
                messages_file_path = os.path.join(channel_folder_path, "messages.jsonl")
                print(f"    🔵 Backing up channel: {channel.name} ({channel.id}) → {channel_folder_path}")

                with open(messages_file_path, "w", encoding="utf-8") as msg_file:

                    # FETCH EVERY MESSAGE (oldest_firt=True TO PRESERVE CHRONOLOGICAL ORDER)
                    async for msg in channel.history(limit=None, oldest_first=True):

                        # BUILD A LIST OF ATTACHMENTS AND DOWNLOAD EACH ONE
                        attachments_info = []
                        for attachment in msg.attachments:

                            # PREFIX LOCAL FILENAME WITH attachment.id TO AVOID COLLISIONS
                            local_filename = f"{attachment.id}_{sanitize_name(attachment.filename)}"
                            local_path = os.path.join(attachments_folder, local_filename)

                            # SAVE THE ATTACHMENT LOCALLY
                            try:
                                await attachment.save(local_path)
                                print(f"        🟢 Saved attachment {attachment.filename} → {local_path}")
                            except Exception as e:
                                print(f"        🟡 Failed to download {attachment.url}: {e}")
                                local_path = None

                            attachments_info.append({
                                "id": attachment.id,
                                "filename": attachment.filename,
                                "url": attachment.url, # ORIGINAL CDN LINK
                                "local_path": local_path, # LOCAL FILE LINK
                            })

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
                            "attachments": attachments_info
                        }

                        # WRITE IT AS ONE JSON-ENCODED LINE
                        msg_file.write(json.dumps(message_data, ensure_ascii=False))
                        msg_file.write("\n")

                print(f"    🟢 Finished backing up channel: {channel.name} ({channel.id})")

        print("🟢 Backup complete for all guilds.")

# ENTRYPOINT
if __name__ == "__main__":

    # INPUT YOUR OWN TOKEN IF YOU WISH TO USE THIS TOOL :P
    TOKEN = ""

    # intents.guilds AND intents.messages ARE ENABLED BY DEFAULT IN Intents.default()
    intents = discord.Intents.default()
    intents.message_content = True
    client = AyeBotBackup(intents=intents)
    client.run(TOKEN)
