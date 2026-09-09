import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/api.dart';
import '../../core/notify.dart';
import '../../core/theme.dart';
import '../../widgets/common.dart';
import 'reader_screen.dart';

/// The daily wird: today's pages, one tap to read, one tap to finish; streak and khatmah progress; a reminder time.
class WirdScreen extends StatefulWidget {
  const WirdScreen({super.key});
  @override
  State<WirdScreen> createState() => _WirdScreenState();
}

class _WirdScreenState extends State<WirdScreen> {
  int _v = 0;
  @override
  Widget build(BuildContext context) {
    if (!Api.I.moduleOn('quran.reading') || !Api.I.can('quran.reading.use')) {
      return const Center(child: EmptyState(title: 'الورد اليومي غير مفعّل', body: 'اطلب من إدارة المؤسسة تفعيل وحدة «الورد اليومي».'));
    }
    return Fetch<Map<String, dynamic>>(
      key: ValueKey(_v),
      cacheKey: 'wird',
      future: () async {
        try {
          return (await Api.I.get('/reading/today')) as Map<String, dynamic>;
        } on ApiException catch (e) {
          if (e.code == 'no_plan') return <String, dynamic>{'none': true};
          rethrow;
        }
      },
      builder: (context, d, refresh) {
        if (d['none'] == true) return _Setup(onDone: () => setState(() => _v++));
        final plan = d['plan'] as Map<String, dynamic>;
        final today = d['today'] as Map<String, dynamic>;
        final done = today['done'] == true;
        final progress = (plan['progress'] as num?)?.toDouble() ?? 0;
        return RefreshIndicator(
          onRefresh: () async => setState(() => _v++),
          child: ListView(padding: EdgeInsets.zero, children: [
            NightHeader(
              eyebrow: 'الورد اليومي',
              title: done ? 'أتممت وردك اليوم' : 'ورد اليوم',
              subtitle: '${today['from_surah']} ${arDigits(today['from_key'].toString().split(':').last)} ← ${today['to_surah']} ${arDigits(today['to_key'].toString().split(':').last)} · الجزء ${arDigits(today['juz'])}',
              trailing: RetentionRing(progress, size: 66, light: true, label: 'الختمة', stroke: 5),
              child: Row(children: [
                Expanded(child: _Stat(arDigits('${today['from_page']}–${today['to_page']}'), 'صفحات اليوم')),
                Expanded(child: _Stat(arDigits(d['streak'] ?? 0), 'يوم متتالٍ')),
                Expanded(child: _Stat(arDigits(d['days_left'] ?? 0), 'يومًا للختمة')),
              ]),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(18, 18, 18, 30),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(color: T.surface, borderRadius: BorderRadius.circular(16), border: Border.all(color: done ? T.sStrong.withValues(alpha: .4) : T.gold.withValues(alpha: .5)),
                      boxShadow: [BoxShadow(color: T.ink.withValues(alpha: .06), blurRadius: 18, offset: const Offset(0, 8))]),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Row(children: [
                      Container(width: 46, height: 46, decoration: BoxDecoration(color: done ? T.sStrong.withValues(alpha: .12) : T.goldTint, borderRadius: BorderRadius.circular(14)),
                          child: Icon(done ? Icons.check_circle_rounded : Icons.menu_book_rounded, color: done ? T.sStrong : T.gold)),
                      const SizedBox(width: 12),
                      Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Text(done ? 'بارك الله فيك' : 'صفحة ${arDigits(today['from_page'])} إلى ${arDigits(today['to_page'])}', style: T.display(size: 17)),
                        Text(done ? 'ورد الغد يبدأ من صفحة ${arDigits(plan['current_page'])}.' : '${arDigits(today['pages'])} صفحات · ${arDigits(plan['pages_per_day'])} يوميًا', style: T.body(size: 13, color: T.ink2)),
                      ])),
                    ]),
                    const SizedBox(height: 14),
                    GoldButton(
                      icon: Icons.auto_stories_rounded,
                      label: done ? 'تابع القراءة' : 'اقرأ الآن',
                      onPressed: () async {
                        final opened = DateTime.now();
                        final r = await Navigator.of(context).push(MaterialPageRoute(builder: (_) => ReaderScreen(
                          fromPage: today['from_page'], toPage: today['to_page'], title: 'ورد اليوم',
                          onFinished: done ? null : (from, to) async {
                            await Api.I.post('/reading/log', {'from_page': from, 'to_page': to, 'minutes': minutesSince(opened)});
                          },
                        )));
                        if (r == true && context.mounted) { toast(context, 'حُفظ وردك اليوم. تقبّل الله.'); setState(() => _v++); }
                      },
                    ),
                    if (!done) ...[
                      const SizedBox(height: 8),
                      Center(child: TextButton(
                        onPressed: () async {
                          HapticFeedback.mediumImpact();
                          await Api.I.post('/reading/log', {'from_page': today['from_page'], 'to_page': today['to_page'], 'minutes': 0});
                          if (context.mounted) { toast(context, 'سُجِّل الورد كمقروء.'); setState(() => _v++); }
                        },
                        child: Text('قرأتُه من مصحفي — سجّله كمقروء', style: T.body(size: 13, color: T.ink2)),
                      )),
                    ],
                  ]),
                ),
                const SizedBox(height: 14),
                _ReminderRow(kind: 'wird', title: 'تذكير الورد', sub: 'إشعار يومي في الوقت الذي تختاره'),
                const SizedBox(height: 14),
                SectionTitle('الختمة', top: 6, trailing: Text('${arDigits(plan['khatmat'])} ختمة مكتملة', style: T.body(size: 12.5, color: T.ink3))),
                _Khatmah(current: plan['current_page'] as int),
                const SizedBox(height: 8),
                Text('بقي ${arDigits(d['remaining_pages'])} صفحة · تنتهي الختمة خلال ${arDigits(d['days_left'])} يومًا بهذا المعدّل.', style: T.body(size: 13, color: T.ink2)),
                SectionTitle('آخر ١٤ يومًا'),
                const _History(),
                const SizedBox(height: 18),
                Row(children: [
                  Expanded(child: OutlinedButton.icon(onPressed: () => _changePlan(context, plan), icon: const Icon(Icons.tune_rounded, size: 18), label: const Text('تعديل الورد'))),
                ]),
              ]),
            ),
          ]),
        );
      },
    );
  }

  Future<void> _changePlan(BuildContext context, Map<String, dynamic> plan) async {
    int perDay = plan['pages_per_day'];
    int page = plan['current_page'];
    final ok = await showModalBottomSheet<bool>(
      context: context, backgroundColor: T.surface, showDragHandle: true, useSafeArea: true, isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(22))),
      builder: (ctx) => StatefulBuilder(builder: (ctx, set) => SingleChildScrollView(
        child: Padding(
          padding: EdgeInsets.fromLTRB(20, 0, 20, 24 + MediaQuery.viewInsetsOf(ctx).bottom),
          child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('تعديل الورد', style: T.display(size: 18)),
            const SizedBox(height: 12),
            Text('صفحات يوميًا', style: T.body(size: 13, color: T.ink2)),
            const SizedBox(height: 6),
            Wrap(spacing: 8, runSpacing: 8, children: [for (final n in [1, 2, 3, 4, 5, 10, 20]) ChoiceChip(label: Text(arDigits(n)), selected: perDay == n, onSelected: (_) => set(() => perDay = n))]),
            const SizedBox(height: 14),
            Text('موضعي الحالي (رقم الصفحة)', style: T.body(size: 13, color: T.ink2)),
            const SizedBox(height: 6),
            TextFormField(initialValue: '$page', keyboardType: TextInputType.number, textDirection: TextDirection.ltr, decoration: const InputDecoration(hintText: '1 – 604'),
                onChanged: (v) => page = int.tryParse(v) ?? page),
            const SizedBox(height: 16),
            FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('حفظ')),
          ]),
        ),
      )),
    );
    if (ok == true) {
      await Api.I.patch('/reading/plan', {'pages_per_day': perDay, 'current_page': page.clamp(1, 604)});
      if (mounted) setState(() => _v++);
    }
  }
}

