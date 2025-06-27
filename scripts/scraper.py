# scripts/scraper_fast.py

from datetime import date, datetime, time as dtime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import pandas as pd
from bs4 import BeautifulSoup
from cloudscraper import CloudScraper
from pytz import timezone

class Lottery:
    def __init__(self):
        self._http = CloudScraper()
        self._data = {}
        self._raw_data = pd.DataFrame()
        self._2_digits_data = pd.DataFrame()
        self._sparse_data = pd.DataFrame()
        self._begin_date = date.today()
        self._last_date = date.today()
        self.data_dir = Path(__file__).parent.parent / 'data'
        self.data_dir.mkdir(exist_ok=True)

    def load(self):
        json_path = self.data_dir / 'xsmb.json'
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = pd.read_json(f)
                if data.empty:
                    raise FileNotFoundError
                self._data = {pd.to_datetime(d['date']).date(): d for d in data.to_dict('records')}
            self.generate_dataframes()
        except (FileNotFoundError, ValueError):
            print("No existing data found. Starting from 2010-01-01.")
            self._begin_date = date(2010, 1, 1)
            self._last_date = self._begin_date - timedelta(days=1)

    def dump(self):
        def _dump(df: pd.DataFrame, file_name: str):
            if df.empty:
                print(f"DataFrame for {file_name} is empty, skipping dump.")
                return
            df_sorted = df.sort_values(by='date').reset_index(drop=True)
            df_sorted.to_csv(self.data_dir / f'{file_name}.csv', index=False)
            df_sorted.to_json(self.data_dir / f'{file_name}.json', orient='records', date_format='iso', indent=2)
            print(f"✅ Dumped: {file_name}.[csv/json]")

        _dump(self._raw_data, 'xsmb')
        _dump(self._2_digits_data, 'xsmb-2-digits')
        _dump(self._sparse_data, 'xsmb-sparse')

    def fetch_single(self, selected_date: date):
        url = f'https://xoso.com.vn/xsmb-{selected_date:%d-%m-%Y}.html'
        try:
            resp = self._http.get(url, timeout=15)
            if resp.status_code != 200:
                return None
        except Exception:
            return None

        soup = BeautifulSoup(resp.text, 'lxml')
        prizes = {
            'special': soup.select_one('span.special-prize'), 'prize1': soup.select_one('span.prize1'),
            'prize2': soup.select('span.prize2'), 'prize3': soup.select('span.prize3'),
            'prize4': soup.select('span.prize4'), 'prize5': soup.select('span.prize5'),
            'prize6': soup.select('span.prize6'), 'prize7': soup.select('span.prize7')
        }

        if prizes['special'] is None or not prizes['special'].text.strip().isdigit():
            return None

        try:
            result = {
                'special': [int(prizes['special'].text)], 'prize1': [int(prizes['prize1'].text)],
                'prize2': [int(p.text) for p in prizes['prize2']], 'prize3': [int(p.text) for p in prizes['prize3']],
                'prize4': [int(p.text) for p in prizes['prize4']], 'prize5': [int(p.text) for p in prizes['prize5']],
                'prize6': [int(p.text) for p in prizes['prize6']], 'prize7': [int(p.text) for p in prizes['prize7']]
            }

            result_dict = {
                'date': selected_date, 'special': result['special'][0], 'prize1': result['prize1'][0],
                'prize2_1': result['prize2'][0], 'prize2_2': result['prize2'][1],
                'prize3_1': result['prize3'][0], 'prize3_2': result['prize3'][1], 'prize3_3': result['prize3'][2], 'prize3_4': result['prize3'][3],
                'prize3_5': result['prize3'][4], 'prize3_6': result['prize3'][5],
                'prize4_1': result['prize4'][0], 'prize4_2': result['prize4'][1], 'prize4_3': result['prize4'][2], 'prize4_4': result['prize4'][3],
                'prize5_1': result['prize5'][0], 'prize5_2': result['prize5'][1], 'prize5_3': result['prize5'][2], 'prize5_4': result['prize5'][3],
                'prize5_5': result['prize5'][4], 'prize5_6': result['prize5'][5],
                'prize6_1': result['prize6'][0], 'prize6_2': result['prize6'][1], 'prize6_3': result['prize6'][2],
                'prize7_1': result['prize7'][0], 'prize7_2': result['prize7'][1], 'prize7_3': result['prize7'][2], 'prize7_4': result['prize7'][3]
            }
            return result_dict
        except Exception:
            return None

    def generate_dataframes(self):
        if not self._data:
            print("⚠️ No data available.")
            return

        self._raw_data = pd.DataFrame(list(self._data.values()))
        self._raw_data['date'] = pd.to_datetime(self._raw_data['date'])
        prize_cols = self._raw_data.columns.drop('date')
        self._raw_data[prize_cols] = self._raw_data[prize_cols].astype('int64')

        self._2_digits_data = self._raw_data.copy()
        self._2_digits_data[prize_cols] = self._2_digits_data[prize_cols].apply(lambda x: x % 100)

        loto_cols = [str(i) for i in range(100)]
        sparse_rows = []
        for _, row in self._2_digits_data.iterrows():
            counts = row.drop('date').value_counts()
            sparse_row = {'date': row['date']}
            for loto in loto_cols:
                sparse_row[loto] = 0
            for num, count in counts.items():
                sparse_row[str(int(num))] = int(count)
            sparse_rows.append(sparse_row)

        self._sparse_data = pd.DataFrame(sparse_rows)
        self._sparse_data['date'] = pd.to_datetime(self._sparse_data['date'])
        self._sparse_data[loto_cols] = self._sparse_data[loto_cols].astype('int8')

        self._begin_date = self._raw_data['date'].min().date()
        self._last_date = self._raw_data['date'].max().date()
        print(f"📅 Data from {self._begin_date} to {self._last_date}")

def main():
    lottery = Lottery()
    lottery.load()

    tz = timezone('Asia/Ho_Chi_Minh')
    now = datetime.now(tz)
    start_fetch_date = lottery._last_date + timedelta(days=1)
    end_fetch_date = now.date()
    if now.time() < dtime(18, 40):
        end_fetch_date -= timedelta(days=1)

    if start_fetch_date > end_fetch_date:
        print("✅ Data is already up to date.")
        return

    date_range = [start_fetch_date + timedelta(days=i) for i in range((end_fetch_date - start_fetch_date).days + 1)]

    print(f"🚀 Fetching {len(date_range)} days from {start_fetch_date} to {end_fetch_date}...")

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(lottery.fetch_single, d): d for d in date_range}
        for future in tqdm(as_completed(futures), total=len(futures)):
            result = future.result()
            if result:
                lottery._data[result['date']] = result

    lottery.generate_dataframes()
    lottery.dump()

if __name__ == '__main__':
    main()
