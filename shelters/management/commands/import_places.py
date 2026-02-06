# csvファイルを読み込むための標準ライブラリ
import csv
# ファイルパスを扱いやすくするPathクラス
from pathlib import Path
# Djangoの管理コマンドを作るための基底クラス
from django.core.management.base import BaseCommand
# タイムゾーン対応の現在時刻を取得するため
from django.utils import timezone
# データを保存するPlaceモデルをインポート
from shelters.models import Place


def to_float(v:str | None):
    """文字列をfloatに変換する。空文字や変換不能な値はNoneを返す"""
    if v is None:
        return None
    v = str(v).strip()
    if v == "":
        return None
    try:
        return float(v)
    except ValueError:
        return None
    
def to_int(v:str | None):
    """
    数値っぽい文字列をintに変換する。
    空文字や変換不可能な値はNoneを返す。
    123.0のような値もあるためfloatを経由して変換する。
    """
    if v is None:
        return None
    v = str(v).strip()
    if v == "":
        return None
    try:
        return int(float(v)) # float経由で整数化
    except ValueError:
        return None

def get_no(row:dict):
    """
    CSVの行からNO/No./No/noのいずれかのキーを取得する。
    データセットごとに列名が揺れるため吸収するための関数。
    """
    return row.get("NO") or row.get("No.") or row.get("No") or row.get("no")

class Command(BaseCommand):
    """
    船橋市の災害関連CSV(避難所・避難場所・帰宅困難者支援施設)を
    Placeモデルに取り込む管理コマンド
    """

    # コマンドの説明文
    help = "Import Funabashi disaster-related CSV datasets into Place."

    def add_arguments(self, parser):
        """コマンドライン引数を定義する"""
        parser.add_argument("--hinanjo", type=str, required=True, help="Path to hinanjo CSV")
        parser.add_argument("--hinanbasyo", type=str, required=True, help="Path to hinanbasyo CSV")
        parser.add_argument("--kitakukonnan", type=str, required=True, help="Path to kitakukonnan CSV")
        parser.add_argument("--truncate", action="store_true", help="Delete all Place records before import")
        # --truncateオプションが付いていたらPlaceテーブルの全レコードを削除してからインポートする

    def handle(self, *args, **options):
        """CSVを読み込み、Placeモデルにデータを取り込むメイン処理"""
        hinanjo_path = Path(options["hinanjo"])
        hinanbasyo_path = Path(options["hinanbasyo"])
        kitakukonnan_path = Path(options["kitakukonnan"])
        truncate = options["truncate"] 

        if truncate:
            # --truncate
            Place.objects.all().delete()
            self.stdout.write(self.style.WARNING("ALL Place records deleted (--truncate)."))

            # 取り込み時刻を記録(全レコード共通)
            synced_at = timezone.now()

            # 3種類のCSVを順番に取り込む
            self.import_hinanjo(hinanjo_path, synced_at)
            self.import_hinanbasyo(hinanbasyo_path, synced_at)
            self.import_kitakukonnan(kitakukonnan_path, synced_at)

            # 最終的な件数を表示
            total = Place.objects.count()
            self.stdout.write(self.style.SUCCESS(f"Import completed. Total records: {total}"))


