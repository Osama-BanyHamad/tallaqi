import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:record/record.dart';

import 'package:flutter/foundation.dart' show kIsWeb;

import '../core/api.dart';
import '../core/recording.dart';
import '../core/theme.dart';
import 'common.dart';
import 'tips.dart';

/// Records the reciter and asks the server to compare the speech against the verified text (module hifz.asr, YELLOW).
/// The transcript is never shown as Quran; only candidate mismatches positioned on the verified words come back.
class ReciteCheck extends StatefulWidget {
  const ReciteCheck({super.key, required this.from, required this.to, this.journeyId, required this.onResult, this.compact = false});
  final int from;
  final int to;
  final String? journeyId;
  final void Function(Map<String, dynamic>? result) onResult;
  final bool compact;
  @override
  State<ReciteCheck> createState() => _ReciteCheckState();
}

class _ReciteCheckState extends State<ReciteCheck> with SingleTickerProviderStateMixin {
  final _rec = AudioRecorder();
  StreamSubscription<Amplitude>? _amp;
  Timer? _timer;
  int _secs = 0;
  double _level = 0;
  String _state = 'idle'; // idle | recording | uploading | error
  String? _msg;

  @override
  void dispose() {
    _amp?.cancel();
    _timer?.cancel();
    _rec.dispose();
    super.dispose();
  }

  Future<void> _start() async {
    setState(() { _msg = null; });
    widget.onResult(null);
    if (!mounted || !await explainMicrophone(context)) return;
    if (!await _rec.hasPermission()) {
      setState(() { _state = 'error'; _msg = 'لم يُسمح باستخدام الميكروفون.'; });
      return;
    }
    await _rec.start(RecordConfig(encoder: kIsWeb ? AudioEncoder.opus : AudioEncoder.aacLc, bitRate: 96000, sampleRate: 44100, numChannels: 1, autoGain: true, noiseSuppress: true),
        path: await recordingPath());
    HapticFeedback.mediumImpact();
    setState(() { _state = 'recording'; _secs = 0; _level = 0; });
    _timer = Timer.periodic(const Duration(seconds: 1), (_) => setState(() => _secs++));
    _amp = _rec.onAmplitudeChanged(const Duration(milliseconds: 120)).listen((a) {
      final db = a.current.isFinite ? a.current : -60.0; // dBFS, roughly -60..0
      setState(() => _level = ((db + 50) / 50).clamp(0, 1).toDouble());
    });
  }

  Future<void> _stop() async {
    _timer?.cancel();
    await _amp?.cancel();
    final path = await _rec.stop();
    HapticFeedback.lightImpact();
    if (path == null) { setState(() { _state = 'error'; _msg = 'لم يُسجَّل صوت.'; }); return; }
    setState(() => _state = 'uploading');
    try {
      final bytes = await readRecording(path);
      if (bytes.length < 2000) { setState(() { _state = 'error'; _msg = 'التسجيل قصير جدًا. حاول مرة أخرى.'; }); return; }
      final isWebm = path.startsWith('blob:') || path.endsWith('.webm');
      final r = await Api.I.postMultipart('/ai/asr-check',
          fields: {'from_ayah_index': '${widget.from}', 'to_ayah_index': '${widget.to}', if (widget.journeyId != null) 'journey_id': widget.journeyId!},
          fileField: 'audio', bytes: bytes, filename: isWebm ? 'recitation.webm' : 'recitation.m4a', mime: isWebm ? 'audio/webm' : 'audio/mp4') as Map<String, dynamic>;
      widget.onResult(r);
      setState(() => _state = 'idle');
      await discardRecording(path);
    } catch (e) {
      setState(() {
        _state = 'error';
        _msg = e is ApiException && e.code == 'ai_unavailable' ? 'خدمة الصوت غير مُعدّة على الخادم.' : e is ApiException && e.code == 'capability_disabled' ? 'التسميع الذكي غير مفعّل لهذه المؤسسة.' : friendlyError(e);
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!Api.I.can('hifz.asr.use') || !Api.I.moduleOn('hifz.asr')) return const SizedBox.shrink();
    final recording = _state == 'recording';
    final busy = _state == 'uploading';
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(children: [
        Expanded(
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 250),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(14),
              gradient: recording ? const LinearGradient(colors: [Color(0xFFB8452B), T.sWeak]) : const LinearGradient(colors: [T.gold2, T.gold]),
              boxShadow: [BoxShadow(color: (recording ? T.sWeak : T.gold).withValues(alpha: .35), blurRadius: 18, offset: const Offset(0, 8))],
            ),
            child: InkWell(
              borderRadius: BorderRadius.circular(14),
              onTap: busy ? null : (recording ? _stop : _start),
              child: Padding(
                padding: EdgeInsets.symmetric(horizontal: 16, vertical: widget.compact ? 10 : 14),
                child: Row(children: [
                  _MicPulse(active: recording, level: _level, busy: busy),
                  const SizedBox(width: 12),
                  Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(busy ? 'يحلّل التلاوة…' : recording ? 'أوقف وحلّل' : 'سمّع بالذكاء الاصطناعي', style: T.body(size: widget.compact ? 14 : 15.5, weight: FontWeight.w700, color: recording ? Colors.white : const Color(0xFF1F1806))),
                    Text(recording ? '${_mmss(_secs)} · اقرأ المقطع بصوت واضح' : busy ? 'يُقارَن الصوت بالنص الموثّق' : 'يقارن تلاوتك بالنص الموثّق ويقترح المواضع', style: T.body(size: 11.5, color: recording ? Colors.white70 : const Color(0xFF5A4A1E))),
                  ])),
                ]),
              ),
            ),
          ),
        ),
      ]),
      if (_msg != null) Padding(padding: const EdgeInsets.only(top: 6), child: Text(_msg!, style: T.body(size: 12.5, color: T.sWeak))),
    ]);
  }

  String _mmss(int s) => '${(s ~/ 60).toString().padLeft(2, '0')}:${(s % 60).toString().padLeft(2, '0')}';
}

