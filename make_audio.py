# -*- coding: utf-8 -*-
"""
퀴즈 문제 읽어주기용 자연스러운 음성(mp3) 만들기  (Microsoft 신경망 음성 - 한국어)

사용법 (index.html, questions.js 가 있는 폴더에서):
    pip install edge-tts
    python make_audio.py              # 전체 만들기 (이미 만든 파일은 건너뜀 → 중단했다가 다시 실행해도 이어서 진행)
    python make_audio.py --clean      # 안 쓰는 옛 mp3 지우기 (문장을 고친 뒤 정리용)
    python make_audio.py --limit 50   # 먼저 50개만 시험 삼아 만들어 들어보기
    python make_audio.py --voice ko-KR-InJoonNeural   # 남성 목소리 (기본: ko-KR-SunHiNeural 여성)

※ 인터넷이 되는 PC에서 실행하세요. 결과는 audio 폴더에 생기며, index.html 과 함께 올리면 됩니다.
※ 문제를 추가·수정했으면 다시 실행하세요 (새 문장만 추가로 만듭니다). node 가 설치돼 있으면 목록도 자동으로 갱신합니다.
"""
import asyncio, json, os, shutil, subprocess, sys, argparse

ap = argparse.ArgumentParser()
ap.add_argument('--voice', default='ko-KR-SunHiNeural')
ap.add_argument('--rate', default='-5%')
ap.add_argument('--limit', type=int, default=0)
ap.add_argument('--workers', type=int, default=8)
ap.add_argument('--clean', action='store_true', help='지금 목록에 없는(안 쓰는) mp3 를 audio 폴더에서 지웁니다')
a = ap.parse_args()

here = os.path.dirname(os.path.abspath(__file__))
os.chdir(here)
if shutil.which('node') and os.path.exists('make_audio_list.js'):
    subprocess.run(['node', 'make_audio_list.js', '.'], check=False)
if not os.path.exists('audio_texts.json'):
    sys.exit('audio_texts.json 이 없습니다. (node 설치 후 다시 실행하거나, 보내드린 audio_texts.json 을 같은 폴더에 두세요)')

try:
    import edge_tts
except ImportError:
    sys.exit('먼저 설치하세요:  pip install edge-tts')

items = json.load(open('audio_texts.json', encoding='utf-8'))
os.makedirs('audio', exist_ok=True)
if a.clean:
    keep = {x['file'] for x in items}
    old = [f for f in os.listdir('audio') if (f.endswith('.mp3') or f.endswith('.tmp')) and f not in keep]
    for f in old:
        os.remove(os.path.join('audio', f))
    print(f'안 쓰는 파일 {len(old)}개를 지웠습니다.')
    sys.exit(0)
todo = [x for x in items if not os.path.exists(os.path.join('audio', x['file']))]
if a.limit:
    todo = todo[:a.limit]
print(f'전체 {len(items)}개 중 새로 만들 것 {len(todo)}개')

done = 0
async def work(q):
    global done
    while True:
        try:
            x = q.get_nowait()
        except asyncio.QueueEmpty:
            return
        path = os.path.join('audio', x['file'])
        for t in range(4):
            try:
                await edge_tts.Communicate(x['text'], a.voice, rate=a.rate).save(path + '.tmp')
                if os.path.getsize(path + '.tmp') > 0:
                    os.replace(path + '.tmp', path)
                    break
            except Exception as e:
                await asyncio.sleep(1 + t * 2)
        else:
            print('실패:', x['text'][:30])
        done += 1
        if done % 100 == 0:
            print(f'{done}/{len(todo)}')

async def main():
    q = asyncio.Queue()
    for x in todo:
        q.put_nowait(x)
    await asyncio.gather(*[work(q) for _ in range(a.workers)])

asyncio.run(main())
print('완료! audio 폴더를 index.html 과 같은 곳에 두세요.')
