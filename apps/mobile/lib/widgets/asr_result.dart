import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../core/audio.dart';
import '../core/theme.dart';
import 'common.dart';

/// The AI recitation report, written for the reciter, not the engineer:
/// a verdict in words, what needs attention (each ayah with the exact words highlighted), and tappable
/// recommendations (listen to the ayah, re-read it). The transcript is never shown as Quran; "heard" text is muted.
class AsrReport extends StatelessWidget {
  const AsrReport(this.r, {super.key, this.onReread, this.onListenAll, this.onAdopt, this.adopted = false, this.onRetry});
  final Map<String, dynamic> r;
  /// Scroll the practice text to this ayah and reveal it.
  final void Function(int ayahIndex)? onReread;
  final VoidCallback? onListenAll;
  final VoidCallback? onAdopt;
  final bool adopted;
  final VoidCallback? onRetry;

  static (int, int) _parse(String key) {
    final p = key.split(':');
    return (int.parse(p[0]), int.parse(p[1]));
  }

  @override
  Widget build(BuildContext context) {
    final acc = ((r['accuracy'] as num?) ?? 0).toDouble();
    final ayat = ((r['ayat'] as List?) ?? const []).cast<Map<String, dynamic>>();
    final issues = ayat.where((a) => a['status'] == 'issues').toList();
    final extra = ((r['extra'] as List?) ?? const []).cast<Map<String, dynamic>>();
    final nothing = r['nothing_heard'] == true;
    final missing = issues.fold<int>(0, (n, a) => n + ((a['missing'] as int?) ?? 0));
    final substituted = issues.fold<int>(0, (n, a) => n + ((a['substituted'] as int?) ?? 0));
    final total = missing + substituted;

    final (String verdict, Color tone, IconData icon) = nothing
        ? ('لم نسمع تلاوة واضحة', T.ink3, Icons.hearing_disabled_rounded)
        : total == 0
            ? ('ما شاء الله — تلاوة مطابقة', T.sStrong, Icons.verified_rounded)
            : acc >= .9
                ? ('جيد جدًا — مواضع قليلة', T.sStrong, Icons.thumb_up_alt_rounded)
                : acc >= .75
                    ? ('جيد — يحتاج تثبيتًا', T.sNeeds, Icons.flag_rounded)
                    : ('يحتاج مراجعة قبل التسميع', T.sWeak, Icons.replay_rounded);

    final summary = nothing
        ? 'قرّب الهاتف واقرأ بصوت واضح، ثم أعد التسجيل.'
        : total == 0
            ? 'كل كلمات المقطع (${arDigits(r['expected_words'] ?? 0)}) سُمعت في موضعها.${extra.isNotEmpty ? ' لكن سُمعت ${arDigits(extra.length)} كلمة زائدة.' : ''}'
            : '${arDigits(total)} ${total == 1 ? 'كلمة تحتاج' : 'كلمات تحتاج'} انتباهك في ${arDigits(issues.length)} ${issues.length == 1 ? 'آية' : 'آيات'}: '
                '${[if (missing > 0) '${arDigits(missing)} منسية', if (substituted > 0) '${arDigits(substituted)} مبدّلة', if (extra.isNotEmpty) '${arDigits(extra.length)} زائدة'].join(' · ')}.';

    return FadeIn(
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(color: T.surface, borderRadius: BorderRadius.circular(16), border: Border.all(color: tone.withValues(alpha: .45)),
            boxShadow: [BoxShadow(color: T.ink.withValues(alpha: .06), blurRadius: 18, offset: const Offset(0, 8))]),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          // ---- verdict
          Row(children: [
            RetentionRing(nothing ? null : acc, size: 62, stroke: 5, label: nothing ? '—' : null),
            const SizedBox(width: 12),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [Icon(icon, size: 18, color: tone), const SizedBox(width: 6), Expanded(child: Text(verdict, style: T.display(size: 16, color: tone)))]),
              const SizedBox(height: 4),
              Text(summary, style: T.body(size: 13, color: T.ink2)),
            ])),
          ]),

          // ---- what needs attention
          if (issues.isNotEmpty) ...[
            const SizedBox(height: 14),
            Text('ما يحتاج انتباهك', style: T.display(size: 14)),
            const SizedBox(height: 6),
            for (final a in issues.take(8)) _AyahCard(a, onReread: onReread),
            if (issues.length > 8) Text('+${arDigits(issues.length - 8)} آيات أخرى', style: T.body(size: 12, color: T.ink3)),
          ],
          if (extra.isNotEmpty) ...[
            const SizedBox(height: 10),
            Wrap(spacing: 6, runSpacing: 6, crossAxisAlignment: WrapCrossAlignment.center, children: [
              Text('كلمات زائدة سُمعت:', style: T.body(size: 12.5, color: T.ink2)),
              for (final e in extra.take(6)) Chip2('${e['heard']}', color: T.sNeeds),
            ]),
          ],

          // ---- recommendations
          const SizedBox(height: 14),
          Text('التوصيات', style: T.display(size: 14)),
          const SizedBox(height: 6),
          ..._recommendations(context, acc: acc, nothing: nothing, issues: issues, extra: extra),

          // ---- teacher: adopt as mistakes
          if (onAdopt != null && total > 0) ...[
            const SizedBox(height: 10),
            SizedBox(width: double.infinity, child: FilledButton.tonal(
              style: FilledButton.styleFrom(backgroundColor: adopted ? T.ground2 : T.lapis, foregroundColor: adopted ? T.ink3 : Colors.white, minimumSize: const Size.fromHeight(42)),
              onPressed: adopted ? null : onAdopt,
              child: Text(adopted ? 'أُضيفت إلى الأخطاء ✓' : 'اعتمد هذه المواضع كأخطاء (يمكن حذف أيٍّ منها)'),
            )),
          ],
          const SizedBox(height: 10),
          Text('كشف آلي يساعد ولا يقرّر: يقارن صوتك بالنص الموثّق ويقترح؛ الإنسان هو من يعتمد.', style: T.body(size: 11, color: T.ink3)),
        ]),
      ),
    );
  }

  List<Widget> _recommendations(BuildContext context, {required double acc, required bool nothing, required List<Map<String, dynamic>> issues, required List<Map<String, dynamic>> extra}) {
    final out = <Widget>[];
    void add(IconData i, String text, {VoidCallback? onTap, Color? color}) => out.add(_Reco(icon: i, text: text, onTap: onTap, color: color));
    if (nothing) {
      add(Icons.mic_rounded, 'أعد التسجيل: اقترب من الميكروفون واقرأ بصوت واضح دون موسيقى أو ضجيج.', onTap: onRetry);
      return out;
    }
    if (issues.isEmpty) {
      add(Icons.record_voice_over_rounded, 'سمّع المقطع لمعلمك (أو لمن يسمّع لك) ليُعتمد ويرتفع ثباته.', color: T.sStrong);
      if (extra.isNotEmpty) add(Icons.info_outline_rounded, 'انتبه للكلمات الزائدة: اقرأ ببطء وتوقّف عند رؤوس الآي.');
      return out;
    }
    final audio = AyahAudio.I.available;
    for (final a in issues.take(3)) {
      final (s, n) = _parse(a['key']);
      final subs = ((a['words'] as List).cast<Map<String, dynamic>>()).where((w) => w['status'] == 'substituted').toList();
      final miss = ((a['words'] as List).cast<Map<String, dynamic>>()).where((w) => w['status'] == 'missing').toList();
      if (audio) {
        add(Icons.play_circle_rounded, 'استمع للآية ${arDigits(a['key'])} بصوت القارئ ثم أعد قراءتها ثلاث مرات.', onTap: () => AyahAudio.I.play(s, n));
      } else if (onReread != null) {
        add(Icons.replay_rounded, 'أعد قراءة الآية ${arDigits(a['key'])} ثلاث مرات من المصحف.', onTap: () => onReread!(a['ayah_index'] as int));
      }
      for (final w in subs.take(1)) {
        if (w['heard'] != null) add(Icons.compare_arrows_rounded, 'انتبه للفرق: الصحيح «${w['expected']}» وسُمع «${w['heard']}».');
      }
      if (miss.length >= 2) add(Icons.visibility_off_rounded, 'الآية ${arDigits(a['key'])} فيها ${arDigits(miss.length)} كلمات منسية: اقرأها ثم أخفِ النص واسترجعها.', onTap: onReread == null ? null : () => onReread!(a['ayah_index'] as int));
    }
    if (issues.length >= 3 && onListenAll != null) add(Icons.playlist_play_rounded, 'المواضع متفرّقة: استمع للمقطع كاملًا ثم سمّعه مرة أخرى.', onTap: onListenAll);
    if (acc < .75) {
      add(Icons.schedule_rounded, 'ثبّت المقطع اليوم وأجّل التسميع للمعلم إلى الغد.', color: T.sWeak);
    } else {
      add(Icons.mic_rounded, 'بعد الإصلاح، سجّل مرة أخرى للتأكد ثم سمّع لمعلمك.', onTap: onRetry);
    }
    return out;
  }
}

