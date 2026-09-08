import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

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
    return Hero(
      tag: 'avatar-$name',
      child: Container(
        width: size, height: size, alignment: Alignment.center,
        decoration: BoxDecoration(color: tones[h % tones.length], shape: BoxShape.circle, boxShadow: [BoxShadow(color: tones[h % tones.length].withValues(alpha: .35), blurRadius: 12, offset: const Offset(0, 6))]),
        child: Text(initials, style: T.display(size: size * .34, color: Colors.white)),
      ),
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
              return TweenAnimationBuilder<double>(
                tween: Tween(begin: 0, end: 1), duration: Duration(milliseconds: 350 + i * 18), curve: Curves.easeOutCubic,
                builder: (_, v, __) => Opacity(opacity: (cov > 0 ? .55 + cov * .45 : 1) * v,
                    child: Container(height: height, decoration: BoxDecoration(color: T.state(st), borderRadius: BorderRadius.circular(2)))),
              );
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
              child: TweenAnimationBuilder<double>(tween: Tween(begin: 0, end: p / 100), duration: const Duration(milliseconds: 700), curve: Curves.easeOutCubic,
                  builder: (_, f, __) => FractionallySizedBox(widthFactor: f, child: Container(decoration: BoxDecoration(color: T.retention(v), borderRadius: BorderRadius.circular(4))))))),
      const SizedBox(width: 8),
      Text(pct(v), style: T.mono(size: 12, color: T.ink2)),
    ]);
  }
}

/// Animated ring for retention / accuracy. Gold track on night, or rule track on paper.
class RetentionRing extends StatelessWidget {
  const RetentionRing(this.v, {super.key, this.size = 72, this.light = false, this.label, this.stroke = 6});
  final double? v;
  final double size;
  final bool light;
  final String? label;
  final double stroke;
  @override
  Widget build(BuildContext context) {
    final val = (v ?? 0).clamp(0, 1).toDouble();
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0, end: val), duration: const Duration(milliseconds: 900), curve: Curves.easeOutCubic,
      builder: (_, f, __) => SizedBox(
        width: size, height: size,
        child: CustomPaint(
          painter: _RingPainter(f, light ? T.gold2 : T.retention(v), light ? Colors.white.withValues(alpha: .14) : T.ground2, stroke),
          child: Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
            Text('${arDigits((f * 100).round())}٪', style: T.display(size: size * .24, color: light ? T.nightInk : T.ink)),
            if (label != null) Text(label!, style: T.body(size: size * .13, color: light ? T.nightMuted : T.ink3)),
          ])),
        ),
      ),
    );
  }
}

