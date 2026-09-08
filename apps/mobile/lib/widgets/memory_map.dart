import 'package:flutter/material.dart';

import '../core/api.dart';
import '../core/quran.dart';
import '../core/theme.dart';
import 'common.dart';

/// The signature visualization: 30 Juz rows × pages, each page a folio tile coloured by retention state.
class MemoryMapView extends StatefulWidget {
  const MemoryMapView({super.key, required this.journeyId});
  final String journeyId;
  @override
  State<MemoryMapView> createState() => _MemoryMapViewState();
}

class _MemoryMapViewState extends State<MemoryMapView> {
  int? _page;
  @override
  Widget build(BuildContext context) {
    return Fetch<Map<String, dynamic>>(
      future: () async => (await Api.I.get('/journeys/${widget.journeyId}/memory-map?level=pages')) as Map<String, dynamic>,
      builder: (context, d, _) {
        final units = (d['units'] as List).cast<Map<String, dynamic>>();
        final byJuz = <int, List<Map<String, dynamic>>>{};
        for (final u in units) {
          byJuz.putIfAbsent(u['juz'] as int, () => []).add(u);
        }
        return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          for (var j = 1; j <= 30; j++)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 2.5),
              child: Row(children: [
                SizedBox(width: 52, child: Text('الجزء ${arDigits(j)}', style: T.body(size: 11.5, color: T.ink2, weight: FontWeight.w600))),
                Expanded(
                  child: Row(children: [
                    for (final u in byJuz[j] ?? const <Map<String, dynamic>>[])
                      Expanded(child: Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 1.5),
                        child: GestureDetector(
                          onTap: () => setState(() => _page = _page == u['number'] ? null : u['number'] as int),
                          child: Container(
                            height: 18,
                            decoration: BoxDecoration(
                              color: T.state(u['state']).withValues(alpha: (u['memorized_ayat'] as int) == 0 ? 1 : .62 + (u['coverage'] as num) * .38),
                              borderRadius: BorderRadius.circular(3),
                              border: _page == u['number'] ? Border.all(color: T.gold, width: 2) : null,
                            ),
                            child: (u['due_ayat'] as int) > 0
                                ? Align(alignment: AlignmentDirectional.topEnd, child: Container(margin: const EdgeInsets.all(2), width: 5, height: 5, decoration: const BoxDecoration(color: T.gold2, shape: BoxShape.circle)))
                                : null,
                          ),
                        ),
                      )),
                  ]),
                ),
              ]),
            ),
          const SizedBox(height: 12),
          Wrap(spacing: 6, runSpacing: 6, children: [
            for (final s in ['mastered', 'strong', 'recent', 'needs_revision', 'weak', 'critical', 'learning', 'not_memorized']) Chip2(stateAr[s]!, color: T.state(s)),
          ]),
          if (_page != null) ...[const SizedBox(height: 18), PageDetail(journeyId: widget.journeyId, page: _page!)],
        ]);
      },
    );
  }
}

class PageDetail extends StatelessWidget {
  const PageDetail({super.key, required this.journeyId, required this.page});
  final String journeyId;
  final int page;
  @override
  Widget build(BuildContext context) {
    return Fetch<Map<String, dynamic>>(
      key: ValueKey(page),
      future: () async => (await Api.I.get('/journeys/$journeyId/memory-map?level=page&number=$page')) as Map<String, dynamic>,
      builder: (context, d, _) {
        final units = (d['units'] as List).cast<Map<String, dynamic>>();
        return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [Text('صفحة ${arDigits(page)}', style: T.display(size: 16)), const SizedBox(width: 10), Chip2(stateAr[d['state']] ?? d['state'], color: T.state(d['state']))]),
          const SizedBox(height: 8),
          for (final a in units)
            Container(
              margin: const EdgeInsets.only(bottom: 6),
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(color: T.surface, border: Border.all(color: T.rule), borderRadius: BorderRadius.circular(8)),
              child: ExpansionTile(
                tilePadding: EdgeInsets.zero, childrenPadding: const EdgeInsets.only(bottom: 8), shape: const Border(),
                title: Row(children: [
                  Chip2(stateAr[a['state']] ?? a['state'], color: T.state(a['state'])),
                  const SizedBox(width: 8),
                  Text(a['key'], style: T.mono(size: 11)),
                  const Spacer(),
                  Text('${((a['retention_score'] as num) * 100).round()}%', style: T.mono(size: 11, color: T.ink2)),
                ]),
                children: [
                  Text(a['text_uthmani'], style: T.quran(size: 21), textDirection: TextDirection.rtl),
                  for (final e in (a['explanation'] as List)) Padding(padding: const EdgeInsets.only(top: 2), child: Text('• $e', style: T.body(size: 12.5, color: T.ink2))),
                ],
              ),
            ),
        ]);
      },
    );
  }
}
