import discord
from discord.ext import commands
from discord import app_commands
import os
import re
from datetime import datetime
from internetarchive import upload
import asyncio
from typing import Optional

DISCORD_BOT_TOKEN = "YOUR_DISCORD_BOT_TOKEN"

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Set up the bot with an activity status
activity = discord.Activity(
    name="github.com/Andres9890/Archive.org-uploading-Discord-Bot",
    type=discord.ActivityType.playing,
)
bot.activity = activity

def generate_unique_id(base_id):
    """Generate a unique identifier using the base ID and timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{base_id}-{timestamp}"

@bot.event
async def on_ready():
    # Sync the slash commands when the bot is ready
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

@bot.tree.command(name="upload", description="Upload up to 10 files to Archive.org")
@app_commands.describe(
    file1="Required file (up to 100MB)",
    file2="Optional file (up to 100MB)",
    file3="Optional file (up to 100MB)",
    file4="Optional file (up to 100MB)",
    file5="Optional file (up to 100MB)",
    file6="Optional file (up to 100MB)",
    file7="Optional file (up to 100MB)",
    file8="Optional file (up to 100MB)",
    file9="Optional file (up to 100MB)",
    file10="Optional file (up to 100MB)",
)
async def upload_files(
    interaction: discord.Interaction,
    file1: discord.Attachment,
    file2: Optional[discord.Attachment] = None,
    file3: Optional[discord.Attachment] = None,
    file4: Optional[discord.Attachment] = None,
    file5: Optional[discord.Attachment] = None,
    file6: Optional[discord.Attachment] = None,
    file7: Optional[discord.Attachment] = None,
    file8: Optional[discord.Attachment] = None,
    file9: Optional[discord.Attachment] = None,
    file10: Optional[discord.Attachment] = None
):
    """
    Slash command that uploads up to 10 attachments to Archive.org.
    The first file is required, while the remaining 9 are optional.
    """

    # Defer the interaction since uploading can take time
    await interaction.response.defer()

    # Gather all provided (non-None) attachments
    all_files = [file1, file2, file3, file4, file5, file6, file7, file8, file9, file10]
    attachments = [f for f in all_files if f is not None]

    # Check if we actually have any attachments (should always have at least one: file1)
    if not attachments:
        await interaction.followup.send("No files attached. Please provide at least one file.")
        return

    # Check each attachment's size and save them locally
    file_paths = []
    for attachment in attachments:
        if attachment.size > 100 * 1024 * 1024:
            await interaction.followup.send(f"File `{attachment.filename}` exceeds the 100MB limit.")
            return

        file_path = f"./{attachment.filename}"
        await attachment.save(file_path)
        file_paths.append(file_path)

    file_count = len(file_paths)
    await interaction.followup.send(f"Uploading {file_count} file(s) to Archive.org...")

    # Generate an item identifier
    #  - If only one file, use the sanitized filename as the base
    #  - If multiple, use a "discord-upload-{username}" style base
    if file_count == 1:
        base_item_id = re.sub(r'[^a-z0-9._-]', '_', attachments[0].filename.lower())
    else:
        base_item_id = f"discord-upload-{interaction.user.name.replace(' ', '_')}".lower()

    item_id = generate_unique_id(base_item_id)

    # Prepare metadata
    file_list_str = "\n".join([os.path.basename(fp) for fp in file_paths])
    metadata = {
        "scanner": "Discord Bot Upload",
        "collection": "opensource_media",
    }

    if file_count == 1:
        # Single file: use the filename in the title/description
        metadata.update({
            "title": attachments[0].filename,
            "description": f"Uploaded via Discord bot by {interaction.user.name}: {attachments[0].filename}",
        })
    else:
        # Multiple files: generic title, include a list in description
        metadata.update({
            "title": f"Files uploaded by {interaction.user.name}",
            "description": (
                f"Uploaded via Discord bot by {interaction.user.name}.\n\n"
                f"Uploaded files:\n{file_list_str}"
            ),
        })

    # Run the upload in a separate thread
    def do_upload():
        upload(identifier=item_id, files=file_paths, metadata=metadata)

    try:
        await asyncio.to_thread(do_upload)
        # Notify success
        if file_count == 1:
            await interaction.followup.send(
                f"File successfully uploaded to Archive.org! [View it here](https://archive.org/details/{item_id})"
            )
        else:
            await interaction.followup.send(
                f"Files successfully uploaded to Archive.org! [View them here](https://archive.org/details/{item_id})"
            )
    except Exception as e:
        await interaction.followup.send(f"An error occurred during upload: {e}")
    finally:
        # Clean up the saved files
        for path in file_paths:
            if os.path.exists(path):
                os.remove(path)

bot.run(DISCORD_BOT_TOKEN)