class _Setup extends StatefulWidget {
  const _Setup({required this.onDone});
  final VoidCallback onDone;
  @override
  State<_Setup> createState() => _SetupState();
}

class _SetupState extends State<_Setup> {
  int? _days = 30;
  int? _perDay;
  int _start = 1;
  bool _busy = false;
  @override
  Widget build(BuildContext context) {
    final remaining = 604 - _start + 1;
    final perDay = _perDay ?? (_days == null ? 2 : (remaining / _days!).ceil());
    return ListView(padding: EdgeInsets.zero, children: [
      const NightHeader(eyebrow: 'الورد اليومي', title: 'ابدأ وردًا ثابتًا', subtitle: 'قليل دائم خير من كثير منقطع. اختر ختمة أو عدد صفحات، ويذكّرك التطبيق كل يوم.'),
      Padding(
        padding: const EdgeInsets.fromLTRB(18, 18, 18, 30),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('ختمة خلال', style: T.display(size: 15)),
          const SizedBox(height: 8),
          Wrap(spacing: 8, runSpacing: 8, children: [
            for (final d in [30, 60, 90, 120, 180, 365])
              ChoiceChip(label: Text('${arDigits(d)} يومًا'), selected: _days == d && _perDay == null, onSelected: (_) => setState(() { _days = d; _perDay = null; })),
          ]),
          const SizedBox(height: 16),
          Text('أو صفحات يوميًا', style: T.display(size: 15)),
          const SizedBox(height: 8),
          Wrap(spacing: 8, runSpacing: 8, children: [
            for (final n in [1, 2, 3, 5, 10, 20])
              ChoiceChip(label: Text(n == 1 ? 'صفحة' : '${arDigits(n)} صفحات'), selected: _perDay == n, onSelected: (_) => setState(() { _perDay = n; _days = null; })),
          ]),
          const SizedBox(height: 16),
          Text('أبدأ من صفحة', style: T.display(size: 15)),
          const SizedBox(height: 8),
          Row(children: [
            SizedBox(width: 120, child: TextFormField(initialValue: '1', keyboardType: TextInputType.number, textDirection: TextDirection.ltr, decoration: const InputDecoration(hintText: '1 – 604'),
                onChanged: (v) => setState(() => _start = (int.tryParse(v) ?? 1).clamp(1, 604)))),
            const SizedBox(width: 12),
            Expanded(child: Text('${arDigits(perDay)} صفحات يوميًا · تنتهي خلال ${arDigits((remaining / perDay).ceil())} يومًا', style: T.body(size: 13, color: T.ink2))),
          ]),
          const SizedBox(height: 22),
          GoldButton(
            icon: Icons.play_arrow_rounded, label: 'ابدأ الورد', busy: _busy,
            onPressed: _busy ? null : () async {
              setState(() => _busy = true);
              try {
                await Api.I.post('/reading/plan', {'kind': _perDay == null ? 'khatmah' : 'pages', if (_perDay != null) 'pages_per_day': _perDay, if (_perDay == null) 'target_days': _days, 'start_page': _start});
                HapticFeedback.mediumImpact();
                widget.onDone();
              } catch (e) {
                if (!context.mounted) return;
                setState(() => _busy = false);
                toast(context, friendlyError(e), error: true);
              }
            },
          ),
          const SizedBox(height: 12),
          Text('الورد قراءة من المصحف، مستقل عن خطة الحفظ. يمكنك تغييره في أي وقت.', style: T.body(size: 12.5, color: T.ink3)),
        ]),
      ),
    ]);
  }
}

