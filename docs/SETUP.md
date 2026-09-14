# MVP 실행 가이드 - Phase 2

이 문서는 개발 지식이 많지 않아도 현재 구현된 **한국어 실시간 음성 인식 + 영어 자동 번역** 기능을 실행할 수 있도록 작성했습니다.

현재 버전은 아직 PowerPoint 위 자막 Overlay 전 단계입니다.

---

## 1. 준비물

- Windows 10 또는 Windows 11 PC
- 인터넷 연결
- 마이크
  - 노트북 내장 마이크도 가능
  - 외부 USB/무선 마이크도 가능
- Python 3.11 또는 3.12 권장
- Azure 계정

---

## 2. Azure에서 준비할 것

현재 프로그램은 두 기능을 사용합니다.

1. **Azure Speech**: 한국어 음성을 글자로 변환
2. **Azure Translator**: 확정된 한국어 문장을 영어로 번역

처음에는 Speech와 Translator를 각각 별도 리소스로 만들어도 됩니다.

Azure의 multi-service 리소스를 사용하는 경우에는 동일한 Key/Region을 두 설정에 사용할 수도 있습니다.

### Speech에서 확인할 값

- Key
- Region

### Translator에서 확인할 값

- Key
- Region
- Endpoint

Translator 기본 Endpoint는 다음 값을 사용할 수 있습니다.

```text
https://api.cognitive.microsofttranslator.com
```

> 실제 Azure 리소스의 Key와 Region을 사용해야 합니다. API Key는 GitHub에 공개하지 마세요.

---

## 3. 프로젝트 다운로드

Git이 설치되어 있다면 PowerShell 또는 명령 프롬프트에서:

```powershell
git clone https://github.com/sanikani/live-translation-overlay.git
cd live-translation-overlay
```

이미 내려받았다면 최신 코드만 받습니다.

```powershell
git pull
```

Git을 사용하지 않는다면 GitHub의 **Code → Download ZIP**으로 내려받은 뒤 압축을 풀어도 됩니다.

---

## 4. Python 가상환경 만들기

프로젝트 폴더에서 PowerShell을 엽니다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

PowerShell 실행 정책 때문에 활성화가 막힌 경우 명령 프롬프트(cmd)에서:

```bat
.venv\Scripts\activate.bat
```

를 실행해도 됩니다.

이미 Phase 1에서 가상환경을 만들었다면 새로 만들 필요는 없습니다.

---

## 5. 필요한 패키지 설치

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Phase 2에서는 Translator 호출을 위해 `requests`가 추가되었습니다.

주요 패키지:

- PySide6: 프로그램 화면
- Azure Speech SDK: 실시간 음성 인식
- requests: Azure Translator 호출
- python-dotenv: Azure 설정 읽기
- sounddevice: 연결된 마이크 목록 확인

---

## 6. Azure Key 설정

프로젝트의 `.env.example` 파일을 복사해서 이름을 `.env`로 변경합니다.

Windows 명령 프롬프트:

```bat
copy .env.example .env
```

그 후 `.env`를 메모장으로 열어 실제 값을 입력합니다.

```text
# Azure Speech-to-Text
AZURE_SPEECH_KEY=실제_Speech_Key
AZURE_SPEECH_REGION=실제_Speech_Region
AZURE_SPEECH_LANGUAGE=ko-KR

# Azure Translator
AZURE_TRANSLATOR_KEY=실제_Translator_Key
AZURE_TRANSLATOR_REGION=실제_Translator_Region
AZURE_TRANSLATOR_ENDPOINT=https://api.cognitive.microsofttranslator.com
```

예:

```text
AZURE_SPEECH_KEY=1234567890abcdef...
AZURE_SPEECH_REGION=koreacentral
AZURE_SPEECH_LANGUAGE=ko-KR

AZURE_TRANSLATOR_KEY=abcdef1234567890...
AZURE_TRANSLATOR_REGION=koreacentral
AZURE_TRANSLATOR_ENDPOINT=https://api.cognitive.microsofttranslator.com
```

### Speech와 Translator가 같은 Azure multi-service 리소스인 경우

해당 리소스가 두 서비스를 모두 지원한다면 Key와 Region을 동일하게 입력할 수 있습니다.

```text
AZURE_SPEECH_KEY=같은_Key
AZURE_SPEECH_REGION=같은_Region

AZURE_TRANSLATOR_KEY=같은_Key
AZURE_TRANSLATOR_REGION=같은_Region
```

