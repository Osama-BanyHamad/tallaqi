import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/api.dart';
import '../../core/quran.dart';
import '../../core/theme.dart';
import '../../widgets/common.dart';
import '../tasmee/tasmee_screen.dart';
import 'student_detail_screen.dart';

/// The teacher's working screen: roster + attendance + today's plan per student, one tap into Tasmee'.
class TodayScreen extends StatefulWidget {
  const TodayScreen({super.key, required this.halaqahId});
  final String halaqahId;
  @override
  State<TodayScreen> createState() => _TodayScreenState();
}

class _TodayScreenState extends State<TodayScreen> {
  int _v = 0;
  String _filter = 'all'; // all | pending | absent
  Future<Map<String, dynamic>> _load() async => (await Api.I.get('/halaqat/${widget.halaqahId}/today')) as Map<String, dynamic>;

  Future<void> _mark(String studentId, String status) async {
    HapticFeedback.selectionClick();
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
          final pending = roster.where((r) => ((r['plan']?['segments'] as List?) ?? const []).any((s) => s['completion'] != 'verified')).length;
          final rows = roster.where((r) => switch (_filter) {
                'pending' => ((r['plan']?['segments'] as List?) ?? const []).any((s) => s['completion'] != 'verified'),
                'absent' => r['attendance'] == null || r['attendance'] == 'absent',
                _ => true,
              }).toList();
          return Column(children: [
            NightHeader(
              leadingBack: true,
              eyebrow: 'حلقة اليوم · ${arDigits(d['date'] ?? '')}',
              title: h['name'],
              subtitle: h['schedule_summary'],
              child: Row(children: [
                Expanded(child: _Stat(arDigits(present), '/ ${arDigits(roster.length)} حاضر', T.gold2)),
                Expanded(child: _Stat(arDigits(pending), 'بانتظار التسميع', T.nightInk)),
                Expanded(child: _Stat(arDigits(roster.where((r) => r['last_session']?['outcome'] == 'pass').length), 'اجتاز آخر مرة', T.sStrong)),
              ]),
            ),
            Container(
              color: T.surface,
              padding: const EdgeInsets.fromLTRB(16, 10, 16, 10),
              child: Row(children: [
                for (final f in const [('all', 'الكل'), ('pending', 'لم يسمّع'), ('absent', 'غائب / لم يُسجَّل')])
                  Padding(
                    padding: const EdgeInsetsDirectional.only(end: 8),
                    child: ChoiceChip(label: Text(f.$2), selected: _filter == f.$1, onSelected: (_) => setState(() => _filter = f.$1), showCheckmark: false,
                        selectedColor: T.lapis, labelStyle: T.body(size: 12.5, weight: FontWeight.w600, color: _filter == f.$1 ? Colors.white : T.ink2), side: const BorderSide(color: T.rule), backgroundColor: T.ground2),
                  ),
              ]),
            ),
            Expanded(
              child: RefreshIndicator(
                onRefresh: () async => setState(() => _v++),
                child: rows.isEmpty
                    ? const EmptyState(title: 'لا طلاب في هذا الفلتر', icon: Icons.filter_alt_off_outlined)
                    : ListView.separated(
                        padding: const EdgeInsets.all(16),
                        itemCount: rows.length,
                        separatorBuilder: (_, __) => const SizedBox(height: 10),
                        itemBuilder: (context, i) => FadeIn(index: i, child: _StudentCard(row: rows[i], halaqahId: widget.halaqahId, onMark: _mark, onDone: () => setState(() => _v++))),
                      ),
              ),
            ),
          ]);
        },
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  const _Stat(this.v, this.l, this.c);
  final String v;
  final String l;
  final Color c;
  @override
  Widget build(BuildContext context) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(v, style: T.display(size: 26, color: c)),
        Text(l, style: T.body(size: 11.5, color: T.nightMuted)),
      ]);
}

class _StudentCard extends StatefulWidget {
  const _StudentCard({required this.row, required this.halaqahId, required this.onMark, required this.onDone});
  final Map<String, dynamic> row;
  final String halaqahId;
  final Future<void> Function(String, String) onMark;
  final VoidCallback onDone;
  @override
  State<_StudentCard> createState() => _StudentCardState();
}

