import 'package:flutter/material.dart';

import '../../core/api.dart';
import '../../core/quran.dart';
import '../../core/theme.dart';
import '../../widgets/common.dart';
import '../../widgets/memory_map.dart';
import '../student/practice_screen.dart';
import '../tasmee/tasmee_screen.dart';

/// One student's Quran journey: retention ring, KPIs, today's plan, memory map, recent sessions, timeline.
/// Shared by teachers (with Tasmee' actions), students ("رحلتي") and parents (read-only).
class StudentDetailScreen extends StatefulWidget {
  const StudentDetailScreen({super.key, required this.journeyId, this.halaqahId, this.canRecite = false, this.canPractice = false, this.embedded = false});
  final String journeyId;
  final String? halaqahId;
  final bool canRecite;
  final bool canPractice;
  final bool embedded;
  @override
  State<StudentDetailScreen> createState() => _StudentDetailScreenState();
}

class _StudentDetailScreenState extends State<StudentDetailScreen> with SingleTickerProviderStateMixin {
  int _v = 0;
  late final _tabs = TabController(length: 3, vsync: this);

  Future<Map<String, dynamic>> _load() async {
    final r = await Future.wait([
      Api.I.get('/journeys/${widget.journeyId}'),
      Api.I.get('/journeys/${widget.journeyId}/plan'),
      Api.I.get('/journeys/${widget.journeyId}/sessions').catchError((_) => <String, dynamic>{'results': []}),
      Api.I.get('/journeys/${widget.journeyId}/timeline').catchError((_) => <dynamic>[]),
    ]);
    final sess = r[2];
    return {'journey': r[0], 'plan': r[1], 'sessions': sess is Map ? sess['results'] : sess, 'timeline': r[3]};
  }

