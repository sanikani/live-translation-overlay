# Phase 1 실행 가이드

이 문서는 개발 지식이 많지 않아도 **마이크 → 한국어 실시간 음성 인식** 기능을 실행할 수 있도록 작성했습니다.

현재 Phase 1에서는 번역과 자막 Overlay는 아직 구현하지 않습니다.

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

## 2. Azure Speech 리소스 준비

Azure Speech를 사용하려면 **Key**와 **Region** 두 값이 필요합니다.

1. Azure Portal에 로그인합니다.
2. Speech 기능을 사용할 수 있는 Azure AI/Foundry 리소스를 생성합니다.
3. 생성한 리소스의 **Keys and Endpoint** 화면에서 Key와 Region을 확인합니다.
4. Key는 다른 사람에게 공개하지 않습니다.

예:

```text
Key     : abcdefg....
Region  : koreacentral
```

> Region은 예시 값을 그대로 쓰는 것이 아니라, 실제 생성한 Azure 리소스의 Region 값을 사용해야 합니다.

---

## 3. 프로젝트 다운로드

Git이 설치되어 있다면 PowerShell 또는 명령 프롬프트에서:

```powershell
git clone https://github.com/sanikani/live-translation-overlay.git
cd live-translation-overlay
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

---

## 5. 필요한 패키지 설치

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

설치되는 주요 패키지:

- PySide6: 프로그램 화면
- Azure Speech SDK: 실시간 음성 인식
- python-dotenv: Azure 설정 읽기
- sounddevice: 연결된 마이크 목록 확인

---

## 6. Azure Key 설정

프로젝트의 `.env.example` 파일을 복사해서 이름을 `.env`로 변경합니다.

Windows 명령 프롬프트:

```bat
copy .env.example .env
```

그 후 `.env`를 메모장으로 열어 아래 내용을 실제 값으로 변경합니다.

```text
AZURE_SPEECH_KEY=실제_Azure_Key
AZURE_SPEECH_REGION=실제_Region
AZURE_SPEECH_LANGUAGE=ko-KR
```

예:

```text
AZURE_SPEECH_KEY=1234567890abcdef...
AZURE_SPEECH_REGION=koreacentral
AZURE_SPEECH_LANGUAGE=ko-KR
```

### 중요

`.env`에는 API Key가 들어가므로 GitHub에 올리면 안 됩니다.

현재 저장소의 `.gitignore`에서 `.env`를 제외하도록 설정되어 있습니다.

---

## 7. 실행

가장 간단한 방법은 프로젝트 폴더에서:

```bat
run.bat
```

을 실행하는 것입니다.

직접 실행하려면:

```powershell
python main.py
```

---

## 8. 사용 방법

프로그램이 실행되면:

1. 마이크를 선택합니다.
2. 처음에는 **기본 마이크** 사용을 권장합니다.
3. **음성 인식 시작**을 누릅니다.
4. 한국어로 자연스럽게 말합니다.
5. 말하는 중간 내용은 **현재 듣는 내용**에 표시됩니다.
6. Azure가 문장을 확정하면 **확정된 문장** 영역에 누적됩니다.
7. 끝나면 **중지**를 누릅니다.

---

## 9. 정상 동작 예시

말하기:

```text
안녕하세요. 오늘은 학부모 교육을 시작하겠습니다.
```

화면:

```text
현재 듣는 내용
안녕하세요 오늘은 학부모 교육을...

확정된 문장
안녕하세요. 오늘은 학부모 교육을 시작하겠습니다.
```

---

## 10. 문제가 생겼을 때

### "Azure Speech 설정이 없습니다"

`.env` 파일이 프로젝트 최상위 폴더에 있는지 확인합니다.

다음 두 값이 비어 있으면 안 됩니다.

```text
AZURE_SPEECH_KEY=
AZURE_SPEECH_REGION=
```

### 인증 오류

Key와 Region이 같은 Azure 리소스의 값인지 확인합니다.

Region 값이 실제 Azure 리소스와 다르면 인증에 실패할 수 있습니다.

### 마이크가 안 보임

1. Windows 설정 → 개인정보 및 보안 → 마이크로 이동합니다.
2. 마이크 접근 권한을 허용합니다.
3. 프로그램에서 **새로고침**을 누릅니다.
4. 그래도 안 되면 기본 마이크를 선택해 테스트합니다.

### 특정 마이크를 선택하면 시작되지 않음

Phase 1에서는 Windows 오디오 장치 이름과 Azure Speech SDK의 장치 선택이 PC 환경에 따라 다를 수 있습니다.

먼저 **기본 마이크**로 기능 자체가 정상 동작하는지 확인합니다.

실제 학교 테스트 단계에서 마이크 장치 선택 호환성을 별도로 검증합니다.

---

## 11. Phase 1 검증 항목

- [ ] 프로그램이 정상 실행된다.
- [ ] 기본 마이크로 음성 인식이 시작된다.
- [ ] 한국어 중간 인식 결과가 표시된다.
- [ ] 한국어 확정 문장이 표시된다.
- [ ] 시작/중지를 반복해도 프로그램이 종료되지 않는다.
- [ ] 30분 연속 인식이 가능하다.
- [ ] 외부 마이크를 사용할 수 있다.

Phase 1의 실기기 검증이 끝나면 다음 단계인 **한국어 확정 문장 → 영어 번역**을 구현합니다.
