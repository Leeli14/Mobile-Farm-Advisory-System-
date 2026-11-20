import 'package:flutter/material.dart';

import 'dashboard_screen.dart';
import '../services/api_services.dart';

class CropSelectionScreen extends StatefulWidget {
  const CropSelectionScreen({super.key, this.apiServices});

  final ApiServices? apiServices;

  @override
  State<CropSelectionScreen> createState() => _CropSelectionScreenState();
}

class _CropSelectionScreenState extends State<CropSelectionScreen> {
  bool _isStartingDemo = false;

  Future<void> _startDemo() async {
    if (_isStartingDemo) return;
    setState(() => _isStartingDemo = true);
    final apiServices = widget.apiServices ?? ApiServices();
    try {
      await apiServices.createDemoReading();
      if (!mounted) return;
      await Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => DashboardScreen(
            selectedCrop: 'tomato',
            apiServices: apiServices,
          ),
        ),
      );
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Could not start demo: $error')),
      );
    } finally {
      if (mounted) setState(() => _isStartingDemo = false);
    }
  }

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
          const SizedBox(height: 16),
          FilledButton.icon(
            onPressed: _isStartingDemo ? null : _startDemo,
            icon: _isStartingDemo
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.play_arrow),
            label: Text(_isStartingDemo ? 'Starting demo...' : 'Start demo'),
          ),
          const SizedBox(height: 8),
          Text(
            'Creates a sample sensor reading and opens the Tomato dashboard.',
            style: Theme.of(context).textTheme.bodySmall,
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