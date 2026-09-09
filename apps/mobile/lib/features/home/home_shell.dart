import 'package:flutter/material.dart';

import '../../core/api.dart';
import '../../core/theme.dart';
import '../../core/prefs.dart';
import '../../widgets/common.dart';
import '../../widgets/tips.dart';
import '../../widgets/ayah_audio.dart';
import '../auth/login_screen.dart';
import '../parent/children_screen.dart';
import '../student/student_home.dart';
import '../teacher/halaqat_screen.dart';
import '../teacher/student_detail_screen.dart';
import '../teacher/students_screen.dart';
import '../reading/wird_screen.dart';
import '../../core/audio.dart';
import '../../core/notify.dart';

/// One codebase, role-based shells: teacher · student · parent (a person may hold several roles).
class HomeShell extends StatefulWidget {
  const HomeShell({super.key});
  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _tab = 0;
  @override
  Widget build(BuildContext context) {
    return Fetch<Map<String, dynamic>>(
      future: () async { final c = await Api.I.caps(); AyahAudio.I.load(); return c; },
      builder: (context, caps, _) {
        final roles = List<String>.from(caps['roles'] ?? const []);
        final staff = roles.any((r) => ['teacher', 'assistant_teacher', 'quran_supervisor', 'owner', 'center_admin', 'branch_manager', 'listener'].contains(r));
        final learner = roles.contains('student') || roles.contains('solo_learner');
        final tipRole = roles.contains('solo_learner') ? 'solo_learner' : roles.contains('student') ? 'student' : roles.contains('guardian') ? 'guardian' : staff ? 'teacher' : '';
        if (tipRole.isNotEmpty && Prefs.I.session.add('tips.$tipRole')) WidgetsBinding.instance.addPostFrameCallback((_) { if (context.mounted) showWelcomeTips(context, role: tipRole); });
        final tabs = <({String label, IconData icon, IconData active, Widget page})>[
          if (staff && !roles.contains('listener')) (label: 'حلقاتي', icon: Icons.radio_button_unchecked_rounded, active: Icons.radio_button_checked_rounded, page: const HalaqatScreen()),
          if (staff) (label: roles.contains('listener') ? 'من أسمّع له' : 'طلابي', icon: Icons.people_outline_rounded, active: Icons.people_rounded, page: const StudentsScreen()),
          if (learner) (label: 'اليوم', icon: Icons.today_outlined, active: Icons.today_rounded, page: const StudentHome()),
          if (learner) (label: 'رحلتي', icon: Icons.map_outlined, active: Icons.map_rounded, page: const _MyJourney()),
          if (roles.contains('guardian')) (label: 'أبنائي', icon: Icons.family_restroom_outlined, active: Icons.family_restroom_rounded, page: const ChildrenScreen()),
          (label: 'الورد', icon: Icons.menu_book_outlined, active: Icons.menu_book_rounded, page: const WirdScreen()),
          (label: 'حسابي', icon: Icons.person_outline_rounded, active: Icons.person_rounded, page: _AccountPage(caps: caps)),
        ];
        final i = _tab.clamp(0, tabs.length - 1);
        return Scaffold(
          body: IndexedStack(index: i, children: [for (final t in tabs) t.page]),
          bottomNavigationBar: tabs.length > 1
              ? NavigationBar(selectedIndex: i, onDestinationSelected: (v) => setState(() => _tab = v),
                  destinations: [for (final t in tabs) NavigationDestination(icon: Icon(t.icon), selectedIcon: Icon(t.active, color: T.lapis), label: t.label)])
              : null,
        );
      },
    );
  }
}

class _MyJourney extends StatelessWidget {
  const _MyJourney();
  @override
  Widget build(BuildContext context) => Fetch<String>(
        future: () async {
          final me = await Api.I.get('/journeys?page_size=1') as Map<String, dynamic>;
          final results = (me['results'] as List);
          if (results.isEmpty) throw ApiException(404, 'no_student', 'لا يوجد ملف طالب مرتبط بهذا الحساب');
          return results.first['id'] as String;
        },
        builder: (context, jid, _) => StudentDetailScreen(journeyId: jid, canPractice: true, embedded: true),
      );
}

