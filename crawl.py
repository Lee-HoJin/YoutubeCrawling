#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
나이키 YouTube 채널 영상 설명 추출기
YouTube Data API v3 사용
"""

import requests
import pandas as pd
import json
from datetime import datetime
import time
import os

class NikeYouTubeScraper:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = 'https://www.googleapis.com/youtube/v3'
        self.nike_channel_handle = '@nike'  # 나이키 채널 핸들
        self.nike_channel_id = None  # 나중에 자동으로 찾을 예정
        
    def get_channel_id_by_handle(self, handle):
        """채널 핸들(@nike)로 채널 ID 찾기"""
        # 핸들에서 @ 제거
        handle = handle.replace('@', '')
        
        # 검색 API로 채널 찾기
        search_url = f"{self.base_url}/search"
        params = {
            'part': 'snippet',
            'q': handle,
            'type': 'channel',
            'key': self.api_key,
            'maxResults': 1
        }
        
        try:
            response = requests.get(search_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['items']:
                channel_id = data['items'][0]['snippet']['channelId']
                channel_title = data['items'][0]['snippet']['title']
                print(f"✅ 채널을 찾았습니다: {channel_title} (ID: {channel_id})")
                return channel_id
            else:
                print("❌ 채널을 찾을 수 없습니다.")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ API 요청 오류: {e}")
            return None
    
    def get_channel_uploads_playlist(self, channel_id):
        """채널의 업로드 재생목록 ID 가져오기"""
        channels_url = f"{self.base_url}/channels"
        params = {
            'part': 'contentDetails',
            'id': channel_id,
            'key': self.api_key
        }
        
        try:
            response = requests.get(channels_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['items']:
                uploads_playlist_id = data['items'][0]['contentDetails']['relatedPlaylists']['uploads']
                print(f"✅ 업로드 재생목록 ID: {uploads_playlist_id}")
                return uploads_playlist_id
            else:
                print("❌ 업로드 재생목록을 찾을 수 없습니다.")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 업로드 재생목록 가져오기 오류: {e}")
            return None
    
    def get_playlist_videos(self, playlist_id, max_results=50):
        """재생목록의 영상 목록 가져오기 (더 안정적인 방법)"""
        videos = []
        next_page_token = None
        
        while len(videos) < max_results:
            playlist_url = f"{self.base_url}/playlistItems"
            params = {
                'part': 'snippet',
                'playlistId': playlist_id,
                'maxResults': min(50, max_results - len(videos)),
                'key': self.api_key
            }
            
            if next_page_token:
                params['pageToken'] = next_page_token
            
            try:
                response = requests.get(playlist_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                for item in data['items']:
                    try:
                        # 썸네일 URL 안전하게 가져오기
                        thumbnail_url = ''
                        thumbnails = item['snippet'].get('thumbnails', {})
                        if 'medium' in thumbnails:
                            thumbnail_url = thumbnails['medium']['url']
                        elif 'default' in thumbnails:
                            thumbnail_url = thumbnails['default']['url']
                        
                        video_info = {
                            'video_id': item['snippet']['resourceId']['videoId'],
                            'title': item['snippet']['title'],
                            'published_at': item['snippet']['publishedAt'],
                            'thumbnail': thumbnail_url
                        }
                        videos.append(video_info)
                        
                    except Exception as e:
                        print(f"⚠️  영상 정보 처리 중 오류: {e}")
                        continue
                
                # 다음 페이지 토큰 확인
                next_page_token = data.get('nextPageToken')
                if not next_page_token:
                    break
                    
                print(f"📹 영상 {len(videos)}개 수집 완료...")
                time.sleep(0.1)  # API 요청 제한 방지
                
            except requests.exceptions.RequestException as e:
                print(f"❌ 재생목록 영상 가져오기 오류: {e}")
                break
            except Exception as e:
                print(f"❌ 예상치 못한 오류: {e}")
                break
        
        print(f"✅ 총 {len(videos)}개 영상 목록 수집 완료!")
        return videos[:max_results]
    
    def get_channel_videos(self, channel_id, max_results=50):
        """채널의 영상 목록 가져오기"""
        videos = []
        next_page_token = None
        
        while len(videos) < max_results:
            search_url = f"{self.base_url}/search"
            params = {
                'part': 'id,snippet',
                'channelId': channel_id,
                'type': 'video',
                'order': 'date',  # 최신순
                'maxResults': min(50, max_results - len(videos)),
                'key': self.api_key
            }
            
            if next_page_token:
                params['pageToken'] = next_page_token
            
            try:
                response = requests.get(search_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                # 디버깅: API 응답 구조 확인
                if not videos and data.get('items'):
                    print(f"🔍 API 응답 구조 확인: {list(data['items'][0].keys())}")
                    if 'id' in data['items'][0]:
                        print(f"🔍 ID 구조: {data['items'][0]['id']}")
                
                for item in data['items']:
                    try:
                        # videoId 추출 (여러 방법 시도)
                        video_id = None
                        if isinstance(item.get('id'), dict):
                            video_id = item['id'].get('videoId')
                        elif isinstance(item.get('id'), str):
                            video_id = item['id']
                        
                        if not video_id:
                            print(f"⚠️  영상 ID를 찾을 수 없음: {item.get('id')}")
                            continue
                        
                        # 썸네일 URL 안전하게 가져오기
                        thumbnail_url = ''
                        thumbnails = item['snippet'].get('thumbnails', {})
                        if 'medium' in thumbnails:
                            thumbnail_url = thumbnails['medium']['url']
                        elif 'default' in thumbnails:
                            thumbnail_url = thumbnails['default']['url']
                        
                        video_info = {
                            'video_id': video_id,
                            'title': item['snippet']['title'],
                            'published_at': item['snippet']['publishedAt'],
                            'thumbnail': thumbnail_url
                        }
                        videos.append(video_info)
                        
                    except Exception as e:
                        print(f"⚠️  영상 정보 처리 중 오류: {e}")
                        print(f"   문제 항목: {item}")
                        continue
                
                # 다음 페이지 토큰 확인
                next_page_token = data.get('nextPageToken')
                if not next_page_token:
                    break
                    
                print(f"📹 영상 {len(videos)}개 수집 완료...")
                time.sleep(0.1)  # API 요청 제한 방지
                
            except requests.exceptions.RequestException as e:
                print(f"❌ 영상 목록 가져오기 오류: {e}")
                break
            except Exception as e:
                print(f"❌ 예상치 못한 오류: {e}")
                break
        
        print(f"✅ 총 {len(videos)}개 영상 목록 수집 완료!")
        return videos[:max_results]
    
    def get_video_details(self, video_ids):
        """영상 상세 정보 (설명 포함) 가져오기"""
        videos_details = []
        
        # None이나 빈 ID 제거
        valid_video_ids = [vid for vid in video_ids if vid and isinstance(vid, str)]
        print(f"📊 유효한 영상 ID: {len(valid_video_ids)}개 (전체: {len(video_ids)}개)")
        
        if not valid_video_ids:
            print("❌ 유효한 영상 ID가 없습니다.")
            return []
        
        # API는 한번에 최대 50개까지 처리 가능
        for i in range(0, len(valid_video_ids), 50):
            batch_ids = valid_video_ids[i:i+50]
            ids_string = ','.join(batch_ids)
            
            videos_url = f"{self.base_url}/videos"
            params = {
                'part': 'snippet,statistics',
                'id': ids_string,
                'key': self.api_key
            }
            
            try:
                response = requests.get(videos_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                for item in data['items']:
                    try:
                        snippet = item['snippet']
                        stats = item.get('statistics', {})
                        
                        video_detail = {
                            'video_id': item['id'],
                            'title': snippet.get('title', ''),
                            'description': snippet.get('description', ''),
                            'published_at': snippet.get('publishedAt', ''),
                            'channel_title': snippet.get('channelTitle', ''),
                            'tags': ', '.join(snippet.get('tags', [])),
                            'view_count': int(stats.get('viewCount', 0)),
                            'like_count': int(stats.get('likeCount', 0)),
                            'comment_count': int(stats.get('commentCount', 0)),
                            'duration_seconds': 0,  # 필요시 추가 가능
                            'video_url': f"https://www.youtube.com/watch?v={item['id']}"
                        }
                        videos_details.append(video_detail)
                        
                    except Exception as e:
                        print(f"⚠️  영상 상세정보 처리 중 오류: {e}")
                        print(f"   문제 영상 ID: {item.get('id', 'Unknown')}")
                        continue
                
                print(f"📝 {len(videos_details)}개 영상 상세정보 수집 완료...")
                time.sleep(0.1)  # API 요청 제한 방지
                
            except requests.exceptions.RequestException as e:
                print(f"❌ 영상 상세정보 가져오기 오류: {e}")
                continue
            except Exception as e:
                print(f"❌ 예상치 못한 오류: {e}")
                continue
        
        print(f"✅ 최종 {len(videos_details)}개 영상 상세정보 수집 완료!")
        return videos_details
    
    def extract_nike_descriptions(self, max_videos=100):
        """나이키 채널의 영상 설명 추출"""
        print("🔍 나이키 채널 검색 중...")
        
        # 1. 채널 ID 찾기
        self.nike_channel_id = self.get_channel_id_by_handle(self.nike_channel_handle)
        if not self.nike_channel_id:
            print("❌ 나이키 채널을 찾을 수 없습니다.")
            return None
        
        # 2. 업로드 재생목록 ID 가져오기
        print("📂 업로드 재생목록 정보 가져오는 중...")
        uploads_playlist_id = self.get_channel_uploads_playlist(self.nike_channel_id)
        
        if uploads_playlist_id:
            # 3-A. 재생목록 방법으로 영상 목록 가져오기 (더 안정적)
            print(f"📹 재생목록에서 최대 {max_videos}개 영상 목록 수집 중...")
            videos = self.get_playlist_videos(uploads_playlist_id, max_videos)
        else:
            # 3-B. 검색 방법으로 폴백 (백업 방법)
            print(f"📹 검색 방법으로 최대 {max_videos}개 영상 목록 수집 중...")
            videos = self.get_channel_videos(self.nike_channel_id, max_videos)
        
        if not videos:
            print("❌ 영상을 찾을 수 없습니다.")
            return None
        
        # 4. 영상 상세 정보 가져오기
        print("📝 영상 상세정보 및 설명 수집 중...")
        video_ids = [video['video_id'] for video in videos]
        detailed_videos = self.get_video_details(video_ids)
        
        return detailed_videos
    
    def save_to_csv(self, videos_data, filename=None):
        """데이터를 CSV 파일로 저장"""
        if not videos_data:
            print("❌ 저장할 데이터가 없습니다.")
            return None
        
        # 파일명 생성
        if not filename:
            # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"nike_youtube_descriptions.csv"
        
        # DataFrame 생성
        df = pd.DataFrame(videos_data)
        
        # 날짜 형식 변환
        df['published_date'] = pd.to_datetime(df['published_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # 컬럼 순서 정리
        columns_order = [
            'video_id', 'title', 'description', 'published_date', 'published_at',
            'channel_title', 'tags', 'view_count', 'like_count', 'comment_count', 'video_url'
        ]
        df = df[columns_order]
        
        # CSV 저장
        try:
            df.to_csv(filename, index=False, encoding='utf-8-sig')  # 한글 지원
            print(f"✅ CSV 파일 저장 완료: {filename}")
            print(f"📊 총 {len(df)}개 영상 데이터 저장됨")
            
            # 간단한 통계 출력
            print(f"\n📈 수집 통계:")
            print(f"   - 평균 조회수: {df['view_count'].mean():,.0f}회")
            print(f"   - 평균 좋아요: {df['like_count'].mean():,.0f}개")
            print(f"   - 평균 설명 길이: {df['description'].str.len().mean():.0f}자")
            print(f"   - 최신 영상: {df['published_date'].max()}")
            print(f"   - 가장 오래된 영상: {df['published_date'].min()}")
            
            return filename
            
        except Exception as e:
            print(f"❌ CSV 저장 오류: {e}")
            return None
    
    def analyze_descriptions(self, videos_data):
        """영상 설명 간단 분석"""
        if not videos_data:
            return
        
        df = pd.DataFrame(videos_data)
        
        print(f"\n🔍 영상 설명 분석:")
        print(f"   - 총 영상 수: {len(df)}개")
        print(f"   - 설명이 있는 영상: {len(df[df['description'].str.len() > 0])}개")
        print(f"   - 빈 설명: {len(df[df['description'].str.len() == 0])}개")
        print(f"   - 평균 설명 길이: {df['description'].str.len().mean():.0f}자")
        print(f"   - 최장 설명 길이: {df['description'].str.len().max()}자")
        
        # 자주 나오는 키워드 (간단 분석)
        all_descriptions = ' '.join(df['description'].fillna('').astype(str))
        common_words = ['Environment', 'environment', 'Carbon', 'carbon', 'social', 'Social', 'Diversity', 'diversity']
        
        print(f"\n🏷️  주요 키워드 출현 빈도:")
        for word in common_words:
            count = all_descriptions.count(word)
            if count > 0:
                print(f"   - '{word}': {count}회")

def main():
    """메인 실행 함수"""
    # ⚠️ 여기에 발급받은 API 키를 입력하세요!
    API_KEY = "AIzaSyBpXmp5WoYBM6lVtcegDXAZrzU0hIL2rkA"
    
    # API 키 확인
    if API_KEY == "YOUR_YOUTUBE_API_KEY_HERE":
        print("❌ API 키를 입력해주세요!")
        print("📝 코드의 API_KEY 변수에 발급받은 키를 입력하세요.")
        return
    
    print("🚀 나이키 YouTube 영상 설명 추출 시작!")
    print("=" * 50)
    
    # 스크래퍼 초기화
    scraper = NikeYouTubeScraper(API_KEY)
    
    try:
        # 영상 설명 추출 (최대 100개)
        videos_data = scraper.extract_nike_descriptions(max_videos=300)
        
        if videos_data and len(videos_data) > 0:
            # 간단 분석
            scraper.analyze_descriptions(videos_data)
            
            # CSV 저장
            print(f"\n💾 CSV 파일로 저장 중...")
            filename = scraper.save_to_csv(videos_data)
            
            if filename:
                print(f"\n🎉 작업 완료!")
                print(f"📁 저장된 파일: {filename}")
                print(f"📊 추출된 영상 수: {len(videos_data)}개")
                
                # 파일 경로 출력
                import os
                full_path = os.path.abspath(filename)
                print(f"📂 전체 경로: {full_path}")
            
        else:
            print("❌ 데이터 추출에 실패했습니다.")
            print("💡 다음을 확인해보세요:")
            print("   - API 키가 올바른지 확인")
            print("   - YouTube Data API v3가 활성화되어 있는지 확인")
            print("   - API 할당량이 남아있는지 확인")
    
    except KeyboardInterrupt:
        print("\n⏹️  사용자가 작업을 중단했습니다.")
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        print("\n🔧 문제 해결 방법:")
        print("   1. API 키가 올바른지 확인")
        print("   2. 인터넷 연결 상태 확인")
        print("   3. YouTube Data API v3 할당량 확인")
        print("   4. 잠시 후 다시 시도")
        
        # 디버깅 정보
        import traceback
        print(f"\n🐛 디버깅 정보:")
        traceback.print_exc()

    def test_api_key(self):
        """API 키가 작동하는지 테스트"""
        print("🔑 API 키 테스트 중...")
        
        # 간단한 API 호출로 테스트
        test_url = f"{self.base_url}/search"
        params = {
            'part': 'snippet',
            'q': 'test',
            'type': 'video',
            'maxResults': 1,
            'key': self.api_key
        }
        
        try:
            response = requests.get(test_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'items' in data:
                print("✅ API 키가 정상적으로 작동합니다!")
                remaining_quota = response.headers.get('X-RateLimit-Remaining')
                if remaining_quota:
                    print(f"📊 남은 할당량: {remaining_quota}")
                return True
            else:
                print("❌ API 응답이 예상과 다릅니다.")
                return False
                
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                print("❌ API 키가 유효하지 않거나 YouTube Data API v3가 비활성화되어 있습니다.")
                print("💡 해결 방법:")
                print("   1. Google Cloud Console에서 YouTube Data API v3 활성화")
                print("   2. API 키 재생성")
                print("   3. 할당량 확인")
            elif e.response.status_code == 429:
                print("❌ API 할당량이 초과되었습니다.")
                print("💡 내일 다시 시도하거나 할당량을 늘려주세요.")
            else:
                print(f"❌ HTTP 오류: {e}")
            return False
        except Exception as e:
            print(f"❌ API 테스트 오류: {e}")
            return False

if __name__ == "__main__":
    main()

# 간단 테스트용 함수
def test_api_only():
    """API 키만 빠르게 테스트"""
    API_KEY = "YOUR_YOUTUBE_API_KEY_HERE"
    
    if API_KEY == "YOUR_YOUTUBE_API_KEY_HERE":
        print("❌ API 키를 입력해주세요!")
        return
    
    scraper = NikeYouTubeScraper(API_KEY)
    scraper.test_api_key()

# 테스트 실행 방법:
# test_api_only()  # 주석 해제 후 실행

# 필요한 패키지 설치 명령어:
# pip install requests pandas

"""
사용 방법:
1. API_KEY 변수에 발급받은 YouTube Data API v3 키 입력
2. 터미널에서 다음 명령어로 필요한 패키지 설치:
   pip install requests pandas
3. 스크립트 실행: python nike_youtube_scraper.py

결과:
- nike_youtube_descriptions_YYYYMMDD_HHMMSS.csv 파일 생성
- 영상 ID, 제목, 설명, 발행일, 조회수, 좋아요 수 등 포함
- 한글 설명도 완벽 지원 (UTF-8)
"""