class _AyahCard extends StatelessWidget {
  const _AyahCard(this.a, {this.onReread});
  final Map<String, dynamic> a;
  final void Function(int ayahIndex)? onReread;
  @override
  Widget build(BuildContext context) {
    final words = (a['words'] as List).cast<Map<String, dynamic>>();
    final (s, n) = AsrReport._parse(a['key']);
    final subs = words.where((w) => w['status'] == 'substituted' && w['heard'] != null).toList();
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.fromLTRB(12, 10, 12, 8),
      decoration: BoxDecoration(color: T.paper, borderRadius: BorderRadius.circular(12), border: Border.all(color: T.rule)),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Text('الآية ${arDigits(a['key'])}', style: T.body(size: 12.5, weight: FontWeight.w700, color: T.lapis)),
          const SizedBox(width: 8),
          if ((a['missing'] ?? 0) > 0) Chip2('${arDigits(a['missing'])} منسية', color: T.sWeak, filled: true),
          if ((a['missing'] ?? 0) > 0) const SizedBox(width: 4),
          if ((a['substituted'] ?? 0) > 0) Chip2('${arDigits(a['substituted'])} مبدّلة', color: T.sNeeds, filled: true),
        ]),
        const SizedBox(height: 6),
        Directionality(
          textDirection: TextDirection.rtl,
          child: Wrap(textDirection: TextDirection.rtl, crossAxisAlignment: WrapCrossAlignment.center, runSpacing: 2, children: [
            for (final w in words)
              _Word(w, onTap: w['status'] == 'ok' ? null : () {
                HapticFeedback.selectionClick();
                final msg = w['status'] == 'missing' ? 'لم تُسمع كلمة «${w['expected']}»' : 'الصحيح «${w['expected']}»${w['heard'] != null ? ' — سُمع «${w['heard']}»' : ''}';
                toast(context, msg);
              }),
            Text(' ﴿${arDigits(n)}﴾', style: T.quran(size: 18, color: T.gold)),
          ]),
        ),
        if (subs.isNotEmpty) Padding(padding: const EdgeInsets.only(top: 4), child: Text([for (final w in subs) '«${w['expected']}» سُمعت «${w['heard']}»'].join(' · '), style: T.body(size: 11.5, color: T.ink3))),
        const SizedBox(height: 4),
        Row(children: [
          if (AyahAudio.I.available)
            TextButton.icon(onPressed: () => AyahAudio.I.play(s, n), style: TextButton.styleFrom(padding: const EdgeInsets.symmetric(horizontal: 8), minimumSize: const Size(0, 34)),
                icon: const Icon(Icons.play_arrow_rounded, size: 18), label: const Text('استمع')),
          if (onReread != null)
            TextButton.icon(onPressed: () => onReread!(a['ayah_index'] as int), style: TextButton.styleFrom(padding: const EdgeInsets.symmetric(horizontal: 8), minimumSize: const Size(0, 34)),
                icon: const Icon(Icons.menu_book_rounded, size: 18), label: const Text('أعد قراءتها')),
        ]),
      ]),
    );
  }
}

