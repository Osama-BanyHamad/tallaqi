import 'package:flutter/material.dart';

import '../../core/api.dart';
import '../../core/progress.dart';
import '../../core/quran.dart';
import '../../core/theme.dart';
import '../../widgets/common.dart';
import '../../widgets/memory_map.dart';
import '../teacher/student_detail_screen.dart';
import 'practice_screen.dart';

/// Student home: calm, no streaks. Today's plan first, then the journey. Every practice tap opens the verified text.
class StudentHome extends StatefulWidget {
  const StudentHome({super.key});
  @override
  State<StudentHome> createState() => _StudentHomeState();
}

class _StudentHomeState extends State<StudentHome> {
  int _v = 0;
  @override
  Widget build(BuildContext context) {
    return Fetch<Map<String, dynamic>>(
      key: ValueKey(_v),
      cacheKey: 'student-home',
      future: () async {
        // Students cannot list the roster; the journeys endpoint is scoped to self.
        final me = await Api.I.get('/journeys?page_size=1') as Map<String, dynamic>;
        final results = (me['results'] as List).cast<Map<String, dynamic>>();
        if (results.isEmpty) throw ApiException(404, 'no_student', 'لا يوجد ملف طالب مرتبط بهذا الحساب');
        final jid = results.first['id'];
        final r = await Future.wait([Api.I.get('/journeys/$jid'), Api.I.get('/journeys/$jid/plan'), Api.I.get('/journeys/$jid/sessions?limit=10').catchError((_) => <String, dynamic>{'results': []})]);
        final sess = r[2];
        return {'journey': r[0], 'plan': r[1], 'sessions': sess is Map ? sess['results'] : sess, 'progress': await Progress.I.all()};
      },
      builder: (context, d, refresh) {
        final j = d['journey'] as Map<String, dynamic>;
        final plan = d['plan'] as Map<String, dynamic>?;
        final segs = ((plan?['segments'] as List?) ?? const []).cast<Map<String, dynamic>>();
        final sessions = ((d['sessions'] as List?) ?? const []).cast<Map<String, dynamic>>();
        final cur = j['current_key'] as Map<String, dynamic>?;
        final progress = (d['progress'] as Map<String, dynamic>?) ?? {};
        final done = segs.where((s) => s['completion'] == 'verified' || progress.containsKey(Progress.keyFor(s['from_ayah_index'], s['to_ayah_index']))).length;
        final hour = DateTime.now().hour;
        final greet = hour < 12 ? 'صباح الخير' : hour < 18 ? 'مساء الخير' : 'مساء النور';
        return RefreshIndicator(
          onRefresh: () async => setState(() => _v++),
          child: ListView(padding: EdgeInsets.zero, children: [
            NightHeader(
              eyebrow: 'اليوم',
              title: '$greet، ${(j['student_name'] ?? '').toString().split(' ').first}',
              subtitle: cur != null ? 'موضع الحفظ الجديد: ${cur['surah_name']} ${arDigits(cur['ayah'])} · صفحة ${arDigits(cur['page'])}' : 'في المراجعة الطويلة',
              trailing: RetentionRing((j['avg_retention'] as num?)?.toDouble(), size: 66, light: true, label: T.stateWord((j['avg_retention'] as num?)?.toDouble()), stroke: 5),
              child: Column(children: [
                Row(children: [
                  Expanded(child: _HeaderStat(arDigits(j['memorized_pages'] ?? 0), 'صفحة محفوظة')),
                  Expanded(child: _HeaderStat('${arDigits(done)} / ${arDigits(segs.length)}', 'مقاطع اليوم')),
                  Expanded(child: _HeaderStat(arDigits(j['critical_ayat'] ?? 0), 'آيات حرجة', color: (j['critical_ayat'] ?? 0) > 0 ? T.sWeak : T.sStrong)),
                ]),
                const SizedBox(height: 12),
                JuzStrip(j['juz_map'] as List?, height: 10),
              ]),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(18, 18, 18, 30),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                SectionTitle('خطة اليوم', top: 0, trailing: Text('${arDigits(segs.length)} مقاطع', style: T.body(size: 12.5, color: T.ink3))),
                if (segs.isEmpty) const EmptyState(title: 'لا مقاطع اليوم', body: 'استرح، أو راجع من خريطة الحفظ.'),
                for (var i = 0; i < segs.length; i++)
                  FadeIn(index: i, child: _PlanCard(segs[i], local: progress[Progress.keyFor(segs[i]['from_ayah_index'], segs[i]['to_ayah_index'])] as Map<String, dynamic>?, onTap: () async {
                    final s = segs[i];
                    await Navigator.of(context).push(MaterialPageRoute(builder: (_) => PracticeScreen(journeyId: j['id'], from: s['from_ayah_index'], to: s['to_ayah_index'], title: purposeAr[s['purpose']] ?? '')));
                    setState(() => _v++);
                  })),
                if (plan?['paused_new'] == true)
                  Container(margin: const EdgeInsets.only(top: 4), padding: const EdgeInsets.all(12), decoration: BoxDecoration(color: T.goldTint, borderRadius: BorderRadius.circular(10)),
                      child: Text('إيقاف مؤقت للحفظ الجديد — ركّز على المراجعة هذا الأسبوع.', style: T.body(size: 13))),
                for (final r in ((plan?['rationale'] as List?) ?? const [])) Padding(padding: const EdgeInsets.only(top: 6), child: Text('• $r', style: T.body(size: 12.5, color: T.ink3))),
                SectionTitle('رحلتي مع القرآن', trailing: TextButton(onPressed: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => StudentDetailScreen(journeyId: j['id'], canPractice: true))), child: const Text('التفاصيل'))),
                Container(padding: const EdgeInsets.all(14), decoration: BoxDecoration(color: T.surface, borderRadius: BorderRadius.circular(14), border: Border.all(color: T.rule)), child: MemoryMapView(journeyId: j['id'])),
                if (sessions.isNotEmpty) ...[
                  const SectionTitle('آخر التسميعات'),
                  for (var i = 0; i < sessions.length && i < 5; i++)
                    FadeIn(index: i, child: Container(
                      margin: const EdgeInsets.only(bottom: 8), padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                      decoration: BoxDecoration(color: T.surface, borderRadius: BorderRadius.circular(12), border: Border.all(color: T.rule)),
                      child: Row(children: [
                        Icon(sessions[i]['outcome'] == 'pass' ? Icons.check_circle_rounded : Icons.replay_circle_filled_rounded, color: sessions[i]['outcome'] == 'pass' ? T.sStrong : T.sNeeds, size: 22),
                        const SizedBox(width: 10),
                        Expanded(child: Text('${purposeAr[sessions[i]['purpose']] ?? ''} · ${outcomeAr[sessions[i]['outcome']] ?? ''}', style: T.body(size: 13.5, weight: FontWeight.w600))),
                        Text((sessions[i]['started_at'] ?? '').toString().substring(0, 10), style: T.mono(size: 10.5)),
                      ]),
                    )),
                ],
                const SizedBox(height: 10),
                Text('الثبات مقياس تعليمي لاستقرار الاسترجاع يُحسب من تسميعات معلمك؛ ليس حكمًا شرعيًا على التلاوة.', style: T.body(size: 12, color: T.ink3)),
              ]),
            ),
          ]),
        );
      },
    );
  }
}

