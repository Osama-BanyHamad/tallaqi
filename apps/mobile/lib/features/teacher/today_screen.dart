import 'package:flutter/material.dart';

import '../../core/api.dart';
import '../../core/quran.dart';
import '../../core/theme.dart';
import '../../widgets/common.dart';
import '../tasmee/tasmee_screen.dart';

/// The teacher's working screen: roster + attendance + today's plan per student, one tap into Tasmee'.
class TodayScreen extends StatefulWidget {
  const TodayScreen({super.key, required this.halaqahId});
  final String halaqahId;
  @override
  State<TodayScreen> createState() => _TodayScreenState();
}

class _TodayScreenState extends State<TodayScreen> {
  int _v = 0;
  Future<Map<String, dynamic>> _load() async => (await Api.I.get('/halaqat/${widget.halaqahId}/today')) as Map<String, dynamic>;

  Future<void> _mark(String studentId, String status) async {
    await Api.I.post('/halaqat/${widget.halaqahId}/attendance', {'records': [{'student_id': studentId, 'status': status}]});
    setState(() => _v++);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Fetch<Map<String, dynamic>>(
        key: ValueKey(_v),
        future: _load,
        builder: (context, d, refresh) {
          final h = d['halaqah'] as Map<String, dynamic>;
          final roster = (d['roster'] as List).cast<Map<String, dynamic>>();
          final present = roster.where((r) => r['attendance'] == 'present' || r['attendance'] == 'late').length;
          return Column(children: [
            NightHeader(
              eyebrow: 'حلقة اليوم',
              title: h['name'],
              subtitle: h['schedule_summary'],
              trailing: IconButton(onPressed: () => Navigator.pop(context), icon: const Icon(Icons.arrow_forward_rounded, color: T.nightInk)),
              child: Row(children: [
                Text(arDigits(present), style: T.display(size: 30, color: T.gold2)),
                Text(' / ${arDigits(roster.length)} حاضر', style: T.body(size: 14, color: T.nightMuted)),
              ]),
            ),
            Expanded(
              child: ListView.separated(
                padding: const EdgeInsets.all(16),
                itemCount: roster.length,
                separatorBuilder: (_, __) => const SizedBox(height: 10),
                itemBuilder: (context, i) => _StudentCard(row: roster[i], halaqahId: widget.halaqahId, onMark: _mark, onDone: () => setState(() => _v++)),
              ),
            ),
          ]);
        },
      ),
    );
  }
}

class _StudentCard extends StatelessWidget {
  const _StudentCard({required this.row, required this.halaqahId, required this.onMark, required this.onDone});
  final Map<String, dynamic> row;
  final String halaqahId;
  final Future<void> Function(String, String) onMark;
  final VoidCallback onDone;

  @override
  Widget build(BuildContext context) {
    final j = row['journey'] as Map<String, dynamic>?;
    final plan = row['plan'] as Map<String, dynamic>?;
    final segs = ((plan?['segments'] as List?) ?? const []).cast<Map<String, dynamic>>();
    final att = row['attendance'] as String?;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Avatar(row['name']),
            const SizedBox(width: 12),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(row['name'], style: T.body(size: 15.5, weight: FontWeight.w600)),
              Text(row['code'] ?? '', style: T.mono(size: 11)),
            ])),
            if (j != null) RetentionBar((j['avg_retention'] as num?)?.toDouble(), width: 60),
          ]),
          if (j != null) ...[const SizedBox(height: 10), JuzStrip(j['juz_map'] as List?, height: 10)],
          const SizedBox(height: 12),
          Row(children: [
            for (final s in const [('present', 'حاضر'), ('late', 'متأخر'), ('absent', 'غائب'), ('excused', 'بعذر')])
              Padding(
                padding: const EdgeInsetsDirectional.only(end: 6),
                child: ChoiceChip(
                  label: Text(s.$2, style: T.body(size: 12, color: att == s.$1 ? Colors.white : T.ink2, weight: FontWeight.w600)),
                  selected: att == s.$1,
                  selectedColor: s.$1 == 'absent' ? T.sWeak : s.$1 == 'present' ? T.sStrong : T.gold,
                  showCheckmark: false, side: const BorderSide(color: T.rule), backgroundColor: T.ground2,
                  onSelected: (_) => onMark(row['student_id'], s.$1),
                ),
              ),
          ]),
          if (segs.isNotEmpty) ...[
            const SizedBox(height: 12),
            for (final s in segs)
              Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: InkWell(
                  borderRadius: BorderRadius.circular(8),
                  onTap: row['journey_id'] == null ? null : () async {
                    await Navigator.of(context).push(MaterialPageRoute(builder: (_) => TasmeeScreen(
                        journeyId: row['journey_id'], studentName: row['name'], purpose: s['purpose'], from: s['from_ayah_index'], to: s['to_ayah_index'],
                        segmentId: s['id'], halaqahId: halaqahId)));
                    onDone();
                  },
                  child: Opacity(
                    opacity: s['completion'] == 'verified' ? .55 : 1,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                      decoration: BoxDecoration(border: Border.all(color: T.rule), borderRadius: BorderRadius.circular(8)),
                      child: Row(children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                          decoration: BoxDecoration(color: s['purpose'] == 'new' ? T.lapisTint : s['purpose'] == 'near' ? T.goldTint : T.ground2, borderRadius: BorderRadius.circular(6)),
                          child: Text(purposeAr[s['purpose']] ?? s['purpose'], style: T.body(size: 11.5, weight: FontWeight.w700, color: s['purpose'] == 'new' ? T.lapis : T.ink2)),
                        ),
                        const SizedBox(width: 10),
                        Expanded(child: Text('${s['from_key']['surah_name']} ${arDigits(s['from_key']['ayah'])} ← ${s['to_key']['surah_name']} ${arDigits(s['to_key']['ayah'])}', style: T.body(size: 13))),
                        Text(s['completion'] == 'verified' ? '✓' : 'سمّع', style: T.body(size: 12.5, weight: FontWeight.w700, color: s['completion'] == 'verified' ? T.sStrong : T.gold)),
                      ]),
                    ),
                  ),
                ),
              ),
          ] else if (plan?['paused_new'] == true)
            Padding(padding: const EdgeInsets.only(top: 8), child: Text('إيقاف مؤقت للحفظ الجديد', style: T.body(size: 12.5, color: T.ink3))),
        ]),
      ),
    );
  }
}