class _Word extends StatelessWidget {
  const _Word(this.w, {this.onTap});
  final Map<String, dynamic> w;
  final VoidCallback? onTap;
  @override
  Widget build(BuildContext context) {
    final st = w['status'];
    final color = st == 'missing' ? T.sWeak : st == 'substituted' ? T.sNeeds : null;
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(6),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 3),
        decoration: color == null ? null : BoxDecoration(color: color.withValues(alpha: .16), borderRadius: BorderRadius.circular(6), border: Border(bottom: BorderSide(color: color, width: 3))),
        child: Text('${w['expected']}', style: T.quran(size: 21, color: color == null ? T.ink : (st == 'missing' ? T.sWeak : T.ink))),
      ),
    );
  }
}

class _Reco extends StatelessWidget {
  const _Reco({required this.icon, required this.text, this.onTap, this.color});
  final IconData icon;
  final String text;
  final VoidCallback? onTap;
  final Color? color;
  @override
  Widget build(BuildContext context) {
    final c = color ?? T.lapis;
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(10),
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 2),
          child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Container(width: 30, height: 30, decoration: BoxDecoration(color: c.withValues(alpha: .12), borderRadius: BorderRadius.circular(9)), child: Icon(icon, size: 17, color: c)),
            const SizedBox(width: 10),
            Expanded(child: Text(text, style: T.body(size: 13.5))),
            if (onTap != null) const Icon(Icons.chevron_left_rounded, size: 18, color: T.ink3),
          ]),
        ),
      ),
    );
  }
}
