from django.urls import path
from . import views

# URLの名前空間を設定。テンプレートで'places:  'みたいに使えるようになる
app_name = "places"

# URLパターンをまとめたリスト(Djangoがここを読み取る)
urlpatterns = [
    # /places/にアクセスしたらviews.place_listを実行
    # name="place_list"はテンプレートやrevers()で使う名前
    path("places/", views.place_list, name="place_list"),

    # /places/にアクセスしたらviews.place_detailを実行
    # <int:pk>はURLの数字部分をpkとしてレビューに渡す
    path("place/<int:pk>/", views.place_detail, name="place_detail"),
]