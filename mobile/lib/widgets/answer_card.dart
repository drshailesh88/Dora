import 'package:flutter/material.dart';
import '../theme.dart';
import '../models/medical_answer.dart';

class AnswerCard extends StatelessWidget {
  final MedicalAnswer answer;

  const AnswerCard({
    super.key,
    required this.answer,
  });

  @override
  Widget build(BuildContext context) {
    final confidenceColor = _getConfidenceColor(answer.confidenceLevel);

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: DoraColors.bgPrimary,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Question
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Icon(
                Icons.help_outline,
                size: 18,
                color: DoraColors.textSecondary,
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  answer.question,
                  style: const TextStyle(
                    fontSize: 14,
                    fontStyle: FontStyle.italic,
                    color: DoraColors.textSecondary,
                  ),
                ),
              ),
            ],
          ),
          const Divider(height: 24),

          // Confidence badge
          Align(
            alignment: Alignment.centerRight,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: confidenceColor.withOpacity(0.1),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    Icons.verified,
                    size: 14,
                    color: confidenceColor,
                  ),
                  const SizedBox(width: 4),
                  Text(
                    '${answer.confidence.toUpperCase()} CONFIDENCE',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      color: confidenceColor,
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),

          // Warnings
          if (answer.warnings.isNotEmpty) ...[
            Container(
              padding: const EdgeInsets.all(12),
              margin: const EdgeInsets.only(bottom: 12),
              decoration: BoxDecoration(
                color: DoraColors.warning.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                children: answer.warnings.map((w) {
                  return Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(
                        Icons.warning_amber,
                        size: 16,
                        color: DoraColors.warning,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          w,
                          style: const TextStyle(
                            fontSize: 13,
                            color: DoraColors.textPrimary,
                          ),
                        ),
                      ),
                    ],
                  );
                }).toList(),
              ),
            ),
          ],

          // Answer
          SelectableText(
            answer.answer,
            style: const TextStyle(
              fontSize: 15,
              height: 1.5,
              color: DoraColors.textPrimary,
            ),
          ),

          // Citations
          if (answer.citations.isNotEmpty) ...[
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.only(top: 16),
              decoration: const BoxDecoration(
                border: Border(
                  top: BorderSide(color: DoraColors.bgTertiary),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'SOURCES',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      color: DoraColors.textTertiary,
                      letterSpacing: 0.5,
                    ),
                  ),
                  const SizedBox(height: 8),
                  ...answer.citations.take(5).toList().asMap().entries.map((e) {
                    final index = e.key;
                    final citation = e.value;
                    return Padding(
                      padding: const EdgeInsets.symmetric(vertical: 4),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Container(
                            width: 20,
                            height: 20,
                            alignment: Alignment.center,
                            decoration: BoxDecoration(
                              color: DoraColors.primary.withOpacity(0.1),
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: Text(
                              '${index + 1}',
                              style: const TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.bold,
                                color: DoraColors.primary,
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  citation.title,
                                  style: const TextStyle(
                                    fontSize: 13,
                                    fontWeight: FontWeight.w500,
                                  ),
                                ),
                                Text(
                                  citation.source,
                                  style: const TextStyle(
                                    fontSize: 12,
                                    color: DoraColors.textSecondary,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    );
                  }),
                ],
              ),
            ),
          ],

          // Footer
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              Text(
                '${answer.latencyMs}ms',
                style: const TextStyle(
                  fontSize: 11,
                  color: DoraColors.textTertiary,
                ),
              ),
              const SizedBox(width: 8),
              Text(
                answer.modelUsed,
                style: const TextStyle(
                  fontSize: 11,
                  color: DoraColors.textTertiary,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Color _getConfidenceColor(ConfidenceLevel level) {
    switch (level) {
      case ConfidenceLevel.high:
        return DoraColors.success;
      case ConfidenceLevel.medium:
        return DoraColors.warning;
      case ConfidenceLevel.low:
        return DoraColors.error;
      case ConfidenceLevel.unknown:
        return DoraColors.textTertiary;
    }
  }
}
