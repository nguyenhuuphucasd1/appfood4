import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:vi_viet/models/user_profile.dart';
import 'package:vi_viet/screens/profile_screen.dart';
import 'package:vi_viet/services/api_client.dart';
import 'package:vi_viet/state/app_state.dart';

http.Response jsonResponse(Object body, [int status = 200]) => http.Response(
  jsonEncode(body),
  status,
  headers: {'content-type': 'application/json; charset=utf-8'},
);

AppState signedInState(http.Client client) =>
    AppState(api: ApiClient(client: client))
      ..user = const UserProfile(
        id: 1,
        email: 'user@example.com',
        fullName: 'Tên ban đầu',
      );

Widget profileHarness(AppState state) => MaterialApp(
  home: Scaffold(
    body: AppStateScope(state: state, child: const ProfileScreen()),
  ),
);

Future<void> openNameDialog(WidgetTester tester) async {
  await tester.tap(find.text('Chỉnh sửa tên'));
  await tester.pumpAndSettle();
  expect(find.byKey(const Key('edit-name-field')), findsOneWidget);
}

void main() {
  testWidgets('validates the trimmed name inside the dialog', (tester) async {
    final state = signedInState(MockClient((_) async => jsonResponse({})));
    await tester.pumpWidget(profileHarness(state));
    await openNameDialog(tester);

    await tester.enterText(find.byKey(const Key('edit-name-field')), ' ');
    await tester.tap(find.byKey(const Key('edit-name-save')));
    await tester.pump();
    expect(find.text('Vui lòng nhập họ và tên.'), findsOneWidget);

    await tester.enterText(find.byKey(const Key('edit-name-field')), 'A');
    await tester.tap(find.byKey(const Key('edit-name-save')));
    await tester.pump();
    expect(find.text('Tên phải có ít nhất 2 ký tự.'), findsOneWidget);
    expect(find.byType(AlertDialog), findsOneWidget);
  });

  testWidgets('keeps input and shows API errors in the dialog', (tester) async {
    final state = signedInState(
      MockClient(
        (_) async => jsonResponse({'detail': 'Máy chủ đang bận.'}, 503),
      ),
    );
    await tester.pumpWidget(profileHarness(state));
    await openNameDialog(tester);

    await tester.enterText(
      find.byKey(const Key('edit-name-field')),
      'Tên vẫn còn',
    );
    await tester.tap(find.byKey(const Key('edit-name-save')));
    await tester.pumpAndSettle();

    expect(find.text('Máy chủ đang bận.'), findsOneWidget);
    expect(find.text('Tên vẫn còn'), findsOneWidget);
    expect(find.byType(AlertDialog), findsOneWidget);
  });

  testWidgets('submits once, trims the name, and closes after success', (
    tester,
  ) async {
    final response = Completer<http.Response>();
    var calls = 0;
    String? sentName;
    final state = signedInState(
      MockClient((request) async {
        calls++;
        sentName =
            (jsonDecode(request.body) as Map<String, dynamic>)['fullName']
                as String?;
        return response.future;
      }),
    );
    await tester.pumpWidget(profileHarness(state));
    await openNameDialog(tester);

    await tester.enterText(
      find.byKey(const Key('edit-name-field')),
      '  Nguyễn An  ',
    );
    await tester.tap(find.byKey(const Key('edit-name-save')));
    await tester.pump();
    await tester.tap(find.byKey(const Key('edit-name-save')));
    await tester.pump();
    expect(calls, 1);

    response.complete(
      jsonResponse({
        'id': 1,
        'email': 'user@example.com',
        'fullName': 'Nguyễn An',
      }),
    );
    await tester.pumpAndSettle();

    expect(sentName, 'Nguyễn An');
    expect(calls, 1);
    expect(find.byType(AlertDialog), findsNothing);
    expect(find.text('Nguyễn An'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'Done saves while the keyboard is open without framework errors',
    (tester) async {
      final state = signedInState(
        MockClient(
          (_) async => jsonResponse({
            'id': 1,
            'email': 'user@example.com',
            'fullName': 'Tên mới',
          }),
        ),
      );
      await tester.pumpWidget(profileHarness(state));
      await openNameDialog(tester);
      await tester.enterText(
        find.byKey(const Key('edit-name-field')),
        'Tên mới',
      );

      await tester.testTextInput.receiveAction(TextInputAction.done);
      await tester.pumpAndSettle();

      expect(find.byType(AlertDialog), findsNothing);
      expect(find.text('Tên mới'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
}
