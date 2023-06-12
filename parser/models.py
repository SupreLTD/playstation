from django.db import models


class Games(models.Model):
    game_id = models.CharField(max_length=100)
    name = models.CharField(max_length=300)
    eng_name = models.CharField(max_length=300)
    description = models.TextField()
    price = models.CharField(max_length=6)
    full_price = models.CharField(max_length=6)
    buy_price = models.CharField(max_length=6)
    cat = models.CharField(max_length=30)
    pspl = models.CharField(max_length=30)
    lang = models.CharField(max_length=200)
    local = models.CharField(max_length=150)
    photo = models.CharField(max_length=200)
    background = models.CharField(max_length=200)
    platform = models.CharField(max_length=10)
    realise = models.CharField(max_length=20)
    author = models.CharField(max_length=150)
    genre = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Игру'
        verbose_name_plural = "Игры"

    def __str__(self):
        return self.name


class DiscountGame(models.Model):
    game_id = models.CharField(max_length=100)
    name = models.CharField(max_length=300)
    eng_name = models.CharField(max_length=300)
    description = models.TextField()
    price = models.CharField(max_length=6)
    full_price = models.CharField(max_length=6)
    buy_price = models.CharField(max_length=6)
    cat = models.CharField(max_length=30)
    pspl = models.CharField(max_length=30)
    lang = models.CharField(max_length=200)
    local = models.CharField(max_length=150)
    photo = models.CharField(max_length=200)
    background = models.CharField(max_length=200)
    platform = models.CharField(max_length=10)
    realise = models.CharField(max_length=20)
    author = models.CharField(max_length=150)
    genre = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Распродажа'
        verbose_name_plural = "Распродажи"

    def __str__(self):
        return self.name


class DlcGames(models.Model):
    game_id = models.CharField(max_length=100)
    name = models.CharField(max_length=300)
    eng_name = models.CharField(max_length=300)
    eng_game = models.CharField(max_length=300)
    rus_game = models.CharField(max_length=300)
    description = models.TextField()
    price = models.CharField(max_length=6)
    full_price = models.CharField(max_length=6)
    buy_price = models.CharField(max_length=6)
    cat = models.CharField(max_length=30)
    pspl = models.CharField(max_length=30)
    lang = models.CharField(max_length=200)
    local = models.CharField(max_length=150)
    photo = models.CharField(max_length=200)
    background = models.CharField(max_length=200)
    platform = models.CharField(max_length=10)
    realise = models.CharField(max_length=20)
    author = models.CharField(max_length=150)
    genre = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Дополнение'
        verbose_name_plural = "Дополнения"

    def __str__(self):
        return self.name


class BaseGames(models.Model):
    game_id = models.CharField(max_length=100)
    link = models.CharField(max_length=200, default='')
    name = models.CharField(max_length=300)
    eng_name = models.CharField(max_length=300)
    description = models.TextField()
    cat = models.CharField(max_length=30)
    pspl = models.CharField(max_length=30)
    lang = models.CharField(max_length=200, null=True)
    local = models.CharField(max_length=150,null=True)
    photo = models.CharField(max_length=200)
    background = models.CharField(max_length=200)
    platform = models.CharField(max_length=10)
    realise = models.CharField(max_length=20)
    author = models.CharField(max_length=150)
    genre = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'База игр'
        verbose_name_plural = "База игр"

    def __str__(self):
        return self.name


class BaseDlcGames(models.Model):
    game_id = models.CharField(max_length=100)
    link = models.CharField(max_length=200, default='')
    name = models.CharField(max_length=300)
    eng_name = models.CharField(max_length=300)
    eng_game = models.CharField(max_length=300)
    rus_game = models.CharField(max_length=300)
    description = models.TextField()
    cat = models.CharField(max_length=30)
    pspl = models.CharField(max_length=30)
    lang = models.CharField(max_length=200, null=True)
    local = models.CharField(max_length=150, null=True)
    photo = models.CharField(max_length=200)
    background = models.CharField(max_length=200)
    platform = models.CharField(max_length=10)
    realise = models.CharField(max_length=20)
    author = models.CharField(max_length=150)
    genre = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'База дополнений'
        verbose_name_plural = "База дополнения"

    def __str__(self):
        return self.name


class Proxy(models.Model):
    proxy = models.CharField(max_length=300)


class Logger(models.Model):
    start = models.CharField(max_length=100)
    finish = models.CharField(max_length=100)
    count_games = models.CharField(max_length=10)
    count_dlc = models.CharField(max_length=10)
    count_discount = models.CharField(max_length=10)
    proxies = models.TextField(null=True)

    class Meta:
        verbose_name = 'Лог'
        verbose_name_plural = "Логи"
