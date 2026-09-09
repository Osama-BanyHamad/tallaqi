import 'package:flutter/material.dart';

import '../core/quran.dart';
import '../core/theme.dart';

/// A Mushaf page rendered verbatim from the Quran Core API. Word taps are overlays; the text is never modified.
/// [marks] are the teacher's confirmed mistakes; [flags] are AI candidates (gold underline) awaiting the teacher.
class MushafPage extends StatelessWidget {
  const MushafPage({super.key, required this.page, this.surahNames = const {}, this.inRange, this.stateOf, this.marks = const {}, this.flags = const {}, this.onWordTap, this.fontSize = 24, this.activeAyah});
  /// ayah_index currently playing (audio); drawn with a lapis wash.
  final Map<String, dynamic> page;
  final Map<int, String> surahNames;
  final bool Function(int ayahIndex)? inRange;
  final String? Function(int ayahIndex)? stateOf;
  final Map<String, String> marks; // "ayahIndex:word" -> severity
  final Set<String> flags;         // "ayahIndex:word"
  final void Function(int ayahIndex, int wordPosition)? onWordTap;
  final double fontSize;
  final int? activeAyah;

  @override
  Widget build(BuildContext context) {
    final ayat = (page['ayat'] as List).cast<Map<String, dynamic>>();
    return Container(
      padding: const EdgeInsets.fromLTRB(18, 22, 18, 18),
      decoration: BoxDecoration(color: T.paper, borderRadius: BorderRadius.circular(8), border: Border.all(color: T.rule),
          boxShadow: [BoxShadow(color: T.ink.withValues(alpha: .12), blurRadius: 30, offset: const Offset(0, 14))]),
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(border: Border.all(color: T.gold.withValues(alpha: .55)), borderRadius: BorderRadius.circular(4)),
        child: Directionality(
          textDirection: TextDirection.rtl,
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            for (final a in ayat) ..._ayah(a),
            const SizedBox(height: 10),
            Center(child: Text(arDigits(page['page']), style: T.mono(size: 12, color: T.gold))),
            Center(child: Text(page['attribution'] ?? '', style: T.body(size: 10.5, color: T.ink3))),
          ]),
        ),
      ),
    );
  }

  List<Widget> _ayah(Map<String, dynamic> a) {
    final idx = a['ayah_index'] as int;
    final split = splitBasmalah(a['text_uthmani'], a['surah'], a['ayah']);
    final dim = inRange != null && !inRange!(idx);
    final st = stateOf?.call(idx);
    final words = split.body.split(' ');
    final out = <Widget>[];
    if (a['ayah'] == 1) {
      out.add(Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: Row(children: [
          Expanded(child: Container(height: 1, decoration: BoxDecoration(gradient: LinearGradient(colors: [Colors.transparent, T.gold, Colors.transparent])))),
          Padding(padding: const EdgeInsets.symmetric(horizontal: 12), child: Text('سورة ${surahNames[a['surah']] ?? a['surah']}', style: T.display(size: 14, color: T.lapis))),
          Expanded(child: Container(height: 1, decoration: BoxDecoration(gradient: LinearGradient(colors: [Colors.transparent, T.gold, Colors.transparent])))),
        ]),
      ));
    }
    if (split.basmalah != null) out.add(Center(child: Text(split.basmalah!, style: T.quran(size: fontSize - 2))));
    out.add(AnimatedOpacity(
      duration: const Duration(milliseconds: 250),
      opacity: dim ? .3 : 1,
      child: Container(
        decoration: BoxDecoration(
          color: activeAyah == idx ? T.lapis.withValues(alpha: .10) : st == 'weak' ? T.sWeak.withValues(alpha: .09) : st == 'critical' ? T.sCritical.withValues(alpha: .11) : null,
          borderRadius: BorderRadius.circular(6),
        ),
        child: Wrap(
          textDirection: TextDirection.rtl, crossAxisAlignment: WrapCrossAlignment.center, runSpacing: 0,
          children: [
            for (var i = 0; i < words.length; i++)
              Builder(builder: (_) {
                final k = '$idx:${i + 1}';
                final sev = marks[k];
                final flagged = sev == null && flags.contains(k);
                return InkWell(
                  onTap: dim || onWordTap == null ? null : () => onWordTap!(idx, i + 1),
                  borderRadius: BorderRadius.circular(4),
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 200),
                    padding: const EdgeInsets.symmetric(horizontal: 3),
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(4),
                      color: switch (sev) { 'major' => T.sWeak.withValues(alpha: .26), 'minor' => T.sNeeds.withValues(alpha: .26), _ => flagged ? T.gold.withValues(alpha: .22) : null },
                      border: sev != null
                          ? Border(bottom: BorderSide(color: sev == 'major' ? T.sWeak : T.sNeeds, width: 3))
                          : flagged ? const Border(bottom: BorderSide(color: T.gold, width: 3)) : null,
                    ),
                    child: Text(words[i], style: T.quran(size: fontSize)),
                  ),
                );
              }),
            Text(' ﴿${arDigits(a['ayah'])}﴾ ', style: T.quran(size: fontSize - 4, color: T.gold)),
          ],
        ),
      ),
    ));
    return out;
  }
}