class _RingPainter extends CustomPainter {
  _RingPainter(this.f, this.color, this.track, this.stroke);
  final double f;
  final Color color;
  final Color track;
  final double stroke;
  @override
  void paint(Canvas c, Size s) {
    final r = (s.shortestSide - stroke) / 2;
    final center = Offset(s.width / 2, s.height / 2);
    c.drawCircle(center, r, Paint()..color = track..style = PaintingStyle.stroke..strokeWidth = stroke);
    c.drawArc(Rect.fromCircle(center: center, radius: r), -math.pi / 2, -2 * math.pi * f, false,
        Paint()..color = color..style = PaintingStyle.stroke..strokeWidth = stroke..strokeCap = StrokeCap.round);
  }
  @override
  bool shouldRepaint(_RingPainter o) => o.f != f || o.color != color;
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
  const Kpi({super.key, required this.label, required this.value, this.accent = false, this.color, this.sub, this.icon});
  final String label;
  final String value;
  final bool accent;
  final Color? color;
  final String? sub;
  final IconData? icon;
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 12),
      decoration: BoxDecoration(
        gradient: accent ? const LinearGradient(colors: [T.lapis2, T.lapis], begin: Alignment.topLeft, end: Alignment.bottomRight) : null,
        color: accent ? null : T.surface,
        borderRadius: BorderRadius.circular(14), border: accent ? null : Border.all(color: T.rule),
        boxShadow: [BoxShadow(color: (accent ? T.lapis : T.ink).withValues(alpha: accent ? .28 : .05), blurRadius: 18, offset: const Offset(0, 8))],
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisAlignment: MainAxisAlignment.center, children: [
        Row(children: [
          if (icon != null) ...[Icon(icon, size: 15, color: accent ? Colors.white70 : T.ink3), const SizedBox(width: 6)],
          Expanded(child: Text(label, style: T.body(size: 12, color: accent ? Colors.white70 : T.ink3, weight: FontWeight.w500), maxLines: 1, overflow: TextOverflow.ellipsis)),
        ]),
        const SizedBox(height: 4),
        Text(value, style: T.display(size: 24, color: accent ? Colors.white : (color ?? T.ink)), maxLines: 1),
        if (sub != null) Text(sub!, style: T.body(size: 11.5, color: accent ? Colors.white60 : T.ink3), maxLines: 1, overflow: TextOverflow.ellipsis),
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

class SectionTitle extends StatelessWidget {
  const SectionTitle(this.text, {super.key, this.trailing, this.top = 22});
  final String text;
  final Widget? trailing;
  final double top;
  @override
  Widget build(BuildContext context) => Padding(
        padding: EdgeInsets.fromLTRB(2, top, 2, 10),
        child: Row(children: [Expanded(child: Text(text, style: T.display(size: 16))), if (trailing != null) trailing!]),
      );
}

/// The night header with the 8-point lattice, a gold hairline, and an optional back/close control.
class NightHeader extends StatelessWidget {
  const NightHeader({super.key, required this.title, this.eyebrow, this.subtitle, this.trailing, this.child, this.leadingBack = false, this.compact = false});
  final String title;
  final String? eyebrow;
  final String? subtitle;
  final Widget? trailing;
  final Widget? child;
  final bool leadingBack;
  final bool compact;
  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      decoration: const BoxDecoration(
        gradient: LinearGradient(colors: [T.night2, T.night], begin: Alignment.topRight, end: Alignment.bottomLeft),
        border: Border(bottom: BorderSide(color: T.gold, width: 1)),
      ),
      child: Stack(children: [
        Positioned.fill(child: CustomPaint(painter: _LatticePainter())),
        Padding(
          padding: EdgeInsets.fromLTRB(20, MediaQuery.paddingOf(context).top + (compact ? 10 : 16), 20, compact ? 16 : 22),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              if (leadingBack)
                Padding(padding: const EdgeInsetsDirectional.only(end: 8), child: IconButton(onPressed: () => Navigator.maybePop(context), icon: const Icon(Icons.arrow_forward_rounded, color: T.nightInk), style: IconButton.styleFrom(backgroundColor: Colors.white.withValues(alpha: .06)))),
              Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                if (eyebrow != null) Eyebrow(eyebrow!, light: true),
                const SizedBox(height: 6),
                Text(title, style: T.display(size: compact ? 20 : 24, color: T.nightInk), maxLines: 2, overflow: TextOverflow.ellipsis),
                if (subtitle != null) Padding(padding: const EdgeInsets.only(top: 4), child: Text(subtitle!, style: T.body(size: 13, color: T.nightMuted))),
              ])),
              if (trailing != null) trailing!,
            ]),
            if (child != null) Padding(padding: const EdgeInsets.only(top: 16), child: child!),
          ]),
        ),
      ]),
    );
  }
}

class _LatticePainter extends CustomPainter {
  @override
  void paint(Canvas c, Size s) {
    final p = Paint()..color = T.gold2.withValues(alpha: .07)..style = PaintingStyle.stroke..strokeWidth = 1;
    const step = 64.0;
    for (var x = -step; x < s.width + step; x += step) {
      for (var y = -step; y < s.height + step; y += step) {
        final path = Path()..moveTo(x + step / 2, y)..lineTo(x + step, y + step / 2)..lineTo(x + step / 2, y + step)..lineTo(x, y + step / 2)..close();
        c.drawPath(path, p);
      }
    }
  }
  @override
  bool shouldRepaint(_LatticePainter o) => false;
}

