# 複数条件検索(OR検索など)を行うためのQオブジェクトをインポート
from django.db.models import Q

# 指定したデータが存在しなければ404を返す関数と、テンプレートを描画するrenderをインポート
from django.shortcuts import get_object_or_404, render

# 同じアプリ内のPlaceモデルを読み込む
from .models import Place

def place_list(request):
    """一覧ページのビュー関数。検索やカテゴリ絞り込みを行う"""

    # GETパラメータからcategoryを取得(なければ空文字)。前後の空白も除去
    category = request.GET.get("category", "").strip()

    # GETパラメータからq(キーワード検索)を取得。こちらも空白除去
    q = request.GET.get("q", "").strip()

    # Placeモデルの全データを取得(ここから絞り込みを行う)
    places = Place.objects.all()

    if category:
        # categoryが指定されていれば、そのカテゴリで絞り込み
        places = places.filter(category=category)

    if q:
        # qが指定されていれば、名前または住所に部分一致するデータを検索(OR条件)
        places = places.filter(
            Q(name__icontains=q) | Q(address__icontains=q)
        )

    # カテゴリ→名前の順で並び替え
    places = places.order_by("category","name")

    # 選択肢として表示するカテゴリ一覧(固定値)
    categories = ["避難所", "避難場所", "帰宅困難者支援施設"]

    context = {
        "places" : places, # 絞り込み後の施設一覧
        "categories" : categories, # カテゴリの選択肢
        "selected_category" : category, # 現在選択されているカテゴリ
        "q" : q, # 現在の検索キーワード
    }

    # place_list.htmlにデータを渡して描画
    return render(request, "shelters/place_list.html", context)

def place_detail(reqest, pk):
    """詳細ページのビュー関数。1件のPlaceを表示する"""

    # pk(主キー)に一致するPlaceを取得。なければ404を返す。
    Place = get_object_or_404(Place, pk=pk)

    # place_detail.htmlにplaceを渡して描画
    return render(reqest, "shelters/place_detail.html",{"place":Place})