class _Stat extends StatelessWidget {
  const _Stat(this.value, this.label);
  final String value;
  final String label;
  @override
  Widget build(BuildContext context) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(value, style: T.display(size: 20, color: T.nightInk), maxLines: 1, overflow: TextOverflow.ellipsis),
        Text(label, style: T.body(size: 11.5, color: T.nightMuted), maxLines: 1, overflow: TextOverflow.ellipsis),
      ]);
}

/// 30 Juz cells; filled up to the current page.
class _Khatmah extends StatelessWidget {
  const _Khatmah({required this.current});
  final int current;
  @override
  Widget build(BuildContext context) {
    final doneJuz = ((current - 1) / 604 * 30);
    return LayoutBuilder(builder: (context, c) {
      final w = (c.maxWidth - 29 * 3) / 30;
      return Row(textDirection: TextDirection.rtl, children: [
        for (var j = 0; j < 30; j++) ...[
          Container(width: w, height: 14, decoration: BoxDecoration(borderRadius: BorderRadius.circular(3), color: j + 1 <= doneJuz ? T.lapis : (j < doneJuz ? T.gold : T.ground2))),
          if (j < 29) const SizedBox(width: 3),
        ],
      ]);
    });
  }
}

class _History extends StatelessWidget {
  const _History();
  @override
  Widget build(BuildContext context) => Fetch<Map<String, dynamic>>(
        cacheKey: 'wird-history',
        future: () async => (await Api.I.get('/reading/history?days=14')) as Map<String, dynamic>,
        builder: (context, d, _) {
          final days = ((d['days'] as List?) ?? const []).cast<Map<String, dynamic>>();
          final byDate = {for (final x in days) x['date'] as String: x};
          final today = DateTime.now();
          final maxPages = days.fold<int>(1, (m, x) => (x['pages'] as int) > m ? x['pages'] as int : m);
          return Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(color: T.surface, borderRadius: BorderRadius.circular(14), border: Border.all(color: T.rule)),
            child: Row(textDirection: TextDirection.rtl, crossAxisAlignment: CrossAxisAlignment.end, children: [
              for (var i = 13; i >= 0; i--)
                Builder(builder: (_) {
                  final day = today.subtract(Duration(days: i));
                  final k = '${day.year}-${day.month.toString().padLeft(2, '0')}-${day.day.toString().padLeft(2, '0')}';
                  final p = (byDate[k]?['pages'] as int?) ?? 0;
                  return Expanded(child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 2),
                    child: Column(mainAxisSize: MainAxisSize.min, children: [
                      Container(height: 6 + 40 * (p / maxPages), decoration: BoxDecoration(color: p > 0 ? T.sStrong : T.ground2, borderRadius: BorderRadius.circular(3))),
                      const SizedBox(height: 4),
                      Text(arDigits(day.day), style: T.mono(size: 9)),
                    ]),
                  ));
                }),
            ]),
          );
        },
      );
}

