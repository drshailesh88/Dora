import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../theme.dart';
import '../../providers/calculator_provider.dart';

class CalculatorDetailScreen extends ConsumerStatefulWidget {
  final Map<String, dynamic> calculator;

  const CalculatorDetailScreen({super.key, required this.calculator});

  @override
  ConsumerState<CalculatorDetailScreen> createState() => _CalculatorDetailScreenState();
}

class _CalculatorDetailScreenState extends ConsumerState<CalculatorDetailScreen> {
  final Map<String, dynamic> _inputs = {};
  Map<String, dynamic>? _result;
  bool _calculating = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.calculator['name'] ?? 'Calculator'),
        backgroundColor: DoraColors.bgPrimary,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.info_outline),
            onPressed: _showInfo,
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildDescription(),
            const SizedBox(height: 24),
            _buildInputFields(),
            const SizedBox(height: 24),
            _buildCalculateButton(),
            if (_result != null) ...[
              const SizedBox(height: 24),
              _buildResult(),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildDescription() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: DoraColors.bgSecondary,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            widget.calculator['description'] ?? '',
            style: TextStyle(color: DoraColors.textSecondary),
          ),
          if (widget.calculator['formula'] != null) ...[
            const SizedBox(height: 12),
            Text(
              'Formula:',
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
            ),
            const SizedBox(height: 4),
            Text(
              widget.calculator['formula'],
              style: TextStyle(
                color: DoraColors.textSecondary,
                fontFamily: 'monospace',
                fontSize: 12,
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildInputFields() {
    final fields = widget.calculator['inputs'] as List? ?? [];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Enter Values',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 16),
        ...fields.map((field) => _buildInputField(field)),
      ],
    );
  }

  Widget _buildInputField(Map<String, dynamic> field) {
    final type = field['type'] ?? 'number';
    final id = field['id'] ?? '';
    final label = field['label'] ?? '';
    final unit = field['unit'] ?? '';
    final options = field['options'] as List?;

    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: const TextStyle(fontWeight: FontWeight.w500),
          ),
          const SizedBox(height: 8),
          if (type == 'select' && options != null)
            _buildDropdownField(id, options)
          else if (type == 'boolean')
            _buildSwitchField(id, label)
          else
            _buildTextField(id, unit, field),
        ],
      ),
    );
  }

  Widget _buildTextField(String id, String unit, Map<String, dynamic> field) {
    return TextField(
      keyboardType: const TextInputType.numberWithOptions(decimal: true),
      onChanged: (value) {
        setState(() {
          _inputs[id] = double.tryParse(value) ?? 0;
        });
      },
      decoration: InputDecoration(
        hintText: field['placeholder'] ?? 'Enter value',
        suffixText: unit,
        filled: true,
        fillColor: DoraColors.bgSecondary,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: DoraColors.borderColor),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: DoraColors.borderColor),
        ),
      ),
    );
  }

  Widget _buildDropdownField(String id, List options) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12),
      decoration: BoxDecoration(
        color: DoraColors.bgSecondary,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: DoraColors.borderColor),
      ),
      child: DropdownButton<String>(
        value: _inputs[id]?.toString(),
        isExpanded: true,
        underline: const SizedBox(),
        hint: const Text('Select...'),
        items: options.map((opt) {
          return DropdownMenuItem<String>(
            value: opt['value']?.toString(),
            child: Text(opt['label'] ?? opt['value'].toString()),
          );
        }).toList(),
        onChanged: (value) {
          setState(() => _inputs[id] = value);
        },
      ),
    );
  }

  Widget _buildSwitchField(String id, String label) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label),
        Switch(
          value: _inputs[id] == true,
          activeColor: DoraColors.primary,
          onChanged: (value) {
            setState(() => _inputs[id] = value);
          },
        ),
      ],
    );
  }

  Widget _buildCalculateButton() {
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton(
        onPressed: _calculating ? null : _calculate,
        style: ElevatedButton.styleFrom(
          backgroundColor: DoraColors.primary,
          padding: const EdgeInsets.symmetric(vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
        child: _calculating
            ? const SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  color: Colors.white,
                ),
              )
            : const Text(
                'Calculate',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
      ),
    );
  }

  Future<void> _calculate() async {
    setState(() => _calculating = true);

    try {
      final result = await ref.read(calculateProvider(
        widget.calculator['id'],
        _inputs,
      ).future);

      setState(() => _result = result);
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    } finally {
      setState(() => _calculating = false);
    }
  }

  Widget _buildResult() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: DoraColors.primary.withOpacity(0.1),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: DoraColors.primary.withOpacity(0.3)),
      ),
      child: Column(
        children: [
          Text(
            _result?['primary_value']?.toString() ?? '--',
            style: TextStyle(
              fontSize: 48,
              fontWeight: FontWeight.bold,
              color: DoraColors.primary,
            ),
          ),
          if (_result?['unit'] != null)
            Text(
              _result!['unit'],
              style: TextStyle(
                fontSize: 18,
                color: DoraColors.textSecondary,
              ),
            ),
          const SizedBox(height: 16),
          if (_result?['interpretation'] != null)
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: _getInterpretationColor(_result?['severity']).withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  Icon(
                    _getInterpretationIcon(_result?['severity']),
                    color: _getInterpretationColor(_result?['severity']),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      _result!['interpretation'],
                      style: TextStyle(
                        color: _getInterpretationColor(_result?['severity']),
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          if (_result?['details'] != null) ...[
            const SizedBox(height: 16),
            ...(_result!['details'] as List).map((d) => _buildDetailRow(d)),
          ],
        ],
      ),
    );
  }

  Widget _buildDetailRow(Map<String, dynamic> detail) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            detail['label'] ?? '',
            style: TextStyle(color: DoraColors.textSecondary),
          ),
          Text(
            detail['value']?.toString() ?? '',
            style: const TextStyle(fontWeight: FontWeight.w500),
          ),
        ],
      ),
    );
  }

  Color _getInterpretationColor(String? severity) {
    switch (severity?.toLowerCase()) {
      case 'normal':
        return DoraColors.success;
      case 'mild':
        return Colors.orange;
      case 'moderate':
        return Colors.deepOrange;
      case 'severe':
        return DoraColors.error;
      default:
        return DoraColors.primary;
    }
  }

  IconData _getInterpretationIcon(String? severity) {
    switch (severity?.toLowerCase()) {
      case 'normal':
        return Icons.check_circle;
      case 'mild':
        return Icons.info;
      case 'moderate':
        return Icons.warning;
      case 'severe':
        return Icons.error;
      default:
        return Icons.info;
    }
  }

  void _showInfo() {
    showModalBottomSheet(
      context: context,
      builder: (context) => Container(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              widget.calculator['name'] ?? 'Calculator',
              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            Text(widget.calculator['long_description'] ?? widget.calculator['description'] ?? ''),
            if (widget.calculator['references'] != null) ...[
              const SizedBox(height: 16),
              const Text(
                'References:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              ...((widget.calculator['references'] as List).map(
                (ref) => Text('• $ref', style: const TextStyle(fontSize: 12)),
              )),
            ],
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }
}
