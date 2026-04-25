# Demo Day Resilience Checklist

**Project**: warvis-hackerton (Proof-of-Merit, EthGlobal OpenAgents)
**Hackathon**: 2026-04-24 to 2026-05-04
**Demo Date**: TBD (during Judges' Review window)

---

## F1: Backup & Recovery Plan

### Backup Media
- [ ] USB Drive #1: meritscore-demo-v1.mp4 stored and tested
- [ ] USB Drive #2: meritscore-demo-v1.mp4 stored and tested
- [ ] Cloud backup: Google Drive or Dropbox copy exists
- [ ] Video bitrate suitable for mobile network playback (≤50MB for 5min demo)

### Network Resilience
- [ ] Mobile hotspot tested with adequate data (≥5GB available)
- [ ] Backup phone number and provider documented
- [ ] WiFi SSID and password shared with team members
- [ ] Ethernet adapter available (if demo venue has wired connection)

---

## F2: Mobile Hotspot (No Code Required)

**Status**: Uses standard device hotspot, no additional implementation needed.

- [ ] iPhone/Android hotspot enabled
- [ ] Data plan has sufficient remaining quota
- [ ] Hotspot password set and shared with demo team
- [ ] Test: Connect another device and verify internet speed (>2Mbps for video streaming)

---

## F3: Emergency Local Fallback (1 hour)

**Purpose**: If cloud server is down, demo can run from laptop with ngrok tunnel.

### Setup
- [ ] `scripts/fallback_demo.sh` created and executable
- [ ] ngrok installed locally (`brew install ngrok` or `choco install ngrok`)
- [ ] ngrok authtoken configured (`ngrok config add-authtoken <token>`)
  - Token available at: https://dashboard.ngrok.com/get-started/your-authtoken

### Testing
- [ ] Run local fallback: `./scripts/fallback_demo.sh`
- [ ] Verify BFF starts on port 61234 without errors
- [ ] Verify Streamlit starts on port 8501 without errors
- [ ] Verify ngrok tunnel is active at http://localhost:4040
- [ ] Test BFF endpoints manually:
  ```bash
  curl http://localhost:61234/health
  curl http://localhost:61234/merit/alice
  ```
- [ ] Test Streamlit UI by opening browser to http://localhost:8501
- [ ] Verify all 5 tabs load (Merit Score, Attestation, KH Workflow, AI Analyze, ZK Proof)
- [ ] Stop script with Ctrl+C and verify cleanup works

### Demo Day Use
1. If cloud server is unreachable, open terminal
2. Run: `./scripts/fallback_demo.sh`
3. Get public ngrok URL from http://localhost:4040
4. Use ngrok URL to access BFF + UI
5. Demo proceeds normally (users can't tell it's local)

---

## F4: Video Upload & Archival (30 minutes)

**Purpose**: Multi-channel archival for judges' offline review.

### YouTube
- [ ] Video uploaded to YouTube
- [ ] URL: [___________________________________]
- [ ] Title: "MeritScore Demo - EthGlobal OpenAgents Hackathon"
- [ ] Visibility: Unlisted or Public
- [ ] Video plays smoothly at 1080p and 720p
- [ ] Audio sync verified
- [ ] No copyright strikes
- [ ] Link shared in submission

### IPFS (Decentralized Backup)
- [ ] Video uploaded to IPFS (via web3.storage or local node)
- [ ] IPFS CID: [___________________________________]
- [ ] Verified at: https://ipfs.io/ipfs/{CID}
- [ ] Backup gateway URLs tested:
  - [ ] https://gateway.pinata.cloud/ipfs/{CID}
  - [ ] https://dweb.link/ipfs/{CID}
- [ ] Video metadata stored in `docs/video-urls.md`

### Video Spec
- [ ] Duration: 3-5 minutes
- [ ] Resolution: 1080p or 720p minimum
- [ ] Bitrate: ≤50MB for ~5min demo
- [ ] Codec: H.264 (MP4) for compatibility
- [ ] Audio: Stereo, audible without volume boost
- [ ] Thumbnail: High-contrast demo screenshot

### Upload Helper
- [ ] Run: `./scripts/upload_demo_video.sh`
- [ ] Follow manual instructions for YouTube
- [ ] Use script's IPFS-add function if local node available:
  ```bash
  ./scripts/upload_demo_video.sh --ipfs-add meritscore-demo-v1.mp4
  ```
- [ ] Record both URLs in `docs/video-urls.md`

---

## F5: Judge 1-Pager QR Code

**Purpose**: Backup link distribution for offline QR scanning.

### HTML Page
- [ ] File exists: `docs/judge-1pager.html`
- [ ] QR code visible and scannable
- [ ] QR code links to: `https://meritscore.warvis.org`
- [ ] Fallback URL in text: https://meritscore.warvis.org
- [ ] Video URLs embedded or linked

### QR Testing
- [ ] Scan QR with iPhone: links to live server
- [ ] Scan QR with Android: links to live server
- [ ] Test with poor lighting (judge's pocket)
- [ ] Test from 1 meter away

### Pre-Demo Updates
- [ ] Update QR code URL if using different domain
- [ ] Update video URLs in HTML if needed
- [ ] Print 5 backup 1-pagers on cardstock
- [ ] Laminate or use page protectors
- [ ] Store in demo kit bag

---

## F6: Live Server Health Checks (Demo Day)

### 30 minutes before demo
- [ ] Check server status: `curl https://meritscore.warvis.org/health`
- [ ] Test merit endpoint: `curl https://meritscore.warvis.org/merit/alice`
- [ ] Test chain connectivity (0G Galileo + Base Sepolia)
- [ ] Verify all 5 Streamlit tabs load
- [ ] Test demo flow: Alice → Bob → Carol (merit scores)
- [ ] Test ZK proof generation (takes ~10-30s)

### During demo (every 5 minutes)
- [ ] Monitor server logs in separate terminal
- [ ] Watch for errors or slow responses
- [ ] Have fallback.sh command ready to paste

### Contingency Decision Tree
```
Server responding (<1s)?
  YES → Continue with live demo
  NO  → Check network connectivity
         Still slow? → Start fallback_demo.sh
              Have ngrok ready
              Get public URL
              Continue demo
         
Meridian endpoint returning scores?
  YES → Continue
  NO  → Check 0G Galileo connectivity
         If chain is down → Use cached demo responses
         
5+ second response time?
  Consider switching to fallback even if live works
```

---

## F7: Demo Script & Flow

### Script Location
- [ ] File exists: `DEMO_SCRIPT.md`
- [ ] Flow matches implementation
- [ ] Timing estimates accurate (rehearse 3+ times)
- [ ] Fallback narratives prepared ("If the chain were slow...")

### Rehearsal Checklist (Do 3x)
- [ ] **Run 1** (Cold start): All services from scratch
  - [ ] Time: ___ minutes
- [ ] **Run 2** (Warm server): Services already running
  - [ ] Time: ___ minutes
- [ ] **Run 3** (With fallback): Using ngrok tunnel
  - [ ] Time: ___ minutes
  - [ ] Ensure timing is similar to live

### Talking Points
- [ ] Explain merit score calculation
- [ ] Describe 0G compute integration
- [ ] Highlight ZK proof privacy feature
- [ ] Mention KeeperHub workflow capability
- [ ] Answer judge questions confidently

---

## F8: Judge Kit Assembly

### Materials
- [ ] Laptop with fallback_demo.sh tested and working
- [ ] USB drives #1 and #2 with backup video
- [ ] Printed judge 1-pagers (5 copies, laminated)
- [ ] QR code cards for direct scanning
- [ ] Backup power bank (2x, fully charged)
- [ ] Ethernet cable (in case WiFi fails)
- [ ] HDMI/USB-C adapter for projector

### Documentation
- [ ] DEMO_SCRIPT.md printed (backup copy)
- [ ] URLs printed on cardstock:
  - [ ] Live: https://meritscore.warvis.org
  - [ ] YouTube: [___________________________________]
  - [ ] IPFS: ipfs://[___________________________________]
- [ ] Offline presentation (PDF) in case web is unavailable
- [ ] Contact info for all team members

### Tech Setup
- [ ] WiFi tethering tested from backup phone
- [ ] ngrok tunnel tested from demo laptop
- [ ] Projector HDMI tested (bring adapter)
- [ ] Microphone works (USB fallback available)
- [ ] Screen sharing tested (Zoom/Teams/Google Meet)

---

## F9: Locked Constants Verification

**CRITICAL**: These values must NEVER change during demo.

- [ ] ALICE_MERIT = 0.2641 ✓
- [ ] BOB_MERIT = 0.6703 ✓
- [ ] CAROL_MERIT = 0.0000 ✓
- [ ] INTEGRITY_HARD_FAIL = 0.85 ✓
- [ ] Chain: 0G Galileo (16602) with `--legacy` flag ✓
- [ ] Chain: Base Sepolia (84532) operational ✓

Verify in contracts:
```bash
grep -r "0\.2641\|0\.6703" contracts/
grep -r "16602\|84532" . --include="*.py" --include="*.ts"
```

---

## F10: Final Sanity Checks (12 hours before demo)

- [ ] All code committed to git: `git status`
- [ ] No `.env` secrets exposed in repo
- [ ] Production contracts deployed and verified on-chain
- [ ] BFF and Streamlit can start without errors
- [ ] All endpoints return valid responses
- [ ] Database/storage is seeded with demo data (alice, bob, carol)
- [ ] Logging is enabled for demo troubleshooting

### Quick Deploy Test
```bash
# Simulate live deployment
docker-compose up -d
sleep 5
curl https://meritscore.warvis.org/health
curl https://meritscore.warvis.org/merit/alice
# Should see merit scores
```

---

## Sign-Off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| **Demo Lead** | | | |
| **Tech Lead** | | | |
| **Witness** | | | |

---

## Notes & Observations

**Add notes here as you complete checklist items:**

```
- [2026-04-25] ngrok authtoken configured, tested tunnel working
- [2026-04-25] Video uploaded to IPFS CID: Qm...
- [2026-04-26] Rehearsal 1 completed in 4m 32s (target 5m)
```

---

## Resources

- **Fallback Script**: `./scripts/fallback_demo.sh`
- **Video Upload Script**: `./scripts/upload_demo_video.sh`
- **Video URLs**: `./docs/video-urls.md`
- **Judge 1-Pager**: `./docs/judge-1pager.html`
- **Demo Script**: `./DEMO_SCRIPT.md`
- **Live Server**: https://meritscore.warvis.org
- **Backup Plan**: In this file (F1-F10)

---

**Last Updated**: 2026-04-25
**Status**: Ready for demo preparation
