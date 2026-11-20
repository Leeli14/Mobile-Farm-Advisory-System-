import 'package:flutter/foundation.dart';
import 'package:farm/screens/crop_selection_screen.dart';
import 'package:farm/screens/dashboard_screen.dart';
import 'package:farm/services/api_services.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class _EmptyApiServices extends ApiServices {
  @override
  Future<Map<String, dynamic>?> getLatestReading() async => null;

  @override
  Future<List<Map<String, dynamic>>> getRecentReadings({
    int limit = 24,
  }) async => [];
}

class _DemoApiServices extends _EmptyApiServices {
  var createdDemoReadingCount = 0;

  Map<String, dynamic> get _demoReading => {
    'device_id': 'demo-field-1',
    'timestamp': DateTime.now().toUtc().toIso8601String(),
    'moisture': 45.0,
    'temperature': 22.0,
    'ph': 6.5,
    'ec': 350.0,
    'nitrogen': 40.0,
    'phosphorus': 35.0,
    'potassium': 50.0,
  };

  @override
  Future<Map<String, dynamic>?> getLatestReading() async =>
      createdDemoReadingCount > 0 ? _demoReading : null;

  @override
  Future<List<Map<String, dynamic>>> getRecentReadings({
    int limit = 24,
  }) async => createdDemoReadingCount > 0 ? [_demoReading] : [];

  @override
  Future<Map<String, dynamic>> createDemoReading() async {
    createdDemoReadingCount++;
    return _demoReading;
  }
}

void main() {
  test('Android defaults to the PC hotspot API address', () {
    debugDefaultTargetPlatformOverride = TargetPlatform.android;
    addTearDown(() => debugDefaultTargetPlatformOverride = null);

    expect(ApiServices().baseUrl, 'http://192.168.137.1:5000');
  });

  testWidgets('crop selection shows the supported crops', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: CropSelectionScreen()));

    expect(find.text('Choose a crop'), findsOneWidget);
    expect(find.text('Tomato'), findsOneWidget);
    expect(find.text('Potato'), findsOneWidget);
    expect(find.text('Onion'), findsOneWidget);
  });

  testWidgets('start demo creates a reading and opens the dashboard', (
    tester,
  ) async {
    final apiServices = _DemoApiServices();
    await tester.pumpWidget(
      MaterialApp(home: CropSelectionScreen(apiServices: apiServices)),
    );

    await tester.tap(find.text('Start demo'));
    await tester.pumpAndSettle();

    expect(apiServices.createdDemoReadingCount, 1);
    expect(find.text('Tomato advisory'), findsOneWidget);
    expect(find.text('Current soil readings'), findsOneWidget);
  });

  testWidgets('dashboard explains when sensor readings are missing', (
    tester,
  ) async {
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

  testWidgets('dashboard can create another demo reading', (tester) async {
    final apiServices = _DemoApiServices();
    await tester.pumpWidget(
      MaterialApp(
        home: DashboardScreen(selectedCrop: 'tomato', apiServices: apiServices),
      ),
    );

    expect(find.byTooltip('Generate demo reading'), findsOneWidget);
    await tester.tap(find.byTooltip('Generate demo reading'));
    await tester.pumpAndSettle();

    expect(apiServices.createdDemoReadingCount, 1);
    expect(find.text('Demo sensor reading created.'), findsOneWidget);
  });
}
