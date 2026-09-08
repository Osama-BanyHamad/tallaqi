import 'package:flutter/material.dart';

import '../../core/api.dart';
import '../../core/theme.dart';
import '../../widgets/common.dart';
import 'student_detail_screen.dart';

/// Teacher's students across their Halaqat, searchable, with the Juz strip and retention at a glance.
class StudentsScreen extends StatefulWidget {
  const StudentsScreen({super.key});
  @override
  State<StudentsScreen> createState() => _StudentsScreenState();
}

class _StudentsScreenState extends State<StudentsScreen> {
  String _q = '';
  String _sort = 'name'; // name | retention | critical
  @override
  Widget build(BuildContext context) {
    return Column(children: [
      NightHeader(
        compact: true,
        eyebrow: 'المعلم',
        title: 'طلابي',
        child: TextField(
          onChanged: (v) => setState(() => _q = v.trim()),
          style: T.body(size: 14, color: T.nightInk),
          decoration: InputDecoration(hintText: 'ابحث بالاسم أو الرقم', hintStyle: T.body(size: 13.5, color: T.nightMuted), prefixIcon: const Icon(Icons.search_rounded, color: T.nightMuted),
              filled: true, fillColor: Colors.white.withValues(alpha: .07), isDense: true, contentPadding: const EdgeInsets.symmetric(vertical: 10),
              enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide(color: Colors.white.withValues(alpha: .12))),
              focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: T.gold2))),
        ),
      ),
      Container(
        color: T.surface,
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
        child: Row(children: [
          Text('ترتيب:', style: T.body(size: 12.5, color: T.ink3)),
          const SizedBox(width: 8),
          for (final s in const [('name', 'الاسم'), ('retention', 'الأضعف ثباتًا'), ('critical', 'الأكثر حرجًا')])
            Padding(padding: const EdgeInsetsDirectional.only(end: 6), child: ChoiceChip(label: Text(s.$2), selected: _sort == s.$1, onSelected: (_) => setState(() => _sort = s.$1), showCheckmark: false,
                selectedColor: T.lapis, labelStyle: T.body(size: 12, weight: FontWeight.w600, color: _sort == s.$1 ? Colors.white : T.ink2), side: const BorderSide(color: T.rule), backgroundColor: T.ground2, visualDensity: VisualDensity.compact)),
        ]),
      ),
      Expanded(
        child: Fetch<Map<String, dynamic>>(
          key: ValueKey(_q),
          future: () async => (await Api.I.get('/students?page_size=100&search=${Uri.encodeQueryComponent(_q)}')) as Map<String, dynamic>,
          builder: (context, d, refresh) {
            final rows = (d['results'] as List).cast<Map<String, dynamic>>();
            rows.sort((a, b) {
              final ja = a['journey_summary'] as Map?, jb = b['journey_summary'] as Map?;
              return switch (_sort) {
                'retention' => ((ja?['avg_retention'] ?? 1) as num).compareTo((jb?['avg_retention'] ?? 1) as num),
                'critical' => ((jb?['critical_ayat'] ?? 0) as num).compareTo((ja?['critical_ayat'] ?? 0) as num),
                _ => (a['person']['display_name_ar'] as String).compareTo(b['person']['display_name_ar'] as String),
              };
            });
            if (rows.isEmpty) return const EmptyState(title: 'لا نتائج', icon: Icons.person_search_outlined);
            return RefreshIndicator(
              onRefresh: () async => refresh(),
              child: ListView.separated(
                padding: const EdgeInsets.all(16),
                itemCount: rows.length,
                separatorBuilder: (_, __) => const SizedBox(height: 8),
                itemBuilder: (context, i) {
                  final s = rows[i];
                  final j = s['journey_summary'] as Map<String, dynamic>?;
                  final name = s['person']['display_name_ar'] as String;
                  return FadeIn(
                    index: i,
                    child: Card(
                      child: InkWell(
                        borderRadius: BorderRadius.circular(12),
                        onTap: j == null ? null : () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => StudentDetailScreen(journeyId: j['id'], halaqahId: s['halaqah']?['id'], canRecite: true))),
                        child: Padding(
                          padding: const EdgeInsets.all(12),
                          child: Row(children: [
                            Avatar(name, size: 40),
                            const SizedBox(width: 12),
                            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                              Text(name, style: T.body(size: 14.5, weight: FontWeight.w600)),
                              Text('${s['student_code']} · ${s['halaqah']?['name'] ?? 'بدون حلقة'}', style: T.body(size: 11.5, color: T.ink3)),
                              if (j != null) Padding(padding: const EdgeInsets.only(top: 6), child: JuzStrip(j['juz_map'] as List?, height: 7)),
                            ])),
                            const SizedBox(width: 10),
                            if (j != null) Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
                              RetentionRing((j['avg_retention'] as num?)?.toDouble(), size: 40, stroke: 3.5),
                              if ((j['critical_ayat'] ?? 0) > 0) Text('${arDigits(j['critical_ayat'])} حرجة', style: T.body(size: 10.5, color: T.sWeak, weight: FontWeight.w600)),
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
