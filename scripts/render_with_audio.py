"""
MeritScore Demo — Video + Narration Audio
- 2~4분, 1440x960 (720p+), 영어 나레이션 TTS
- gTTS로 각 섹션 음성 생성 → 영상 타이밍 맞춤 → 합성
"""

import subprocess
import tempfile
from pathlib import Path

import imageio
import imageio.v3 as iio3
import imageio_ffmpeg
from gtts import gTTS
from pydub import AudioSegment

FRAMES_DIR = Path("/home/jang/Workspace/warvis-hackerton/docs/demo/frames2")
OUT_DIR    = Path("/home/jang/Workspace/warvis-hackerton/docs/demo")
OUT_VIDEO  = OUT_DIR / "demo_silent.mp4"
OUT_AUDIO  = OUT_DIR / "narration.wav"   # WAV — no libmp3lame needed
OUT_FINAL  = OUT_DIR / "demo_final.mp4"
TMP_DIR    = Path(tempfile.mkdtemp())

FPS = 24

# ── 나레이션 스크립트 (프레임 키 → 텍스트) ──────────────────────────────
NARRATION = [
    # (frame_stem_prefix, text, min_hold_sec)
    ("000_landing_load",
     "Welcome to MeritScore — privacy-preserving credit scores for DeFi AI agents, "
     "built on 0G Galileo and Base Sepolia.",
     5.0),

    ("001_landing_header",
     "AI agents are entering DeFi at scale. "
     "How do you tell a trusted arbitrage bot from a malicious sandwich attacker? "
     "MeritScore answers with verifiable on-chain agent credit scoring.",
     6.0),

    ("002_agent_cards_overview",
     "Three demo agents: Alice, a sandwich bot rejected at 0.26. "
     "Bob, an honest arbitrage agent approved at 0.67. "
     "Carol, unverified and blocked at zero.",
     6.0),

    ("004_live_eval_tab_empty",
     "Pillar one — Live Evaluation. "
     "We query the MeritCore smart contract on 0G Galileo "
     "and run real Gemma 4 AI analysis simultaneously.",
     5.0),

    ("005_live_eval_input_ready",
     "Typing alice and pressing evaluate. "
     "The system fetches her on-chain merit score "
     "and runs Gemma 4 26-billion-parameter analysis in parallel.",
     5.0),

    ("009_live_eval_result",
     "Result: Alice scores 0.26, REJECTED. "
     "Sandwich attack detected by Gemma 4. Penalty of 0.5 applied. "
     "Real on-chain data, real LLM inference — no mocks.",
     7.0),

    ("011_tee_attestation_hashes",
     "Pillar two — TEE Attestation. "
     "The compute hash comes from 0G Compute TeeML inside a trusted execution environment. "
     "Storage root is anchored on-chain via EvidenceRegistry.",
     6.0),

    ("014_kh_workflow_bob_ready",
     "Pillar three — KeeperHub Workflow. "
     "Bob triggers a four-step pipeline: CHECK identity, VALIDATE attestation, "
     "ZK Verify the Merkle proof, and EXECUTE capital access.",
     6.0),

    ("018_kh_workflow_complete",
     "All four steps complete. CHECK passed. VALIDATE matched TEE attestation. "
     "ZK Verify confirmed the Merkle proof. EXECUTE returned OK — "
     "Bob is granted capital access through KeeperHub.",
     8.0),

    ("021_ai_tab_ready",
     "Pillar four — AI Analysis. "
     "Dedicated sandwich attack detection powered by Gemma 4, 26 billion parameters.",
     4.0),

    ("024_ai_result_sandwich",
     "Analyzing Carol. Gemma 4 identified frontrun and backrun transaction pairs "
     "surrounding victim swaps in the same block. "
     "Sandwich attack confirmed. Merit penalty of 0.5 applied. "
     "Real LLM inference, not a heuristic.",
     9.0),

    ("026_zk_proof_ready",
     "Pillar five — Zero Knowledge Proof. "
     "Bob proves his score exceeds the threshold "
     "without revealing the actual value. "
     "Cryptographic privacy via Groth16 on BN254.",
     5.0),

    ("029_zk_proof_result",
     "Proof verified and on-chain ready. "
     "Public signals show only the Merkle root and threshold — "
     "the score of 0.67 remains private. "
     "This proof can be submitted to our MeritVerifier contract on Base Sepolia.",
     8.0),

    ("032_meritguard_overview",
     "Finally — MeritGuard, our fully autonomous monitoring agent. "
     "It scans all agents every 60 seconds, "
     "reading from the MeritCore contract on 0G Galileo.",
     6.0),

    ("034_meritguard_action_log",
     "Alice and Carol flagged automatically. "
     "Over 30 KeeperHub actions triggered with zero human intervention.",
     5.0),

    ("036_final_overview_top",
     "MeritScore: proof-of-merit for DeFi AI agents. "
     "0G Galileo, Base Sepolia, KeeperHub, Gemma 4, and Groth16 ZK proofs — "
     "all live, all real.",
     6.0),

    ("037_final_agent_cards",
     "Alice rejected. Bob approved. Carol blocked. "
     "The future of DeFi needs agent credit infrastructure. MeritScore delivers it.",
     5.0),
]


