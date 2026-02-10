from django.db import models
from django.utils.http import urlencode
# Create your models here.

# 避難施設(避難所・避難場所・帰宅困難者支援施設など)を表すモデル
class Place(models.Model):

    # データの元になったCSVの種類を表す(例：hinanjo/hinanbasyo/kitakukonnan)
    source = models.CharField(max_length=32)

    # 元データ(CSV)内の管理番号(NO,No. など)
    # データによっては無い場合もあるので、空欄・NULLを許可
    source_no = models.CharField(max_length=32, blank=True, null=True)

    # 画面表示や検索用の大分類(避難所/避難場所/帰宅困難者支援施設)
    category = models.CharField(max_length=64)

    # CSVにある「種別」列をそのまま保持するための項目
    # (例：一時滞在可能、福祉避難所など)
    subtype = models.CharField(max_length=64, blank=True, null=True)

    # 施設名(表示・検索の中心となる項目)
    name = models.CharField(max_length=256)

    # 施設名のカナ表記(避難場所データにあるため任意で保持)
    name_kana = models.CharField(max_length=256, blank=True, null=True)


    # 施設の住所(検索・表示用)
    address = models.CharField(max_length=255, blank=True, default="")

    # 緯度(地図表示や距離計算の将来拡張用)
    lat = models.FloatField(blank=True, null=True)

    # 経度(地図表示や距離計算の将来拡張用)
    lng = models.FloatField(blank=True, null=True)

    # 想定収容人数(数値として扱える場合のみ保存)
    capacity = models.IntegerField(blank=True, null=True)

    # この避難場所が、どの災害に対応しているか(洪水・地震など)をまとめて保存するJSON
    # データ構造が柔軟なため、将来の項目にも対応しやすい
    disaster_flags = models.JSONField(blank=True, null=True)

    # 関連URL(施設ページなど)
    url = models.URLField(blank=True, null=True)

    # 備考欄(CSVの備考や、数値化できなかった情報を格納)
    notes = models.TextField(blank=True, null=True)

    # データを端末に同期した日時(オフライン利用時の基準)
    synced_at = models.DateTimeField()

    @property
    def map_url(self) -> str:
        # 座標があれば座標優先
        if self.lat is not None and self.lng is not None:
            return f"https://www.google.com/maps?q={self.lat},{self.lng}"
        # 住所があれば検索
        q = self.address.strip()
        if q:
            return "https://www.google.com/maps/search/?" + urlencode({"api": 1, "query": q})
        # 最後の保険: 名称で検索
        return "https://www.google.com/maps/search/?" + urlencode({"api": 1, "query": getattr(self, "name", "")})

    # モデル全体の設定
    class Meta:
        indexes = [
            # カテゴリ検索を高速化するためのインデックス
            models.Index(fields=["category"]),
            # 施設名検索を高速化するためのインデックス
            models.Index(fields=["name"]),
        ]

    # 管理画面やデバック時に表示される文字列
    def __str__(self):
        # 「避難所：船橋小学校」のように表示される
        return f"{self.category}:{self.name}"

