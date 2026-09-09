import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/api.dart';
import '../../core/prefs.dart';
import '../../core/progress.dart';
import '../../core/quran.dart';
import '../../core/theme.dart';
import '../../widgets/common.dart';
import '../../widgets/recite_check.dart';
import '../../core/audio.dart';
import '../../widgets/ayah_audio.dart';

/// Self-practice on a plan segment: read → hide → recall → reveal, plus the AI recitation check.
/// Every hint is the exact verified text from the Quran Core; nothing generative exists in this path.
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
  @override
  void initState() { super.initState(); Prefs.I.fontSize().then((v) { if (mounted) setState(() => _font = v); }); }
  @override
  void dispose() { _rc.dispose(); super.dispose(); }
  final Set<int> _revealed = {};
  bool _hideAll = false;
  int _hints = 0;
  Map<String, dynamic>? _asr;
  final _rc = ReciteController();
  double _font = 24;
  void _bumpFont() { setState(() => _font = _font >= 30 ? 20 : _font + 3); Prefs.I.setFontSize(_font); }

  Set<int> get _flaggedAyat => {for (final a in ((_asr?['ayat'] as List?) ?? const []).cast<Map<String, dynamic>>()) if (a['status'] == 'issues') a['ayah_index'] as int};
  Set<String> get _flaggedWords => {
        for (final a in ((_asr?['ayat'] as List?) ?? const []).cast<Map<String, dynamic>>())
          for (final w in (a['words'] as List).cast<Map<String, dynamic>>())
            if (w['status'] != 'ok') '${a['ayah_index']}:${w['position']}',
      };

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      bottomNavigationBar: const SafeArea(child: AudioBar()),
      floatingActionButton: RecordingPill(_rc),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerFloat,
      body: Fetch<Map<String, dynamic>>(
        cacheKey: 'range:${widget.from}-${widget.to}',
        future: () async => (await Api.I.get('/quran/hafs_asim/range?from=${widget.from}&to=${widget.to}')) as Map<String, dynamic>,
        builder: (context, d, _) {
          final ayat = (d['ayat'] as List).cast<Map<String, dynamic>>();
          return Column(children: [
            NightHeader(
              compact: true,
              eyebrow: 'تدريب ذاتي · ${widget.title}', title: '${ayat.first['key']} ← ${ayat.last['key']}',
              subtitle: 'اقرأ، ثم أخفِ النص واسترجع، ثم اكشف للتحقق — أو سمّع بصوتك ليقارن النظام تلاوتك بالنص الموثّق.',
              trailing: Row(mainAxisSize: MainAxisSize.min, children: [
                IconButton(onPressed: _bumpFont, icon: const Icon(Icons.format_size_rounded, color: T.nightMuted)),
                IconButton(onPressed: () => Navigator.pop(context), icon: const Icon(Icons.close_rounded, color: T.nightInk)),
              ]),
              child: Row(children: [
                Expanded(child: OutlinedButton.icon(
                  style: OutlinedButton.styleFrom(foregroundColor: T.nightInk, side: BorderSide(color: Colors.white.withValues(alpha: .25)), minimumSize: const Size(0, 42), backgroundColor: _hideAll ? Colors.white.withValues(alpha: .08) : null),
                  onPressed: () { HapticFeedback.selectionClick(); setState(() { _hideAll = !_hideAll; _revealed.clear(); }); },
                  icon: Icon(_hideAll ? Icons.visibility_rounded : Icons.visibility_off_rounded, size: 18),
                  label: Text(_hideAll ? 'أظهر الكل' : 'أخفِ واسترجع'),
                )),
                const SizedBox(width: 10),
                Text('تلميحات ${arDigits(_hints)}', style: T.body(size: 13, color: T.nightMuted)),
              ]),
            ),
            Expanded(
              child: ListView(padding: const EdgeInsets.fromLTRB(16, 14, 16, 40), children: [
                ReciteCheck(from: widget.from, to: widget.to, journeyId: widget.journeyId, controller: _rc, onResult: (r) {
                  setState(() => _asr = r);
                  if (r != null) {
                    final acc = (r['accuracy'] as num).toDouble();
                    Progress.I.mark(Progress.keyFor(widget.from, widget.to), accuracy: acc, hints: _hints);
                    if (acc >= .9) { HapticFeedback.heavyImpact(); toast(context, 'ما شاء الله — ${arDigits((acc * 100).round())}٪ مطابقة. أخبر معلمك أنك جاهز للتسميع.'); }
                  }
                }),
                if (_asr != null) ...[const SizedBox(height: 10), AsrSummary(_asr!)],
                const SizedBox(height: 10),
                Row(children: [
                  Expanded(child: OutlinedButton.icon(
                    onPressed: () async { try { await AyahAudio.I.load(); await AyahAudio.I.playAll([for (final a in ayat) (a['surah'] as int, a['ayah'] as int)]); } catch (e) { if (context.mounted) toast(context, 'تعذّر تشغيل الصوت: ${friendlyError(e)}', error: true); } },
                    icon: const Icon(Icons.play_circle_outline_rounded, size: 18), label: const Text('استمع للمقطع بصوت القارئ'),
                  )),
                  const SizedBox(width: 8),
                  IconButton(tooltip: 'القارئ', onPressed: () => showReciterPicker(context), icon: const Icon(Icons.record_voice_over_rounded, color: T.lapis)),
                ]),
                const SizedBox(height: 10),
                Row(children: [
                  Expanded(child: OutlinedButton.icon(
                    onPressed: () async { await Progress.I.mark(Progress.keyFor(widget.from, widget.to), hints: _hints); if (context.mounted) { HapticFeedback.mediumImpact(); toast(context, 'سُجِّل تدريبك اليوم على هذا المقطع (محليًا)'); Navigator.pop(context, true); } },
                    icon: const Icon(Icons.task_alt_rounded, size: 18), label: const Text('أنهيت التدريب'),
                  )),
                ]),
                const SizedBox(height: 14),
                Container(
                  padding: const EdgeInsets.all(18),
                  decoration: BoxDecoration(color: T.paper, borderRadius: BorderRadius.circular(8), border: Border.all(color: T.gold.withValues(alpha: .55)),
                      boxShadow: [BoxShadow(color: T.ink.withValues(alpha: .08), blurRadius: 24, offset: const Offset(0, 10))]),
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
    final flagged = _flaggedAyat.contains(idx);
    final fw = _flaggedWords;
    return InkWell(
      onLongPress: () => showAyahSheet(context, surah: a['surah'], ayah: a['ayah'], key: a['key'], preview: a['text_uthmani']),
      onTap: hidden ? () { HapticFeedback.selectionClick(); setState(() { _revealed.add(idx); _hints++; }); } : () => showAyahSheet(context, surah: a['surah'], ayah: a['ayah'], key: a['key'], preview: a['text_uthmani']),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 250),
        padding: const EdgeInsets.symmetric(vertical: 4, horizontal: 4),
        decoration: BoxDecoration(color: flagged ? T.sNeeds.withValues(alpha: .14) : null, borderRadius: BorderRadius.circular(6)),
        child: Directionality(
          textDirection: TextDirection.rtl,
          child: hidden
              ? Row(children: [
                  Expanded(child: Text('${words.first} ${'ـــ ' * (words.length - 1).clamp(1, 12)}', style: T.quran(size: _font - 2, color: T.ink3), maxLines: 1, overflow: TextOverflow.ellipsis)),
                  Text(' ﴿${arDigits(a['ayah'])}﴾', style: T.quran(size: _font - 4, color: T.gold)),
                  const SizedBox(width: 6),
                  const Icon(Icons.visibility_outlined, size: 18, color: T.gold),
                ])
              : Wrap(textDirection: TextDirection.rtl, crossAxisAlignment: WrapCrossAlignment.center, children: [
                  if (split.basmalah != null) SizedBox(width: double.infinity, child: Text(split.basmalah!, style: T.quran(size: _font - 2), textAlign: TextAlign.center)),
                  for (var i = 0; i < words.length; i++)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 2),
                      decoration: fw.contains('$idx:${i + 1}') ? const BoxDecoration(border: Border(bottom: BorderSide(color: T.gold, width: 3))) : null,
                      child: Text(words[i], style: T.quran(size: _font)),
                    ),
                  Text(' ﴿${arDigits(a['ayah'])}﴾ ', style: T.quran(size: _font - 4, color: T.gold)),
                ]),
        ),
      ),
    );
  }
}
