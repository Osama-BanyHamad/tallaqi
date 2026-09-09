import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/api.dart';
import '../../core/theme.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../widgets/common.dart';
import '../home/home_shell.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _email = TextEditingController(text: 'teacher1@demo.talaqqi');
  final _password = TextEditingController();
  String? _error;
  bool _busy = false;
  bool _showPw = false;

  static const demo = [
    ('معلم', 'teacher1@demo.talaqqi', Icons.school_rounded, T.lapis),
    ('طالب', 'student1@demo.talaqqi', Icons.auto_stories_rounded, T.sStrong),
    ('ولي أمر', 'parent1@demo.talaqqi', Icons.family_restroom_rounded, T.gold),
    ('مشرف', 'supervisor@demo.talaqqi', Icons.insights_rounded, T.sRecent),
  ];

  Future<void> _submit({String? email, String? password}) async {
    if (email != null) { _email.text = email; _password.text = password ?? 'Talaqqi@2026'; }
    setState(() { _busy = true; _error = null; });
    try {
      await Api.I.login(_email.text.trim(), _password.text);
      if (!mounted) return;
      HapticFeedback.mediumImpact();
      Navigator.of(context).pushAndRemoveUntil(PageRouteBuilder(pageBuilder: (_, a, __) => FadeTransition(opacity: a, child: const HomeShell()), transitionDuration: const Duration(milliseconds: 350)), (_) => false);
    } catch (e) {
      setState(() => _error = friendlyError(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: ListView(padding: EdgeInsets.zero, children: [
        Container(
          width: double.infinity,
          decoration: const BoxDecoration(gradient: RadialGradient(center: Alignment(0.9, -0.9), radius: 1.6, colors: [T.night2, T.night])),
          child: Stack(children: [
            const Positioned.fill(child: _Lattice()),
            Padding(
              padding: EdgeInsets.fromLTRB(28, MediaQuery.paddingOf(context).top + 40, 28, 28),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                FadeIn(child: Text('تَلَقِّي', style: T.quran(size: 64, color: T.nightInk).copyWith(height: 1.25))),
                const SizedBox(height: 18),
                FadeIn(index: 1, child: Text('TALAQQI', style: T.display(size: 11, color: T.gold2).copyWith(letterSpacing: 3))),
                const SizedBox(height: 16),
                FadeIn(index: 2, child: Text('رحلة الطالب مع القرآن: ما حُفظ، وما ثبت، وما يُراجَع اليوم.', style: T.body(size: 16, color: T.nightInk))),
                const SizedBox(height: 22),
                FadeIn(index: 3, child: _SampleStrip()),
              ]),
            ),
          ]),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(28, 26, 28, 28),
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            Text('تسجيل الدخول', style: T.display(size: 24)),
            const SizedBox(height: 16),
            Text('البريد الإلكتروني', style: T.body(size: 13, color: T.ink2)),
            const SizedBox(height: 6),
            TextField(controller: _email, keyboardType: TextInputType.emailAddress, textDirection: TextDirection.ltr, autocorrect: false,
                decoration: const InputDecoration(prefixIcon: Icon(Icons.alternate_email_rounded, size: 18))),
            const SizedBox(height: 14),
            Text('كلمة المرور', style: T.body(size: 13, color: T.ink2)),
            const SizedBox(height: 6),
            TextField(controller: _password, obscureText: !_showPw, textDirection: TextDirection.ltr, onSubmitted: (_) => _submit(),
                decoration: InputDecoration(prefixIcon: const Icon(Icons.lock_outline_rounded, size: 18),
                    suffixIcon: IconButton(onPressed: () => setState(() => _showPw = !_showPw), icon: Icon(_showPw ? Icons.visibility_off_rounded : Icons.visibility_rounded, size: 18)))),
            AnimatedSize(duration: const Duration(milliseconds: 200), child: _error == null ? const SizedBox.shrink() : Padding(padding: const EdgeInsets.only(top: 10), child: Row(children: [const Icon(Icons.error_outline_rounded, color: T.sWeak, size: 16), const SizedBox(width: 6), Expanded(child: Text(_error!, style: T.body(size: 13, color: T.sWeak)))]))),
            const SizedBox(height: 18),
            FilledButton(onPressed: _busy ? null : () => _submit(), child: _busy ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)) : const Text('ادخل')),
            const SizedBox(height: 26),
            Row(children: [Expanded(child: Divider(color: T.rule)), Padding(padding: const EdgeInsets.symmetric(horizontal: 10), child: Text('جرّب العرض التجريبي بلمسة', style: T.body(size: 12.5, color: T.ink3))), Expanded(child: Divider(color: T.rule))]),
            const SizedBox(height: 12),
            GridView.count(
              crossAxisCount: 2, shrinkWrap: true, physics: const NeverScrollableScrollPhysics(), mainAxisSpacing: 10, crossAxisSpacing: 10, childAspectRatio: 2.6,
              children: [
                for (final d in demo)
                  OutlinedButton(
                    style: OutlinedButton.styleFrom(alignment: AlignmentDirectional.centerStart, padding: const EdgeInsets.symmetric(horizontal: 12), side: BorderSide(color: d.$4.withValues(alpha: .35)), backgroundColor: d.$4.withValues(alpha: .05)),
                    onPressed: _busy ? null : () => _submit(email: d.$2),
                    child: Row(children: [Icon(d.$3, size: 18, color: d.$4), const SizedBox(width: 8), Text(d.$1, style: T.body(size: 14, weight: FontWeight.w700, color: T.ink))]),
                  ),
              ],
            ),
            const SizedBox(height: 10),
            Text('كلمة المرور لحسابات العرض: Talaqqi@2026 · البيانات تجريبية وقد تُعاد تهيئتها.', style: T.body(size: 11.5, color: T.ink3)),
            const SizedBox(height: 18),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(color: T.goldTint, borderRadius: BorderRadius.circular(14), border: Border.all(color: T.gold.withValues(alpha: .4))),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('تحفظ وحدك؟', style: T.display(size: 15)),
                Text('أنشئ رحلتك الخاصة مجانًا في دقيقة، ثم سجّل الدخول هنا بحسابك.', style: T.body(size: 13, color: T.ink2)),
                const SizedBox(height: 8),
                GoldButton(compact: true, icon: Icons.open_in_new_rounded, label: 'ابدأ رحلتك على tallaqi.com', onPressed: () => launchUrl(Uri.parse('https://tallaqi.com/start'), mode: LaunchMode.externalApplication)),
              ]),
            ),
          ]),
        ),
      ]),
    );
  }
}

