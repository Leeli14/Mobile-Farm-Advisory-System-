import 'package:farm/screens/crop_selection_screen.dart';
import 'package:farm/screens/dashboard_screen.dart';
import 'package:farm/services/api_services.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class _EmptyApiServices extends ApiServices {
  @override
  Future<Map<String, dynamic>?> getLatestReading() async => null;

  @override
  Future<List<Map<String, dynamic>>> getRecentReadings({int limit = 24}) async =>
      [];
}

void main() {
  testWidgets('crop selection shows the supported crops', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(home: CropSelectionScreen()),
    );

    expect(find.text('Choose a crop'), findsOneWidget);
    expect(find.text('Tomato'), findsOneWidget);
    expect(find.text('Potato'), findsOneWidget);
    expect(find.text('Onion'), findsOneWidget);
  });

  testWidgets('dashboard explains when sensor readings are missing',
      (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: DashboardScreen(
          selectedCrop: 'tomato',
          apiServices: _EmptyApiServices(),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(
      find.text('No sensor readings have been received yet.'),
      findsOneWidget,
    );
  });
}
