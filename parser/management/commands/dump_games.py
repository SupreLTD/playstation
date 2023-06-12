import pandas as pd
from django.core.management import BaseCommand

from parser.models import BaseGames, BaseDlcGames


def dump_db() -> None:
    columns = ['game_id', 'link', 'name', 'eng_name', 'description', 'cat', 'pspl', 'lang',
               'local', 'photo', 'background', 'platform', 'realise', 'author', 'genre']
    data = [
        [i.game_id, i.link, i.name, i.eng_name, i.description, i.cat, i.pspl, i.lang, i.local, i.photo, i.background,
         i.platform, i.realise, i.author, i.genre] for i in BaseGames.objects.all()]

    df = pd.DataFrame(data, columns=columns)
    df.to_csv(fr'static/dump_games.csv', index=False)

class Command(BaseCommand):
    help = 'db'

    def handle(self, *args, **options):
        dump_db()