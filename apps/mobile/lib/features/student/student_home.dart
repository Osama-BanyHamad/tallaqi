import 'package:flutter/material.dart';

import '../../core/api.dart';
import '../../core/quran.dart';
import '../../core/theme.dart';
import '../../widgets/common.dart';
import '../../widgets/memory_map.dart';
import 'practice_screen.dart';

/// Student home: today's Hifz and revision, then the journey. Calm, no streaks, no gamification.
class StudentHome extends StatelessWidget {
  const StudentHome({super.key});
  @override
  Widget build(BuildContext context) {
    return Fetch<Map<String, dynamic>>(
      future: () async {
        // Students cannot list the roster; the journeys endpoint is scoped to self.
        final me = await Api.I.get('/journeys?page_size=1') as Map<String, dynamic>;
        final results = (me['results'] as List).cast<Map<String, dynamic>>();
        if (results.isEmpty) throw ApiException(404, 'no_student', 'لا يوجد ملف طالب مرتبط بهذا الحساب');
        final jid = results.first['id'];
        final journey = await Api.I.get('/journeys/$jid') as Map<String, dynamic>;
        final plan = await Api.I.get('/journeys/$jid/plan') as Map<String, dynamic>;
        return {'student': results.first, 'journey': journey, 'plan': plan};
      },
      builder: (context, d, refresh) {
        final j = d['journey'] as Map<String, dynamic>;
        final plan = d['plan'] as Map<String, dynamic>;
        final segs = (plan['segments'] as List).cast<Map<String, dynamic>>();
        final cur = j['current_key'] as Map<String, dynamic>?;
        return RefreshIndicator(
          onRefresh: () async => refresh(),
          child: ListView(padding: EdgeInsets.zero, children: [
            NightHeader(
              eyebrow: 'اليوم', title: j['student_name'],
              subtitle: cur == null ? 'في المراجعة الطويلة' : 'موضع الحفظ الجديد: ${cur['surah_name']} ${arDigits(cur['ayah'])} · صفحة ${arDigits(cur['page'])}',
              child: Row(children: [
                Expanded(child: Kpi(label: 'صفحات محفوظة', value: arDigits(j['memorized_pages']), accent: true)),
                const SizedBox(width: 10),
                Expanded(child: Kpi(label: 'متوسط الثبات', value: pct((j['avg_retention'] as num?)?.toDouble()))),
              ]),
            ),
            Padding(
              padding: const EdgeInsets.all(18),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('خطة اليوم', style: T.display(size: 18)),
                const SizedBox(height: 10),
                if (segs.isEmpty) Text(plan['paused_new'] == true ? 'إيقاف مؤقت للحفظ الجديد — ركّز على المراجعة.' : 'لا توجد مقاطع اليوم.', style: T.body(size: 14, color: T.ink3)),
                for (final s in segs)
                  Card(
                    child: ListTile(
                      contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                      leading: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(color: s['purpose'] == 'new' ? T.lapisTint : s['purpose'] == 'near' ? T.goldTint : T.ground2, borderRadius: BorderRadius.circular(6)),
                        child: Text(purposeAr[s['purpose']] ?? s['purpose'], style: T.body(size: 11.5, weight: FontWeight.w700, color: s['purpose'] == 'new' ? T.lapis : T.ink2)),
                      ),
                      title: Text('${s['from_key']['surah_name']} ${arDigits(s['from_key']['ayah'])} ← ${s['to_key']['surah_name']} ${arDigits(s['to_key']['ayah'])}', style: T.body(size: 14.5, weight: FontWeight.w600)),
                      subtitle: Text(s['reason'] ?? '', style: T.body(size: 12, color: T.ink3)),
                      trailing: const Icon(Icons.arrow_back_ios_new_rounded, size: 16, color: T.gold),
                      onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => PracticeScreen(journeyId: j['id'], from: s['from_ayah_index'], to: s['to_ayah_index'], title: purposeAr[s['purpose']] ?? ''))),
                    ),
                  ),
                for (final r in (plan['rationale'] as List)) Padding(padding: const EdgeInsets.only(top: 6), child: Text('$r', style: T.body(size: 12.5, color: T.ink2))),
                const SizedBox(height: 24),
                Text('رحلتي مع القرآن', style: T.display(size: 18)),
                const SizedBox(height: 6),
                JuzStrip(j['juz_map'] as List?, height: 18),
                const SizedBox(height: 16),
                Card(child: Padding(padding: const EdgeInsets.all(14), child: MemoryMapView(journeyId: j['id']))),
                const SizedBox(height: 16),
                Text('الثبات مقياس تعليمي لاستقرار الاسترجاع، يُحسب من تسميعات معلمك. ليس حكمًا شرعيًا على التلاوة.', style: T.body(size: 12, color: T.ink3)),
              ]),
            ),
          ]),
        );
      },
    );
  }
}
