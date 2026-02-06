"""shelterのURLパターンの定義"""

# URLパターンを定義するためのpath関数をインポート
from django.urls import path
# 同じアプリ内のviews.pyをインポート
from . import views

# URLの名前空間をsherterに設定(逆引きURL用)
app_name = "shelters"

urlpatterns = [
    # /place/にアクセスしたらplace_listビューを呼ぶ
    path("place/", views.place_list, name="place_list"),
    # /places/数値/にアクセスしたらplace_detalビューを呼ぶ
    # <int:pk>はPlaceの主キーをURLから受け取る
    path("places/<int:pk>/", views.place_detail, name="place_detail"),
]