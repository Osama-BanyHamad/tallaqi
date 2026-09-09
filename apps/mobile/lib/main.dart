import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_native_splash/flutter_native_splash.dart';

import 'core/api.dart';
import 'core/notify.dart';
import 'core/theme.dart';
import 'features/auth/login_screen.dart';
import 'features/home/home_shell.dart';

Future<void> main() async {
  final binding = WidgetsFlutterBinding.ensureInitialized();
  FlutterNativeSplash.preserve(widgetsBinding: binding);
  await Api.I.restore();
  runApp(const TalaqqiApp());
  Notify.I.rearm();
  // The native splash stays until the first frame of the real app is ready, then fades.
  WidgetsBinding.instance.addPostFrameCallback((_) => FlutterNativeSplash.remove());
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
