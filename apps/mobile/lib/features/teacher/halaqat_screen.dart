import 'package:flutter/material.dart';

import '../../core/api.dart';
import '../../core/theme.dart';
import '../../widgets/common.dart';
import 'today_screen.dart';

class HalaqatScreen extends StatelessWidget {
  const HalaqatScreen({super.key});
  @override
  Widget build(BuildContext context) {
    return Column(children: [
      const NightHeader(eyebrow: 'المعلم', title: 'حلقاتي', subtitle: 'افتح الحلقة لتسجيل الحضور والتسميع من خطة اليوم.'),
      Expanded(
        child: Fetch<Map<String, dynamic>>(
          future: () async => (await Api.I.get('/halaqat?page_size=50')) as Map<String, dynamic>,
          builder: (context, d, refresh) {
            final rows = (d['results'] as List).cast<Map<String, dynamic>>();
            return RefreshIndicator(
              onRefresh: () async => refresh(),
              child: ListView.separated(
                padding: const EdgeInsets.all(18),
                itemCount: rows.length,
                separatorBuilder: (_, __) => const SizedBox(height: 10),
                itemBuilder: (context, i) {
                  final h = rows[i];
                  return Card(
                    child: InkWell(
                      borderRadius: BorderRadius.circular(12),
                      onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => TodayScreen(halaqahId: h['id']))),
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          Row(children: [Expanded(child: Text(h['name'], style: T.display(size: 17))), Chip2({'in_person': 'حضوري', 'online': 'عن بُعد', 'hybrid': 'مدمج'}[h['kind']] ?? '', color: T.lapis)]),
                          const SizedBox(height: 4),
                          Text('${h['branch_name']} · ${h['schedule_summary']}', style: T.body(size: 12.5, color: T.ink3)),
                          const SizedBox(height: 10),
                          Row(children: [
                            Text(arDigits(h['student_count']), style: T.display(size: 22)),
                            Text(' / ${arDigits(h['capacity'])} طالب', style: T.body(size: 13, color: T.ink3)),
                            const Spacer(),
                            const Icon(Icons.arrow_back_ios_new_rounded, size: 16, color: T.gold),
                          ]),
                        ]),
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