class _HeaderStat extends StatelessWidget {
  const _HeaderStat(this.v, this.l, {this.color});
  final String v;
  final String l;
  final Color? color;
  @override
  Widget build(BuildContext context) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(v, style: T.display(size: 22, color: color ?? T.nightInk)),
        Text(l, style: T.body(size: 11, color: T.nightMuted)),
      ]);
}

class _PlanCard extends StatelessWidget {
  const _PlanCard(this.s, {required this.onTap, this.local});
  final Map<String, dynamic> s;
  final VoidCallback onTap;
  final Map<String, dynamic>? local;
  @override
  Widget build(BuildContext context) {
    final done = s['completion'] == 'verified';
    final practiced = local != null;
    final acc = (local?['accuracy'] as num?)?.toDouble();
    final c = s['purpose'] == 'new' ? T.lapis : s['purpose'] == 'near' ? T.gold : T.sRecent;
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(children: [
            Container(width: 46, height: 46, decoration: BoxDecoration(color: c.withValues(alpha: .14), borderRadius: BorderRadius.circular(12)),
                child: Icon(done ? Icons.check_rounded : s['purpose'] == 'new' ? Icons.auto_stories_rounded : Icons.replay_rounded, color: done ? T.sStrong : c)),
            const SizedBox(width: 12),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(purposeAr[s['purpose']] ?? s['purpose'], style: T.body(size: 12, color: c, weight: FontWeight.w700)),
              Text('${s['from_key']['surah_name']} ${arDigits(s['from_key']['ayah'])} ← ${s['to_key']['surah_name']} ${arDigits(s['to_key']['ayah'])}', style: T.body(size: 15, weight: FontWeight.w600)),
              if ((s['reason'] ?? '').toString().isNotEmpty) Text(s['reason'], style: T.body(size: 12, color: T.ink3), maxLines: 1, overflow: TextOverflow.ellipsis),
            ])),
            Column(children: [
              if (acc != null) RetentionRing(acc, size: 38, stroke: 3.5)
              else Icon(done ? Icons.verified_rounded : practiced ? Icons.task_alt_rounded : Icons.mic_rounded, color: done ? T.sStrong : practiced ? T.sRecent : T.gold, size: 22),
              Text(done ? 'سمّعت' : practiced ? 'تدرّبت' : 'تدرّب', style: T.body(size: 11, color: done ? T.sStrong : practiced ? T.sRecent : T.gold, weight: FontWeight.w700)),
            ]),
          ]),
        ),
      ),
    );
  }
}
