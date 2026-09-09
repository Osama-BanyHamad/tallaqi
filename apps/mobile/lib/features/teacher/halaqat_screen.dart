import 'package:flutter/material.dart';

import '../../core/api.dart';
import '../../core/theme.dart';
import '../../core/prefs.dart';
import '../../widgets/common.dart';
import 'today_screen.dart';

/// Teacher home: today's date, the Halaqat, and what is waiting in each one.
class HalaqatScreen extends StatelessWidget {
  const HalaqatScreen({super.key});
  @override
  Widget build(BuildContext context) {
    final now = DateTime.now();
    const days = ['الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد'];
    return Fetch<Map<String, dynamic>>(
      future: () async => (await Api.I.get('/halaqat?page_size=50')) as Map<String, dynamic>,
      builder: (context, d, refresh) {
        final rows = (d['results'] as List).cast<Map<String, dynamic>>();
        if (rows.length == 1 && Prefs.I.session.add('auto-open')) {
          WidgetsBinding.instance.addPostFrameCallback((_) { if (context.mounted) Navigator.of(context).push(MaterialPageRoute(builder: (_) => TodayScreen(halaqahId: rows.first['id']))); });
        }
        final students = rows.fold<int>(0, (a, h) => a + ((h['student_count'] as num?)?.toInt() ?? 0));
        return Column(children: [
          NightHeader(
            eyebrow: '${days[now.weekday - 1]} · ${arDigits('${now.year}/${now.month}/${now.day}')}',
            title: 'أهلًا، ${Api.I.session?.fullName ?? ''}',
            subtitle: 'افتح الحلقة لتسجيل الحضور والتسميع من خطة اليوم.',
            child: Row(children: [
              Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(arDigits(rows.length), style: T.display(size: 26, color: T.gold2)), Text('حلقة', style: T.body(size: 11.5, color: T.nightMuted))])),
              Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(arDigits(students), style: T.display(size: 26, color: T.nightInk)), Text('طالب', style: T.body(size: 11.5, color: T.nightMuted))])),
              Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(Api.I.moduleOn('hifz.asr') ? 'مفعّل' : 'معطّل', style: T.display(size: 18, color: Api.I.moduleOn('hifz.asr') ? T.sStrong : T.nightMuted)), Text('التسميع الذكي', style: T.body(size: 11.5, color: T.nightMuted))])),
            ]),
          ),
          Expanded(
            child: RefreshIndicator(
              onRefresh: () async => refresh(),
              child: rows.isEmpty
                  ? const EmptyState(title: 'لا حلقات مرتبطة بحسابك', body: 'اطلب من الإدارة ربط حسابك بحلقة.')
                  : ListView.separated(
                      padding: const EdgeInsets.all(18),
                      itemCount: rows.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 12),
                      itemBuilder: (context, i) {
                        final h = rows[i];
                        final cap = (h['capacity'] as num?)?.toInt() ?? 0;
                        final n = (h['student_count'] as num?)?.toInt() ?? 0;
                        return FadeIn(
                          index: i,
                          child: Card(
                            child: InkWell(
                              borderRadius: BorderRadius.circular(12),
                              onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => TodayScreen(halaqahId: h['id']))),
                              child: Padding(
                                padding: const EdgeInsets.all(16),
                                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                                  Row(children: [
                                    Container(width: 42, height: 42, decoration: BoxDecoration(color: T.lapisTint, borderRadius: BorderRadius.circular(12)), child: const Icon(Icons.radio_button_checked_rounded, color: T.lapis)),
                                    const SizedBox(width: 12),
                                    Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                                      Text(h['name'], style: T.display(size: 16)),
                                      Text('${h['branch_name']} · ${h['schedule_summary']}', style: T.body(size: 12.5, color: T.ink3)),
                                    ])),
                                    Chip2({'in_person': 'حضوري', 'online': 'عن بُعد', 'hybrid': 'مدمج'}[h['kind']] ?? '', color: T.lapis),
                                  ]),
                                  const SizedBox(height: 14),
                                  Row(children: [
                                    Text(arDigits(n), style: T.display(size: 22)),
                                    Text(' / ${arDigits(cap)} طالب', style: T.body(size: 13, color: T.ink3)),
                                    const Spacer(),
                                    Container(padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6), decoration: BoxDecoration(color: T.gold, borderRadius: BorderRadius.circular(999)),
                                        child: Text('افتح حلقة اليوم', style: T.body(size: 12.5, weight: FontWeight.w700, color: const Color(0xFF1F1806)))),
                                  ]),
                                  const SizedBox(height: 10),
                                  ClipRRect(borderRadius: BorderRadius.circular(4), child: LinearProgressIndicator(value: cap > 0 ? (n / cap).clamp(0, 1) : 0, minHeight: 5, backgroundColor: T.ground2, color: T.lapis)),
                                ]),
                              ),
                            ),
                          ),
                        );
                      },
                    ),
            ),
          ),
        ]);
      },
    );
  }
}
