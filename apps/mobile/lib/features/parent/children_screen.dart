import 'package:flutter/material.dart';

import '../../core/api.dart';
import '../../core/theme.dart';
import '../../widgets/common.dart';
import 'weekly_screen.dart';

/// Parent: the linked children, each with the plain answer to "is my child improving?"
class ChildrenScreen extends StatelessWidget {
  const ChildrenScreen({super.key});
  @override
  Widget build(BuildContext context) {
    return Column(children: [
      NightHeader(eyebrow: 'ولي الأمر', title: 'أبنائي', subtitle: 'هل حضر؟ ماذا حفظ؟ ماذا راجع؟ هل يتحسّن؟ ماذا يوصي المعلم؟ ما المطلوب اليوم؟',
          trailing: Avatar(Api.I.session?.fullName ?? '', size: 40)),
      Expanded(
        child: Fetch<Map<String, dynamic>>(
          future: () async => (await Api.I.get('/students?page_size=20')) as Map<String, dynamic>,
          builder: (context, d, refresh) {
            final rows = (d['results'] as List).cast<Map<String, dynamic>>();
            if (rows.isEmpty) return const EmptyState(title: 'لا أبناء مرتبطون بحسابك', body: 'اطلب من المركز ربط حسابك بملف الطالب.', icon: Icons.family_restroom_rounded);
            return RefreshIndicator(
              onRefresh: () async => refresh(),
              child: ListView.separated(
                padding: const EdgeInsets.all(18),
                itemCount: rows.length,
                separatorBuilder: (_, __) => const SizedBox(height: 12),
                itemBuilder: (context, i) {
                  final s = rows[i];
                  final j = s['journey_summary'] as Map<String, dynamic>?;
                  final name = s['person']['display_name_ar'] as String;
                  final critical = (j?['critical_ayat'] ?? 0) as num;
                  return FadeIn(
                    index: i,
                    child: Card(
                      child: InkWell(
                        borderRadius: BorderRadius.circular(12),
                        onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => WeeklyScreen(studentId: s['id'], journeyId: j?['id']))),
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                            Row(children: [
                              Avatar(name),
                              const SizedBox(width: 12),
                              Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                                Text(name, style: T.body(size: 16, weight: FontWeight.w600)),
                                Text('${s['halaqah']?['name'] ?? ''} · ${s['branch_name']}', style: T.body(size: 12.5, color: T.ink3)),
                              ])),
                              if (j != null) RetentionRing((j['avg_retention'] as num?)?.toDouble(), size: 52, stroke: 4.5),
                            ]),
                            if (j != null) ...[
                              const SizedBox(height: 14),
                              JuzStrip(j['juz_map'] as List?, height: 12),
                              const SizedBox(height: 10),
                              Row(children: [
                                Text('${arDigits(j['memorized_pages'])} صفحة محفوظة', style: T.body(size: 13, color: T.ink2)),
                                const Spacer(),
                                Chip2(critical > 0 ? '${arDigits(critical)} آيات تحتاج متابعة' : 'على المسار', color: critical > 0 ? T.sWeak : T.sStrong, filled: true),
                              ]),
                            ],
                            const SizedBox(height: 12),
                            Row(children: [
                              const Icon(Icons.arrow_back_ios_new_rounded, size: 14, color: T.gold),
                              const SizedBox(width: 6),
                              Text('تقرير الأسبوع والإجابات الست', style: T.body(size: 12.5, color: T.gold, weight: FontWeight.w700)),
                            ]),
                          ]),
                        ),
                      ),
                    ),
                  );
                },
              ),
            );
          },
        ),
      ),
    ]);
  }
}
