import 'package:flutter/material.dart';

import '../core/theme.dart';

class Avatar extends StatelessWidget {
  const Avatar(this.name, {super.key, this.size = 44});
  final String name;
  final double size;
  static const tones = [T.lapis, T.sStrong, T.sRecent, Color(0xFF7A4A9A), Color(0xFFB0662A), Color(0xFF4A5F8F)];
  @override
  Widget build(BuildContext context) {
    final parts = name.replaceFirst(RegExp(r'^(أبو|أم|د\.|الشيخ|الأستاذة|الأستاذ)\s+'), '').split(RegExp(r'\s+')).where((p) => p.isNotEmpty).toList();
    final initials = parts.take(2).map((p) => p.characters.first).join();
    var h = 0;
    for (final c in name.codeUnits) {
      h = (h * 31 + c) & 0x7fffffff;
    }
    return Container(
      width: size, height: size, alignment: Alignment.center,
      decoration: BoxDecoration(color: tones[h % tones.length], shape: BoxShape.circle),
      child: Text(initials, style: T.display(size: size * .34, color: Colors.white)),
    );
  }
}

/// 30 cells, Juz 1 → 30, right-to-left; each coloured by the materialized Juz state.
class JuzStrip extends StatelessWidget {
  const JuzStrip(this.map, {super.key, this.height = 14});
  final List? map;
  final double height;
  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Row(children: [
        for (var i = 0; i < 30; i++)
          Expanded(child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 1),
            child: Builder(builder: (_) {
              final c = (map != null && map!.length > i) ? map![i] as List : null;
              final cov = (c?[0] as num?)?.toDouble() ?? 0;
              final st = cov > 0 ? (c?[2]?.toString() ?? 'not_memorized') : 'not_memorized';
              return Opacity(opacity: cov > 0 ? .55 + cov * .45 : 1,
                  child: Container(height: height, decoration: BoxDecoration(color: T.state(st), borderRadius: BorderRadius.circular(2))));
            }),
          )),
      ]),
    );
  }
}

class RetentionBar extends StatelessWidget {
  const RetentionBar(this.v, {super.key, this.width = 90});
  final double? v;
  final double width;
  @override
  Widget build(BuildContext context) {
    final p = ((v ?? 0) * 100).round();
    return Row(mainAxisSize: MainAxisSize.min, children: [
      Container(width: width, height: 7, decoration: BoxDecoration(color: T.ground2, borderRadius: BorderRadius.circular(4)),
          child: Align(alignment: AlignmentDirectional.centerStart,
              child: FractionallySizedBox(widthFactor: p / 100, child: Container(decoration: BoxDecoration(color: T.retention(v), borderRadius: BorderRadius.circular(4)))))),
      const SizedBox(width: 8),
      Text(pct(v), style: T.mono(size: 12, color: T.ink2)),
    ]);
  }
}

class Chip2 extends StatelessWidget {
  const Chip2(this.text, {super.key, this.color, this.filled = false});
  final String text;
  final Color? color;
  final bool filled;
  @override
  Widget build(BuildContext context) {
    final c = color ?? T.ink3;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
      decoration: BoxDecoration(color: filled ? c.withValues(alpha: .12) : T.surface, borderRadius: BorderRadius.circular(999),
          border: Border.all(color: filled ? c.withValues(alpha: .35) : T.rule)),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Container(width: 8, height: 8, decoration: BoxDecoration(color: c, shape: BoxShape.circle)),
        const SizedBox(width: 6),
        Text(text, style: T.body(size: 12, color: T.ink2, weight: FontWeight.w500)),
      ]),
    );
  }
}