  @override
  Widget build(BuildContext context) {
    final body = Fetch<Map<String, dynamic>>(
      key: ValueKey(_v),
      future: _load,
      builder: (context, d, refresh) {
        final j = d['journey'] as Map<String, dynamic>;
        final plan = d['plan'] as Map<String, dynamic>?;
        final segs = ((plan?['segments'] as List?) ?? const []).cast<Map<String, dynamic>>();
        final sessions = ((d['sessions'] as List?) ?? const []).cast<Map<String, dynamic>>();
        final timeline = ((d['timeline'] as List?) ?? const []).cast<Map<String, dynamic>>();
        final cur = j['current_key'] as Map<String, dynamic>?;
        return Column(children: [
          NightHeader(
            leadingBack: !widget.embedded,
            eyebrow: 'رحلة الطالب مع القرآن',
            title: j['student_name'] ?? '',
            subtitle: cur != null ? 'موضع الحفظ الجديد: ${cur['surah_name']} ${arDigits(cur['ayah'])} · صفحة ${arDigits(cur['page'])}' : 'في المراجعة الطويلة',
            trailing: RetentionRing((j['avg_retention'] as num?)?.toDouble(), size: 64, light: true, label: T.stateWord((j['avg_retention'] as num?)?.toDouble()), stroke: 5),
            child: Column(children: [
              JuzStrip(j['juz_map'] as List?, height: 12),
              const SizedBox(height: 12),
              Row(children: [
                _Stat(arDigits(j['memorized_pages'] ?? 0), 'صفحة محفوظة'),
                _Stat(arDigits(j['memorized_ayat'] ?? 0), 'آية'),
                _Stat(arDigits(j['weak_ayat'] ?? 0), 'ضعيفة', color: T.sNeeds),
                _Stat(arDigits(j['critical_ayat'] ?? 0), 'حرجة', color: (j['critical_ayat'] ?? 0) > 0 ? T.sWeak : T.nightMuted),
              ]),
            ]),
          ),
          Container(
            color: T.surface,
            child: TabBar(controller: _tabs, labelColor: T.lapis, unselectedLabelColor: T.ink3, indicatorColor: T.gold, indicatorWeight: 2.5,
                labelStyle: T.body(size: 13.5, weight: FontWeight.w700), unselectedLabelStyle: T.body(size: 13.5), tabs: const [Tab(text: 'اليوم'), Tab(text: 'خريطة الحفظ'), Tab(text: 'السجل')]),
          ),
          Expanded(
            child: TabBarView(controller: _tabs, children: [
              // ---- Today
              RefreshIndicator(
                onRefresh: () async => setState(() => _v++),
                child: ListView(padding: const EdgeInsets.all(16), children: [
                  if (plan?['paused_new'] == true)
                    Container(margin: const EdgeInsets.only(bottom: 10), padding: const EdgeInsets.all(12), decoration: BoxDecoration(color: T.goldTint, borderRadius: BorderRadius.circular(10)),
                        child: Row(children: [const Icon(Icons.pause_circle_outline_rounded, color: T.gold, size: 20), const SizedBox(width: 8), Expanded(child: Text('إيقاف مؤقت للحفظ الجديد بسبب تراكم المراجعة.', style: T.body(size: 13)))])),
                  if (segs.isEmpty) const EmptyState(title: 'لا مقاطع لهذا اليوم', body: 'تُولَّد الخطة من الثبات والسياسة المعتمدة للحلقة.'),
                  for (var i = 0; i < segs.length; i++) FadeIn(index: i, child: _SegmentTile(segs[i], onTap: _openSegment)),
                  for (final r in ((plan?['rationale'] as List?) ?? const [])) Padding(padding: const EdgeInsets.only(top: 4), child: Text('• $r', style: T.body(size: 12.5, color: T.ink3))),
                ]),
              ),
              // ---- Memory map
              ListView(padding: const EdgeInsets.all(16), children: [MemoryMapView(journeyId: widget.journeyId)]),
              // ---- History
              ListView(padding: const EdgeInsets.all(16), children: [
                SectionTitle('جلسات التسميع', top: 0),
                if (sessions.isEmpty) Text('لا جلسات بعد.', style: T.body(size: 13, color: T.ink3)),
                for (var i = 0; i < sessions.length && i < 20; i++) FadeIn(index: i, child: _SessionTile(sessions[i])),
                if (timeline.isNotEmpty) ...[
                  const SectionTitle('المسار الزمني'),
                  for (final e in timeline.take(15))
                    Padding(padding: const EdgeInsets.only(bottom: 8), child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Container(width: 8, height: 8, margin: const EdgeInsets.only(top: 7), decoration: const BoxDecoration(color: T.gold, shape: BoxShape.circle)),
                      const SizedBox(width: 10),
                      Expanded(child: Text(_eventText(e), style: T.body(size: 13.5))),
                      Text(_day(e['occurred_at']), style: T.mono(size: 10.5)),
                    ])),
                ],
              ]),
            ]),
          ),
        ]);
      },
    );
    return widget.embedded ? body : Scaffold(body: body);
  }

  Future<void> _openSegment(Map<String, dynamic> s) async {
    final j = await Api.I.get('/journeys/${widget.journeyId}') as Map<String, dynamic>;
    if (!mounted) return;
    if (widget.canRecite) {
      await Navigator.of(context).push(MaterialPageRoute(builder: (_) => TasmeeScreen(
          journeyId: widget.journeyId, studentName: j['student_name'] ?? '', purpose: s['purpose'], from: s['from_ayah_index'], to: s['to_ayah_index'], segmentId: s['id'], halaqahId: widget.halaqahId)));
      setState(() => _v++);
    } else if (widget.canPractice) {
      await Navigator.of(context).push(MaterialPageRoute(builder: (_) => PracticeScreen(journeyId: widget.journeyId, from: s['from_ayah_index'], to: s['to_ayah_index'], title: purposeAr[s['purpose']] ?? '')));
    }
  }

  String _eventText(Map<String, dynamic> e) {
    final p = (e['payload'] as Map?) ?? {};
    return switch (e['event_type']) {
      'surah_completed' => 'أتمّ سورة ${p['surah_name'] ?? ''}',
      'juz_completed' => 'أتمّ الجزء ${arDigits(p['juz'] ?? '')}',
      'page_memorized' => 'حفظ صفحة ${arDigits(p['page'] ?? '')}',
      'assessment' => 'اختبار: ${arDigits(p['grade'] ?? '')}',
      _ => (p['title'] ?? e['event_type']).toString(),
    };
  }

  String _day(dynamic iso) => iso == null ? '' : iso.toString().substring(0, 10);
}

