import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:just_audio/just_audio.dart' show ProcessingState;

import '../core/audio.dart';
import '../core/theme.dart';
import 'common.dart';

/// Mini player pinned under the text while something plays: reciter, ayah, pause/stop.
class AudioBar extends StatelessWidget {
  const AudioBar({super.key, this.surahNames = const {}});
  final Map<int, String> surahNames;
  @override
  Widget build(BuildContext context) {
    final a = AyahAudio.I;
    return ListenableBuilder(
      listenable: a,
      builder: (context, _) {
        final cur = a.current;
        if (cur == null) return const SizedBox.shrink();
        return StreamBuilder(
          stream: a.state,
          builder: (context, snap) {
            final playing = snap.data?.playing ?? a.playing;
            final buffering = snap.data?.processingState == ProcessingState.buffering || snap.data?.processingState == ProcessingState.loading;
            return Container(
              margin: const EdgeInsets.fromLTRB(14, 0, 14, 10),
              padding: const EdgeInsets.fromLTRB(14, 10, 10, 10),
              decoration: BoxDecoration(color: T.night, borderRadius: BorderRadius.circular(16), boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: .25), blurRadius: 18, offset: const Offset(0, 8))]),
              child: Row(children: [
                Container(width: 38, height: 38, decoration: BoxDecoration(color: T.gold.withValues(alpha: .18), shape: BoxShape.circle),
                    child: buffering ? const Padding(padding: EdgeInsets.all(10), child: CircularProgressIndicator(strokeWidth: 2, color: T.gold)) : const Icon(Icons.graphic_eq_rounded, color: T.gold)),
                const SizedBox(width: 12),
                Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisSize: MainAxisSize.min, children: [
                  Text('${surahNames[cur.$1] ?? 'سورة ${arDigits(cur.$1)}'} · آية ${arDigits(cur.$2)}', style: T.body(size: 14, weight: FontWeight.w700, color: T.nightInk), maxLines: 1, overflow: TextOverflow.ellipsis),
                  Text(a.reciter?['name_ar'] ?? '', style: T.body(size: 12, color: T.nightMuted), maxLines: 1, overflow: TextOverflow.ellipsis),
                ])),
                IconButton(onPressed: () => playing ? a.pause() : a.resume(), icon: Icon(playing ? Icons.pause_rounded : Icons.play_arrow_rounded, color: T.nightInk)),
                IconButton(onPressed: a.stop, icon: const Icon(Icons.close_rounded, color: T.nightMuted)),
              ]),
            );
          },
        );
      },
    );
  }
}

/// Bottom sheet on an ayah: listen to it, listen from here onward, pick the reciter.
Future<void> showAyahSheet(BuildContext context, {required int surah, required int ayah, required String key, String? surahName, Future<void> Function()? onPlayFromHere, String? preview}) async {
  final a = AyahAudio.I;
  await a.load();
  HapticFeedback.selectionClick();
  if (!context.mounted) return;
  await showModalBottomSheet(
    context: context, backgroundColor: T.surface, showDragHandle: true, useSafeArea: true, isScrollControlled: true,
    shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(22))),
    builder: (ctx) => SingleChildScrollView(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
        child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('${surahName != null ? 'سورة $surahName' : 'سورة ${arDigits(surah)}'} · آية ${arDigits(ayah)}', style: T.display(size: 17)),
          Text(key, style: T.mono(size: 11.5)),
          if (preview != null) Padding(padding: const EdgeInsets.only(top: 10), child: Text(preview, style: T.quran(size: 20), textDirection: TextDirection.rtl, maxLines: 3, overflow: TextOverflow.ellipsis)),
          const SizedBox(height: 14),
          if (!a.available)
            Container(padding: const EdgeInsets.all(12), decoration: BoxDecoration(color: T.ground2, borderRadius: BorderRadius.circular(12)),
                child: Text('الاستماع غير متاح: لم تُفعَّل وحدة الصوت لهذه المؤسسة أو لا يوجد اتصال.', style: T.body(size: 13, color: T.ink2)))
          else ...[
            _Action(icon: Icons.play_arrow_rounded, title: 'استمع لهذه الآية', sub: a.reciter?['name_ar'] ?? '', onTap: () { Navigator.pop(ctx); a.play(surah, ayah); }),
            if (onPlayFromHere != null) _Action(icon: Icons.playlist_play_rounded, title: 'استمع من هنا حتى نهاية المقطع', sub: 'الآيات بالترتيب', onTap: () { Navigator.pop(ctx); onPlayFromHere(); }),
            _Action(icon: Icons.record_voice_over_rounded, title: 'اختر القارئ', sub: a.reciter?['name_ar'] ?? '', onTap: () async { Navigator.pop(ctx); await showReciterPicker(context); }),
            const SizedBox(height: 6),
            Text('الصوت يُبثّ من مصدر خارجي للتلاوات آية بآية؛ لا يُحفظ على الجهاز ولا يوزّعه تَلَقِّي.', style: T.body(size: 11.5, color: T.ink3)),
          ],
        ]),
      ),
    ),
  );
}

