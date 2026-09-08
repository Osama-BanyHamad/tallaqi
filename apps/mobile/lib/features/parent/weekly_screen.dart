import 'package:flutter/material.dart';

import '../../core/api.dart';
import '../../core/quran.dart';
import '../../core/theme.dart';
import '../../widgets/common.dart';
import '../teacher/student_detail_screen.dart';

/// The weekly report a parent actually wants: six answers, then the 30-day attendance strip and the journey.
class WeeklyScreen extends StatelessWidget {
  const WeeklyScreen({super.key, required this.studentId, this.journeyId});
  final String studentId;
  final String? journeyId;
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Fetch<Map<String, dynamic>>(
        future: () async {
          final r = await Future.wait([Api.I.get('/students/$studentId/weekly'), Api.I.get('/students/$studentId/attendance?days=30').catchError((_) => <String, dynamic>{'records': []})]);
          return {'w': r[0], 'att': r[1]};
        },
        builder: (context, d, refresh) {
          final w = d['w'] as Map<String, dynamic>;
          final attHist = d['att'] as Map<String, dynamic>;
          final att = w['attendance'] as Map<String, dynamic>;
          final plan = w['plan'] as Map<String, dynamic>?;
          final segs = ((plan?['segments'] as List?) ?? const []).cast<Map<String, dynamic>>();
          final cur = w['current'] as Map<String, dynamic>?;
          final records = ((attHist['records'] as List?) ?? const []).cast<Map<String, dynamic>>();
          final improving = (w['critical_ayat'] ?? 0) == 0;
          return Column(children: [
            NightHeader(
              leadingBack: true,
              eyebrow: 'تقرير الأسبوع', title: w['student']['name'],
              subtitle: '${arDigits(w['week']['from'])} → ${arDigits(w['week']['to'])}',
              trailing: RetentionRing((w['retention'] as num?)?.toDouble(), size: 62, light: true, label: 'الثبات', stroke: 5),
              child: JuzStrip(w['juz_map'] as List?, height: 12),
            ),
            Expanded(
              child: RefreshIndicator(
                onRefresh: () async => refresh(),
                child: ListView(padding: const EdgeInsets.all(18), children: [
                  GridView.count(
                    crossAxisCount: 2, shrinkWrap: true, physics: const NeverScrollableScrollPhysics(), mainAxisSpacing: 10, crossAxisSpacing: 10, childAspectRatio: 1.5,
                    children: [
                      Kpi(label: 'هل حضر؟', value: '${arDigits(att['present'])} / ${arDigits(att['total'])}', accent: true, icon: Icons.event_available_rounded),
                      Kpi(label: 'ماذا حفظ؟', value: '${arDigits(w['new_pages'])} صفحة', icon: Icons.auto_stories_rounded),
                      Kpi(label: 'ماذا راجع؟', value: '${arDigits(w['revision_pages'])} صفحة', icon: Icons.replay_rounded),
                      Kpi(label: 'التسميع', value: '${arDigits(w['passed'])} / ${arDigits(w['sessions'])}', sub: 'اجتاز من الجلسات', icon: Icons.mic_rounded),
                    ],
                  ),
                  const SizedBox(height: 16),
                  FadeIn(index: 1, child: _Answer('هل يتحسّن؟', improving
                      ? 'نعم. لا آيات حرجة هذا الأسبوع، واجتاز ${arDigits(w['passed'])} من ${arDigits(w['sessions'])} تسميعات.'
                      : 'يحتاج متابعة: ${arDigits(w['critical_ayat'])} آيات حرجة و${arDigits(w['weak_ayat'])} ضعيفة تحتاج مراجعة مع المعلم.', tone: improving ? T.sStrong : T.sNeeds)),
                  FadeIn(index: 2, child: _Answer('ماذا يوصي المعلم؟', (w['teacher_note'] as String?)?.isNotEmpty == true ? w['teacher_note'] : 'لا توجد ملاحظة هذا الأسبوع.')),
                  if (cur != null) FadeIn(index: 3, child: _Answer('أين وصل؟', '${cur['surah_name']} — آية ${arDigits(cur['key'].toString().split(':').last)}')),
                  if (segs.isNotEmpty)
                    FadeIn(index: 4, child: _Answer('ما المطلوب اليوم؟', segs.map((s) => '${purposeAr[s['purpose']]}: ${s['from_key']['surah_name']} ${arDigits(s['from_key']['ayah'])} ← ${s['to_key']['surah_name']} ${arDigits(s['to_key']['ayah'])}').join('\n'))),
                  const SectionTitle('الحضور · آخر ٣٠ يومًا'),
                  Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(color: T.surface, borderRadius: BorderRadius.circular(12), border: Border.all(color: T.rule)),
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Wrap(spacing: 5, runSpacing: 5, children: [
                        for (final r in records)
                          Tooltip(message: '${r['date']} · ${_attAr[r['status']] ?? r['status']}', child: Container(width: 16, height: 16, decoration: BoxDecoration(color: _attColor[r['status']] ?? T.sNone, borderRadius: BorderRadius.circular(3)))),
                        if (records.isEmpty) Text('لا سجلات بعد.', style: T.body(size: 12.5, color: T.ink3)),
                      ]),
                      const SizedBox(height: 10),
                      Wrap(spacing: 6, runSpacing: 6, children: [for (final e in _attAr.entries) Chip2(e.value, color: _attColor[e.key])]),
                    ]),
                  ),
                  if (journeyId != null) ...[
                    const SizedBox(height: 14),
                    OutlinedButton.icon(onPressed: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => StudentDetailScreen(journeyId: journeyId!))), icon: const Icon(Icons.map_outlined), label: const Text('خريطة الحفظ الكاملة والسجل')),
                  ],
                  const SizedBox(height: 12),
                  Text('الثبات مقياس تعليمي لاستقرار الاسترجاع يُحسب من تسميعات المعلم؛ ليس حكمًا شرعيًا على التلاوة.', style: T.body(size: 12, color: T.ink3)),
                ]),
              ),
            ),
          ]);
        },
      ),
    );
  }
}

const _attAr = {'present': 'حاضر', 'late': 'متأخر', 'absent': 'غائب', 'excused': 'بعذر', 'left_early': 'انصرف مبكرًا'};
const _attColor = {'present': T.sStrong, 'late': T.sNeeds, 'absent': T.sWeak, 'excused': T.gold, 'left_early': T.sRecent};

class _Answer extends StatelessWidget {
  const _Answer(this.q, this.a, {this.tone});
  final String q;
  final String a;
  final Color? tone;
  @override
  Widget build(BuildContext context) => Container(
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(color: T.surface, borderRadius: BorderRadius.circular(14), border: Border.all(color: tone?.withValues(alpha: .35) ?? T.rule),
            boxShadow: [BoxShadow(color: T.ink.withValues(alpha: .05), blurRadius: 16, offset: const Offset(0, 8))]),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Eyebrow(q),
          const SizedBox(height: 6),
          Text(a, style: T.body(size: 15)),
        ]),
      );
}
