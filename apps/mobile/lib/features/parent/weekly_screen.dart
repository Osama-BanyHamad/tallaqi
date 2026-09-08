import 'package:flutter/material.dart';

import '../../core/api.dart';
import '../../core/quran.dart';
import '../../core/theme.dart';
import '../../widgets/common.dart';

/// The weekly report a parent actually wants: six answers, no analytics dashboard.
class WeeklyScreen extends StatelessWidget {
  const WeeklyScreen({super.key, required this.studentId});
  final String studentId;
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Fetch<Map<String, dynamic>>(
        future: () async => (await Api.I.get('/students/$studentId/weekly')) as Map<String, dynamic>,
        builder: (context, d, refresh) {
          final att = d['attendance'] as Map<String, dynamic>;
          final plan = d['plan'] as Map<String, dynamic>?;
          final segs = ((plan?['segments'] as List?) ?? const []).cast<Map<String, dynamic>>();
          final cur = d['current'] as Map<String, dynamic>?;
          return Column(children: [
            NightHeader(
              eyebrow: 'تقرير الأسبوع', title: d['student']['name'],
              subtitle: '${d['week']['from']} → ${d['week']['to']}',
              trailing: IconButton(onPressed: () => Navigator.pop(context), icon: const Icon(Icons.arrow_forward_rounded, color: T.nightInk)),
              child: JuzStrip(d['juz_map'] as List?, height: 14),
            ),
            Expanded(
              child: ListView(padding: const EdgeInsets.all(18), children: [
                GridView.count(
                  crossAxisCount: 2, shrinkWrap: true, physics: const NeverScrollableScrollPhysics(), mainAxisSpacing: 10, crossAxisSpacing: 10, childAspectRatio: 1.7,
                  children: [
                    Kpi(label: 'الحضور', value: '${arDigits(att['present'])} / ${arDigits(att['total'])}', accent: true),
                    Kpi(label: 'حفظ جديد', value: '${arDigits(d['new_pages'])} صفحة'),
                    Kpi(label: 'مراجعة', value: '${arDigits(d['revision_pages'])} صفحة'),
                    Kpi(label: 'الثبات', value: pct((d['retention'] as num?)?.toDouble()), color: T.retention((d['retention'] as num?)?.toDouble())),
                  ],
                ),
                const SizedBox(height: 18),
                _Answer('هل يتحسّن؟', d['critical_ayat'] == 0
                    ? 'نعم. لا آيات حرجة هذا الأسبوع، و${arDigits(d['passed'])} من ${arDigits(d['sessions'])} تسميعات اجتازها.'
                    : 'يحتاج متابعة: ${arDigits(d['critical_ayat'])} آيات حرجة و${arDigits(d['weak_ayat'])} ضعيفة تحتاج مراجعة مع المعلم.'),
                _Answer('ماذا يوصي المعلم؟', (d['teacher_note'] as String?)?.isNotEmpty == true ? d['teacher_note'] : 'لا توجد ملاحظة هذا الأسبوع.'),
                if (cur != null) _Answer('أين وصل؟', '${cur['surah_name']} — آية ${cur['key'].toString().split(':').last}'),
                if (segs.isNotEmpty)
                  _Answer('ما المطلوب اليوم؟', segs.map((s) => '${purposeAr[s['purpose']]}: ${s['from_key']['surah_name']} ${arDigits(s['from_key']['ayah'])} ← ${s['to_key']['surah_name']} ${arDigits(s['to_key']['ayah'])}').join('\n')),
                const SizedBox(height: 10),
                Text('الثبات مقياس تعليمي لاستقرار الاسترجاع يُحسب من تسميعات المعلم؛ ليس حكمًا شرعيًا على التلاوة.', style: T.body(size: 12, color: T.ink3)),
              ]),
            ),
          ]);
        },
      ),
    );
  }
}

class _Answer extends StatelessWidget {
  const _Answer(this.q, this.a);
  final String q;
  final String a;
  @override
  Widget build(BuildContext context) => Container(
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(color: T.surface, borderRadius: BorderRadius.circular(12), border: Border.all(color: T.rule),
            boxShadow: [BoxShadow(color: T.ink.withValues(alpha: .05), blurRadius: 16, offset: const Offset(0, 8))]),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Eyebrow(q),
          const SizedBox(height: 6),
          Text(a, style: T.body(size: 15)),
        ]),
      );
}