class _MicPulse extends StatelessWidget {
  const _MicPulse({required this.active, required this.level, required this.busy});
  final bool active;
  final double level;
  final bool busy;
  @override
  Widget build(BuildContext context) {
    final double ring = 36 + (active ? level * 18 : 0);
    return SizedBox(
      width: 54, height: 54,
      child: Stack(alignment: Alignment.center, children: [
        AnimatedContainer(duration: const Duration(milliseconds: 120), width: ring, height: ring,
            decoration: BoxDecoration(shape: BoxShape.circle, color: Colors.white.withValues(alpha: active ? .22 : .18))),
        Container(width: 36, height: 36, decoration: BoxDecoration(shape: BoxShape.circle, color: active ? Colors.white : const Color(0xFF1F1806).withValues(alpha: .12)),
            child: busy
                ? const Padding(padding: EdgeInsets.all(9), child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF1F1806)))
                : Icon(active ? Icons.stop_rounded : Icons.mic_rounded, color: active ? T.sWeak : const Color(0xFF1F1806), size: 22)),
      ]),
    );
  }
}

/// Result card: accuracy ring, candidates (with what was heard in muted text — never styled as Quran), optional adopt action.
class AsrSummary extends StatelessWidget {
  const AsrSummary(this.r, {super.key, this.onAdopt, this.adopted = false});
  final Map<String, dynamic> r;
  final VoidCallback? onAdopt;
  final bool adopted;
  @override
  Widget build(BuildContext context) {
    final acc = (r['accuracy'] as num).toDouble();
    final cands = (r['candidates'] as List).cast<Map<String, dynamic>>();
    final ayat = (r['ayat'] as List).cast<Map<String, dynamic>>();
    String keyOf(int idx) => ayat.firstWhere((a) => a['ayah_index'] == idx, orElse: () => {'key': '$idx'})['key'].toString();
    String label(String kind) => kind == 'omission' ? 'إسقاط' : kind == 'addition' ? 'زيادة' : 'إبدال';
    return FadeIn(
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(color: T.goldTint, borderRadius: BorderRadius.circular(14), border: Border.all(color: T.gold.withValues(alpha: .45))),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            RetentionRing(acc, size: 64, stroke: 5),
            const SizedBox(width: 14),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Eyebrow('كشف آلي · YELLOW'),
              const SizedBox(height: 4),
              Text('${arDigits(r['matched'])} من ${arDigits(r['expected_words'])} كلمة مطابقة', style: T.body(size: 14, weight: FontWeight.w600)),
              Text(cands.isEmpty ? 'لا فروق مسموعة عن النص الموثّق.' : '${arDigits(cands.length)} موضع يحتاج نظر المعلم', style: T.body(size: 12.5, color: T.ink2)),
            ])),
          ]),
          if (cands.isNotEmpty) ...[
            const SizedBox(height: 10),
            for (final c in cands.take(10))
              Padding(
                padding: const EdgeInsets.only(bottom: 5),
                child: Row(children: [
                  Chip2(label(c['kind']), color: c['kind'] == 'addition' ? T.sNeeds : T.sWeak, filled: true),
                  const SizedBox(width: 8),
                  Text('${keyOf(c['ayah_index'] as int)} · ${arDigits(c['word_position'])}', style: T.mono(size: 11)),
                  const Spacer(),
                  if (c['expected'] != null) Text(c['expected'], style: T.quran(size: 16).copyWith(height: 1.2)),
                  if (c['heard'] != null) Padding(padding: const EdgeInsetsDirectional.only(start: 8), child: Text('سُمع: ${c['heard']}', style: T.body(size: 11.5, color: T.ink3))),
                ]),
              ),
            if (cands.length > 10) Text('+${arDigits(cands.length - 10)}', style: T.body(size: 12, color: T.ink3)),
            if (onAdopt != null) ...[
              const SizedBox(height: 8),
              SizedBox(width: double.infinity, child: FilledButton.tonal(
                style: FilledButton.styleFrom(backgroundColor: adopted ? T.ground2 : T.lapis, foregroundColor: adopted ? T.ink3 : Colors.white, minimumSize: const Size.fromHeight(42)),
                onPressed: adopted ? null : onAdopt,
                child: Text(adopted ? 'أُضيفت إلى الأخطاء ✓' : 'اعتمد المقترحات كأخطاء (يمكن حذف أيٍّ منها)'),
              )),
            ],
          ],
          const SizedBox(height: 8),
          Text('${r['disclaimer']} · ${r['model']}', style: T.body(size: 11, color: T.ink3)),
        ]),
      ),
    );
  }
}
