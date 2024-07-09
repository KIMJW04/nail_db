import json
import os

# JSON 파일들이 있는 디렉터리
json_dir = './missing_firle_total'

# 결과를 저장할 파일 경로
output_file = 'merged_missing_shops.json'

# JSON 파일 목록 생성
json_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]

# 결합할 데이터를 저장할 리스트
merged_data = []

# 각 파일을 읽어서 merged_data에 추가
for json_file in json_files:
    file_path = os.path.join(json_dir, json_file)
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        merged_data.extend(data)  # 데이터를 리스트에 추가

# 결합된 데이터를 하나의 파일로 저장
with open(output_file, 'w', encoding='utf-8') as file:
    json.dump(merged_data, file, ensure_ascii=False, indent=4)

print(f'Merged {len(json_files)} files into {output_file}')
