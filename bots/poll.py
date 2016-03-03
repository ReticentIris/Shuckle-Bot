import asyncio
from shuckle.command import command
import humanfriendly
import json
import os
import pygal
from pygal.style import Style
import time
import traceback

DiscordStyle = Style(
    background='#ffffff',
    plot_background='#ffffff',
    font_family='Open Sans',
    foreground='#546e7a',
    foreground_strong='#546e7a',
    foreground_subtle='#546e7a',
    colors=('#738bd7', '#1abc9c', '#3498db', '#e91e63', '#f1c40f')
)

HELP = """
__Poll Commands:__

Create a new poll in the current channel:
```
@{bot_name} poll make {{
    "title": <string>,
    "duration": <integer|seconds>,
    "options": [<string>]
}}
```
Shorthand for the above (does not support colons in options):
```
@{bot_name} poll make <title>:<duration>:<option>[:<option>]
```
Cast your vote for the current poll:
```
@{bot_name} poll vote <integer>
```
Delete the current poll and don't show the results [U:MM]:
```
@{bot_name} poll delete
```
"""

def make_chart(title, values):
    chart = pygal.Pie(
        title=title,
        legend_at_bottom=True,
        style=DiscordStyle
    )

    for value in values:
        chart.add('{} ({})'.format(value[0], value[1]), value[1])

    now = time.time()
    path = os.path.join('/tmp', '{}.png'.format(now))

    chart.render_to_png(path)

    return path

class Poll(object):
    def __init__(self, title, options):
        self.title = title
        self.votes = {}
        self.options = options
        self.closed = False

    def vote(self, option, uid):
        self.votes[uid] = option

    def get_results(self):
        results = [0 for x in self.options]

        for x in self.votes:
            results[self.votes[x] - 1] += 1

        if sum(results) == 0:
            return None

        return zip(self.options, results)

    def get_top(self):
        results = self.get_results()

        if results is None:
            return None

        return sorted(results, key=lambda x: x[1], reverse=True)

class PollBot(object):
    __group__ = 'poll'
    polls = {}

    def __init__(self, client):
        self.client = client

    @command()
    async def help(self, message):
        await self.client.say(HELP.strip().format(bot_name=self.client.user.name))

    @command()
    async def make(self, message):
        # Only one poll per channel
        if message.channel in self.polls:
            return
        try:
            data = message.args

            try:
                data = json.loads(data)
            except:
                # Shorthand
                try:
                    data = data.split(':')
                    duration = int(humanfriendly.parse_timespan(data[1]))

                    if self.client.__DEBUG__ and duration > 5 * 60:
                        return

                    data = {
                        'title': data[0],
                        'duration': duration,
                        'options': data[2:]
                    }
                except:
                    return

            poll = Poll(data['title'], data['options'])
            self.polls[message.channel] = poll

            # Create poll message and send it
            poll_msg = '**POLL: {}** - Ends in {}'.format(
                data['title'],
                humanfriendly.format_timespan(data['duration'])
            )

            for x in range(len(data['options'])):
                poll_msg += '\n{}. {}'.format(x + 1, data['options'][x])

            await self.client.say(poll_msg)

            # Sleep for some time
            await asyncio.sleep(data['duration'])

            if poll.closed:
                return

            # Get top options and send a message
            top = poll.get_top()

            if top is not None:
                chart = make_chart(data['title'], top)

                # Upload chart.
                with open(chart, 'rb') as f:
                    await self.client.upload(f)

                try:
                    os.remove(chart)
                except:
                    pass
            else:
                await self.client.say('**POLL: {}** - No Results'.format(data['title']))

            '''
            poll_msg = '**POLL: {}** - Results'.format(data['title'])

            for x in range(len(top)):
                poll_msg += '\n{}. {} ({})'.format(x + 1, top[x][0], top[x][1])

            await self.client.say(poll_msg)
            '''

            # Delete current poll to allow a new one
            del self.polls[message.channel]
        except:
            traceback.print_exc()

    @command()
    async def vote(self, message):
        # Check to see if there's even a poll to vote on
        if not message.channel in self.polls:
            return
        try:
            # Get vote option
            option = int(message.args)
            self.polls[message.channel].vote(option, message.author.id)
        except:
            traceback.print_exc()

    @command(perm=['manage_messages'])
    async def delete(self, message):
        try:
            self.polls[message.channel].closed = True
            del self.polls[message.channel]
        except:
            pass

bot = PollBot
