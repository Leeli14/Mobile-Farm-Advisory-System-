import 'package:flutter/material.dart';

import 'screens/crop_selection_screen.dart';

void main() {
  runApp(const SoilAdvisorApp());
}

class SoilAdvisorApp extends StatelessWidget {
  const SoilAdvisorApp({super.key});

  @override
  Widget build(BuildContext context) {
    const green = Color(0xFF2E7D32);

    return MaterialApp(
      title: 'Soil Advisor',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: green,
          brightness: Brightness.light,
        ),
        useMaterial3: true,
        scaffoldBackgroundColor: const Color(0xFFF5F7F2),
      ),
      home: const CropSelectionScreen(),
    );
  }
}