def generate_tts(text: str, idx: int) -> tuple[Path, float]:
    path = TMP_DIR / f"tts_{idx:03d}.mp3"
    tts = gTTS(text=text, lang="en", slow=False)
    tts.save(str(path))
    audio = AudioSegment.from_mp3(str(path))
    duration_sec = len(audio) / 1000.0
    return path, duration_sec


def main():
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    frames = {f.stem: f for f in FRAMES_DIR.glob("*.png")}

    print("🎙  TTS 나레이션 생성 중...")
    segments = []  # (frame_path, audio_path, hold_sec)
    audio_parts = []

    for i, (key, text, min_hold) in enumerate(NARRATION):
        matched = next((f for stem, f in frames.items() if stem.startswith(key[:6])), None)
        if matched is None:
            matched = frames.get(key, list(frames.values())[0])

        audio_path, tts_dur = generate_tts(text, i)
        hold_sec = max(min_hold, tts_dur + 0.5)
        segments.append((matched, audio_path, hold_sec))
        audio_parts.append((audio_path, tts_dur, hold_sec))
        print(f"  [{i:02d}] {key[:30]:30s}  tts={tts_dur:.1f}s  hold={hold_sec:.1f}s")

    total_sec = sum(s[2] for s in segments)
    print(f"\n총 영상 길이: {total_sec:.0f}초 ({total_sec/60:.1f}분)")

    # ── 비디오 합성 ────────────────────────────────────────────────────────
    print("\n🎬 비디오 합성 중...")
    writer = imageio.get_writer(str(OUT_VIDEO), fps=FPS, codec="libx264", quality=8)
    for frame_path, _, hold_sec in segments:
        img = iio3.imread(str(frame_path))
        n = max(1, int(hold_sec * FPS))
        for _ in range(n):
            writer.append_data(img)
    writer.close()
    print(f"  → {OUT_VIDEO}")

    # ── 오디오 합성 (WAV — libmp3lame 불필요) ─────────────────────────────
    print("\n🔊 오디오 합성 중...")
    combined = AudioSegment.silent(duration=0)
    for audio_path, tts_dur, hold_sec in audio_parts:
        tts_audio = AudioSegment.from_mp3(str(audio_path))
        silence_dur = max(0, (hold_sec - tts_dur) * 1000)
        combined += tts_audio + AudioSegment.silent(duration=int(silence_dur))

    combined.export(str(OUT_AUDIO), format="wav")
    print(f"  → {OUT_AUDIO}  ({len(combined)/1000:.0f}s)")

    # ── 비디오 + 오디오 합성 (imageio-ffmpeg 내장 바이너리 사용) ──────────
    print("\n🎞  최종 합성 (video + audio)...")
    subprocess.run([
        ffmpeg, "-y",
        "-i", str(OUT_VIDEO),
        "-i", str(OUT_AUDIO),
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        str(OUT_FINAL)
    ], check=True)

    size_mb = OUT_FINAL.stat().st_size / 1024 / 1024
    print(f"\n✅ demo_final.mp4 완성!")
    print(f"   길이: {total_sec:.0f}초 ({total_sec/60:.1f}분)")
    print(f"   크기: {size_mb:.1f} MB")
    print(f"   해상도: 1440×960 (720p+)")
    print(f"   오디오: 영어 나레이션 (gTTS, no music)")
    print(f"   경로: {OUT_FINAL}")


if __name__ == "__main__":
    main()
