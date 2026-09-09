import 'package:shared_preferences/shared_preferences.dart';

/// Small remembered conveniences: font size, filters, one-time tips. Never anything sensitive.
class Prefs {
  Prefs._();
  static final Prefs I = Prefs._();
  SharedPreferences? _p;

  Future<SharedPreferences> get _sp async => _p ??= await SharedPreferences.getInstance();

  Future<double> fontSize({double fallback = 24}) async => (await _sp).getDouble('ui.font') ?? fallback;
  Future<void> setFontSize(double v) async => (await _sp).setDouble('ui.font', v);

  Future<String?> getString(String key) async => (await _sp).getString(key);
  Future<void> setString(String key, String v) async => (await _sp).setString(key, v);
  Future<void> remove(String key) async => (await _sp).remove(key);

  Future<void> removeWhere(String prefix) async { final p = await _sp; for (final k in p.getKeys().where((k) => k.startsWith(prefix)).toList()) { await p.remove(k); } }

  Future<bool> seen(String key) async => (await _sp).getBool('seen.$key') ?? false;
  Future<void> markSeen(String key) async => (await _sp).setBool('seen.$key', true);

  /// Per app run, not persisted: used to auto-open the single Halaqah only once per launch.
  final Set<String> session = {};
}
