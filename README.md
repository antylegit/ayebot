# AyeBot - A Fun Discord Utility Bot

A utility-focused/experimental Discord bot written in Python using [Discord.py](https://github.com/Rapptz/discord.py). (pronounced "eye")

I initially made this bot in early 2020 in order to visualize colors and convert between digital color notation formats (and because I wanted an excuse to learn a new technology - it was my very first Discord bot). Since then I've slowly been adding new features and expanding functionality whenever I felt like it, which quickly turned into spaghetti-code as the foundation all the features were based on was a tad dreadful (again, first ever bot I made and all).

Recently, prompted by the increasing difficulty of trying to add more features, I decided to rewrite the entire bot from scratch in order to make it much more scalable and overall more professional. This repository is assigned to that overhaul, AyeBot v2 if you wish.

**Note**: As with most of my projects, this is done entirely for fun and to solve problems **I** encounter. All features are grouped into different [cogs](https://github.com/antylegit/ayebot/tree/main/cogs), feel free to pick and choose whichever ones you like and add them to your own discord bot (complying with the [license](https://github.com/antylegit/ayebot/blob/main/LICENSE) in the process). Below is a list of features currently available in this repository: 

## Features:
- **[Server Backup](https://github.com/antylegit/ayebot/blob/main/cogs/backup.py)** - Backs up selected guilds/servers and channels within a specified directory. Optionally archives all CDN files or compares changes in previously archived data.

## Coming soon:
- **Color Tools** - Color/Palette visualization, generation and format conversion.
- **Message Edit/Deletion Tracking** - Tracks and notifies message edits or deletions within a specified server or channel.
- **Coinflips & RNG** - Run a command for when you're feeling indecisive :P
- **Streaks** - Incentivize people to talk in your Discord server Duolingo-style (for legal reasons this feature is *not* "Duolingo"-style).
- **Gambling** - Gamifying dark patterns to make you lose money for fun. All virtual currency is completely fake and has no ties to real, tangible assets.
- **Fun & Misc.** - Whatever other insignificant nonsense I felt like adding.

All features listed above will be progressively expanded throughout the project's development.
