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
        parser.add_argument("--hinanjyo", type=str, required=True, help="Path to hinanjyo CSV")
        parser.add_argument("--hinanbasyo", type=str, required=True, help="Path to hinanbasyo CSV")
        parser.add_argument("--kitakukonnan", type=str, required=True, help="Path to kitakukonnan CSV")
        parser.add_argument("--truncate", action="store_true", help="Delete all Place records before import")
        # --truncateオプションが付いていたらPlaceテーブルの全レコードを削除してからインポートする

    def handle(self, *args, **options):
        """CSVを読み込み、Placeモデルにデータを取り込むメイン処理"""
        hinanjyo_path = Path(options["hinanjyo"])
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
        self.import_hinanjyo(hinanjyo_path, synced_at)
        self.import_hinanbasyo(hinanbasyo_path, synced_at)
        self.import_kitakukonnan(kitakukonnan_path, synced_at)

        # 最終的な件数を表示
        total = Place.objects.count()
        self.stdout.write(self.style.SUCCESS(f"Import completed. Total records: {total}"))

    def import_hinanjyo(self, path:Path, synced_at):
        """避難所(hinanjyo)CSVを読み込み、Placeに登録する"""
        if not path.exists():
            raise FileNotFoundError(path)
        
        created = 0
        with path.open("r", encoding="UTF-8", newline="") as f:
            reader = csv.DictReader(f)
            # CSVを１行ずつdictとして読み込む
            for row in reader:
                Place.objects.create(
                    source = "hinanjyo",
                    source_no = get_no(row),
                    category = "避難所",
                    subtype = (row.get("種別") or "").strip() or None,
                    name = (row.get("施設名") or "").strip(),
                    address = (row.get("住所") or "").strip(),
                    synced_at = synced_at,
                )
                created += 1

        self.stdout.write(self.style.SUCCESS(f"[hinanjyo] created:{created}"))

    def import_hinanbasyo(self, path:Path, synced_at):
        """避難場所(hinanbasyo)CSVを読み込み、Placeに登録する"""
        if not path.exists():
            raise FileNotFoundError(path)
        
        disaster_cols = [
            # 災害種別の列名一覧(元データのまま保持する)
            "災害種別_洪水",
            "災害種別_崖崩れ、土石及び地滑り",
            "災害種別_高潮",
            "災害種別_地震",
            "災害種別_津波",
            "災害種別_大規模な火災",
            "災害種別_内水氾濫",
            "災害種別_火山現象",
        ]

        created = 0
        with path.open("r", encoding="UTF-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 住所 + 方書を結合
                address = (row.get("住所") or "").strip()
                katagaki = (row.get("方書") or "").strip()
                if katagaki:
                    address = f"{address} {katagaki}" .strip()

                # 災害種別フラグをまとめてdictにする
                flags = {c:(row.get(c) or "").strip() for c in disaster_cols}

                # 収容人数(数値化できなければnotesに逃がす)
                capacity_raw = (row.get("想定収容人数") or "").strip()
                capacity = to_int(capacity_raw)

                notes_parts = []
                if capacity is None and capacity_raw:
                    notes_parts.append(f"想定収容人数：{capacity_raw}")
                if (v := (row.get("対象となる町会・自治会") or "").strip()):
                    notes_parts.append(f"対象町会・自治会：{v}")
                if (v := (row.get("指定避難所との重複") or "").strip()):
                    notes_parts.append(f"指定避難所との重複：{v}")
                if (v := (row.get("備考") or "").strip()):
                    notes_parts.append(f"備考：{v}")
                if (v := (row.get("電話番号") or "").strip()):
                    notes_parts.append(f"電話番号：{v}")
                if (v := (row.get("内線番号") or "").strip()):
                    notes_parts.append(f"内線番号：{v}")

                Place.objects.create(
                    source = "hinanbasyo",
                    source_no = get_no(row),
                    category = "避難場所",
                    name = (row.get("名称") or "").strip(),
                    name_kana = (row.get("名称_カナ") or "").strip() or None,
                    address = address,
                    lat = to_float(row.get("緯度")),
                    lng = to_float(row.get("経度")),
                    capacity = capacity,
                    disaster_flags = flags,
                    url = (row.get("URL") or "").strip() or None,
                    notes = "\n".join(notes_parts) or None,
                    synced_at = synced_at,
                )
                created += 1

            self.stdout.write(self.style.SUCCESS(f"[hinanbasyo] created: {created}"))

    def import_kitakukonnan(self, path:Path, synced_at):
        """帰宅困難者支援施設(kitakukonnan)CSVを読み込み、Placeに登録する"""

        if not path.exists():
            raise FileNotFoundError(path)
        
        created = 0
        with path.open("r", encoding="UTF-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                Place.objects.create(
                    source = "kitakukonnan",
                    source_no = get_no(row),
                    category = "帰宅困難者支援施設",
                    subtype = (row.get("種別") or "").strip() or None,
                    name = (row.get("施設名") or "").strip(),
                    address = (row.get("住所") or "").strip(),
                    synced_at = synced_at,
                )
                created += 1

            self.stdout.write(self.style.SUCCESS(f"[kitakukonnan] created: {created}"))