class Kpi extends StatelessWidget {
  const Kpi({super.key, required this.label, required this.value, this.accent = false, this.color});
  final String label;
  final String value;
  final bool accent;
  final Color? color;
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 12),
      decoration: BoxDecoration(
        gradient: accent ? const LinearGradient(colors: [T.lapis2, T.lapis], begin: Alignment.topLeft, end: Alignment.bottomRight) : null,
        color: accent ? null : T.surface,
        borderRadius: BorderRadius.circular(12), border: accent ? null : Border.all(color: T.rule),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(label, style: T.body(size: 12, color: accent ? Colors.white70 : T.ink3, weight: FontWeight.w500)),
        const SizedBox(height: 4),
        Text(value, style: T.display(size: 26, color: accent ? Colors.white : (color ?? T.ink))),
      ]),
    );
  }
}

class Eyebrow extends StatelessWidget {
  const Eyebrow(this.text, {super.key, this.light = false});
  final String text;
  final bool light;
  @override
  Widget build(BuildContext context) => Row(mainAxisSize: MainAxisSize.min, children: [
        Container(width: 20, height: 1.5, color: light ? T.gold2 : T.gold),
        const SizedBox(width: 8),
        Text(text, style: T.body(size: 12, color: light ? T.gold2 : T.gold, weight: FontWeight.w600)),
      ]);
}

class NightHeader extends StatelessWidget {
  const NightHeader({super.key, required this.title, this.eyebrow, this.subtitle, this.trailing, this.child});
  final String title;
  final String? eyebrow;
  final String? subtitle;
  final Widget? trailing;
  final Widget? child;
  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: EdgeInsets.fromLTRB(20, MediaQuery.paddingOf(context).top + 16, 20, 22),
      decoration: const BoxDecoration(
        gradient: LinearGradient(colors: [T.night2, T.night], begin: Alignment.topRight, end: Alignment.bottomLeft),
        border: Border(bottom: BorderSide(color: T.gold, width: 1)),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            if (eyebrow != null) Eyebrow(eyebrow!, light: true),
            const SizedBox(height: 6),
            Text(title, style: T.display(size: 24, color: T.nightInk)),
            if (subtitle != null) Padding(padding: const EdgeInsets.only(top: 4), child: Text(subtitle!, style: T.body(size: 13, color: T.nightMuted))),
          ])),
          if (trailing != null) trailing!,
        ]),
        if (child != null) Padding(padding: const EdgeInsets.only(top: 16), child: child!),
      ]),
    );
  }
}

class LoadingBox extends StatelessWidget {
  const LoadingBox({super.key});
  @override
  Widget build(BuildContext context) => const Center(child: Padding(padding: EdgeInsets.all(40), child: CircularProgressIndicator(color: T.gold, strokeWidth: 2.5)));
}

class ErrorBox extends StatelessWidget {
  const ErrorBox(this.error, {super.key, this.onRetry});
  final Object error;
  final VoidCallback? onRetry;
  @override
  Widget build(BuildContext context) => Center(child: Padding(padding: const EdgeInsets.all(28), child: Column(mainAxisSize: MainAxisSize.min, children: [
        Text('تعذّر التحميل', style: T.display(size: 16, color: T.sWeak)),
        const SizedBox(height: 6),
        Text('$error', style: T.body(size: 13, color: T.ink3), textAlign: TextAlign.center),
        if (onRetry != null) ...[const SizedBox(height: 14), OutlinedButton(onPressed: onRetry, child: const Text('أعد المحاولة'))],
      ])));
}

/// Async data helper: keeps screens small.
class Fetch<T> extends StatefulWidget {
  const Fetch({super.key, required this.future, required this.builder});
  final Future<T> Function() future;
  final Widget Function(BuildContext, T, VoidCallback refresh) builder;
  @override
  State<Fetch<T>> createState() => _FetchState<T>();
}

class _FetchState<T> extends State<Fetch<T>> {
  late Future<T> _f = widget.future();
  void _refresh() => setState(() => _f = widget.future());
  @override
  Widget build(BuildContext context) => FutureBuilder<T>(
        future: _f,
        builder: (c, s) {
          if (s.hasError) return ErrorBox(s.error!, onRetry: _refresh);
          if (!s.hasData) return const LoadingBox();
          return widget.builder(c, s.data as T, _refresh);
        },
      );
}
