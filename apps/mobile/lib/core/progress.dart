import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

/// Local-only practice memory: which plan segments the student practiced today and the best self-check score.
/// Never sent to the server — the teacher's Tasmee' is the only record that counts.
class Progress {
  Progress._();
  static final Progress I = Progress._();
  Map<String, dynamic> _data = {};
  bool _loaded = false;

  Future<void> _load() async {
    if (_loaded) return;
    final p = await SharedPreferences.getInstance();
    final raw = p.getString('practice.progress');
    _data = raw == null ? {} : (jsonDecode(raw) as Map<String, dynamic>);
    final today = _day();
    if (_data['day'] != today) _data = <String, dynamic>{'day': today, 'segments': <String, dynamic>{}};
    _loaded = true;
  }

  /// Tolerates whatever shape an older build persisted.
  Map<String, dynamic> get _segments {
    final raw = _data['segments'];
    if (raw is! Map) { _data['segments'] = <String, dynamic>{}; }
    else if (raw is! Map<String, dynamic>) { _data['segments'] = raw.cast<String, dynamic>(); }
    return _data['segments'] as Map<String, dynamic>;
  }

  String _day() => DateTime.now().toIso8601String().substring(0, 10);

  Future<Map<String, dynamic>?> get(String segmentKey) async {
    await _load();
    return (_segments[segmentKey] as Map?)?.cast<String, dynamic>();
  }

  Future<Map<String, dynamic>> all() async {
    await _load();
    return Map<String, dynamic>.from(_segments);
  }

  /// Records a practice pass; keeps the best accuracy of the day.
  Future<void> mark(String segmentKey, {double? accuracy, int hints = 0}) async {
    await _load();
    final segs = _segments;
    final prev = (segs[segmentKey] as Map?)?.cast<String, dynamic>() ?? <String, dynamic>{};
    final best = [(prev['accuracy'] as num?)?.toDouble() ?? -1, accuracy ?? -1].reduce((a, b) => a > b ? a : b);
    segs[segmentKey] = {'practiced': true, 'accuracy': best < 0 ? null : best, 'hints': hints, 'at': DateTime.now().toIso8601String()};
    final p = await SharedPreferences.getInstance();
    await p.setString('practice.progress', jsonEncode(_data));
  }

  static String keyFor(int from, int to) => '$from-$to';
}
