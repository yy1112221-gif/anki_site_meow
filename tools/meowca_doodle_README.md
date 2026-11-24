# 묘카냥이 펜 낙서 제작 키트 (meowca_doodle)

원본 묘카냥이(3D 정면 실루엣·얼굴 배치, `cat_base.json`)를 그대로 쓰고, **선만 손으로 대충 그은 조잡한 펜화**로 다시 그리는 도구.
표정 × 자세 × 그림체 × 구도를 조합하고, 옛날 애니메이션처럼 **펜선이 부들부들 떨리는 움직임(라인 보일)**과 **그림체가 바뀌며 지직거리는 전환**을 PNG / GIF / MP4로 뽑는다.

- 필요한 것: Python 3, `numpy`, `Pillow` (MP4는 `ffmpeg`)
- 파일: `doodle.py`(전부), `cat_base.json`(냥이 실루엣·얼굴 위치), `examples/`(카탈로그·예시)
- 저장소 안에서는 `tools/meowca_doodle.py` + `tools/meowca_doodle_base.json` (아래 명령의 `doodle.py` 자리에 `tools/meowca_doodle.py`)
- 스타일 레퍼런스는 "조잡한 펜 낙서 느낌"뿐. 남의 캐릭터·장면을 베끼지 않는다. 냥이는 항상 원본 묘카냥이.

## 빠른 사용

```bash
# 한 장 (정사각 1080, 종이 배경)
python3 doodle.py still --style B --expr mad --pose squash:.6 --out mad.png

# 투명 배경, 냥이만
python3 doodle.py still --expr happy --size 0 --out happy_alpha.png

# 펜선 떨림 반복 (초당 4장, 8장 반복, 떨림 세기 1.8)
python3 doodle.py boil --style B --expr cry --boil 1.8 --fps 4 --frames 8 --out cry.gif

# 릴스(1080×1920): 컷을 이어 붙이고, 바뀔 때마다 지직
python3 doodle.py seq --size 1080x1920 --boil 1.8 --out reel.mp4 \
  --shots "A:base:sit:1.5, B:shock:stretch:.5:1, B:mad:squash:.6:1.5, C:cry:melt:.5:1.5"

# 표정·자세 카탈로그 한 장
python3 doodle.py sheet --style B --out catalog.png
```

`boil`의 `--out`이 `.gif`/`.mp4`가 아니면 그 이름의 폴더에 **투명 PNG 연속**(000.png…)으로 저장 → 영상 편집기·앱에 얹어 쓰기.

## 고를 수 있는 것

### 그림체 `--style`
| 값 | 느낌 |
|---|---|
| `A` | 볼펜 낙서 — 가늘고 떨리는 선, 색 거의 없음 |
| `B` | 매직 + 어긋난 색칠 — 굵은 선, 색이 선에서 어긋남 (기본) |
| `C` | 두 번 긋기 — 외곽선을 두 번 덧그음, 귀는 빗금 |

### 표정 `--expr`
`base`(기본) · `meh`(멍) · `mad`(빡침) · `cry`(울음) · `happy`(∩∩) · `shock`(충격·!·땀) · `sleepy`(ㅡㅡ zZ) · `smug`(의기양양) · `love`(하트 눈) · `dead`(X눈·영혼 이탈) · `confused`(뱅글 눈·?) · `hungry`(초롱 눈·혀·침) · `blank`(정색)

새 표정은 `doodle.py`의 `EXPR`에 한 줄 추가: `eyes`(dot·tiny·big·ring·happy·line·half·x·heart·spiral·cry) + `mouth`(omega·tongue·open·flat·wavy·smile·frown) + `extra`(brows·vein·tears·wobble·sweat·exclaim·question·zzz·sparkle·soul·drool).
**입은 웬만하면 ω 유지**(묘카냥이 정체성).

### 자세 `--pose` (`+`로 이어 붙임, `:값`은 세기)
| 값 | 모양 |
|---|---|
| `sit` | 기본 |
| `squash:1` | 납작 (눌림) |
| `stretch:1` | 길쭉 (놀람·점프 직전) |
| `melt:1` | 녹아내림 (지침·사망) |
| `puff:1` | 빵빵 (화남·뿌듯) |
| `tilt:도` | 바닥 기준 기울기 (−면 왼쪽) |
| `lean:도` | 윗몸만 쏠림 |
| `jump:1` | 붕 뜸 + 바닥 그림자 |
| `flip` | 좌우 반전 |

예: `jump:1+stretch:.4`, `flip+tilt:10`, `melt:.5+tilt:-6`

### 구도
- `--size 1080x1920`(릴스) / `1080x1080`(피드) / `0`(냥이만 투명)
- `--x .5 --y .82` = 냥이 바닥 가운데 위치(0~1), `--w .8` = 냥이 폭(캔버스 대비). 클로즈업은 `--w 1.6 --y 1.1`처럼 키우고 내림.
- `--bg paper`(종이색) / `none`(투명) / `#ffffff`

### 움직임
- `--boil` 떨림 세기 (0 = 안 떨림, 1 = 약, **1.8 = 기본 권장**, 2.5 = 과격). 매 프레임 펜선만 새로 긋고 모양·표정은 유지.
- `--fps 4` 옛날 애니 느낌. 8~12면 더 부드러움.
- `seq --glitch 1.0` 컷 전환 지직 세기(0 = 끔). 앞 컷과 반쯤 섞인 프레임에 가로 띠 밀림 + 색 어긋남 + 노이즈.
- `--seed` 같은 값이면 같은 냥이(짝짝이 눈·삐뚤기). 여러 마리를 다르게 하려면 seed만 바꿈.

## 파이썬에서 직접 (여러 마리·자유 구도)

```python
import sys; sys.path.insert(0, 'meowca_doodle')
from doodle import draw_cat, compose, save_anim, glitch
frames = []
for k in range(8):   # 두 마리, 서로 다른 표정, 펜선 떨림
    a = draw_cat('B', 'mad',   'puff:.6',  seed=2, frame=k + 1, boil=1.8)
    b = draw_cat('A', 'meh',   'tilt:-8', seed=5, frame=k + 1, boil=1.8)
    frames.append(compose(1080, 1080, [(a, .3, .8, .5), (b, .72, .85, .4)]))
save_anim(frames, 'duo.gif', fps=4)
```
`draw_cat(style, expr, pose, seed, frame, boil, scale=.5)` → 투명 RGBA 한 장 (frame=0, boil=0이면 안 떨리는 기준 그림).

## 지킬 것
- 냥이 모양(몸·귀·ω 입·볼 빗금·수염·앞발)은 `cat_base.json` 기준. 꼬리 없음.
- 레퍼런스 작품의 캐릭터·포즈·장면·대사를 따라 하지 않는다(느낌만).
- 앱(index.html)에 넣는 건 ① 개발 채팅이 결정. 그림·데이터는 PR로.
