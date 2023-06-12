from django.contrib import admin
from .models import Games, DiscountGame, DlcGames, Proxy, Logger, BaseGames, BaseDlcGames


@admin.register(Games)
class GamesAdmin(admin.ModelAdmin):
    list_display = 'eng_name', 'name', 'realise', 'price', 'full_price', 'buy_price'
    search_fields = 'name',
    sortable_by = 'realise',


@admin.register(DiscountGame)
class GamesDAdmin(admin.ModelAdmin):
    list_display = 'eng_name', 'name', 'realise', 'price', 'full_price', 'buy_price'
    search_fields = 'name',


@admin.register(DlcGames)
class GamesDLCAdmin(admin.ModelAdmin):
    list_display = 'eng_game', 'rus_game', 'eng_name', 'name', 'realise',  'price', 'full_price', 'buy_price'
    search_fields = 'name',
    sortable_by = 'realise',


@admin.register(BaseGames)
class GamesDLCAdmin(admin.ModelAdmin):
    list_display = 'eng_name', 'name', 'realise',
    search_fields = 'game_id','name'
    sortable_by = 'realise',


@admin.register(BaseDlcGames)
class GamesDLCAdmin(admin.ModelAdmin):
    list_display = 'eng_game', 'rus_game', 'eng_name', 'name', 'realise'
    search_fields = 'name','game_id'
    sortable_by = 'realise',


@admin.register(Proxy)
class GamesDLCAdmin(admin.ModelAdmin):
    list_display = 'proxy',


@admin.register(Logger)
class GamesDLCAdmin(admin.ModelAdmin):
    list_display = 'start', 'finish', 'count_games', 'count_dlc', 'count_discount'


