"""
MeritScore 5-Minute Demo Recorder
Full UI visible (1440x960), ~300s total
"""

import imageio
import subprocess
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "https://meritscore.warvis.org"
OUT_DIR = Path("/home/jang/Workspace/warvis-hackerton/docs/demo")
FRAMES_DIR = OUT_DIR / "frames2"
OUT_DIR.mkdir(parents=True, exist_ok=True)
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

# 전체 UI가 패딩 포함해서 보이는 크기
WIDTH, HEIGHT = 1440, 960
FPS = 24

shot_index = [0]

def s(page, name, hold_sec=3.0):
    """스크린샷 찍고 hold_sec 초 동안 유지할 프레임 수 반환."""
    idx = shot_index[0]
    shot_index[0] += 1
    fname = f"{idx:03d}_{name}.png"
    path = str(FRAMES_DIR / fname)
    page.screenshot(path=path, full_page=False)
    print(f"  📸 [{idx:03d}] {name} ({hold_sec}s)")
    return path, hold_sec

def scroll(page, px):
    page.evaluate(f"window.scrollBy(0, {px})")
    page.wait_for_timeout(400)

def top(page):
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(300)

def click_tab(page, text):
    page.click(f"button:has-text('{text}')")
    page.wait_for_timeout(800)

def run_demo():
    entries = []  # (path, hold_sec)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        ctx = browser.new_context(
            viewport={"width": WIDTH, "height": HEIGHT},
            record_video_dir=str(OUT_DIR),
            record_video_size={"width": WIDTH, "height": HEIGHT},
        )
        page = ctx.new_page()

        # ── 0. 로딩 ─────────────────────────────────────────
        print("\n[0] 사이트 로딩...")
        page.goto(URL, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2500)
        entries.append(s(page, "landing_load", 4.0))

        # 헤더 강조 (상단 유지)
        entries.append(s(page, "landing_header", 5.0))

        # 아래로 조금 스크롤 — 에이전트 카드 전체 표시
        scroll(page, 80)
        entries.append(s(page, "agent_cards_overview", 6.0))

        # ── 1. Alice 카드 선택 ─────────────────────────────
        print("\n[1] Alice 카드 선택...")
        top(page)
        page.wait_for_timeout(300)
        page.click(".agent-card:first-child")
        page.wait_for_timeout(800)
        scroll(page, 60)
        entries.append(s(page, "alice_selected", 4.0))

        # ── 2. Live Eval (Pillar #1) ────────────────────────
        print("\n[2] Live Eval — alice 평가...")
        top(page)
        click_tab(page, "Live Eval")
        scroll(page, 200)
        entries.append(s(page, "live_eval_tab_empty", 3.0))

        page.fill(".live-eval-input", "alice")
        page.wait_for_timeout(500)
        entries.append(s(page, "live_eval_input_ready", 3.0))

        page.click(".eval-btn")
        page.wait_for_timeout(800)
        entries.append(s(page, "live_eval_running_1", 3.0))
        page.wait_for_timeout(3000)
        entries.append(s(page, "live_eval_running_2", 3.0))
        page.wait_for_timeout(3000)
        entries.append(s(page, "live_eval_running_3", 3.0))

        # 결과 대기 (최대 30초)
        try:
            page.wait_for_selector(".eval-result", timeout=30000)
            page.wait_for_timeout(1200)
        except Exception:
            pass
        entries.append(s(page, "live_eval_result", 8.0))
        entries.append(s(page, "live_eval_result_hold", 6.0))

        # ── 3. TEE Attestation (Pillar #2) ─────────────────
        print("\n[3] TEE Attestation...")
        top(page)
        click_tab(page, "TEE Attestation")
        page.wait_for_timeout(1000)
        scroll(page, 200)
        entries.append(s(page, "tee_attestation_hashes", 6.0))
        entries.append(s(page, "tee_attestation_hold1", 5.0))
        # 하단 footer 까지 스크롤
        scroll(page, 200)
        entries.append(s(page, "tee_attestation_hold2", 5.0))

        # ── 4. KH Workflow (Pillar #3) — bob ───────────────
        print("\n[4] KH Workflow — bob...")
        top(page)
        # Bob 카드 선택
        page.click(".agent-card:nth-child(2)")
        page.wait_for_timeout(600)
        click_tab(page, "KH Workflow")
        scroll(page, 200)
        entries.append(s(page, "kh_workflow_bob_ready", 4.0))

        # Run
        page.click(".run-btn")
        page.wait_for_timeout(600)
        entries.append(s(page, "kh_workflow_running", 3.0))
        page.wait_for_timeout(1500)
        entries.append(s(page, "kh_workflow_step1", 3.0))
        page.wait_for_timeout(1500)
        entries.append(s(page, "kh_workflow_step2", 3.0))
        page.wait_for_timeout(2000)
        entries.append(s(page, "kh_workflow_complete", 8.0))
        # 로그 스크롤
        scroll(page, 200)
        entries.append(s(page, "kh_workflow_log", 6.0))
        entries.append(s(page, "kh_workflow_hold", 5.0))

        # ── 5. AI Analysis (Pillar #4) — carol ─────────────
        print("\n[5] AI Analysis — carol...")
        top(page)
        page.click(".agent-card:nth-child(3)")
        page.wait_for_timeout(600)
        click_tab(page, "AI Analysis")
        scroll(page, 200)
        entries.append(s(page, "ai_tab_ready", 3.0))

        page.fill("input[placeholder*='bob / carol']", "carol")
        page.wait_for_timeout(400)
        entries.append(s(page, "ai_carol_input", 3.0))

        page.click(".eval-btn")
        page.wait_for_timeout(600)
        entries.append(s(page, "ai_analyzing", 3.0))

        try:
            page.wait_for_function(
                "() => !document.querySelector('.eval-btn.running')",
                timeout=30000
            )
        except Exception:
            pass
        page.wait_for_timeout(1000)
        entries.append(s(page, "ai_result_sandwich", 8.0))
        entries.append(s(page, "ai_result_hold", 6.0))

        # ── 6. ZK Proof (Pillar #5) — bob ──────────────────
        print("\n[6] ZK Proof — bob...")
        top(page)
        page.click(".agent-card:nth-child(2)")
        page.wait_for_timeout(600)
        click_tab(page, "ZK Proof")
        scroll(page, 200)
        entries.append(s(page, "zk_proof_ready", 4.0))

        page.click("button:has-text('Generate ZK Proof')")
        page.wait_for_timeout(800)
        entries.append(s(page, "zk_proving_1", 4.0))
        page.wait_for_timeout(5000)
        entries.append(s(page, "zk_proving_2", 4.0))

        # ZK 완료 대기 (최대 90초)
        try:
            page.wait_for_function(
                "() => !document.querySelector('button[disabled]')",
                timeout=90000
            )
        except Exception:
            pass
        page.wait_for_timeout(1000)
        entries.append(s(page, "zk_proof_result", 8.0))
        scroll(page, 200)
        entries.append(s(page, "zk_proof_result_detail", 6.0))
        entries.append(s(page, "zk_proof_hold", 5.0))

        # ── 7. MeritGuard (자율 에이전트) ──────────────────
        print("\n[7] MeritGuard 자율 에이전트...")
        top(page)
        click_tab(page, "MeritGuard")
        page.wait_for_timeout(1000)
        scroll(page, 200)
        entries.append(s(page, "meritguard_overview", 6.0))
        scroll(page, 200)
        entries.append(s(page, "meritguard_stats", 6.0))
        scroll(page, 200)
        entries.append(s(page, "meritguard_action_log", 8.0))
        scroll(page, 200)
        entries.append(s(page, "meritguard_log_bottom", 6.0))

        # ── 8. 마무리 — 전체 개요 ─────────────────────────
        print("\n[8] 마무리 샷...")
        top(page)
        page.wait_for_timeout(500)
        entries.append(s(page, "final_overview_top", 5.0))
        scroll(page, 100)
        entries.append(s(page, "final_agent_cards", 6.0))
        entries.append(s(page, "final_hold", 4.0))

        ctx.close()
        browser.close()

    # ── 비디오 합성 ─────────────────────────────────────────
    total_sec = sum(e[1] for e in entries)
    print(f"\n총 {len(entries)} 프레임, 예상 {total_sec:.0f}초")
    print("비디오 합성 중...")

    import imageio as iio2
    import imageio.v3 as iio3

    OUT_MP4 = OUT_DIR / "demo.mp4"
    writer = iio2.get_writer(str(OUT_MP4), fps=FPS, codec="libx264", quality=8)

    for path, hold_sec in entries:
        img = iio3.imread(path)
        n_frames = max(1, int(hold_sec * FPS))
        for _ in range(n_frames):
            writer.append_data(img)

    writer.close()

    size_mb = OUT_MP4.stat().st_size / 1024 / 1024
    actual_sec = sum(e[1] for e in entries)
    print(f"\n✅ demo.mp4 생성 완료")
    print(f"   길이: {actual_sec:.0f}초 ({actual_sec/60:.1f}분)")
    print(f"   크기: {size_mb:.1f} MB")
    print(f"   경로: {OUT_MP4}")


if __name__ == "__main__":
    run_demo()
