# [테스트] API 3종 응답 스키마 검증



from app.services.football_api import fetch_matches


data = fetch_matches()

print("API 호출 성공")
print("응답 키:", data.keys())

matches = data.get("matches", [])

print("경기 수:", len(matches))

if matches:
    first = matches[0]
    print("첫 번째 경기:")
    print(first)