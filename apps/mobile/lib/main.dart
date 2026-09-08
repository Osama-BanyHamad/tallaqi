import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import 'core/api.dart';
import 'core/theme.dart';
import 'features/auth/login_screen.dart';
import 'features/home/home_shell.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Api.I.restore();
  runApp(const TalaqqiApp());
}

class TalaqqiApp extends StatelessWidget {
  const TalaqqiApp({super.key});
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'تَلَقِّي',
      debugShowCheckedModeBanner: false,
      theme: T.theme(),
      locale: const Locale('ar'),
      supportedLocales: const [Locale('ar'), Locale('en')],
      localizationsDelegates: const [GlobalMaterialLocalizations.delegate, GlobalWidgetsLocalizations.delegate, GlobalCupertinoLocalizations.delegate],
      builder: (context, child) => Directionality(textDirection: TextDirection.rtl, child: child!),
      home: Api.I.session == null ? const LoginScreen() : const HomeShell(),
    );
  }
}
