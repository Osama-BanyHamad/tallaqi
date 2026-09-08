import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:talaqqi/features/auth/login_screen.dart';

void main() {
  testWidgets('login screen renders in Arabic', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: Directionality(textDirection: TextDirection.rtl, child: LoginScreen())));
    expect(find.text('تسجيل الدخول'), findsOneWidget);
  });
}