/// Staggered entrance for list children: fade + slide up, keyed by index.
class FadeIn extends StatelessWidget {
  const FadeIn({super.key, required this.child, this.index = 0, this.delayMs = 60});
  final Widget child;
  final int index;
  final int delayMs;
  @override
  Widget build(BuildContext context) => TweenAnimationBuilder<double>(
        tween: Tween(begin: 0, end: 1),
        duration: Duration(milliseconds: 380 + (index.clamp(0, 12)) * delayMs),
        curve: Curves.easeOutCubic,
        builder: (_, v, ch) => Opacity(opacity: v, child: Transform.translate(offset: Offset(0, (1 - v) * 18), child: ch)),
        child: child,
      );
}

class GoldButton extends StatelessWidget {
  const GoldButton({super.key, required this.label, required this.onPressed, this.icon, this.compact = false, this.busy = false});
  final String label;
  final VoidCallback? onPressed;
  final IconData? icon;
  final bool compact;
  final bool busy;
  @override
  Widget build(BuildContext context) => FilledButton(
        style: FilledButton.styleFrom(backgroundColor: T.gold, foregroundColor: const Color(0xFF1F1806), minimumSize: Size(0, compact ? 40 : 48), padding: EdgeInsets.symmetric(horizontal: compact ? 14 : 18)),
        onPressed: busy ? null : () { HapticFeedback.selectionClick(); onPressed?.call(); },
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          if (busy) const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF1F1806)))
          else if (icon != null) Icon(icon, size: 18),
          if (icon != null || busy) const SizedBox(width: 8),
          Text(label, style: T.body(size: compact ? 13.5 : 15, weight: FontWeight.w700, color: const Color(0xFF1F1806))),
        ]),
      );
}

class EmptyState extends StatelessWidget {
  const EmptyState({super.key, required this.title, this.body, this.icon = Icons.auto_stories_outlined});
  final String title;
  final String? body;
  final IconData icon;
  @override
  Widget build(BuildContext context) => Center(child: Padding(padding: const EdgeInsets.all(32), child: Column(mainAxisSize: MainAxisSize.min, children: [
        Container(width: 64, height: 64, decoration: BoxDecoration(color: T.lapisTint, shape: BoxShape.circle), child: Icon(icon, color: T.lapis, size: 30)),
        const SizedBox(height: 14),
        Text(title, style: T.display(size: 16), textAlign: TextAlign.center),
        if (body != null) Padding(padding: const EdgeInsets.only(top: 6), child: Text(body!, style: T.body(size: 13.5, color: T.ink3), textAlign: TextAlign.center)),
      ])));
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

/// Async data helper: keeps screens small. Supports pull-to-refresh via [refresh].
class Fetch<D> extends StatefulWidget {
  const Fetch({super.key, required this.future, required this.builder});
  final Future<D> Function() future;
  final Widget Function(BuildContext, D, VoidCallback refresh) builder;
  @override
  State<Fetch<D>> createState() => _FetchState<D>();
}

class _FetchState<D> extends State<Fetch<D>> {
  late Future<D> _f = widget.future();
  void _refresh() => setState(() => _f = widget.future());
  @override
  Widget build(BuildContext context) => FutureBuilder<D>(
        future: _f,
        builder: (c, s) {
          if (s.hasError) return ErrorBox(s.error!, onRetry: _refresh);
          if (!s.hasData) return const LoadingBox();
          return widget.builder(c, s.data as D, _refresh);
        },
      );
}

void toast(BuildContext context, String text, {bool error = false}) {
  ScaffoldMessenger.of(context)
    ..hideCurrentSnackBar()
    ..showSnackBar(SnackBar(content: Text(text, style: T.body(size: 13.5, color: Colors.white)), backgroundColor: error ? T.sWeak : T.ink, behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10))));
}
