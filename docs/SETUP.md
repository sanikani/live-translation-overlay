# MVP 실행 가이드 - Phase 4

현재 버전은 **한국어 발표 음성 인식 → 여러 언어 동시 번역 → 강의자료 위 자막 Overlay**까지 구현되어 있습니다.

아직 실제 Windows PC, Azure 계정, PowerPoint 전체화면 환경에서의 검증은 진행하지 않은 상태입니다.

---

## 1. 준비물

- Windows 10 또는 Windows 11
- 인터넷 연결
- 마이크
- Python 3.11 또는 3.12 권장
- Azure 계정
- 테스트용 PowerPoint / PDF / 브라우저 화면

---

## 2. 현재 지원 번역 언어

프로그램에서 필요한 언어만 체크할 수 있습니다.

- English
- 中文 (중국어 간체)
- Tiếng Việt
- ภาษาไทย

여러 언어를 동시에 선택할 수 있습니다.

---

## 3. Azure에서 준비할 것

현재 두 기능을 사용합니다.

1. **Azure Speech** - 한국어 음성을 텍스트로 변환
2. **Azure Translator** - 확정된 한국어 문장을 선택 언어로 번역

필요한 값:

### Azure Speech

- Key
- Region

### Azure Translator

- Key
- Region
- Endpoint

기본 Translator Endpoint:

```text
https://api.cognitive.microsofttranslator.com
```

---

## 4. 프로젝트 다운로드

처음 받는 경우:

```powershell
git clone https://github.com/sanikani/live-translation-overlay.git
cd live-translation-overlay
```

이미 받은 경우:

```powershell
git pull
```

Git을 사용하지 않는 경우 GitHub의 **Code → Download ZIP**을 이용해도 됩니다.

---

## 5. Python 환경 준비

프로젝트 폴더에서:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

이미 가상환경을 만들었다면:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

만 다시 실행하면 됩니다.

---

## 6. Azure 설정

`.env.example`을 복사해서 `.env`를 만듭니다.

```bat
copy .env.example .env
```

그 후 `.env`에 실제 값을 입력합니다.

```text
AZURE_SPEECH_KEY=실제_Speech_Key
AZURE_SPEECH_REGION=실제_Speech_Region
AZURE_SPEECH_LANGUAGE=ko-KR

AZURE_TRANSLATOR_KEY=실제_Translator_Key
AZURE_TRANSLATOR_REGION=실제_Translator_Region
AZURE_TRANSLATOR_ENDPOINT=https://api.cognitive.microsofttranslator.com
```

API Key는 GitHub에 올리면 안 됩니다. `.env`는 이미 `.gitignore`에 포함되어 있습니다.

---

## 7. 실행

가장 간단한 실행 방법:

```bat
run.bat
```

또는:

```powershell
python main.py
```

---

## 8. 실제 사용 순서

프로그램에서 다음 순서로 설정합니다.

### 1) 마이크 선택

처음에는 **기본 마이크**를 권장합니다.

### 2) 번역 언어 선택

예:

```text
☑ English
☑ 中文
☑ Tiếng Việt
☐ ภาษาไทย
```

한 개 이상 선택해야 합니다.

### 3) 자막을 띄울 화면 선택

노트북에 프로젝터나 외부 모니터가 연결되어 있으면:

```text
화면 1 - 노트북
화면 2 - 프로젝터
```

처럼 표시됩니다.

강의자료가 표시되는 화면을 선택합니다.

### 4) 자막 위치 선택

- 화면 하단
- 화면 상단

### 5) 글자 크기 조절

슬라이더로 18~52 범위에서 조절할 수 있습니다.

### 6) 실시간 번역 시작

**실시간 번역 시작** 버튼을 누릅니다.

그 후 평소처럼 PowerPoint, PDF 또는 웹 브라우저에서 강의자료를 엽니다.

---

## 9. 자막 동작 방식

강사가 말합니다.

```text
다음 주 금요일까지 신청서를 제출해 주세요.
```

음성 인식 결과가 확정되면 한 번의 Translator 요청으로 선택한 여러 언어를 번역합니다.

예:

```text
English   Please submit the application by next Friday.
中文      请在下周五之前提交申请表。
Tiếng Việt  Vui lòng nộp đơn trước thứ Sáu tuần sau.
```

이 결과가 선택한 화면 위의 반투명 자막창에 표시됩니다.

---

## 10. Overlay 특징

자막창은 다음 방식으로 동작하도록 구현되어 있습니다.

- 강의자료보다 위에 표시
- 창 테두리 없음
- 반투명 배경
- 마우스 클릭이 자막창을 통과함
- 키보드 포커스를 가져가지 않음
- 최신 번역 문장만 화면에 표시
- 메인 프로그램에는 전체 번역 기록 누적

따라서 자막이 PowerPoint 버튼이나 화면 조작을 막지 않는 것을 목표로 합니다.

---

## 11. 현재 꼭 확인해야 하는 테스트

테스트는 나중에 진행해도 되지만 아래 항목은 실제 PC에서 반드시 확인해야 합니다.

### 음성 인식

- [ ] 기본 마이크로 한국어 인식
- [ ] 외부 마이크 인식
- [ ] 중간 문장 / 확정 문장 구분
- [ ] 30분 이상 연속 동작

### 번역

- [ ] 영어 번역
- [ ] 중국어 간체 번역
- [ ] 베트남어 번역
- [ ] 태국어 번역
- [ ] 2~4개 언어 동시 번역
- [ ] 실제 번역 지연 시간

### Overlay

- [ ] PowerPoint 일반 창 위 표시
- [ ] PowerPoint 슬라이드쇼 전체화면 위 표시
- [ ] PDF 위 표시
- [ ] 브라우저 전체화면 위 표시
- [ ] 하단 위치
- [ ] 상단 위치
- [ ] 글자 크기 조절
- [ ] 자막 위를 클릭해도 아래 강의자료가 조작됨

### 듀얼 모니터 / 프로젝터

- [ ] 화면 1 선택
- [ ] 화면 2 선택
- [ ] 프로젝터 화면에 자막 표시
- [ ] 발표자 화면과 프로젝터 화면이 다른 경우 정상 동작

---

## 12. 문제가 생겼을 때 우선 확인할 것

### 음성 인식이 안 됨

- Windows 마이크 권한
- Azure Speech Key
- Azure Speech Region
- 기본 마이크 설정

### 번역이 안 됨

- Azure Translator Key
- Azure Translator Region
- 인터넷 연결

### 자막이 안 보임

- 올바른 화면을 선택했는지 확인
- PowerPoint가 어느 모니터에서 실행 중인지 확인
- 프로그램에서 번역 결과가 실제로 나오고 있는지 확인

### 자막이 너무 큼 / 작음

프로그램의 **글자 크기** 슬라이더를 조절합니다.

---

## 13. 현재 단계

현재 코드 기준 핵심 MVP는 다음 흐름까지 연결되어 있습니다.

```text
마이크
→ 한국어 STT
→ 확정 문장
→ 다국어 동시 번역
→ Overlay
→ PowerPoint / PDF 위 표시
```

다음 작업은 기능 추가보다 **실제 Windows 환경에서 오류를 확인하고 수정하는 작업**이 우선입니다.
