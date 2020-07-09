from discord.ext import commands
import discord, sheets, episode

class Episodes(commands.Cog):
    @commands.command()
    async def episode(self, ctx, *, args):
        '''Search for a specific episode and get the links
        '''
        episodes = await sheets.get_episodes()
        matching = []
        for i in episodes:
            if args.lower().strip() in i:
                matching += [episodes[i]]
        if len(matching) == 0:
            await ctx.send(f"Couldn't find any episodes matching {args.strip()}")
        else:
            episode = matching[0]
            output = f"**{episode.name}**:\n"
            if episode.website:
                output += f"> **Website**: <{episode.website}>\n"
            if episode.spotify:
                output += f"> **Spotify**: <{episode.spotify}>\n"
            if episode.itunes:
                output += f"> **Itunes**: <{episode.itunes}>\n"
            if episode.youtube:
                output += f"> **Youtube**: <{episode.youtube}>\n"
            if len(matching) > 1:
                titles = []
                for i in matching[1:]:
                    titles += [i.name]
                output += f"> **See also**: {', '.join(titles)}"
            await ctx.send(output)
