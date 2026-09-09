import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_timezone/flutter_timezone.dart';
import 'package:timezone/data/latest_all.dart' as tzdata;
import 'package:timezone/timezone.dart' as tz;

import 'prefs.dart';

/// Local reminders (no push service, nothing leaves the device):
///  • daily wird reminder, • daily plan reminder for learners, • Halaqah reminder for teachers.
/// Each reminder is a repeating daily notification at a time the user picks; the schedule survives reboot.
class Notify {
  Notify._();
  static final Notify I = Notify._();
  final _plugin = FlutterLocalNotificationsPlugin();
  bool _ready = false;

  static const kinds = {
    'wird': (id: 101, title: 'وردك اليومي', body: 'حان وقت قراءة وردك من المصحف. صفحاتك جاهزة في تَلَقِّي.'),
    'plan': (id: 102, title: 'خطة اليوم', body: 'مقاطع اليوم بانتظارك: حفظ جديد ومراجعة قريبة وبعيدة.'),
    'halaqah': (id: 103, title: 'حلقتك اليوم', body: 'افتح حلقة اليوم لتسجيل الحضور والتسميع.'),
  };

  Future<bool> init() async {
    if (_ready) return true;
    if (kIsWeb) return false;
    tzdata.initializeTimeZones();
    try {
      final name = await FlutterTimezone.getLocalTimezone();
      tz.setLocalLocation(tz.getLocation(name.identifier));
    } catch (_) {
      // fall back to UTC-based local; still schedules correctly relative to device time in most cases
    }
    const android = AndroidInitializationSettings('@mipmap/ic_launcher');
    const ios = DarwinInitializationSettings();
    await _plugin.initialize(settings: const InitializationSettings(android: android, iOS: ios));
    _ready = true;
    return true;
  }

  Future<bool> requestPermission() async {
    if (!await init()) return false;
    final a = _plugin.resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>();
    if (a != null) {
      final ok = await a.requestNotificationsPermission();
      return ok ?? true;
    }
    final i = _plugin.resolvePlatformSpecificImplementation<IOSFlutterLocalNotificationsPlugin>();
    if (i != null) return (await i.requestPermissions(alert: true, badge: true, sound: true)) ?? true;
    return true;
  }

  /// Schedules (or reschedules) a daily reminder and remembers the time.
  Future<bool> scheduleDaily(String kind, TimeOfDay at) async {
    final k = kinds[kind]!;
    if (!await requestPermission()) return false;
    await _plugin.cancel(id: k.id);
    final now = tz.TZDateTime.now(tz.local);
    var when = tz.TZDateTime(tz.local, now.year, now.month, now.day, at.hour, at.minute);
    if (when.isBefore(now)) when = when.add(const Duration(days: 1));
    await _plugin.zonedSchedule(
      id: k.id, title: k.title, body: k.body, scheduledDate: when,
      notificationDetails: const NotificationDetails(
        android: AndroidNotificationDetails('talaqqi_reminders', 'تذكيرات تَلَقِّي', channelDescription: 'الورد اليومي وخطة اليوم والحلقة', importance: Importance.high, priority: Priority.high),
        iOS: DarwinNotificationDetails(),
      ),
      androidScheduleMode: AndroidScheduleMode.inexactAllowWhileIdle,
      matchDateTimeComponents: DateTimeComponents.time,
    );
    await Prefs.I.setString('notify.$kind', '${at.hour.toString().padLeft(2, '0')}:${at.minute.toString().padLeft(2, '0')}');
    return true;
  }

  Future<void> cancel(String kind) async {
    if (!await init()) return;
    await _plugin.cancel(id: kinds[kind]!.id);
    await Prefs.I.remove('notify.$kind');
  }

  Future<TimeOfDay?> timeFor(String kind) async {
    final v = await Prefs.I.getString('notify.$kind');
    if (v == null) return null;
    final p = v.split(':');
    return TimeOfDay(hour: int.parse(p[0]), minute: int.parse(p[1]));
  }

  /// Re-arms everything that was set (call at app start; harmless if nothing is set).
  Future<void> rearm() async {
    if (kIsWeb) return;
    for (final kind in kinds.keys) {
      final t = await timeFor(kind);
      if (t != null) {
        try { await scheduleDaily(kind, t); } catch (_) {}
      }
    }
  }
}
