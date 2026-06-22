---
name: source-handler
description: >
  Prepare the scan target source safely: auto-detect type (local path / ZIP / GitHub URL),
  extract or clone, enforce 100MB size limit, manage sandbox environment.
---

# Source Handler Skill

## 개요

검사 대상 소스를 안전하게 준비하는 스킬. ZIP 파일 압축 해제, GitHub 리포지토리 클론 등 다양한 소스 유형을 처리하여 샌드박스 환경에 준비합니다.

## 역할

1. 소스 유형 자동 감지 (로컬 경로, ZIP 파일, GitHub URL)
2. ZIP 파일 안전한 압축 해제
3. GitHub 리포지토리 shallow clone
4. 용량 제한 검증 (100MB)
5. 샌드박스 환경 관리

## 호출 방법

```
@source-handler <source> [options]
```

### 소스 유형

| 유형 | 예시 |
|------|------|
| 로컬 경로 | `/Users/user/project` |
| ZIP 파일 | `/path/to/project.zip` |
| GitHub URL | `https://github.com/owner/repo` |
| GitHub 단축 | `owner/repo` |

### 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--max-size` | 최대 허용 용량 (MB) | `100` |
| `--sandbox` | 샌드박스 경로 | `/tmp/security-scan` |
| `--keep` | 스캔 후 소스 유지 | `false` |
| `--branch` | 클론할 브랜치 | `main` or `master` |

---

## 샌드박스 환경

### 기본 경로
```
/tmp/security-scan/
├── sources/           # 추출/클론된 소스
│   └── {session-id}/  # 세션별 격리
├── reports/           # 생성된 보고서
└── temp/              # 임시 파일
```

### 세션 ID 생성
```
{timestamp}-{random-hash}
예: 20260205-143022-a1b2c3d4
```

### 자동 정리
- 스캔 완료 후 자동 삭제 (기본)
- `--keep` 옵션으로 유지 가능
- 24시간 후 자동 만료

---

## ZIP 파일 처리

### 지원 형식
| 형식 | 확장자 |
|------|--------|
| ZIP | `.zip` |
| TAR.GZ | `.tar.gz`, `.tgz` |
| TAR | `.tar` |
| 7Z | `.7z` |

### 처리 절차

```
1. 파일 유효성 검증
   - 파일 존재 확인
   - 용량 확인 (≤ 100MB)
   - 형식 확인

2. 보안 검증
   - Zip Slip 취약점 방지
   - 심볼릭 링크 제한
   - 숨김 파일 경고

3. 압축 해제
   - 샌드박스 경로로 추출
   - 경로 탈출 방지

4. 결과 반환
   - 추출된 경로
   - 파일 통계
```

### Zip Slip 방지

```python
# 경로 탈출 공격 방지
def safe_extract(zip_path, extract_to):
    for member in archive.namelist():
        # 절대 경로 거부
        if member.startswith('/'):
            raise SecurityError("Absolute path not allowed")
        
        # 상위 디렉토리 탐색 거부
        if '..' in member:
            raise SecurityError("Path traversal not allowed")
        
        # 추출 경로가 샌드박스 내부인지 확인
        target = os.path.join(extract_to, member)
        if not target.startswith(extract_to):
            raise SecurityError("Path escape detected")
```

### 용량 검증

```python
def validate_zip_size(zip_path, max_size_mb=100):
    # 압축 파일 크기
    compressed_size = os.path.getsize(zip_path)
    
    # 압축 해제 후 예상 크기
    with zipfile.ZipFile(zip_path) as zf:
        uncompressed_size = sum(f.file_size for f in zf.infolist())
    
    if uncompressed_size > max_size_mb * 1024 * 1024:
        raise SizeError(f"Uncompressed size exceeds {max_size_mb}MB limit")
```

---

## GitHub 리포지토리 처리

### 지원 URL 형식

```
# HTTPS URL
https://github.com/owner/repo
https://github.com/owner/repo.git
https://github.com/owner/repo/tree/branch

# 단축 형식
owner/repo
owner/repo@branch

# GitLab (추후 지원)
https://gitlab.com/owner/repo
```

### Shallow Clone (권장)

소스 코드만 필요하므로 히스토리 제외:

```bash
# 기본: 깊이 1, 단일 브랜치
git clone --depth 1 --single-branch <url> <path>

# 특정 브랜치
git clone --depth 1 --single-branch --branch <branch> <url> <path>
```

### 제외 항목

| 제외 대상 | 방법 |
|-----------|------|
| Git 히스토리 | `--depth 1` |
| 다른 브랜치 | `--single-branch` |
| Git LFS 파일 | `GIT_LFS_SKIP_SMUDGE=1` |
| 서브모듈 | 기본 제외 (옵션으로 포함 가능) |

### 용량 사전 확인

```bash
# GitHub API로 리포지토리 크기 확인
curl -s https://api.github.com/repos/{owner}/{repo} | jq '.size'
# 결과: KB 단위

# GitLab API
curl -s https://gitlab.com/api/v4/projects/{id} | jq '.statistics.repository_size'
```

### 처리 절차

```
1. URL 파싱
   - owner, repo, branch 추출
   - URL 유효성 검증

2. 용량 사전 확인
   - GitHub/GitLab API 호출
   - 예상 크기 확인 (≤ 100MB)

3. Shallow Clone
   - 깊이 1로 클론
   - LFS 스킵
   - 단일 브랜치

4. 후처리
   - .git 디렉토리 제거 (선택)
   - 불필요 파일 정리

5. 결과 반환
   - 클론된 경로
   - 파일 통계
```

---

## 출력 형식

