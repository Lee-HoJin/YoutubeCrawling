import pandas as pd
import re
from collections import Counter

# CSV 파일 읽기
df = pd.read_csv('patagonia_youtube_descriptions.csv')
print(f"📊 총 {len(df)}개 영상 분석 중...")

# 방법 1: 기본적인 소문자 변환 방법
print("\n" + "="*50)
print("🔍 방법 1: 기본 소문자 변환")
print("="*50)

# 모든 설명을 소문자로 변환하여 합치기
all_descriptions_lower = ' '.join(df['description'].fillna('').astype(str)).lower()

# 키워드도 소문자로 통일
keywords = ['environment', 'carbon', 'social', 'diversity', 'sustainability', 'green', 'eco', 'esg']

print(f"🏷️  키워드 출현 빈도 (기본 매칭):")
for keyword in keywords:
    count = all_descriptions_lower.count(keyword)
    if count > 0:
        print(f"   - '{keyword}': {count}회")

# 방법 2: 정규표현식을 사용한 단어 경계 매칭 (더 정확함)
print("\n" + "="*50)
print("🔍 방법 2: 정확한 단어 매칭 (추천)")
print("="*50)

def count_word_exact(text, word):
    """단어 경계를 고려한 정확한 카운팅"""
    # \b는 단어 경계를 의미 (예: "carbon"이 "carbonate"에 포함되지 않도록)
    pattern = r'\b' + re.escape(word.lower()) + r'\b'
    return len(re.findall(pattern, text.lower()))

print(f"🏷️  키워드 출현 빈도 (정확한 단어 매칭):")
keyword_counts = {}
for keyword in keywords:
    count = count_word_exact(all_descriptions_lower, keyword)
    keyword_counts[keyword] = count
    if count > 0:
        print(f"   - '{keyword}': {count}회")

# 방법 3: 복수형/변형도 함께 고려
print("\n" + "="*50)
print("🔍 방법 3: 복수형/변형 포함 매칭")
print("="*50)

# 키워드와 그 변형들을 그룹으로 정의
keyword_groups = {
    'environment': ['environment', 'environmental', 'environments'],
    'carbon': ['carbon', 'carbons', 'carbon-neutral', 'carbon-free'],
    'social': ['social', 'socially', 'society'],
    'diversity': ['diversity', 'diverse', 'inclusion', 'inclusive'],
    'sustainability': ['sustainability', 'sustainable', 'sustain'],
    'green': ['green', 'eco-friendly', 'eco'],
    'climate': ['climate', 'global warming', 'warming']
}

def count_keyword_group(text, word_list):
    """키워드 그룹의 모든 변형을 카운팅"""
    total_count = 0
    details = {}
    for word in word_list:
        count = count_word_exact(text, word)
        if count > 0:
            details[word] = count
        total_count += count
    return total_count, details

print(f"🏷️  키워드 그룹별 출현 빈도:")
group_results = {}
for group_name, word_list in keyword_groups.items():
    total_count, details = count_keyword_group(all_descriptions_lower, word_list)
    group_results[group_name] = {'total': total_count, 'details': details}
    
    if total_count > 0:
        print(f"   📂 '{group_name}': {total_count}회")
        for word, count in details.items():
            print(f"      └ '{word}': {count}회")

# 방법 4: 영상별 키워드 분석
print("\n" + "="*50)
print("🔍 방법 4: 영상별 키워드 분석")
print("="*50)

def analyze_video_keywords(df, keywords):
    """각 영상별로 키워드 출현 분석"""
    video_keyword_data = []
    
    for idx, row in df.iterrows():
        description = str(row['description']).lower() if pd.notna(row['description']) else ''
        video_data = {
            'video_id': row['video_id'],
            'title': row['title'][:50] + '...' if len(str(row['title'])) > 50 else row['title'],
            'total_keywords': 0
        }
        
        # 각 키워드 카운팅
        for keyword in keywords:
            count = count_word_exact(description, keyword)
            video_data[keyword] = count
            video_data['total_keywords'] += count
        
        video_keyword_data.append(video_data)
    
    return pd.DataFrame(video_keyword_data)