class _StudentCardState extends State<_StudentCard> {
  bool _open = true;
  @override
  Widget build(BuildContext context) {
    final row = widget.row;
    final j = row['journey'] as Map<String, dynamic>?;
    final plan = row['plan'] as Map<String, dynamic>?;
    final segs = ((plan?['segments'] as List?) ?? const []).cast<Map<String, dynamic>>();
    final att = row['attendance'] as String?;
    final last = row['last_session'] as Map<String, dynamic>?;
    return Card(
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: row['journey_id'] == null ? null : () async {
            await Navigator.of(context).push(MaterialPageRoute(builder: (_) => StudentDetailScreen(journeyId: row['journey_id'], halaqahId: widget.halaqahId, canRecite: true)));
            widget.onDone();
          },
          child: Padding(
            padding: const EdgeInsets.fromLTRB(14, 14, 14, 0),
            child: Row(children: [
              Avatar(row['name']),
              const SizedBox(width: 12),
              Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(row['name'], style: T.body(size: 15.5, weight: FontWeight.w600)),
                Row(children: [
                  Text(row['code'] ?? '', style: T.mono(size: 11)),
                  if (last != null) ...[Text(' · ', style: T.body(size: 11, color: T.ink3)), Text('آخر تسميع: ${outcomeAr[last['outcome']] ?? ''}', style: T.body(size: 11.5, color: last['outcome'] == 'pass' ? T.sStrong : T.sNeeds))],
                ]),
              ])),
              if (j != null) RetentionRing((j['avg_retention'] as num?)?.toDouble(), size: 46, stroke: 4),
              IconButton(onPressed: () => setState(() => _open = !_open), icon: AnimatedRotation(turns: _open ? .5 : 0, duration: const Duration(milliseconds: 200), child: const Icon(Icons.expand_more_rounded))),
            ]),
          ),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(14, 10, 14, 14),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            if (j != null) JuzStrip(j['juz_map'] as List?, height: 9),
            const SizedBox(height: 12),
            SizedBox(
              height: 34,
              child: ListView(scrollDirection: Axis.horizontal, children: [
                for (final s in const [('present', 'حاضر'), ('late', 'متأخر'), ('absent', 'غائب'), ('excused', 'بعذر')])
                  Padding(
                    padding: const EdgeInsetsDirectional.only(end: 6),
                    child: ChoiceChip(
                      label: Text(s.$2, style: T.body(size: 12, color: att == s.$1 ? Colors.white : T.ink2, weight: FontWeight.w600)),
                      selected: att == s.$1,
                      selectedColor: s.$1 == 'absent' ? T.sWeak : s.$1 == 'present' ? T.sStrong : T.gold,
                      showCheckmark: false, side: const BorderSide(color: T.rule), backgroundColor: T.ground2, visualDensity: VisualDensity.compact,
                      onSelected: (_) => widget.onMark(row['student_id'], s.$1),
                    ),
                  ),
              ]),
            ),
            AnimatedCrossFade(
              duration: const Duration(milliseconds: 220),
              crossFadeState: _open ? CrossFadeState.showFirst : CrossFadeState.showSecond,
              secondChild: const SizedBox(width: double.infinity),
              firstChild: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                if (segs.isNotEmpty) const SizedBox(height: 10),
                for (final s in segs)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 6),
                    child: InkWell(
                      borderRadius: BorderRadius.circular(10),
                      onTap: row['journey_id'] == null ? null : () async {
                        await Navigator.of(context).push(MaterialPageRoute(builder: (_) => TasmeeScreen(
                            journeyId: row['journey_id'], studentName: row['name'], purpose: s['purpose'], from: s['from_ayah_index'], to: s['to_ayah_index'],
                            segmentId: s['id'], halaqahId: widget.halaqahId)));
                        widget.onDone();
                      },
                      child: AnimatedOpacity(
                        duration: const Duration(milliseconds: 200),
                        opacity: s['completion'] == 'verified' ? .55 : 1,
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 9),
                          decoration: BoxDecoration(color: s['completion'] == 'verified' ? T.ground : T.surface, border: Border.all(color: T.rule), borderRadius: BorderRadius.circular(10)),
                          child: Row(children: [
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                              decoration: BoxDecoration(color: s['purpose'] == 'new' ? T.lapisTint : s['purpose'] == 'near' ? T.goldTint : T.ground2, borderRadius: BorderRadius.circular(6)),
                              child: Text(purposeAr[s['purpose']] ?? s['purpose'], style: T.body(size: 11.5, weight: FontWeight.w700, color: s['purpose'] == 'new' ? T.lapis : T.ink2)),
                            ),
                            const SizedBox(width: 10),
                            Expanded(child: Text('${s['from_key']['surah_name']} ${arDigits(s['from_key']['ayah'])} ← ${s['to_key']['surah_name']} ${arDigits(s['to_key']['ayah'])}', style: T.body(size: 13))),
                            s['completion'] == 'verified'
                                ? const Icon(Icons.check_circle_rounded, color: T.sStrong, size: 20)
                                : Container(padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4), decoration: BoxDecoration(color: T.gold, borderRadius: BorderRadius.circular(8)),
                                    child: Text('سمّع', style: T.body(size: 12, weight: FontWeight.w700, color: const Color(0xFF1F1806)))),
                          ]),
                        ),
                      ),
                    ),
                  ),
                if (segs.isEmpty && plan?['paused_new'] == true)
                  Padding(padding: const EdgeInsets.only(top: 8), child: Text('إيقاف مؤقت للحفظ الجديد — تراكم مراجعة', style: T.body(size: 12.5, color: T.ink3))),
              ]),
            ),
          ]),
        ),
      ]),
    );
  }
}
