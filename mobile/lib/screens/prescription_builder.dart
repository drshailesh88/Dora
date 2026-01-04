import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class PrescriptionBuilderScreen extends StatefulWidget {
  const PrescriptionBuilderScreen({Key? key}) : super(key: key);

  @override
  State<PrescriptionBuilderScreen> createState() =>
      _PrescriptionBuilderScreenState();
}

class _PrescriptionBuilderScreenState extends State<PrescriptionBuilderScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final TextEditingController _doraAnswerController = TextEditingController();

  List<PrescriptionItem> _extractedItems = [];
  List<ValidationWarning> _validationWarnings = [];
  List<DrugAlternative> _alternatives = [];
  String _preview = '';
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    _doraAnswerController.dispose();
    super.dispose();
  }

  Future<void> _extractFromDora() async {
    setState(() => _loading = true);

    try {
      final response = await http.post(
        Uri.parse('https://api.dora.com/api/prescription/extract'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'answer_text': _doraAnswerController.text,
          'dora_answer_id': 'DORA-${DateTime.now().millisecondsSinceEpoch}',
          'patient': {
            'patient_id': 'PAT-001',
            'name': 'Sample Patient',
            'age': 45,
            'gender': 'M',
            'known_allergies': [],
          },
          'doctor': {
            'doctor_id': 'DOC-001',
            'name': 'Dr. Sample',
            'qualifications': 'MD, MBBS',
            'registration_number': 'REG-001',
          },
          'use_llm': false,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);

        if (data['success']) {
          setState(() {
            _extractedItems = (data['prescription']?['items'] as List?)
                    ?.map((item) => PrescriptionItem.fromJson(item))
                    .toList() ??
                [];
            _preview = data['preview'] ?? '';
            _alternatives = (data['alternatives'] as List?)
                    ?.map((alt) => DrugAlternative.fromJson(alt))
                    .toList() ??
                [];

            // Parse validation warnings
            _validationWarnings = [];
            if (data['validation']?['errors'] != null) {
              for (var err in data['validation']['errors']) {
                _validationWarnings
                    .add(ValidationWarning('error', err.toString()));
              }
            }
            if (data['validation']?['warnings'] != null) {
              for (var warn in data['validation']['warnings']) {
                _validationWarnings
                    .add(ValidationWarning('warning', warn.toString()));
              }
            }
          });

          _tabController.animateTo(2); // Switch to preview tab
        }
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: ${e.toString()}')),
      );
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Prescription Builder'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(icon: Icon(Icons.auto_awesome), text: 'Extract'),
            Tab(icon: Icon(Icons.medication), text: 'Manual'),
            Tab(icon: Icon(Icons.preview), text: 'Preview'),
            Tab(icon: Icon(Icons.money_off), text: 'Savings'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildExtractTab(),
          _buildManualTab(),
          _buildPreviewTab(),
          _buildAlternativesTab(),
        ],
      ),
    );
  }

  Widget _buildExtractTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: const [
                      Icon(Icons.auto_awesome, color: Colors.purple),
                      SizedBox(width: 8),
                      Text(
                        'AI-Powered Extraction',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Paste Dora\'s answer to automatically extract prescription',
                    style: TextStyle(color: Colors.grey),
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: _doraAnswerController,
                    maxLines: 10,
                    decoration: const InputDecoration(
                      border: OutlineInputBorder(),
                      hintText:
                          'Paste Dora\'s medical recommendation here...\n\nExample:\n1. Tab. Metformin 500mg - 1-0-1 x 30 days\n2. Tab. Amlodipine 5mg - 0-0-1 x 30 days',
                    ),
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: _loading ? null : _extractFromDora,
                    style: ElevatedButton.styleFrom(
                      minimumSize: const Size.fromHeight(50),
                    ),
                    child: _loading
                        ? const CircularProgressIndicator()
                        : const Text('Extract Prescription'),
                  ),
                ],
              ),
            ),
          ),
          if (_extractedItems.isNotEmpty) ...[
            const SizedBox(height: 16),
            Text(
              'Extracted Medications (${_extractedItems.length})',
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            ..._extractedItems.map((item) => Card(
                  margin: const EdgeInsets.only(bottom: 8),
                  child: ListTile(
                    leading: const Icon(Icons.medication),
                    title: Text('${item.drugName} ${item.strength}'),
                    subtitle: Text(
                        '${item.frequency} × ${item.durationDays} days\nQty: ${item.quantity}'),
                    trailing: item.confidenceScore != null
                        ? Chip(
                            label: Text(
                                '${(item.confidenceScore! * 100).round()}%'),
                          )
                        : null,
                  ),
                )),
          ],
        ],
      ),
    );
  }

  Widget _buildManualTab() {
    return const Center(
      child: Text('Manual entry coming soon...'),
    );
  }

  Widget _buildPreviewTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (_validationWarnings.isNotEmpty) ...[
            ..._validationWarnings.map((warning) => Card(
                  color: warning.type == 'error'
                      ? Colors.red.shade50
                      : Colors.orange.shade50,
                  child: ListTile(
                    leading: Icon(
                      warning.type == 'error'
                          ? Icons.error
                          : Icons.warning,
                      color: warning.type == 'error'
                          ? Colors.red
                          : Colors.orange,
                    ),
                    title: Text(warning.message),
                  ),
                )),
            const SizedBox(height: 16),
          ],
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Prescription Preview',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 16),
                  if (_preview.isNotEmpty)
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.grey.shade100,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        _preview,
                        style: const TextStyle(fontFamily: 'monospace'),
                      ),
                    )
                  else
                    const Text(
                      'No prescription to preview. Extract from Dora answer first.',
                      style: TextStyle(color: Colors.grey),
                    ),
                ],
              ),
            ),
          ),
          if (_preview.isNotEmpty) ...[
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () {},
                    icon: const Icon(Icons.download),
                    label: const Text('PDF'),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () {},
                    icon: const Icon(Icons.send),
                    label: const Text('Pharmacy'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            ElevatedButton.icon(
              onPressed: () {},
              icon: const Icon(Icons.check_circle),
              label: const Text('Sign & Save'),
              style: ElevatedButton.styleFrom(
                minimumSize: const Size.fromHeight(50),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildAlternativesTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: const [
              Icon(Icons.money_off, color: Colors.green),
              SizedBox(width: 8),
              Text(
                'Cost-Saving Alternatives',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          const Text(
            'Generic equivalents and therapeutic alternatives',
            style: TextStyle(color: Colors.grey),
          ),
          const SizedBox(height: 16),
          if (_alternatives.isNotEmpty)
            ..._alternatives.map((alt) => Card(
                  margin: const EdgeInsets.only(bottom: 8),
                  child: ListTile(
                    leading: const Icon(Icons.savings, color: Colors.green),
                    title: Text(alt.alternativeDrug),
                    subtitle: Text(alt.reasonForSuggestion),
                    trailing: Chip(
                      label: Text('₹${alt.savingsPerMonth}/mo'),
                      backgroundColor: Colors.green.shade50,
                    ),
                  ),
                ))
          else
            const Center(
              child: Text(
                'No alternatives available. Extract prescription first.',
                style: TextStyle(color: Colors.grey),
              ),
            ),
        ],
      ),
    );
  }
}

// Models

class PrescriptionItem {
  final String drugName;
  final String strength;
  final String dosageForm;
  final String frequency;
  final int durationDays;
  final int quantity;
  final String? instructions;
  final double? confidenceScore;

  PrescriptionItem({
    required this.drugName,
    required this.strength,
    required this.dosageForm,
    required this.frequency,
    required this.durationDays,
    required this.quantity,
    this.instructions,
    this.confidenceScore,
  });

  factory PrescriptionItem.fromJson(Map<String, dynamic> json) {
    return PrescriptionItem(
      drugName: json['drug_name'] ?? '',
      strength: json['strength'] ?? '',
      dosageForm: json['dosage_form'] ?? '',
      frequency: json['dosage']?['frequency'] ?? '',
      durationDays: json['dosage']?['duration_days'] ?? 0,
      quantity: json['quantity'] ?? 0,
      instructions: json['instructions'],
      confidenceScore: json['confidence_score']?.toDouble(),
    );
  }
}

class ValidationWarning {
  final String type;
  final String message;

  ValidationWarning(this.type, this.message);
}

class DrugAlternative {
  final String alternativeDrug;
  final double savingsPerMonth;
  final String reasonForSuggestion;

  DrugAlternative({
    required this.alternativeDrug,
    required this.savingsPerMonth,
    required this.reasonForSuggestion,
  });

  factory DrugAlternative.fromJson(Map<String, dynamic> json) {
    return DrugAlternative(
      alternativeDrug: json['alternative_drug'] ?? '',
      savingsPerMonth: (json['savings_per_month'] ?? 0).toDouble(),
      reasonForSuggestion: json['reason_for_suggestion'] ?? '',
    );
  }
}