Future<void> showReciterPicker(BuildContext context) async {
  final a = AyahAudio.I;
  await a.load();
  if (!context.mounted) return;
  await showModalBottomSheet(
    context: context, backgroundColor: T.surface, showDragHandle: true, useSafeArea: true, isScrollControlled: true,
    shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(22))),
    builder: (ctx) => SingleChildScrollView(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
        child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('القارئ', style: T.display(size: 17)),
          const SizedBox(height: 10),
          for (final r in a.reciters)
            ListTile(
              contentPadding: EdgeInsets.zero,
              leading: Container(width: 40, height: 40, decoration: BoxDecoration(color: r['key'] == a.reciterKey ? T.lapis : T.lapisTint, shape: BoxShape.circle),
                  child: Icon(Icons.record_voice_over_rounded, color: r['key'] == a.reciterKey ? Colors.white : T.lapis, size: 20)),
              title: Text(r['name_ar'] ?? '', style: T.body(size: 15, weight: FontWeight.w600)),
              subtitle: Text(r['name_en'] ?? '', style: T.body(size: 12, color: T.ink3)),
              trailing: r['key'] == a.reciterKey ? const Icon(Icons.check_rounded, color: T.sStrong) : null,
              onTap: () async { await a.setReciter(r['key']); if (ctx.mounted) Navigator.pop(ctx); },
            ),
        ]),
      ),
    ),
  );
}

class _Action extends StatelessWidget {
  const _Action({required this.icon, required this.title, required this.sub, required this.onTap});
  final IconData icon;
  final String title;
  final String sub;
  final VoidCallback onTap;
  @override
  Widget build(BuildContext context) => ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 4),
        leading: Container(width: 42, height: 42, decoration: BoxDecoration(color: T.goldTint, borderRadius: BorderRadius.circular(12)), child: Icon(icon, color: T.gold)),
        title: Text(title, style: T.body(size: 15, weight: FontWeight.w700)),
        subtitle: Text(sub, style: T.body(size: 12.5, color: T.ink3)),
        onTap: onTap,
      );
}

/// Legend line shared by screens that show the audio bar.
class AudioHint extends StatelessWidget {
  const AudioHint({super.key});
  @override
  Widget build(BuildContext context) => Row(children: [
        const Icon(Icons.touch_app_rounded, size: 16, color: T.ink3),
        const SizedBox(width: 6),
        Expanded(child: Text('اضغط أي كلمة لسماع آيتها بصوت القارئ.', style: T.body(size: 12, color: T.ink3))),
        Chip2(AyahAudio.I.reciter?['name_ar'] ?? 'القارئ', color: T.lapis),
      ]);
}
