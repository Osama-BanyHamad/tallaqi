import 'package:flutter/material.dart';

import '../core/prefs.dart';
import '../core/theme.dart';

/// A one-time welcome sheet per role: three short lines that explain the loop, then never again.
Future<void> showWelcomeTips(BuildContext context, {required String role}) async {
  if (await Prefs.I.seen('welcome.$role')) return;
  final tips = switch (role) {
    'teacher' => (
        'حلقتك في يدك',
        [
          (Icons.done_all_rounded, 'الحضور بنقرة', 'افتح حلقة اليوم واضغط «الكل حاضر»، ثم عدّل الاستثناءات فقط.'),
          (Icons.touch_app_rounded, 'التسميع من المصحف', 'اضغط «سمّع» عند الطالب، انقر الكلمة الخاطئة، اختر النوع، ثم «اجتاز».'),
          (Icons.auto_awesome_rounded, 'الذكاء الاصطناعي يساعد ولا يقرّر', 'سجّل التلاوة ليقترح المواضع على النص الموثّق، وأنت من يعتمدها.'),
        ]
      ),
    'student' || 'solo_learner' => (
        'رحلتك تبدأ اليوم',
        [
          (Icons.today_rounded, 'خطة اليوم', 'مقاطع قليلة كل يوم: حفظ جديد ومراجعة قريبة ومراجعة بعيدة، مرتّبة حسب الثبات.'),
          (Icons.visibility_off_rounded, 'أخفِ واسترجع', 'افتح المقطع، اقرأه، ثم أخفِ النص واسترجعه. كل تلميح من النص الموثّق.'),
          (Icons.mic_rounded, 'سمّع بصوتك', 'اضغط «سمّع بالذكاء الاصطناعي» لترى مواضع الاختلاف — ثم سمّع لمعلمك أو لمن يسمّع لك.'),
        ]
      ),
    'guardian' => (
        'ست إجابات كل أسبوع',
        [
          (Icons.family_restroom_rounded, 'اختر ابنك', 'كل ابن بطاقة: خريطة حفظه وثباته وما يحتاج متابعة.'),
          (Icons.question_answer_rounded, 'الإجابات الست', 'هل حضر؟ ماذا حفظ؟ ماذا راجع؟ هل يتحسّن؟ ماذا يوصي المعلم؟ ما المطلوب اليوم؟'),
          (Icons.ios_share_rounded, 'شارك التقرير', 'زر المشاركة يرسل التقرير نصًا إلى واتساب أو مجموعة العائلة.'),
        ]
      ),
    _ => null,
  };
  if (tips == null || !context.mounted) return;
  await showModalBottomSheet(
    context: context, backgroundColor: T.surface, showDragHandle: true, isScrollControlled: true,
    shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(22))),
    builder: (_) => Padding(
      padding: const EdgeInsets.fromLTRB(22, 0, 22, 28),
      child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('تَلَقِّي', style: T.quran(size: 30, color: T.lapis).copyWith(height: 1.1)),
        Text(tips.$1, style: T.display(size: 20)),
        const SizedBox(height: 14),
        for (final t in tips.$2)
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Container(width: 40, height: 40, decoration: BoxDecoration(color: T.lapisTint, borderRadius: BorderRadius.circular(12)), child: Icon(t.$1, color: T.lapis, size: 22)),
              const SizedBox(width: 12),
              Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(t.$2, style: T.body(size: 15, weight: FontWeight.w700)),
                Text(t.$3, style: T.body(size: 13.5, color: T.ink2)),
              ])),
            ]),
          ),
        const SizedBox(height: 6),
        FilledButton(onPressed: () => Navigator.pop(context), child: const Text('فهمت، لنبدأ')),
      ]),
    ),
  );
  await Prefs.I.markSeen('welcome.$role');
}

/// Explain the microphone once, in our words, before the operating system asks.
Future<bool> explainMicrophone(BuildContext context) async {
  if (await Prefs.I.seen('mic')) return true;
  if (!context.mounted) return true;
  final ok = await showDialog<bool>(
    context: context,
    builder: (_) => AlertDialog(
      backgroundColor: T.surface,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      title: Row(children: [const Icon(Icons.mic_rounded, color: T.gold), const SizedBox(width: 8), Text('إذن الميكروفون', style: T.display(size: 17))]),
      content: Text('نسجّل تلاوتك فقط عندما تضغط الزر، ونرسلها لمقارنتها بالنص الموثّق، ثم نحذفها من الجهاز. لا يُحفظ الصوت على الخادم.', style: T.body(size: 14, color: T.ink2)),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('لاحقًا')),
        FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('حسنًا')),
      ],
    ),
  );
  if (ok == true) await Prefs.I.markSeen('mic');
  return ok == true;
}