/// A reminder row: switch + time; used for wird, plan and Halaqah reminders.
class _ReminderRow extends StatefulWidget {
  const _ReminderRow({required this.kind, required this.title, required this.sub});
  final String kind;
  final String title;
  final String sub;
  @override
  State<_ReminderRow> createState() => _ReminderRowState();
}

class _ReminderRowState extends State<_ReminderRow> {
  TimeOfDay? _t;
  @override
  void initState() { super.initState(); Notify.I.timeFor(widget.kind).then((v) { if (mounted) setState(() => _t = v); }); }
  @override
  Widget build(BuildContext context) => ReminderTile(kind: widget.kind, title: widget.title, sub: widget.sub, time: _t, onChanged: (v) => setState(() => _t = v));
}

/// Shared tile (also used on the account page).
class ReminderTile extends StatelessWidget {
  const ReminderTile({super.key, required this.kind, required this.title, required this.sub, required this.time, required this.onChanged});
  final String kind;
  final String title;
  final String sub;
  final TimeOfDay? time;
  final void Function(TimeOfDay?) onChanged;
  @override
  Widget build(BuildContext context) {
    final on = time != null;
    return Container(
      padding: const EdgeInsets.fromLTRB(14, 8, 8, 8),
      decoration: BoxDecoration(color: T.surface, borderRadius: BorderRadius.circular(14), border: Border.all(color: T.rule)),
      child: Row(children: [
        Container(width: 40, height: 40, decoration: BoxDecoration(color: on ? T.lapisTint : T.ground2, borderRadius: BorderRadius.circular(12)), child: Icon(Icons.notifications_active_rounded, color: on ? T.lapis : T.ink3, size: 20)),
        const SizedBox(width: 12),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(title, style: T.body(size: 14.5, weight: FontWeight.w700)),
          Text(on ? 'يوميًا الساعة ${time!.format(context)}' : sub, style: T.body(size: 12, color: T.ink3)),
        ])),
        if (on) TextButton(onPressed: () => _pick(context), child: const Text('الوقت')),
        Switch(value: on, onChanged: (v) async {
          if (v) { await _pick(context); } else { await Notify.I.cancel(kind); onChanged(null); }
        }),
      ]),
    );
  }

  Future<void> _pick(BuildContext context) async {
    final t = await showTimePicker(context: context, initialTime: time ?? const TimeOfDay(hour: 6, minute: 0), helpText: title);
    if (t == null) return;
    final ok = await Notify.I.scheduleDaily(kind, t);
    if (!context.mounted) return;
    if (ok) { onChanged(t); toast(context, 'سيصلك تذكير يوميًا الساعة ${t.format(context)}'); } else { toast(context, 'لم يُسمح بالإشعارات. فعّلها من إعدادات الجهاز.', error: true); }
  }
}
