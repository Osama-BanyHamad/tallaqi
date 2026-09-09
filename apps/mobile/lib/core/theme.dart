import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Design tokens shared with the web app (المَتْن والحاشية): paper ground, night bars, lapis voice, one gold hairline.
class T {
  static const ground = Color(0xFFF3F2EE);
  static const ground2 = Color(0xFFEBE9E2);
  static const surface = Color(0xFFFFFFFF);
  static const paper = Color(0xFFFBF8F0);
  static const ink = Color(0xFF101320);
  static const ink2 = Color(0xFF474B58);
  static const ink3 = Color(0xFF868A96);
  static const rule = Color(0xFFE5E3DC);
  static const lapis = Color(0xFF1B2C74);
  static const lapis2 = Color(0xFF2A3F95);
  static const lapisTint = Color(0xFFE9ECF8);
  static const gold = Color(0xFFB99441);
  static const gold2 = Color(0xFFD4B56A);
  static const goldTint = Color(0xFFF6EEDA);
  static const night = Color(0xFF0D1230);
  static const night2 = Color(0xFF182253);
  static const nightInk = Color(0xFFEEEADF);
  static const nightMuted = Color(0xFF8F97C4);

  static const sNone = Color(0xFFE4E1D7);
  static const sLearning = Color(0xFFCFC9B5);
  static const sRecent = Color(0xFF3C9AA2);
  static const sStrong = Color(0xFF2F7A5B);
  static const sMastered = Color(0xFF1B2C74);
  static const sNeeds = Color(0xFFD19A2B);
  static const sWeak = Color(0xFFC2582E);
  static const sCritical = Color(0xFF8A1F2B);

  static Color state(String s) => switch (s) {
        'mastered' => sMastered,
        'strong' => sStrong,
        'recent' => sRecent,
        'needs_revision' => sNeeds,
        'weak' => sWeak,
        'critical' => sCritical,
        'learning' => sLearning,
        _ => sNone,
      };

  /// The word people understand before the percent.
  static String stateWord(double? v) {
    final p = ((v ?? 0) * 100).round();
    return p >= 95 ? 'متقن' : p >= 85 ? 'متين' : p >= 60 ? 'يحتاج مراجعة' : p >= 35 ? 'ضعيف' : 'حرج';
  }

  static Color retention(double? v) {
    final p = ((v ?? 0) * 100).round();
    return p >= 85 ? sStrong : p >= 60 ? sNeeds : p >= 35 ? sWeak : sCritical;
  }

  static TextStyle display({double size = 26, Color color = ink, FontWeight weight = FontWeight.w700}) =>
      GoogleFonts.notoKufiArabic(fontSize: size, fontWeight: weight, color: color, height: 1.3);
  static TextStyle body({double size = 15, Color color = ink, FontWeight weight = FontWeight.w400}) =>
      GoogleFonts.ibmPlexSansArabic(fontSize: size, fontWeight: weight, color: color, height: 1.6);
  static TextStyle quran({double size = 26, Color color = ink}) =>
      GoogleFonts.amiriQuran(fontSize: size, color: color, height: 2.1);
  static TextStyle mono({double size = 12, Color color = ink3}) =>
      GoogleFonts.ibmPlexMono(fontSize: size, color: color, fontFeatures: const [FontFeature.tabularFigures()]);

  static ThemeData theme() {
    final base = ThemeData(useMaterial3: true, colorSchemeSeed: lapis, brightness: Brightness.light);
    return base.copyWith(
      scaffoldBackgroundColor: ground,
      colorScheme: base.colorScheme.copyWith(primary: lapis, secondary: gold, surface: surface, onSurface: ink),
      textTheme: GoogleFonts.ibmPlexSansArabicTextTheme(base.textTheme).apply(bodyColor: ink, displayColor: ink),
      appBarTheme: AppBarTheme(backgroundColor: night, foregroundColor: nightInk, elevation: 0, centerTitle: false,
          titleTextStyle: GoogleFonts.notoKufiArabic(fontSize: 18, fontWeight: FontWeight.w700, color: nightInk)),
      cardTheme: CardThemeData(color: surface, elevation: 0, margin: EdgeInsets.zero,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12), side: const BorderSide(color: rule))),
      filledButtonTheme: FilledButtonThemeData(style: FilledButton.styleFrom(backgroundColor: lapis, foregroundColor: Colors.white,
          minimumSize: const Size.fromHeight(48), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          textStyle: GoogleFonts.ibmPlexSansArabic(fontSize: 15, fontWeight: FontWeight.w600))),
      outlinedButtonTheme: OutlinedButtonThemeData(style: OutlinedButton.styleFrom(foregroundColor: ink, side: const BorderSide(color: rule),
          minimumSize: const Size.fromHeight(44), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)))),
      inputDecorationTheme: InputDecorationTheme(filled: true, fillColor: surface,
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: rule)),
          enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: rule)),
          focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: lapis, width: 1.5))),
      navigationBarTheme: NavigationBarThemeData(backgroundColor: surface, indicatorColor: lapisTint, height: 68,
          labelTextStyle: WidgetStatePropertyAll(GoogleFonts.ibmPlexSansArabic(fontSize: 12, fontWeight: FontWeight.w600))),
      dividerColor: rule,
    );
  }
}

String arDigits(Object n) => '$n'.replaceAllMapped(RegExp(r'\d'), (m) => '٠١٢٣٤٥٦٧٨٩'[int.parse(m[0]!)]);
String pct(double? v) => v == null ? '—' : '${arDigits((v * 100).round())}٪';
