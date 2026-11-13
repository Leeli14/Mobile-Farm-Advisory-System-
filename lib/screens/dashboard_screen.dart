import 'dart:async';
import 'package:flutter/material.dart';

import '../services/api_services.dart';

class DashboardScreen extends StatefulWidget {
  DashboardScreen({
    super.key,
    required this.selectedCrop,
    ApiServices? apiServices,
  }) : apiServices = apiServices ?? ApiServices();

  final String selectedCrop;
  final ApiServices apiServices;

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  Map<String, dynamic>? _reading;
  List<Map<String, dynamic>> _history = const [];
  Map<String, dynamic>? _prediction;
  String? _error;
  bool _isRefreshing = false;
  bool _isPredicting = false;
  Timer? _refreshTimer;

  @override
  void initState() {
    super.initState();
    _refresh();
    _refreshTimer = Timer.periodic(
      const Duration(seconds: 20),
      (_) => _refresh(),
    );
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  Future<void> _refresh() async {
    if (_isRefreshing) return;
    setState(() => _isRefreshing = true);
    try {
      final results = await Future.wait([
        widget.apiServices.getLatestReading(),
        widget.apiServices.getRecentReadings(),
      ]);
      if (!mounted) return;
      setState(() {
        _reading = results[0] as Map<String, dynamic>?;
        _history = results[1] as List<Map<String, dynamic>>;
        _error = null;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _isRefreshing = false);
    }
  }

  Future<void> _getPrediction() async {
    final reading = _reading;
    if (reading == null || _isPredicting) return;

    setState(() => _isPredicting = true);
    try {
      final result = await widget.apiServices.getPrediction(
        widget.selectedCrop,
        {
          for (final key in _sensorFields)
            key: reading[key],
        },
      );
      if (mounted) setState(() => _prediction = result);
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Could not get advice: $error')),
      );
    } finally {
      if (mounted) setState(() => _isPredicting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final reading = _reading;
    final readingTime = DateTime.tryParse(reading?['timestamp']?.toString() ?? '');
    final isStale = readingTime == null ||
        DateTime.now().difference(readingTime.toLocal()) >
            const Duration(minutes: 5);

    return Scaffold(
      appBar: AppBar(
        title: Text('${_titleCase(widget.selectedCrop)} advisory'),
        actions: [
          IconButton(
            tooltip: 'Refresh readings',
            onPressed: _isRefreshing ? null : _refresh,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 850),
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              if (_error != null)
                _ErrorBanner(message: _error!, onRetry: _refresh),
              if (reading == null)
                _EmptyReadings(isLoading: _isRefreshing)
              else ...[
                _SensorStatusCard(
                  readingTime: readingTime,
                  isStale: isStale,
                ),
                const SizedBox(height: 12),
                _SensorReadingsCard(reading: reading),
                if (_history.length > 1) ...[
                  const SizedBox(height: 12),
                  _MoistureHistoryCard(readings: _history),
                ],
                const SizedBox(height: 16),
                FilledButton.icon(
                  onPressed: _isPredicting ? null : _getPrediction,
                  icon: _isPredicting
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.eco_outlined),
                  label: Text(
                    _isPredicting ? 'Preparing advice...' : 'Get crop advice',
                  ),
                ),
                if (_prediction != null) ...[
                  const SizedBox(height: 12),
                  _PredictionCard(data: _prediction!),
                ],
              ],
              if (_isRefreshing && reading != null)
                const Padding(
                  padding: EdgeInsets.only(top: 12),
                  child: LinearProgressIndicator(),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

const _sensorFields = [
  'moisture',
  'temperature',
  'ph',
  'ec',
  'nitrogen',
  'phosphorus',
  'potassium',
];

class _SensorReadingsCard extends StatelessWidget {
  const _SensorReadingsCard({required this.reading});

  final Map<String, dynamic> reading;

  @override
  Widget build(BuildContext context) {
    const labels = {
      'moisture': 'Moisture',
      'temperature': 'Temperature',
      'ph': 'Soil pH',
      'ec': 'Electrical conductivity',
      'nitrogen': 'Nitrogen',
      'phosphorus': 'Phosphorus',
      'potassium': 'Potassium',
    };

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Current soil readings',
                style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            ..._sensorFields.map((field) {
              final value = reading[field];
              return ListTile(
                contentPadding: EdgeInsets.zero,
                dense: true,
                leading: const Icon(Icons.science_outlined),
                title: Text(labels[field]!),
                trailing: Text(
                  value == null ? '—' : value.toString(),
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              );
            }),
          ],
        ),
      ),
    );
  }
}

class _SensorStatusCard extends StatelessWidget {
  const _SensorStatusCard({
    required this.readingTime,
    required this.isStale,
  });

  final DateTime? readingTime;
  final bool isStale;

  @override
  Widget build(BuildContext context) {
    final color = isStale ? Colors.orange.shade800 : Colors.green.shade800;
    final updated = readingTime == null
        ? 'Update time unavailable'
        : 'Updated ${readingTime!.toLocal().toString().substring(0, 16)}';
    return Card(
      child: ListTile(
        leading: Icon(
          isStale ? Icons.sensors_off_outlined : Icons.sensors_outlined,
          color: color,
        ),
        title: Text(isStale ? 'Sensor data may be stale' : 'Sensor connected'),
        subtitle: Text(updated),
      ),
    );
  }
}

class _MoistureHistoryCard extends StatelessWidget {
  const _MoistureHistoryCard({required this.readings});

  final List<Map<String, dynamic>> readings;

  @override
  Widget build(BuildContext context) {
    final values = readings.reversed
        .map((reading) => (reading['moisture'] as num).toDouble())
        .toList();
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Recent moisture trend',
                style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 16),
            SizedBox(
              height: 120,
              width: double.infinity,
              child: CustomPaint(
                painter: _TrendPainter(
                  values: values,
                  color: Theme.of(context).colorScheme.primary,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _TrendPainter extends CustomPainter {
  const _TrendPainter({required this.values, required this.color});

  final List<double> values;
  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    if (values.length < 2) return;
    final minValue = values.reduce((a, b) => a < b ? a : b);
    final maxValue = values.reduce((a, b) => a > b ? a : b);
    final range = (maxValue - minValue).abs();
    final line = Paint()
      ..color = color
      ..strokeWidth = 3
      ..strokeCap = StrokeCap.round
      ..style = PaintingStyle.stroke;
    final path = Path();
    for (var index = 0; index < values.length; index++) {
      final x = size.width * index / (values.length - 1);
      final normalized = range == 0 ? 0.5 : (values[index] - minValue) / range;
      final y = size.height * (1 - normalized);
      if (index == 0) {
        path.moveTo(x, y);
      } else {
        path.lineTo(x, y);
      }
    }
    canvas.drawPath(path, line);
  }

  @override
  bool shouldRepaint(covariant _TrendPainter oldDelegate) =>
      oldDelegate.values != values || oldDelegate.color != color;
}

class _PredictionCard extends StatelessWidget {
  const _PredictionCard({required this.data});

  final Map<String, dynamic> data;

  @override
  Widget build(BuildContext context) {
    final fertilization = data['fertilization'];
    final confidence = data['confidence'];
    return Card(
      color: Theme.of(context).colorScheme.primaryContainer,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Crop advice', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 12),
            _AdviceLine(
              title: 'Predicted disease',
              content: data['predicted_disease']?.toString() ?? 'Unavailable',
            ),
            if (confidence is num)
              _AdviceLine(
                title: 'Model confidence',
                content: '${(confidence * 100).toStringAsFixed(1)}%',
              ),
            _AdviceLine(
              title: 'Recommended action',
              content: data['solution']?.toString() ?? 'Unavailable',
            ),
            _AdviceLine(
              title: 'Irrigation',
              content: data['irrigation']?.toString() ?? 'Unavailable',
            ),
            _AdviceLine(
              title: 'Fertilization',
              content: fertilization is List
                  ? fertilization.join('\n')
                  : fertilization?.toString() ?? 'Unavailable',
            ),
          ],
        ),
      ),
    );
  }
}

class _AdviceLine extends StatelessWidget {
  const _AdviceLine({required this.title, required this.content});

  final String title;
  final String content;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: Theme.of(context).textTheme.labelLarge),
          const SizedBox(height: 3),
          Text(content),
        ],
      ),
    );
  }
}

class _EmptyReadings extends StatelessWidget {
  const _EmptyReadings({required this.isLoading});

  final bool isLoading;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 64),
      child: Column(
        children: [
          if (isLoading) const CircularProgressIndicator(),
          if (!isLoading) const Icon(Icons.sensors_off_outlined, size: 44),
          const SizedBox(height: 12),
          Text(isLoading
              ? 'Loading the latest sensor readings...'
              : 'No sensor readings have been received yet.'),
        ],
      ),
    );
  }
}

class _ErrorBanner extends StatelessWidget {
  const _ErrorBanner({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Theme.of(context).colorScheme.errorContainer,
      child: ListTile(
        leading: const Icon(Icons.cloud_off_outlined),
        title: const Text('Could not refresh sensor data'),
        subtitle: Text(message),
        trailing: IconButton(
          tooltip: 'Retry',
          onPressed: onRetry,
          icon: const Icon(Icons.refresh),
        ),
      ),
    );
  }
}

String _titleCase(String value) => value
    .split(' ')
    .map((word) => word.isEmpty
        ? word
        : '${word[0].toUpperCase()}${word.substring(1).toLowerCase()}')
    .join(' ');
