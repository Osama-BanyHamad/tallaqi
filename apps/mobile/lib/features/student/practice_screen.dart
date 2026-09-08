import 'package:flutter/material.dart';

import '../../core/api.dart';
import '../../core/quran.dart';
import '../../core/theme.dart';
import '../../widgets/common.dart';

/// Self-practice on a plan segment: read → hide → recall → reveal. Every hint is the exact verified text from the Quran Core.
/// No generative text or audio exists anywhere in this path.
class PracticeScreen extends StatefulWidget {
  const PracticeScreen({super.key, required this.journeyId, required this.from, required this.to, required this.title});
  final String journeyId;
  final int from;
  final int to;
  final String title;
  @override
  State<PracticeScreen> createState() => _PracticeScreenState();
}

class _PracticeScreenState extends State<PracticeScreen> {
  final Set<int> _revealed = {};
  bool _hideAll = false;
  int _hints = 0;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Fetch<Map<String, dynamic>>(
        future: () async => (await Api.I.get('/quran/hafs_asim/range?from=${widget.from}&to=${widget.to}')) as Map<String, dynamic>,
        builder: (context, d, _) {
          final ayat = (d['ayat'] as List).cast<Map<String, dynamic>>();
          return Column(children: [
            NightHeader(
              eyebrow: 'تدريب ذاتي · ${widget.title}', title: '${ayat.first['key']} ← ${ayat.last['key']}',
              subtitle: 'اقرأ، ثم أخفِ النص واسترجع، ثم اكشف للتحقق. التلميحات من النص الموثّق فقط.',
              trailing: IconButton(onPressed: () => Navigator.pop(context), icon: const Icon(Icons.close_rounded, color: T.nightInk)),
              child: Row(children: [
                FilledButton.tonal(
                  style: FilledButton.styleFrom(backgroundColor: T.gold, foregroundColor: const Color(0xFF1F1806), minimumSize: const Size(0, 40)),
                  onPressed: () => setState(() { _hideAll = !_hideAll; _revealed.clear(); }),
                  child: Text(_hideAll ? 'أظهر الكل' : 'أخفِ النص واسترجع'),
                ),
                const SizedBox(width: 12),
                Text('تلميحات: ${arDigits(_hints)}', style: T.body(size: 13, color: T.nightMuted)),
              ]),
            ),
            Expanded(
              child: ListView(padding: const EdgeInsets.all(16), children: [
                Container(
                  padding: const EdgeInsets.all(18),
                  decoration: BoxDecoration(color: T.paper, borderRadius: BorderRadius.circular(6), border: Border.all(color: T.gold.withValues(alpha: .55))),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                    for (final a in ayat) _ayah(a),
                    const SizedBox(height: 8),
                    Center(child: Text(d['attribution'] ?? '', style: T.body(size: 10.5, color: T.ink3))),
                  ]),
                ),
              ]),
            ),
          ]);
        },
      ),
    );
  }

  Widget _ayah(Map<String, dynamic> a) {
    final idx = a['ayah_index'] as int;
    final hidden = _hideAll && !_revealed.contains(idx);
    final split = splitBasmalah(a['text_uthmani'], a['surah'], a['ayah']);
    final words = split.body.split(' ');
    return InkWell(
      onTap: hidden ? () => setState(() { _revealed.add(idx); _hints++; }) : null,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Directionality(
          textDirection: TextDirection.rtl,
          child: hidden
              ? Row(children: [
                  Expanded(child: Text('${words.first} ${'ـــ ' * (words.length - 1).clamp(1, 12)}', style: T.quran(size: 22, color: T.ink3), maxLines: 1, overflow: TextOverflow.ellipsis)),
                  Text(' ﴿${arDigits(a['ayah'])}﴾', style: T.quran(size: 20, color: T.gold)),
                  const SizedBox(width: 6),
                  const Icon(Icons.visibility_outlined, size: 18, color: T.gold),
                ])
              : Text.rich(TextSpan(children: [
                  if (split.basmalah != null) TextSpan(text: '${split.basmalah}\n'),
                  TextSpan(text: split.body),
                  TextSpan(text: ' ﴿${arDigits(a['ayah'])}﴾', style: T.quran(size: 20, color: T.gold)),
                ]), style: T.quran(size: 24), textAlign: TextAlign.justify),
        ),
      ),
    );
  }
}