### 중요

`.env`에는 API Key가 들어가므로 GitHub에 올리면 안 됩니다.

저장소의 `.gitignore`에서 `.env`를 제외하도록 설정되어 있습니다.

---

## 7. 실행

가장 간단한 방법:

```bat
run.bat
```

직접 실행:

```powershell
python main.py
```

---

## 8. 사용 방법

프로그램이 실행되면:

1. 사용할 마이크를 선택합니다.
2. 처음에는 **기본 마이크** 사용을 권장합니다.
3. **음성 인식 및 번역 시작**을 누릅니다.
4. 한국어로 자연스럽게 발표합니다.
5. 말하는 중간 내용은 **현재 듣는 내용**에 표시됩니다.
6. 문장이 확정되면 **확정된 한국어** 영역에 누적됩니다.
7. 확정된 문장만 Azure Translator로 전송됩니다.
8. 번역 결과가 **영어 번역** 영역에 표시됩니다.
9. 끝나면 **중지**를 누릅니다.

---

## 9. 왜 말하는 중간 문장은 번역하지 않나요?

음성 인식기는 발표자가 말을 끝내기 전까지 결과를 계속 수정합니다.

예:

```text
다음
다음 주
다음 주 금요일
다음 주 금요일까지 신청
다음 주 금요일까지 신청해 주세요.
```

이 내용을 전부 번역하면 화면이 계속 바뀌고 번역 API 호출량도 불필요하게 증가합니다.

그래서 현재 프로그램은 마지막 문장이 확정되었을 때만 한 번 번역합니다.

---

## 10. 정상 동작 예시

강사가 말합니다.

```text
다음 주 금요일까지 신청서를 제출해 주세요.
```

화면:

```text
확정된 한국어
다음 주 금요일까지 신청서를 제출해 주세요.

영어 번역
Please submit the application form by next Friday.
```

실제 번역 표현은 Azure Translator 결과에 따라 조금 달라질 수 있습니다.

---

## 11. 번역 오류가 발생하면

번역 API 오류가 발생해도 **음성 인식 자체는 중단하지 않도록 구현**되어 있습니다.

예를 들어 인터넷 상태가 잠시 나빠져 번역 요청 하나가 실패하더라도 다음 한국어 음성은 계속 인식합니다.

프로그램 하단에 번역 오류 메시지가 표시됩니다.

---

## 12. 문제가 생겼을 때

### "Azure Speech 설정 필요"

다음 값이 `.env`에 있는지 확인합니다.

```text
AZURE_SPEECH_KEY=
AZURE_SPEECH_REGION=
```

### 영어 번역 상태가 "설정 필요"

다음 값이 비어 있는지 확인합니다.

```text
AZURE_TRANSLATOR_KEY=
```

Translator Region도 실제 Azure 리소스 값으로 설정하는 것을 권장합니다.

### Translator 인증 오류

- Key가 올바른지 확인
- Region이 리소스와 일치하는지 확인
- Speech Key와 Translator Key를 서로 잘못 넣지 않았는지 확인

### 마이크가 안 보임

1. Windows 설정 → 개인정보 및 보안 → 마이크
2. 마이크 접근 권한 허용
3. 프로그램에서 **새로고침**
4. 우선 **기본 마이크**로 테스트

---

## 13. 현재 검증할 항목

### Phase 1

- [ ] 프로그램이 정상 실행된다.
- [ ] 기본 마이크로 음성 인식이 시작된다.
- [ ] 한국어 중간 인식 결과가 표시된다.
- [ ] 한국어 확정 문장이 표시된다.
- [ ] 30분 연속 인식이 가능하다.
- [ ] 외부 마이크를 사용할 수 있다.

### Phase 2

- [ ] 확정된 한국어만 번역된다.
- [ ] 영어 번역 결과가 표시된다.
- [ ] 같은 확정 이벤트가 연속 발생해도 중복 번역되지 않는다.
- [ ] 번역 중에도 UI와 음성 인식이 멈추지 않는다.
- [ ] 번역 요청 하나가 실패해도 STT는 계속된다.

테스트는 이후 실제 Windows PC와 Azure 계정으로 진행합니다.

다음 구현 단계는 **Phase 3: 영어·중국어·베트남어·태국어를 동시에 선택해 번역하는 기능**입니다.
