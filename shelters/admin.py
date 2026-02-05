from django.contrib import admin

# models.pyからPlaceモデルをインポートする
from .models import Place

# PlaceモデルをDjango管理画面に登録するデコレータ
@admin.register(Place)

class PlaceAdmin(admin.ModelAdmin):
    """Placeモデルをカスタマイズするためのクラス"""

    # 管理画面の一覧ページに表示するフィールドを指定する
    list_display = ("category", "name", "address", "source")

    # 管理画面の検索ボックスで検索対象にするフィールドを指定する
    search_fields = ("name", "address")

    # 右側に表示されるフィルター(絞り込み)項目を指定
    list_filter = ("category", "source")