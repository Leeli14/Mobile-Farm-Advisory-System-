import 'package:flutter/material.dart';

import 'dashboard_screen.dart';

class CropSelectionScreen extends StatelessWidget {
  const CropSelectionScreen({super.key});

  @override
  Widget build(BuildContext context) {
    const crops = ["Tomato", "Potato", "Onion"];
    return Scaffold(
      appBar: AppBar(
        title: const Text("Soil Advisor"),
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Text(
            'Choose a crop',
            style: Theme.of(context).textTheme.headlineMedium,
          ),
          const SizedBox(height: 8),
          Text(
            'View soil readings and get advice tailored to your field.',
            style: Theme.of(context).textTheme.bodyLarge,
          ),
          const SizedBox(height: 20),
          ...crops.map(
            (crop) => Card(
              child: ListTile(
                leading: const Icon(Icons.eco_outlined),
                title: Text(crop),
                trailing: const Icon(Icons.arrow_forward_ios, size: 18),
                onTap: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) =>
                          DashboardScreen(selectedCrop: crop.toLowerCase()),
                    ),
                  );
                },
              ),
            ),
          ),
        ],
      ),
    );
  }
}