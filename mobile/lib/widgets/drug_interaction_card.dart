import 'package:flutter/material.dart';
import '../theme.dart';
import '../models/drug_interaction.dart';

class DrugInteractionCard extends StatelessWidget {
  final DrugInteraction interaction;

  const DrugInteractionCard({
    super.key,
    required this.interaction,
  });

  @override
  Widget build(BuildContext context) {
    final severityColor = Color(interaction.severity.colorValue);

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: DoraColors.bgPrimary,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: DoraColors.bgTertiary),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Row(
            children: [
              // Severity badge
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: severityColor,
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  interaction.severity.displayName,
                  style: const TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w700,
                    color: Colors.white,
                    letterSpacing: 0.5,
                  ),
                ),
              ),
              const SizedBox(width: 12),
              // Drug names
              Expanded(
                child: Text(
                  '${interaction.drug1} + ${interaction.drug2}',
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w600,
                    color: DoraColors.textPrimary,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // Description
          Text(
            interaction.description,
            style: const TextStyle(
              fontSize: 14,
              color: DoraColors.textPrimary,
              height: 1.4,
            ),
          ),
          const SizedBox(height: 12),

          // Management
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: DoraColors.info.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Icon(
                  Icons.medical_services,
                  size: 16,
                  color: DoraColors.info,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Management',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: DoraColors.info,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        interaction.management,
                        style: const TextStyle(
                          fontSize: 13,
                          color: DoraColors.info,
                          fontStyle: FontStyle.italic,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),

          // Source
          const SizedBox(height: 8),
          Text(
            'Source: ${interaction.source}',
            style: const TextStyle(
              fontSize: 11,
              color: DoraColors.textTertiary,
            ),
          ),
        ],
      ),
    );
  }
}
