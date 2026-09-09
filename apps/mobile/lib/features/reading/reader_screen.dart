import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/api.dart';
import '../../core/audio.dart';
import '../../core/prefs.dart';
import '../../core/theme.dart';
import '../../widgets/ayah_audio.dart';
import '../../widgets/common.dart';
import '../../widgets/mushaf_page.dart';

/// Mushaf reader by page: swipe between pages, tap a word to hear its ayah, finish the wird from the last page.
class ReaderScreen extends StatefulWidget {
  const ReaderScreen({super.key, required this.fromPage, required this.toPage, this.title = 'قراءة', this.onFinished});
  final int fromPage;
  final int toPage;
  final String title;
  /// Called with (fromPage, toPage) when the reader marks the range done.
  final Future<void> Function(int from, int to)? onFinished;
  @override
  State<ReaderScreen> createState() => _ReaderScreenState();
}

class _ReaderScreenState extends State<ReaderScreen> {
  late final PageController _pc = PageController(initialPage: 0);
  late int _first = widget.fromPage;
  late int _last = widget.toPage;
  int _index = 0;
  double _font = 24;
  Map<int, String> _surahs = const {};
  final _pages = <int, Map<String, dynamic>>{};

  @override
  void initState() {
    super.initState();
    Prefs.I.fontSize().then((v) { if (mounted) setState(() => _font = v); });
    AyahAudio.I.load();
    Api.I.get('/quran/hafs_asim/surahs').then((d) {
      if (!mounted) return;
      final list = ((d is Map ? d['surahs'] ?? d['results'] : d) as List).cast<Map<String, dynamic>>();
      setState(() => _surahs = {for (final s in list) s['number'] as int: s['name_ar'] as String});
    }).catchError((_) {});
  }

  @override
  void dispose() {
    _pc.dispose();
    super.dispose();
  }

  int get _page => _first + _index;
  int get _count => _last - _first + 1;

  void _bumpFont() { setState(() => _font = _font >= 30 ? 20 : _font + 3); Prefs.I.setFontSize(_font); }

  Future<Map<String, dynamic>> _load(int page) async {
    final c = _pages[page];
    if (c != null) return c;
    final d = await Api.I.get('/quran/hafs_asim/page/$page') as Map<String, dynamic>;
    _pages[page] = d;
    return d;
  }

  void _extend({bool before = false}) {
    setState(() {
      if (before && _first > 1) { _first--; _index++; _pc.jumpToPage(_index); }
      if (!before && _last < 604) _last++;
    });
  }

