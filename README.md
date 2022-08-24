# Utah Esports Bot
This is a discord bot for University of Utah League of Legends Esports. We welcome student contributions for new engineers looking to get their feet wet!

*If you know what you're doing, feel free to skip around as much as you need.*

**Cool stuff includes:**
- A fully built Inhouse system, including a queue for joining games, automatic team assignment, W/L and point tracking, and a leaderboard
- Integration with the Riot API for a soloqueue leaderboard (WIP) and rewards for playing games with other community members

**Coming Soon TM:**
- Currency system with rewards for being active in the community, playing games, and supporting the teams
- Currency betting on pro games and rewards
---
## Running the Bot
There are 2 ways to run the bot:
### Docker (preferred)
There is docker tooling for both the bot and the database, along with a compose file, at the root of the repository. To bring everything up:
```sh
# Build with your new changes (you need to run this if you've changed source code)
docker-compose build bot

# Attached, so you can see logging:
docker-compose up bot

# Detached:
docker-compose up -d bot
```
And down:
```sh
docker-compose down -v
```
The compose file handles all networking and config. Some quick points to be aware of:
- The ONLY port that should need to be exposed (especially in a deployed bot) should be `443` to be able to talk to the Discord/Riot APIs. **You should not need to expose another port.** This is especially important for the database, which should only be networked to the bot container.
- The compose file assumes that you have a `.env.dev` or `.env.prod` file at the root of the repository with environment config. Here's a sample config for a local testing container:
```env
DB_HOST='localhost'
DB_NAME='inhouse-bot-db'
DB_USER='utahesports'
DB_PASS='starforger'
GUILD_ID='<Guild ID for the discord server you're testing in>'
Discord_Key='<Discord API Key>'
Riot_Api_Key='<Riot API Key>'
```

You can find more details on docker in the "For Students" section under "Contributing" below.

### Local Terminal
You can simply run the bot from your command line using
```sh
python3 bot.py
```
Be aware that this means you need to have a database set up for the bot to talk to, either through the database container in the repo or a local postgres instance.

---
## Contributing
- Docs for the `pycord` Discord API wrapper can be found [here](https://docs.pycord.dev/en/master/index.html)
- Docs for the `riotwatcher` Riot API wrapper can be found [here](https://riot-watcher.readthedocs.io/en/latest/index.html)

We follow a standard PR-based contribution workflow. Create a branch off of main, make something cool, and then submit a PR with your changes and ask for a review from a maintainer.

When working, please follow [Conventional Commit](https://www.conventionalcommits.org/en/v1.0.0/#summary) patterns as much as possible.

### Adding a command
1. Create the handling for your command in the appropriate file in the `/command_handlers` directory (or create a new one if needed)
2. Add your command to the top level in `bot.py`. Note that the name of the function is what the command will need to be typed as in discord:
```python
# This command can be triggered with `/wonko_is_the_best_ekko` in a discord channel
@bot.slash_command(description="Tell everyone who the best Ekko in the server is.")
async def wonko_is_the_best_ekko(ctx):
    your_handler.do_some_work()
```

### For Students
We're so glad you want to help with the bot! If you're completely new (or maybe need a refresher) to any of the tools mentioned so far, here's a quick list of useful documentation:
- [Python](https://www.python.org/doc/)
- [Docker](https://docs.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Postgres](https://www.postgresql.org/docs/14/index.html)
- [git](https://git-scm.com/doc)

And some useful tools that we recommend for beginners and experienced engineers alike:
- [Git Fork](https://git-fork.com/) If you prefer a GUI, although knowing git from the command line is a worthwhile skill!
- [PGAdmin](https://www.pgadmin.org/) Makes checking your databases much less painful.
- [VSCode](https://code.visualstudio.com/) and the [Python Extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python) One of the bestt all-round dev environments out there
- [iTerm2](https://iterm2.com/) if you're a mac user

## Troubleshooting
### No python print output in container
By default, python outputs to `sys.stdout` instead of flushing. You can override this behavior by setting `PYTHONUNBUFFERED=1` in your environment config.