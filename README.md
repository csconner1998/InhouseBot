# Inhouse Bot
Inhouse bot for University of Utah League of Legends Esports.

# Contributing
## Adding a command
1. Create a handler function for your command in the `/inhouse/command_handlers` directory in the correct file (or create a new one if necessary)
2. Add your command to the top level in `bot.py`. Note that the name of the function is what the command will need to be typed as in discord:
```python
# This command can be triggered with `/wonkoIsTheBestEkko` in a discord channel
@bot.command(help='Describe your command here')
async def wonkoIsTheBestEkko(ctx):
    handler.hesJustSoGood(ctx, db_handler=db_handler)
```
3. Add a test for your command.