```json
{
  "status": "success",
  "source_type": "github",
  "original_source": "https://github.com/owner/repo",
  "sandbox_path": "/tmp/security-scan/sources/20260205-143022-a1b2c3d4/repo",
  "session_id": "20260205-143022-a1b2c3d4",
  "statistics": {
    "total_files": 156,
    "total_size_bytes": 2457600,
    "total_size_mb": 2.34
  },
  "metadata": {
    "branch": "main",
    "clone_depth": 1,
    "git_history_excluded": true,
    "lfs_skipped": true
  },
  "warnings": [],
  "expires_at": "2026-02-06T14:30:22Z"
}
```

---

## 보안 제약

### 용량 제한
| 항목 | 제한 |
|------|------|
| 압축 파일 크기 | 100MB |
| 압축 해제 후 크기 | 100MB |
| GitHub 리포지토리 | 100MB |
| 단일 파일 | 50MB |

### 파일 유형 제한
```
# 압축 해제 시 제외
*.exe, *.dll, *.so      # 실행 파일 (분석 대상으로는 포함)
*.iso, *.dmg, *.img     # 디스크 이미지
*.mp4, *.avi, *.mov     # 비디오
*.mp3, *.wav            # 오디오
```

### 경로 제한
```
# 허용된 샌드박스 경로만 사용
/tmp/security-scan/
$TMPDIR/security-scan/  # macOS
/var/tmp/security-scan/ # 대안
```

### 네트워크 제한
```
# 허용된 도메인만 클론
- github.com
- gitlab.com
- bitbucket.org
```

---

## 에러 처리

| 에러 코드 | 설명 | 조치 |
|-----------|------|------|
| `SIZE_EXCEEDED` | 용량 초과 | 100MB 이하 소스 사용 |
| `INVALID_FORMAT` | 지원하지 않는 형식 | ZIP, TAR.GZ, GitHub URL 사용 |
| `PATH_TRAVERSAL` | 경로 탈출 시도 | 보안 위반, 처리 중단 |
| `CLONE_FAILED` | Git 클론 실패 | URL 및 권한 확인 |
| `NETWORK_ERROR` | 네트워크 오류 | 연결 상태 확인 |
| `API_RATE_LIMIT` | GitHub API 한도 | 잠시 후 재시도 |

---

## 사용 예시

### ZIP 파일 처리

```
사용자: @source-handler /path/to/project.zip

응답:
[SOURCE_HANDLER] ZIP 파일 처리 중...

✓ 파일 검증 완료
  - 압축 크기: 15.2 MB
  - 예상 해제 크기: 42.8 MB
  - 용량 제한 내 (≤ 100MB)

✓ 보안 검증 완료
  - Zip Slip: 안전
  - 심볼릭 링크: 없음

✓ 압축 해제 완료
  - 경로: /tmp/security-scan/sources/20260205-143022-a1b2c3d4/project
  - 파일 수: 234개
  - 총 크기: 42.8 MB

[스캔 준비 완료]
→ @threat-scan-orchestrator /tmp/security-scan/sources/20260205-143022-a1b2c3d4/project
```

### GitHub 리포지토리 처리

```
사용자: @source-handler https://github.com/expressjs/express

응답:
[SOURCE_HANDLER] GitHub 리포지토리 처리 중...

✓ 리포지토리 정보 확인
  - Owner: expressjs
  - Repo: express
  - 예상 크기: 8.5 MB (API 기준)
  - 용량 제한 내 (≤ 100MB)

✓ Shallow Clone 실행
  - 브랜치: master
  - 깊이: 1
  - Git 히스토리: 제외
  - LFS: 스킵

✓ 클론 완료
  - 경로: /tmp/security-scan/sources/20260205-143522-b2c3d4e5/express
  - 파일 수: 189개
  - 총 크기: 7.2 MB

[스캔 준비 완료]
→ @threat-scan-orchestrator /tmp/security-scan/sources/20260205-143522-b2c3d4e5/express
```

### 용량 초과 처리

```
사용자: @source-handler https://github.com/large/repository

응답:
[SOURCE_HANDLER] 오류

✗ 용량 초과
  - 리포지토리 크기: 250 MB
  - 허용 한도: 100 MB

권장 조치:
1. 특정 디렉토리만 스캔하려면 직접 클론 후 경로 지정
2. --max-size 옵션으로 한도 조정 (주의 필요)
3. 리포지토리 일부만 포함된 ZIP 파일 사용
```

---

## 정리 명령

### 수동 정리
```
@source-handler cleanup [session-id]
@source-handler cleanup --all
```

### 자동 정리 정책
- 스캔 완료 후 즉시 삭제 (기본)
- `--keep` 사용 시 24시간 후 만료
- 시스템 재시작 시 `/tmp` 자동 정리

---

## 통합 워크플로우

```
[사용자 입력]
     │
     ├─ 로컬 경로 ────→ 직접 스캔
     │
     ├─ ZIP 파일 ─────→ @source-handler (압축 해제)
     │                         │
     ├─ GitHub URL ───→ @source-handler (shallow clone)
     │                         │
     └─────────────────────────┴──→ 샌드박스 경로
                                         │
                               @threat-scan-orchestrator
                                         │
                                   스캔 완료
                                         │
                                   자동 정리
```

---

## 제약 사항

1. **시스템 명령 실행**: `git clone`, `unzip` 등 필요
2. **네트워크 접근**: GitHub API 및 클론 필요
3. **파일 시스템 접근**: 샌드박스 경로 쓰기 권한 필요
4. **Private 리포지토리**: 인증 필요 (현재 미지원)

---

## 버전 정보

- **Skill Version**: 1.0.0
- **지원 소스**: 로컬 경로, ZIP, GitHub
- **용량 제한**: 100MB