class _Stat extends StatelessWidget {
  const _Stat(this.v, this.l, {this.color});
  final String v;
  final String l;
  final Color? color;
  @override
  Widget build(BuildContext context) => Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(v, style: T.display(size: 20, color: color ?? T.nightInk)),
        Text(l, style: T.body(size: 11, color: T.nightMuted)),
      ]));
}

class _SegmentTile extends StatelessWidget {
  const _SegmentTile(this.s, {required this.onTap});
  final Map<String, dynamic> s;
  final Future<void> Function(Map<String, dynamic>) onTap;
  @override
  Widget build(BuildContext context) {
    final done = s['completion'] == 'verified';
    final c = s['purpose'] == 'new' ? T.lapis : s['purpose'] == 'near' ? T.gold : T.ink3;
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => onTap(s),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(children: [
            Container(width: 4, height: 44, decoration: BoxDecoration(color: done ? T.sStrong : c, borderRadius: BorderRadius.circular(2))),
            const SizedBox(width: 12),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                Chip2(purposeAr[s['purpose']] ?? s['purpose'], color: c, filled: true),
                const Spacer(),
                Text(done ? 'تم ✓' : 'افتح', style: T.body(size: 12.5, weight: FontWeight.w700, color: done ? T.sStrong : T.gold)),
              ]),
              const SizedBox(height: 6),
              Text('${s['from_key']['surah_name']} ${arDigits(s['from_key']['ayah'])} ← ${s['to_key']['surah_name']} ${arDigits(s['to_key']['ayah'])}', style: T.body(size: 14.5, weight: FontWeight.w600)),
              if ((s['reason'] ?? '').toString().isNotEmpty) Text(s['reason'], style: T.body(size: 12, color: T.ink3)),
            ])),
          ]),
        ),
      ),
    );
  }
}

class _SessionTile extends StatelessWidget {
  const _SessionTile(this.s);
  final Map<String, dynamic> s;
  @override
  Widget build(BuildContext context) {
    final o = s['outcome']?.toString() ?? '';
    final color = o == 'pass' ? T.sStrong : o == 'partial' ? T.sNeeds : T.sWeak;
    final range = s['range'] ?? (s['from_key'] != null ? '${s['from_key']['surah_name']} ${arDigits(s['from_key']['ayah'])} ← ${s['to_key']['surah_name']} ${arDigits(s['to_key']['ayah'])}' : '');
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(color: T.surface, borderRadius: BorderRadius.circular(12), border: Border.all(color: T.rule)),
      child: Row(children: [
        Container(width: 38, height: 38, decoration: BoxDecoration(color: color.withValues(alpha: .14), shape: BoxShape.circle), child: Icon(o == 'pass' ? Icons.check_rounded : o == 'partial' ? Icons.remove_rounded : Icons.replay_rounded, color: color, size: 20)),
        const SizedBox(width: 12),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Text(purposeAr[s['purpose']] ?? s['purpose'].toString(), style: T.body(size: 13.5, weight: FontWeight.w700)),
            const SizedBox(width: 8),
            Text(outcomeAr[o] ?? o, style: T.body(size: 12.5, color: color, weight: FontWeight.w600)),
            const Spacer(),
            Text((s['started_at'] ?? '').toString().substring(0, 10), style: T.mono(size: 10.5)),
          ]),
          if (range.toString().isNotEmpty) Text(range.toString(), style: T.body(size: 12.5, color: T.ink2)),
          if ((s['note'] ?? '').toString().isNotEmpty) Text(s['note'], style: T.body(size: 12, color: T.ink3), maxLines: 2, overflow: TextOverflow.ellipsis),
          if (s['mistake_count'] != null || s['mistakes'] is List)
            Text('${arDigits(s['mistake_count'] ?? (s['mistakes'] as List).length)} خطأ', style: T.body(size: 11.5, color: T.ink3)),
        ])),
      ]),
    );
  }
}
