"""Recitation mismatch detection (module hifz.asr, YELLOW).

The verified Quran text is the only reference. A transcript from the speech provider is *never* shown as Quran:
it is compared word by word against the expected Ayat, and the result is a list of *candidate* mismatches
(missing / substituted / extra words) positioned on the verified text. Candidates go to a human: the student
sees them as hints during self-practice; the teacher confirms or rejects them before anything is recorded.
"""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field

from packages.quran_core import get_core

_TASHKEEL = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭـ]")
_NON_LETTERS = re.compile(r"[^ء-ي\s]")
_BASMALAH_WORDS = ("بسم", "الله", "الرحمن", "الرحيم")


def normalize_word(w: str) -> str:
    w = _TASHKEEL.sub("", w)
    w = w.replace("ٱ", "ا").replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    w = w.replace("ة", "ه").replace("ى", "ي").replace("ؤ", "و").replace("ئ", "ي")
    w = w.replace("ۥ", "").replace("ۦ", "")
    w = _NON_LETTERS.sub("", w)
    return w.strip()


def normalize_text(text: str) -> list[str]:
    return [n for n in (normalize_word(w) for w in re.split(r"\s+", text or "")) if n]


def _similar(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


@dataclass
class ExpectedWord:
    ayah_index: int
    key: str
    position: int          # 1-based within the Ayah, same positions the Mushaf UI uses
    display: str           # Uthmani form for the UI
    norm: str
    status: str = "ok"     # ok | missing | substituted
    heard: str | None = None


@dataclass
class AsrResult:
    transcript: str
    words: list[ExpectedWord]
    extra: list[dict] = field(default_factory=list)   # words heard but not expected: {after_ayah_index, after_position, heard}

    @property
    def matched(self) -> int:
        return sum(1 for w in self.words if w.status == "ok")

    @property
    def accuracy(self) -> float:
        return round(self.matched / len(self.words), 3) if self.words else 0.0

    def to_payload(self) -> dict:
        by_ayah: dict[int, dict] = {}
        for w in self.words:
            a = by_ayah.setdefault(w.ayah_index, {"ayah_index": w.ayah_index, "key": w.key, "words": [], "missing": 0, "substituted": 0})
            a["words"].append({"position": w.position, "expected": w.display, "status": w.status, "heard": w.heard})
            if w.status != "ok":
                a[w.status] += 1
        for a in by_ayah.values():
            a["status"] = "ok" if not (a["missing"] or a["substituted"]) else "issues"
        # mistake_type uses the platform's standard keys so the teacher can adopt a candidate as-is; `kind` is the detector's own label.
        candidates = [{"ayah_index": w.ayah_index, "word_position": w.position, "kind": "omission" if w.status == "missing" else "substitution",
                       "mistake_type": "forgotten_word" if w.status == "missing" else "incorrect_word",
                       "severity": "major", "heard": w.heard, "expected": w.display} for w in self.words if w.status != "ok"]
        candidates += [{"ayah_index": e["after_ayah_index"], "word_position": e["after_position"], "kind": "addition", "mistake_type": None,
                        "severity": "minor", "heard": e["heard"], "expected": None} for e in self.extra]
        return {"transcript": self.transcript, "accuracy": self.accuracy, "expected_words": len(self.words), "matched": self.matched,
                "ayat": list(by_ayah.values()), "extra": self.extra, "candidates": candidates, "nothing_heard": not self.transcript.strip()}


def expected_words(from_index: int, to_index: int, riwayah: str = "hafs_asim") -> list[ExpectedWord]:
    """Words of the verified text in the range. The Basmalah that opens a Surah is skipped (it is part of Ayah 1 in Tanzil)
    so the positions match the Mushaf display, which splits it off."""
    core = get_core(riwayah)
    out: list[ExpectedWord] = []
    for idx in range(from_index, to_index + 1):
        a = core.ayah_by_index(idx)
        words = a.text_uthmani.split(" ")
        if a.ayah == 1 and a.surah not in (1, 9) and len(words) > 4 and [normalize_word(w) for w in words[:4]] == list(_BASMALAH_WORDS):
            words = words[4:]
        for pos, w in enumerate(words, start=1):
            n = normalize_word(w)
            if n:
                out.append(ExpectedWord(idx, a.key, pos, w, n))
    return out


def align(expected: list[ExpectedWord], transcript: str, *, fuzzy: float = 0.78) -> AsrResult:
    """Word-level alignment of the transcript against the expected words.
    Near-identical tokens (ASR spelling noise) count as matches; real differences become candidates."""
    heard = normalize_text(transcript)
    # drop a leading basmalah / isti'adha the reciter may say before the range
    while heard[:1] and heard[0] in ("اعوذ", "بالله", "من", "الشيطان", "الرجيم") and len(heard) > 4:
        heard.pop(0)
    if heard[:4] == list(_BASMALAH_WORDS) and (not expected or expected[0].norm != "بسم"):
        heard = heard[4:]
    exp_norm = [w.norm for w in expected]
    sm = difflib.SequenceMatcher(None, exp_norm, heard, autojunk=False)
    res = AsrResult(transcript=transcript, words=expected)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        if tag == "delete":
            for w in expected[i1:i2]:
                w.status = "missing"
        elif tag == "insert":
            anchor = expected[i1 - 1] if i1 > 0 else (expected[0] if expected else None)
            for h in heard[j1:j2]:
                res.extra.append({"after_ayah_index": anchor.ayah_index if anchor else None, "after_position": anchor.position if anchor else 0, "heard": h})
        else:  # replace: pair greedily, then leftovers
            exp_seg, heard_seg = expected[i1:i2], heard[j1:j2]
            n = min(len(exp_seg), len(heard_seg))
            for k in range(n):
                w, h = exp_seg[k], heard_seg[k]
                if _similar(w.norm, h) >= fuzzy:
                    w.status = "ok"
                else:
                    w.status, w.heard = "substituted", h
            for w in exp_seg[n:]:
                w.status = "missing"
            anchor = exp_seg[-1] if exp_seg else (expected[i1 - 1] if i1 > 0 else None)
            for h in heard_seg[n:]:
                res.extra.append({"after_ayah_index": anchor.ayah_index if anchor else None, "after_position": anchor.position if anchor else 0, "heard": h})
    return res


def check_recitation(transcript: str, from_index: int, to_index: int, riwayah: str = "hafs_asim") -> dict:
    return align(expected_words(from_index, to_index, riwayah), transcript).to_payload()