class _Lattice extends StatelessWidget {
  const _Lattice();
  @override
  Widget build(BuildContext context) => CustomPaint(painter: _LatticePainter());
}

class _LatticePainter extends CustomPainter {
  @override
  void paint(Canvas c, Size s) {
    final p = Paint()..color = T.gold2.withValues(alpha: .07)..style = PaintingStyle.stroke..strokeWidth = 1;
    const step = 64.0;
    for (var x = -step; x < s.width + step; x += step) {
      for (var y = -step; y < s.height + step; y += step) {
        c.drawPath(Path()..moveTo(x + step / 2, y)..lineTo(x + step, y + step / 2)..lineTo(x + step / 2, y + step)..lineTo(x, y + step / 2)..close(), p);
      }
    }
  }
  @override
  bool shouldRepaint(_LatticePainter o) => false;
}

class _SampleStrip extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    const cols = [T.sMastered, T.sStrong, T.sRecent, T.sNeeds, T.sWeak, T.sCritical];
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Column(children: [
        for (var r = 0; r < 3; r++)
          Padding(
            padding: const EdgeInsets.only(bottom: 4),
            child: Row(children: [
              for (var i = 0; i < 20; i++)
                Expanded(child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 1.5),
                  child: TweenAnimationBuilder<double>(
                    tween: Tween(begin: 0, end: 1), duration: Duration(milliseconds: 400 + (r * 20 + i) * 12), curve: Curves.easeOut,
                    builder: (_, v, __) => Opacity(opacity: v, child: Container(height: 10, decoration: BoxDecoration(color: (r * 7 + i * 3) % 5 == 0 ? cols[(r + i) % cols.length] : cols[(i * 2 + r) % 3], borderRadius: BorderRadius.circular(2)))),
                  ),
                )),
            ]),
          ),
      ]),
    );
  }
}