class _AccountPage extends StatelessWidget {
  const _AccountPage({required this.caps});
  final Map<String, dynamic> caps;
  static const roleAr = {'owner': 'مالك المؤسسة', 'quran_supervisor': 'مشرف القرآن', 'teacher': 'معلم', 'assistant_teacher': 'معلم مساعد', 'guardian': 'ولي أمر', 'finance': 'مالية', 'center_admin': 'مدير المركز', 'student': 'طالب', 'support': 'دعم', 'branch_manager': 'مدير الفرع'};
  @override
  Widget build(BuildContext context) {
    final s = Api.I.session!;
    final tenant = caps['tenant'] as Map<String, dynamic>;
    final modules = (caps['modules'] as Map<String, dynamic>?) ?? {};
    return Column(children: [
      NightHeader(eyebrow: tenant['name'] ?? '', title: s.fullName, subtitle: s.email, trailing: Avatar(s.fullName, size: 52)),
      Expanded(child: ListView(padding: const EdgeInsets.all(20), children: [
        Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('الأدوار', style: T.display(size: 14)),
          const SizedBox(height: 6),
          Wrap(spacing: 6, runSpacing: 6, children: [for (final r in (caps['roles'] as List)) Chip2(roleAr[r] ?? r.toString(), color: T.lapis, filled: true)]),
          const SizedBox(height: 14),
          Text('الرواية', style: T.display(size: 14)),
          Text(tenant['riwayah'] == 'hafs_asim' ? 'حفص عن عاصم' : '${tenant['riwayah']}', style: T.body(size: 14, color: T.ink2)),
          const SizedBox(height: 14),
          Text('الذكاء الاصطناعي (اختياري · YELLOW)', style: T.display(size: 14)),
          const SizedBox(height: 6),
          Row(children: [
            Chip2('المساعد الذكي', color: modules['ai.assist']?['enabled'] == true ? T.sStrong : T.ink3),
            const SizedBox(width: 6),
            Chip2('التسميع الذكي', color: modules['hifz.asr']?['enabled'] == true ? T.sStrong : T.ink3),
          ]),
          const SizedBox(height: 6),
          Text('لا نص قرآني مولّد ولا صوت مولّد. المقترحات تُقارَن بالنص الموثّق ويعتمدها المعلم.', style: T.body(size: 12, color: T.ink3)),
        ]))),
        const SizedBox(height: 14),
        Text('التذكيرات', style: T.display(size: 15)),
        const SizedBox(height: 8),
        const _Reminders(),
        const SizedBox(height: 14),
        Text('القارئ', style: T.display(size: 15)),
        const SizedBox(height: 8),
        ListenableBuilder(listenable: AyahAudio.I, builder: (context, _) => Material(
          color: T.surface, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14), side: const BorderSide(color: T.rule)), clipBehavior: Clip.antiAlias,
          child: ListTile(leading: const Icon(Icons.record_voice_over_rounded, color: T.lapis), title: Text(AyahAudio.I.reciter?['name_ar'] ?? 'اختر القارئ', style: T.body(size: 14.5, weight: FontWeight.w700)),
            subtitle: Text('لسماع الآيات في الورد والتدريب', style: T.body(size: 12, color: T.ink3)), trailing: const Icon(Icons.chevron_left_rounded), onTap: () => showReciterPicker(context)),
        )),
        const SizedBox(height: 14),
        OutlinedButton.icon(onPressed: () async {
          await Api.I.logout();
          if (context.mounted) Navigator.of(context).pushAndRemoveUntil(MaterialPageRoute(builder: (_) => const LoginScreen()), (_) => false);
        }, icon: const Icon(Icons.logout_rounded, size: 18), label: const Text('تسجيل الخروج')),
        const SizedBox(height: 20),
        Text('نص القرآن: مشروع تنزيل — tanzil.net · tallaqi.com · v0.5.1', style: T.body(size: 12, color: T.ink3), textAlign: TextAlign.center),
      ])),
    ]);
  }
}


/// Reminder tiles on the account page: wird for everyone, plan for learners, Halaqah for teachers.
class _Reminders extends StatefulWidget {
  const _Reminders();
  @override
  State<_Reminders> createState() => _RemindersState();
}

class _RemindersState extends State<_Reminders> {
  final Map<String, TimeOfDay?> _t = {};
  @override
  void initState() {
    super.initState();
    for (final k in Notify.kinds.keys) {
      Notify.I.timeFor(k).then((v) { if (mounted) setState(() => _t[k] = v); });
    }
  }
  @override
  Widget build(BuildContext context) {
    final roles = Api.I.roles;
    final learner = roles.contains('student') || roles.contains('solo_learner');
    final teacher = roles.any((r) => ['teacher', 'assistant_teacher', 'quran_supervisor'].contains(r));
    return Column(children: [
      ReminderTile(kind: 'wird', title: 'الورد اليومي', sub: 'تذكير بقراءة وردك', time: _t['wird'], onChanged: (v) => setState(() => _t['wird'] = v)),
      if (learner) ...[const SizedBox(height: 8), ReminderTile(kind: 'plan', title: 'خطة اليوم', sub: 'تذكير بمقاطع الحفظ والمراجعة', time: _t['plan'], onChanged: (v) => setState(() => _t['plan'] = v))],
      if (teacher) ...[const SizedBox(height: 8), ReminderTile(kind: 'halaqah', title: 'حلقة اليوم', sub: 'تذكير قبل موعد الحلقة', time: _t['halaqah'], onChanged: (v) => setState(() => _t['halaqah'] = v))],
    ]);
  }
}
