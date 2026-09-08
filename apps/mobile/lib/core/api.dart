import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

/// API base. Override at build time: flutter run --dart-define=API_URL=https://tallaqi.com
const apiUrl = String.fromEnvironment('API_URL', defaultValue: 'http://localhost:8000');

class ApiException implements Exception {
  ApiException(this.status, this.code, this.message);
  final int status;
  final String code;
  final String message;
  @override
  String toString() => message;
}

class Session {
  Session({required this.access, required this.refresh, required this.tenant, required this.fullName, required this.email});
  String access;
  String refresh;
  final String tenant;
  final String fullName;
  final String email;

  Map<String, dynamic> toJson() => {'access': access, 'refresh': refresh, 'tenant': tenant, 'fullName': fullName, 'email': email};
  static Session fromJson(Map<String, dynamic> j) =>
      Session(access: j['access'], refresh: j['refresh'], tenant: j['tenant'], fullName: j['fullName'] ?? '', email: j['email'] ?? '');
}

class Api {
  Api._();
  static final Api I = Api._();
  Session? session;
  Map<String, dynamic>? capabilities;

  Future<void> restore() async {
    final p = await SharedPreferences.getInstance();
    final raw = p.getString('session');
    if (raw != null) session = Session.fromJson(jsonDecode(raw));
  }

  Future<void> _persist() async {
    final p = await SharedPreferences.getInstance();
    if (session == null) {
      await p.remove('session');
    } else {
      await p.setString('session', jsonEncode(session!.toJson()));
    }
  }

  Future<void> logout() async {
    session = null;
    capabilities = null;
    await _persist();
  }

  Future<Session> login(String email, String password) async {
    final r = await http.post(Uri.parse('$apiUrl/api/v1/auth/login'),
        headers: {'Content-Type': 'application/json', 'Accept-Language': 'ar'}, body: jsonEncode({'email': email, 'password': password}));
    final j = jsonDecode(utf8.decode(r.bodyBytes)) as Map<String, dynamic>;
    if (r.statusCode != 200) throw ApiException(r.statusCode, j['code'] ?? 'error', j['detail'] ?? 'تعذّر تسجيل الدخول');
    final ms = (j['memberships'] as List?) ?? [];
    session = Session(access: j['access'], refresh: j['refresh'], tenant: ms.isNotEmpty ? ms.first['tenant_slug'] : '',
        fullName: j['account']?['full_name'] ?? '', email: j['account']?['email'] ?? email);
    await _persist();
    capabilities = await get('/me/capabilities');
    return session!;
  }

  Future<bool> _refresh() async {
    final s = session;
    if (s == null) return false;
    final r = await http.post(Uri.parse('$apiUrl/api/v1/auth/refresh'), headers: {'Content-Type': 'application/json'}, body: jsonEncode({'refresh': s.refresh}));
    if (r.statusCode != 200) return false;
    final j = jsonDecode(r.body);
    s.access = j['access'];
    if (j['refresh'] != null) s.refresh = j['refresh'];
    await _persist();
    return true;
  }

  Map<String, String> _headers({bool json = false}) => {
        'Accept': 'application/json',
        'Accept-Language': 'ar',
        if (json) 'Content-Type': 'application/json',
        if (session != null) 'Authorization': 'Bearer ${session!.access}',
        if (session != null && session!.tenant.isNotEmpty) 'X-Tenant': session!.tenant,
      };

  Future<dynamic> _send(Future<http.Response> Function() call, {bool retry = true}) async {
    final r = await call();
    if (r.statusCode == 401 && retry && await _refresh()) return _send(call, retry: false);
    final body = r.bodyBytes.isEmpty ? null : jsonDecode(utf8.decode(r.bodyBytes));
    if (r.statusCode >= 400) {
      final m = body is Map ? body : {};
      throw ApiException(r.statusCode, m['code']?.toString() ?? 'error', m['detail']?.toString() ?? 'خطأ ${r.statusCode}');
    }
    return body;
  }

  Future<dynamic> get(String path) => _send(() => http.get(Uri.parse('$apiUrl/api/v1$path'), headers: _headers()));
  Future<dynamic> post(String path, Map<String, dynamic> body) =>
      _send(() => http.post(Uri.parse('$apiUrl/api/v1$path'), headers: _headers(json: true), body: jsonEncode(body)));

  Future<Map<String, dynamic>> caps() async => capabilities ??= (await get('/me/capabilities')) as Map<String, dynamic>;
  List<String> get roles => List<String>.from(capabilities?['roles'] ?? const []);
  bool can(String p) => (capabilities?['permissions'] as List?)?.contains(p) ?? false;
}
