import 'package:flutter/material.dart';

import '../../core/api.dart';
import '../../core/theme.dart';
import '../../widgets/common.dart';
import '../auth/login_screen.dart';
import '../parent/children_screen.dart';
import '../student/student_home.dart';
import '../teacher/halaqat_screen.dart';

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
      future: () => Api.I.caps(),
      builder: (context, caps, _) {
        final roles = List<String>.from(caps['roles'] ?? const []);
        final tabs = <({String label, IconData icon, Widget page})>[
          if (roles.any((r) => ['teacher', 'assistant_teacher', 'quran_supervisor', 'owner', 'center_admin', 'branch_manager'].contains(r)))
            (label: 'حلقاتي', icon: Icons.radio_button_checked_rounded, page: const HalaqatScreen()),
          if (roles.contains('student')) (label: 'اليوم', icon: Icons.today_rounded, page: const StudentHome()),
          if (roles.contains('guardian')) (label: 'أبنائي', icon: Icons.family_restroom_rounded, page: const ChildrenScreen()),
          (label: 'حسابي', icon: Icons.person_rounded, page: _AccountPage(caps: caps)),
        ];
        final i = _tab.clamp(0, tabs.length - 1);
        return Scaffold(
          body: tabs[i].page,
          bottomNavigationBar: tabs.length > 1
              ? NavigationBar(selectedIndex: i, onDestinationSelected: (v) => setState(() => _tab = v),
                  destinations: [for (final t in tabs) NavigationDestination(icon: Icon(t.icon), label: t.label)])
              : null,
        );
      },
    );
  }
}

class _AccountPage extends StatelessWidget {
  const _AccountPage({required this.caps});
  final Map<String, dynamic> caps;
  @override
  Widget build(BuildContext context) {
    final s = Api.I.session!;
    final tenant = caps['tenant'] as Map<String, dynamic>;
    return Column(children: [
      NightHeader(eyebrow: tenant['name'] ?? '', title: s.fullName, subtitle: s.email),
      Expanded(child: ListView(padding: const EdgeInsets.all(20), children: [
        Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('الأدوار', style: T.display(size: 14)),
          const SizedBox(height: 6),
          Wrap(spacing: 6, children: [for (final r in (caps['roles'] as List)) Chip2(r.toString(), color: T.lapis)]),
          const SizedBox(height: 14),
          Text('الرواية', style: T.display(size: 14)),
          Text(tenant['riwayah'] == 'hafs_asim' ? 'حفص عن عاصم' : '${tenant['riwayah']}', style: T.body(size: 14, color: T.ink2)),
        ]))),
        const SizedBox(height: 14),
        OutlinedButton(onPressed: () async {
          await Api.I.logout();
          if (context.mounted) Navigator.of(context).pushAndRemoveUntil(MaterialPageRoute(builder: (_) => const LoginScreen()), (_) => false);
        }, child: const Text('تسجيل الخروج')),
        const SizedBox(height: 20),
        Text('نص القرآن: مشروع تنزيل — tanzil.net · tallaqi.com', style: T.body(size: 12, color: T.ink3), textAlign: TextAlign.center),
      ])),
    ]);
  }
}