# 영상별 분석 실행
video_analysis = analyze_video_keywords(df, keywords)

# 키워드가 많이 포함된 영상 상위 10개
top_videos = video_analysis.nlargest(10, 'total_keywords')

print(f"🎬 키워드가 많이 포함된 영상 TOP 10:")
for idx, video in top_videos.iterrows():
    if video['total_keywords'] > 0:
        print(f"   {video['total_keywords']}개 - {video['title']}")

# 방법 5: 전체 통계 및 인사이트
print("\n" + "="*50)
print("📈 전체 통계 및 인사이트")
print("="*50)

total_videos = len(df)
videos_with_keywords = len(video_analysis[video_analysis['total_keywords'] > 0])
keyword_videos_percentage = (videos_with_keywords / total_videos) * 100

print(f"📊 전체 통계:")
print(f"   - 총 영상 수: {total_videos}개")
print(f"   - 키워드 포함 영상: {videos_with_keywords}개")
print(f"   - 키워드 포함 비율: {keyword_videos_percentage:.1f}%")

# 가장 자주 사용되는 키워드
most_common_keywords = []
for keyword in keywords:
    total_count = video_analysis[keyword].sum()
    if total_count > 0:
        most_common_keywords.append((keyword, total_count))

most_common_keywords.sort(key=lambda x: x[1], reverse=True)

print(f"\n🏆 가장 자주 사용되는 키워드:")
for keyword, count in most_common_keywords:
    print(f"   - '{keyword}': {count}회")

# 키워드별 영상 분포
print(f"\n📈 키워드별 영상 분포:")
for keyword in keywords:
    videos_with_keyword = len(video_analysis[video_analysis[keyword] > 0])
    if videos_with_keyword > 0:
        percentage = (videos_with_keyword / total_videos) * 100
        print(f"   - '{keyword}': {videos_with_keyword}개 영상 ({percentage:.1f}%)")

# 선택적으로 상세 결과를 CSV로 저장
save_detailed_results = input("\n💾 상세 결과를 CSV로 저장하시겠습니까? (y/n): ").lower().strip()

if save_detailed_results == 'y':
    # 영상별 키워드 분석 결과 저장
    output_filename = 'nike_keyword_analysis.csv'
    video_analysis.to_csv(output_filename, index=False, encoding='utf-8-sig')
    print(f"✅ 상세 분석 결과 저장 완료: {output_filename}")
    
    # 키워드 통계 요약 저장
    summary_data = []
    for keyword in keywords:
        total_count = video_analysis[keyword].sum()
        videos_count = len(video_analysis[video_analysis[keyword] > 0])
        summary_data.append({
            'keyword': keyword,
            'total_mentions': total_count,
            'videos_with_keyword': videos_count,
            'percentage_of_videos': (videos_count / total_videos) * 100
        })
    
    summary_df = pd.DataFrame(summary_data)
    summary_filename = 'nike_keyword_summary.csv'
    summary_df.to_csv(summary_filename, index=False, encoding='utf-8-sig')
    print(f"✅ 키워드 요약 저장 완료: {summary_filename}")

print(f"\n🎉 키워드 분석 완료!")

"""
개선된 점들:
1. ✅ 모든 텍스트를 소문자로 변환하여 대소문자 구분 제거
2. ✅ 정규표현식으로 정확한 단어 매칭 (부분 문자열 방지)
3. ✅ 복수형/변형 키워드도 함께 고려
4. ✅ 영상별 키워드 분석
5. ✅ 전체 통계 및 인사이트 제공
6. ✅ 결과를 CSV로 저장 가능

사용 방법:
1. 위 코드를 keyword_analysis.py로 저장
2. nike_youtube_descriptions.csv 파일과 같은 폴더에 위치
3. python keyword_analysis.py 실행
"""