import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/api.dart';
import '../../core/quran.dart';
import '../../core/theme.dart';
import '../../widgets/common.dart';
import '../../widgets/mushaf_page.dart';
import '../../widgets/recite_check.dart';

/// Tasmee': the teacher's eyes stay on the Mushaf. Tap a word → pick a type → Pass. Designed for one hand on a phone.
/// The AI recitation check is a helper: its candidates are gold underlines until the teacher adopts them.
class TasmeeScreen extends StatefulWidget {
  const TasmeeScreen({super.key, required this.journeyId, required this.studentName, required this.purpose, required this.from, required this.to, this.segmentId, this.halaqahId});
  final String journeyId;
  final String studentName;
  final String purpose;
  final int from;
  final int to;
  final String? segmentId;
  final String? halaqahId;
  @override
  State<TasmeeScreen> createState() => _TasmeeScreenState();
}

class _TasmeeScreenState extends State<TasmeeScreen> {
  final List<Map<String, dynamic>> _mistakes = [];
  List<Map<String, dynamic>> _types = [];
  Map<int, String> _surahs = {};
  Map<int, String> _states = {};
  Map<String, dynamic>? _page;
  Map<String, dynamic>? _asr;
  bool _adopted = false;
  Object? _error;
  bool _saving = false;
  double _font = 24;
  final _note = TextEditingController();
  late final String _idem = '${widget.journeyId}-${widget.from}-${widget.to}-${DateTime.now().millisecondsSinceEpoch}';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final range = await Api.I.get('/quran/hafs_asim/range?from=${widget.from}&to=${widget.to}');
      final firstPage = (range['ayat'] as List).first['page'];
      final results = await Future.wait([
        Api.I.get('/quran/hafs_asim/page/$firstPage'),
        Api.I.get('/journeys/${widget.journeyId}/memory-map?level=page&number=$firstPage'),
        Api.I.get('/recitations/mistake-types'),
        Api.I.get('/quran/hafs_asim/surahs'),
      ]);
      setState(() {
        _page = results[0] as Map<String, dynamic>;
        _states = {for (final u in (results[1]['units'] as List)) u['ayah_index'] as int: u['state'] as String};
        _types = (results[2] as List).cast<Map<String, dynamic>>();
        _surahs = {for (final s in (results[3]['surahs'] as List)) s['number'] as int: s['name_ar'] as String};
      });
    } catch (e) {
      setState(() => _error = e);
    }
  }

  bool _inRange(int i) => i >= widget.from && i <= widget.to;

  void _tapWord(int ayahIndex, int word) async {
    HapticFeedback.selectionClick();
    final existing = _mistakes.indexWhere((m) => m['ayah_index'] == ayahIndex && m['word_position'] == word);
    if (existing >= 0) {
      setState(() => _mistakes.removeAt(existing));
      return;
    }
    final tp = await showModalBottomSheet<Map<String, dynamic>>(
      context: context, backgroundColor: T.surface, showDragHandle: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(18))),
      builder: (_) => Padding(
        padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
        child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('نوع الخطأ', style: T.display(size: 16)),
          Text('${_keyOf(ayahIndex)} · الكلمة ${arDigits(word)}', style: T.mono(size: 11.5)),
          const SizedBox(height: 12),
          Wrap(spacing: 8, runSpacing: 8, children: [
            for (final t in _types)
              SizedBox(
                width: (MediaQuery.sizeOf(context).width - 40) / 2,
                child: OutlinedButton(
                  style: OutlinedButton.styleFrom(alignment: AlignmentDirectional.centerStart, padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
                      side: BorderSide(color: t['severity'] == 'major' ? T.sWeak.withValues(alpha: .5) : T.sNeeds.withValues(alpha: .5))),
                  onPressed: () => Navigator.pop(context, t),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(t['name_ar'], style: T.body(size: 14, weight: FontWeight.w600)),
                    Text(t['severity'] == 'major' ? 'خطأ جسيم' : 'خطأ خفيف', style: T.body(size: 11, color: T.ink3)),
                  ]),
                ),
              ),
          ]),
        ]),
      ),
    );
    if (tp != null) setState(() => _mistakes.add({'ayah_index': ayahIndex, 'word_position': word, 'mistake_type': tp['key'], 'severity': tp['severity']}));
  }

  void _adopt() {
    final known = _types.map((t) => t['key']).toSet();
    final cands = ((_asr?['candidates'] as List?) ?? const []).cast<Map<String, dynamic>>();
    var added = 0;
    for (final c in cands) {
      if (c['kind'] == 'addition' || c['mistake_type'] == null) continue;
      if (_mistakes.any((m) => m['ayah_index'] == c['ayah_index'] && m['word_position'] == c['word_position'])) continue;
      _mistakes.add({'ayah_index': c['ayah_index'], 'word_position': c['word_position'], 'mistake_type': known.contains(c['mistake_type']) ? c['mistake_type'] : _types.first['key'], 'severity': c['severity']});
      added++;
    }
    HapticFeedback.mediumImpact();
    setState(() => _adopted = true);
    toast(context, 'أُضيف ${arDigits(added)} خطأ من مقترحات الكشف الآلي — راجعها قبل الحفظ');
  }

  /// YELLOW-class assistant: drafts a parent note from the student's real data; the teacher edits before saving.
  Future<void> _aiDraft() async {
    try {
      final r = await Api.I.post('/ai/weekly-note', {'journey_id': widget.journeyId}) as Map<String, dynamic>;
      setState(() => _note.text = r['text'] as String);
      if (mounted) toast(context, r['disclaimer'] as String);
    } catch (e) {
      if (mounted) toast(context, e is ApiException && e.code == 'capability_disabled' ? 'المساعد الذكي غير مفعّل لهذه المؤسسة' : e is ApiException && e.code == 'ai_unavailable' ? 'المساعد الذكي غير مُعدّ على الخادم' : friendlyError(e), error: true);
    }
  }

  Future<void> _save(String outcome) async {
    setState(() => _saving = true);
    try {
      await Api.I.post('/recitations', {
        'journey': widget.journeyId, 'purpose': widget.purpose, 'from_ayah_index': widget.from, 'to_ayah_index': widget.to,
        'outcome': outcome, 'mistakes': _mistakes, 'note': _note.text, 'plan_segment': widget.segmentId, 'halaqah': widget.halaqahId, 'idempotency_key': _idem,
      });
      if (!mounted) return;
      HapticFeedback.heavyImpact();
      await _resultSheet(outcome);
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      setState(() { _saving = false; _error = e; });
    }
  }

  /// A short, calm summary after saving: outcome, mistakes by type, what the engine will do next.
  Future<void> _resultSheet(String outcome) {
    final color = outcome == 'pass' ? T.sStrong : outcome == 'partial' ? T.sNeeds : T.sWeak;
    final byType = <String, int>{};
    for (final m in _mistakes) {
      byType[m['mistake_type']] = (byType[m['mistake_type']] ?? 0) + 1;
    }
    return showModalBottomSheet(
      context: context, backgroundColor: T.surface, isDismissible: true, showDragHandle: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (_) => Padding(
        padding: const EdgeInsets.fromLTRB(20, 0, 20, 28),
        child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            TweenAnimationBuilder<double>(tween: Tween(begin: 0, end: 1), duration: const Duration(milliseconds: 500), curve: Curves.elasticOut,
                builder: (_, v, ch) => Transform.scale(scale: v, child: ch),
                child: Container(width: 56, height: 56, decoration: BoxDecoration(color: color.withValues(alpha: .14), shape: BoxShape.circle),
                    child: Icon(outcome == 'pass' ? Icons.check_rounded : outcome == 'partial' ? Icons.remove_rounded : Icons.replay_rounded, color: color, size: 30))),
            const SizedBox(width: 14),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('حُفظ التقييم — ${outcomeAr[outcome]}', style: T.display(size: 18)),
              Text('${widget.studentName} · ${purposeAr[widget.purpose] ?? widget.purpose}', style: T.body(size: 13, color: T.ink3)),
            ])),
          ]),
          const SizedBox(height: 16),
          if (byType.isEmpty) Text('بلا أخطاء مسجّلة — سيرتفع ثبات آيات هذا المقطع.', style: T.body(size: 14, color: T.sStrong))
          else Wrap(spacing: 6, runSpacing: 6, children: [
            for (final e in byType.entries)
              Chip2('${_types.firstWhere((t) => t['key'] == e.key, orElse: () => {'name_ar': e.key})['name_ar']} × ${arDigits(e.value)}', color: T.sWeak, filled: true),
          ]),
          const SizedBox(height: 12),
          Text(outcome == 'repeat' ? 'سيعود هذا المقطع في خطة الغد بوصفه مراجعة قريبة.' : outcome == 'partial' ? 'تُحدَّث الخريطة جزئيًا وتُقترح مراجعة قريبة للآيات المتعثّرة.' : 'تُحدَّث خريطة الحفظ الآن، وتُحسب المراجعة القادمة من الثبات.',
              style: T.body(size: 13, color: T.ink2)),
          const SizedBox(height: 18),
          FilledButton(onPressed: () => Navigator.pop(context), child: const Text('التالي')),
        ]),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final marks = {for (final m in _mistakes) '${m['ayah_index']}:${m['word_position']}': m['severity'] as String};
    final flags = <String>{
      for (final a in ((_asr?['ayat'] as List?) ?? const []).cast<Map<String, dynamic>>())
        for (final w in (a['words'] as List).cast<Map<String, dynamic>>())
          if (w['status'] != 'ok') '${a['ayah_index']}:${w['position']}',
    };
    final major = _mistakes.where((m) => m['severity'] == 'major').length;
    return Scaffold(
      body: Column(children: [
        NightHeader(
          compact: true,
          eyebrow: 'التسميع · ${purposeAr[widget.purpose] ?? widget.purpose}',
          title: widget.studentName,
          subtitle: _page == null ? null : 'صفحة ${arDigits(_page!['page'])} · الجزء ${arDigits(_page!['juz'])} — انقر الكلمة لتسجيل خطأ',
          trailing: Row(mainAxisSize: MainAxisSize.min, children: [
            IconButton(tooltip: 'حجم الخط', onPressed: () => setState(() => _font = _font >= 30 ? 20 : _font + 3), icon: const Icon(Icons.format_size_rounded, color: T.nightMuted)),
            IconButton(onPressed: () => Navigator.pop(context), icon: const Icon(Icons.close_rounded, color: T.nightInk)),
          ]),
          child: Row(children: [
            _Pill('${arDigits(_mistakes.length)} خطأ', major > 0 ? T.sWeak : T.sStrong),
            const SizedBox(width: 8),
            if (major > 0) _Pill('${arDigits(major)} جسيم', T.sWeak),
            if (major > 0) const SizedBox(width: 8),
            if (_asr != null) _Pill('كشف آلي ${arDigits(((_asr!['accuracy'] as num) * 100).round())}٪', T.gold2),
            const Spacer(),
            if (_mistakes.isNotEmpty)
              TextButton.icon(onPressed: () => setState(() => _mistakes.removeLast()), style: TextButton.styleFrom(foregroundColor: T.nightMuted, padding: EdgeInsets.zero, minimumSize: const Size(0, 30)),
                  icon: const Icon(Icons.undo_rounded, size: 16), label: Text('تراجع', style: T.body(size: 12, color: T.nightMuted))),
          ]),
        ),
        Expanded(
          child: _error != null
              ? ErrorBox(_error!, onRetry: () { setState(() => _error = null); _load(); })
              : _page == null
                  ? const LoadingBox()
                  : ListView(
                      padding: const EdgeInsets.fromLTRB(14, 14, 14, 130),
                      children: [
                        ReciteCheck(from: widget.from, to: widget.to, journeyId: widget.journeyId, compact: true, onResult: (r) => setState(() { _asr = r; _adopted = false; })),
                        if (_asr != null) ...[const SizedBox(height: 10), AsrSummary(_asr!, onAdopt: _adopt, adopted: _adopted)],
                        const SizedBox(height: 12),
                        MushafPage(page: _page!, surahNames: _surahs, inRange: _inRange, stateOf: (i) => _states[i], marks: marks, flags: flags, onWordTap: _tapWord, fontSize: _font),
                        const SizedBox(height: 14),
                        if (_mistakes.isNotEmpty) ...[
                          SectionTitle('الأخطاء (${arDigits(_mistakes.length)})', top: 4),
                          for (final m in _mistakes)
                            FadeIn(child: Container(
                              margin: const EdgeInsets.only(bottom: 6),
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                              decoration: BoxDecoration(color: T.surface, borderRadius: BorderRadius.circular(10), border: Border.all(color: T.rule)),
                              child: Row(children: [
                                Chip2(_types.firstWhere((t) => t['key'] == m['mistake_type'], orElse: () => {'name_ar': m['mistake_type']})['name_ar'], color: m['severity'] == 'major' ? T.sWeak : T.sNeeds, filled: true),
                                const SizedBox(width: 8),
                                Text('${_keyOf(m['ayah_index'])} · ${arDigits(m['word_position'])}', style: T.mono(size: 11)),
                                const Spacer(),
                                IconButton(onPressed: () => setState(() => _mistakes.remove(m)), icon: const Icon(Icons.close_rounded, size: 18)),
                              ]),
                            )),
                          const SizedBox(height: 8),
                        ],
                        TextField(controller: _note, minLines: 2, maxLines: 4, decoration: InputDecoration(hintText: 'ملاحظة للمعلم (تظهر لولي الأمر)',
                            suffixIcon: Api.I.moduleOn('ai.assist') && Api.I.can('ai.assist.use') ? IconButton(tooltip: 'مسودة بالذكاء الاصطناعي', icon: const Icon(Icons.auto_awesome_rounded, color: T.gold), onPressed: _aiDraft) : null)),
                      ],
                    ),
        ),
      ]),
      bottomSheet: _page == null ? null : Container(
        padding: EdgeInsets.fromLTRB(16, 12, 16, 12 + MediaQuery.paddingOf(context).bottom),
        decoration: BoxDecoration(color: T.surface, border: const Border(top: BorderSide(color: T.gold, width: 1.5)), boxShadow: [BoxShadow(color: T.ink.withValues(alpha: .12), blurRadius: 24, offset: const Offset(0, -8))]),
        child: Row(children: [
          Expanded(flex: 2, child: FilledButton(style: FilledButton.styleFrom(backgroundColor: T.sStrong), onPressed: _saving ? null : () => _save('pass'), child: const Text('اجتاز ✓'))),
          const SizedBox(width: 8),
          Expanded(child: OutlinedButton(onPressed: _saving ? null : () => _save('partial'), child: const Text('جزئي'))),
          const SizedBox(width: 8),
          Expanded(child: OutlinedButton(style: OutlinedButton.styleFrom(foregroundColor: T.sWeak, side: BorderSide(color: T.sWeak.withValues(alpha: .5))),
              onPressed: _saving ? null : () => _save('repeat'), child: const Text('يعيد'))),
        ]),
      ),
    );
  }

  String _keyOf(int ayahIndex) {
    final a = (_page?['ayat'] as List?)?.cast<Map<String, dynamic>>().where((x) => x['ayah_index'] == ayahIndex).firstOrNull;
    return a?['key'] ?? '$ayahIndex';
  }
}

class _Pill extends StatelessWidget {
  const _Pill(this.text, this.color);
  final String text;
  final Color color;
  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: BoxDecoration(color: color.withValues(alpha: .18), borderRadius: BorderRadius.circular(999), border: Border.all(color: color.withValues(alpha: .5))),
        child: Text(text, style: T.body(size: 12, color: T.nightInk, weight: FontWeight.w600)),
      );
}
