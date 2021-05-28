import discord


class ListMessage:

    def __init__(self, items, object_type, count_on_page=10):
        self.items = items
        self.splitted_items = self._split_items(count_on_page)
        self.count_on_page = count_on_page
        self.current_page = 0
        self.message = None
        self.all_emojis = {0: ['➡️'],
                           len(self.splitted_items) - 1: ['⬅️']
                           }
        self.options = {'playlist': {'title': 'Choose playlist', 'color': discord.Color.green(), 'emojis': ['1️⃣', '2️⃣', '3️⃣', '4️⃣',
                                                                                                            '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']},
                        'songs_list': {'title': 'List', 'color': discord.Color.greyple(), 'emojis': []}}
        self.object_type = object_type
        self.is_updating_reactions = False

    def _split_items(self, count):
        return [self.items[i:i + count] for i in range(0, len(self.items), count)]

    def next_page(self):
        if self.current_page + 1 < len(self.items):
            self.current_page += 1

    def previous_page(self):
        if self.current_page - 1 >= 0:
            self.current_page -= 1

    async def refresh_page(self):
        await self.message.clear_reactions()
        await self.message.edit(embed=self.get_embed())
        emojis = self.options[self.object_type]['emojis']
        if len(self.splitted_items) > 1:
            arrows = self.all_emojis.get(self.current_page, ['⬅️', '➡️'])
        else:
            arrows = []
        self.is_updating_reactions = True
        for emoji in emojis[:len(self.splitted_items[self.current_page])] + arrows:
            await self.message.add_reaction(emoji=emoji)
        self.is_updating_reactions = False

    def _get_description(self):
        res = ''
        for i in range(len(self.splitted_items[self.current_page])):
            if self.object_type == 'playlist':
                res += f'{i + 1}. {self.splitted_items[self.current_page][i].name}\n'
            elif self.object_type == 'songs_list':
                res += f'{self.current_page * self.count_on_page + i + 1}. {self.splitted_items[self.current_page][i]}\n'
        return res

    def get_embed(self):
        return (discord.Embed(title=self.options[self.object_type]['title'], description=self._get_description(),
                              color=self.options[self.object_type]['color']).set_footer(text='Made with ❤️'))
