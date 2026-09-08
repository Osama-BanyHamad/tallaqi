import 'package:flutter/material.dart';

import '../../core/api.dart';
import '../../core/theme.dart';
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

  Future<void> _submit() async {
    setState(() { _busy = true; _error = null; });
    try {
      await Api.I.login(_email.text.trim(), _password.text);
      if (!mounted) return;
      Navigator.of(context).pushAndRemoveUntil(MaterialPageRoute(builder: (_) => const HomeShell()), (_) => false);
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
          padding: EdgeInsets.fromLTRB(28, MediaQuery.paddingOf(context).top + 48, 28, 28),
          decoration: const BoxDecoration(gradient: RadialGradient(center: Alignment(0.9, -0.9), radius: 1.6, colors: [T.night2, T.night])),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('تَلَقِّي', style: T.quran(size: 64, color: T.nightInk).copyWith(height: 1.25)),
            const SizedBox(height: 22),
            Text('TALAQQI', style: T.display(size: 11, color: T.gold2).copyWith(letterSpacing: 3)),
            const SizedBox(height: 18),
            Text('رحلة الطالب مع القرآن: ما حُفظ، وما ثبت، وما يُراجَع اليوم.', style: T.body(size: 16, color: T.nightInk)),
            const SizedBox(height: 22),
            _SampleStrip(),
          ]),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(28, 30, 28, 28),
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            Text('تسجيل الدخول', style: T.display(size: 24)),
            const SizedBox(height: 18),
            Text('البريد الإلكتروني', style: T.body(size: 13, color: T.ink2)),
            const SizedBox(height: 6),
            TextField(controller: _email, keyboardType: TextInputType.emailAddress, textDirection: TextDirection.ltr, autocorrect: false),
            const SizedBox(height: 14),
            Text('كلمة المرور', style: T.body(size: 13, color: T.ink2)),
            const SizedBox(height: 6),
            TextField(controller: _password, obscureText: true, textDirection: TextDirection.ltr, onSubmitted: (_) => _submit()),
            if (_error != null) Padding(padding: const EdgeInsets.only(top: 10), child: Text(_error!, style: T.body(size: 13, color: T.sWeak))),
            const SizedBox(height: 20),
            FilledButton(onPressed: _busy ? null : _submit, child: Text(_busy ? '…' : 'ادخل')),
            const SizedBox(height: 12),
            Text('العرض التجريبي: teacher1@demo.talaqqi · parent1@ · owner@ — كلمة المرور Talaqqi@2026', style: T.body(size: 12, color: T.ink3)),
          ]),
        ),
      ]),
    );
  }
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
                  child: Container(height: 10, decoration: BoxDecoration(
                    color: ((r * 20 + i) * 2654435761 % 1000) / 1000 < (r == 0 ? .35 : r == 1 ? .8 : .97)
                        ? cols[((r * 20 + i) * 7 + r) % (r == 2 ? 3 : 6)]
                        : Colors.white.withValues(alpha: .08),
                    borderRadius: BorderRadius.circular(2))),
                )),
            ]),
          ),
      ]),
    );
  }
}


/// Turn transport exceptions into one calm Arabic line; API errors already carry a readable message.
String friendlyError(Object e) {
  final t = e.toString();
  if (t.contains('SocketException') || t.contains('Failed host lookup') || t.contains('Connection refused') || t.contains('Network is unreachable')) {
    return 'تعذّر الاتصال بالخادم. تحقّق من اتصال الإنترنت ثم حاول مجددًا.';
  }
  if (t.contains('TimeoutException')) return 'انتهت مهلة الاتصال. حاول مجددًا.';
  return t.replaceFirst('Exception: ', '');
}