  Future<void> _playPage(Map<String, dynamic> d, {int? fromAyahIndex}) async {
    final ayat = (d['ayat'] as List).cast<Map<String, dynamic>>().where((a) => fromAyahIndex == null || (a['ayah_index'] as int) >= fromAyahIndex).toList();
    try {
      await AyahAudio.I.playAll([for (final a in ayat) (a['surah'] as int, a['ayah'] as int)]);
    } catch (e) {
      if (mounted) toast(context, 'تعذّر تشغيل الصوت: ${friendlyError(e)}', error: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final atEnd = _page >= widget.toPage;
    return Scaffold(
      backgroundColor: T.ground,
      body: Column(children: [
        NightHeader(
          compact: true, leadingBack: true,
          eyebrow: widget.title,
          title: 'صفحة ${arDigits(_page)}',
          subtitle: 'الصفحة ${arDigits(_index + 1)} من ${arDigits(_count)} · اسحب للتنقّل · اضغط كلمة لسماع آيتها',
          trailing: Row(mainAxisSize: MainAxisSize.min, children: [
            IconButton(tooltip: 'القارئ', onPressed: () => showReciterPicker(context), icon: const Icon(Icons.record_voice_over_rounded, color: T.nightMuted)),
            IconButton(tooltip: 'حجم الخط', onPressed: _bumpFont, icon: const Icon(Icons.format_size_rounded, color: T.nightMuted)),
          ]),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: LinearProgressIndicator(value: (_index + 1) / _count, minHeight: 6, backgroundColor: Colors.white.withValues(alpha: .12), color: T.gold),
          ),
        ),
        Expanded(
          child: PageView.builder(
            controller: _pc,
            reverse: false,
            itemCount: _count,
            onPageChanged: (i) { HapticFeedback.selectionClick(); setState(() => _index = i); },
            itemBuilder: (context, i) {
              final page = _first + i;
              return FutureBuilder<Map<String, dynamic>>(
                future: _load(page),
                builder: (context, s) {
                  if (s.hasError) return ErrorBox(s.error!, onRetry: () => setState(() => _pages.remove(page)));
                  if (!s.hasData) return const LoadingBox();
                  final d = s.data!;
                  return ListenableBuilder(
                    listenable: AyahAudio.I,
                    builder: (context, _) {
                      final cur = AyahAudio.I.current;
                      final ayat = (d['ayat'] as List).cast<Map<String, dynamic>>();
                      int? activeIdx;
                      if (cur != null) {
                        for (final a in ayat) { if (a['surah'] == cur.$1 && a['ayah'] == cur.$2) activeIdx = a['ayah_index'] as int; }
                      }
                      return ListView(padding: const EdgeInsets.fromLTRB(14, 12, 14, 120), children: [
                        Row(children: [
                          Expanded(child: OutlinedButton.icon(onPressed: () => _playPage(d), icon: const Icon(Icons.play_circle_outline_rounded, size: 18), label: const Text('استمع للصفحة'))),
                          const SizedBox(width: 8),
                          Chip2('الجزء ${arDigits(d['juz'])}', color: T.lapis),
                        ]),
                        const SizedBox(height: 10),
                        MushafPage(
                          page: d, surahNames: _surahs, fontSize: _font, activeAyah: activeIdx,
                          onWordTap: (idx, _) {
                            final a = ayat.firstWhere((x) => x['ayah_index'] == idx);
                            showAyahSheet(context, surah: a['surah'], ayah: a['ayah'], key: a['key'], surahName: _surahs[a['surah']],
                                preview: a['text_uthmani'], onPlayFromHere: () => _playPage(d, fromAyahIndex: idx));
                          },
                        ),
                        const SizedBox(height: 12),
                        if (i == 0 && _first > 1) TextButton.icon(onPressed: () => _extend(before: true), icon: const Icon(Icons.arrow_forward_rounded, size: 16), label: const Text('الصفحة السابقة')),
                        if (i == _count - 1 && _last < 604) TextButton.icon(onPressed: () => _extend(), icon: const Icon(Icons.arrow_back_rounded, size: 16), label: const Text('تابع القراءة بعد الورد')),
                      ]);
                    },
                  );
                },
              );
            },
          ),
        ),
      ]),
      bottomNavigationBar: SafeArea(
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          AudioBar(surahNames: _surahs),
          if (widget.onFinished != null)
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
              child: GoldButton(
                icon: atEnd ? Icons.task_alt_rounded : Icons.arrow_back_rounded,
                label: atEnd ? 'أنهيت وردي اليوم' : 'الصفحة التالية',
                onPressed: () async {
                  if (!atEnd) { _pc.nextPage(duration: const Duration(milliseconds: 260), curve: Curves.easeOutCubic); return; }
                  HapticFeedback.heavyImpact();
                  await AyahAudio.I.stop();
                  await widget.onFinished!(widget.fromPage, _page.clamp(widget.fromPage, 604));
                  if (context.mounted) Navigator.pop(context, true);
                },
              ),
            ),
        ]),
      ),
    );
  }
}

/// Minutes spent in the reader, for the log.
int minutesSince(DateTime? t) => t == null ? 0 : DateTime.now().difference(t).inMinutes.clamp(0, 600);
