import 'package:flutter/material.dart';

import '../../core/api.dart';
import '../../core/quran.dart';
import '../../core/theme.dart';
import '../../widgets/common.dart';
import '../../widgets/mushaf_page.dart';

/// Tasmee': the teacher's eyes stay on the Mushaf. Tap a word → pick a type → Pass. Designed for one hand on a phone.
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
  Object? _error;
  bool _saving = false;
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

  Future<void> _save(String outcome) async {
    setState(() => _saving = true);
    try {
      await Api.I.post('/recitations', {
        'journey': widget.journeyId, 'purpose': widget.purpose, 'from_ayah_index': widget.from, 'to_ayah_index': widget.to,
        'outcome': outcome, 'mistakes': _mistakes, 'note': _note.text, 'plan_segment': widget.segmentId, 'halaqah': widget.halaqahId, 'idempotency_key': _idem,
      });
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('حُفظ التقييم — ${outcomeAr[outcome]}'), backgroundColor: T.ink));
      Navigator.pop(context, true);
    } catch (e) {
      setState(() { _saving = false; _error = e; });
    }
  }

  @override
  Widget build(BuildContext context) {
    final marks = {for (final m in _mistakes) '${m['ayah_index']}:${m['word_position']}': m['severity'] as String};
    return Scaffold(
      body: Column(children: [
        NightHeader(
          eyebrow: 'التسميع · ${purposeAr[widget.purpose] ?? widget.purpose}',
          title: widget.studentName,
          subtitle: _page == null ? null : 'صفحة ${arDigits(_page!['page'])} · الجزء ${arDigits(_page!['juz'])} — انقر الكلمة لتسجيل خطأ',
          trailing: IconButton(onPressed: () => Navigator.pop(context), icon: const Icon(Icons.close_rounded, color: T.nightInk)),
        ),
        Expanded(
          child: _error != null
              ? ErrorBox(_error!, onRetry: () { setState(() => _error = null); _load(); })
              : _page == null
                  ? const LoadingBox()
                  : SingleChildScrollView(
                      padding: const EdgeInsets.fromLTRB(14, 14, 14, 120),
                      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                        MushafPage(page: _page!, surahNames: _surahs, inRange: _inRange, stateOf: (i) => _states[i], marks: marks, onWordTap: _tapWord),
                        const SizedBox(height: 14),
                        if (_mistakes.isNotEmpty) ...[
                          Text('الأخطاء (${arDigits(_mistakes.length)})', style: T.display(size: 14)),
                          const SizedBox(height: 6),
                          for (final m in _mistakes)
                            Row(children: [
                              Chip2(_types.firstWhere((t) => t['key'] == m['mistake_type'], orElse: () => {'name_ar': m['mistake_type']})['name_ar'], color: m['severity'] == 'major' ? T.sWeak : T.sNeeds, filled: true),
                              const SizedBox(width: 8),
                              Text(_keyOf(m['ayah_index']), style: T.mono(size: 11)),
                              const Spacer(),
                              IconButton(onPressed: () => setState(() => _mistakes.remove(m)), icon: const Icon(Icons.close_rounded, size: 18)),
                            ]),
                          const SizedBox(height: 8),
                        ],
                        TextField(controller: _note, minLines: 2, maxLines: 4, decoration: const InputDecoration(hintText: 'ملاحظة للمعلم (تظهر لولي الأمر)')),
                      ]),
                    ),
        ),
      ]),
      bottomSheet: _page == null ? null : Container(
        padding: EdgeInsets.fromLTRB(16, 12, 16, 12 + MediaQuery.paddingOf(context).bottom),
        decoration: const BoxDecoration(color: T.surface, border: Border(top: BorderSide(color: T.gold, width: 1.5))),
        child: Row(children: [
          Expanded(flex: 2, child: FilledButton(onPressed: _saving ? null : () => _save('pass'), child: const Text('اجتاز ✓'))),
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
