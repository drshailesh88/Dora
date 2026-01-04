/// Drug interaction result model
class DrugInteractionResult {
  final bool success;
  final List<DrugInteraction> interactions;
  final List<String> warnings;
  final String? error;

  DrugInteractionResult({
    required this.success,
    required this.interactions,
    required this.warnings,
    this.error,
  });

  factory DrugInteractionResult.fromJson(Map<String, dynamic> json) {
    return DrugInteractionResult(
      success: json['success'] ?? false,
      interactions: (json['interactions'] as List<dynamic>?)
              ?.map((i) => DrugInteraction.fromJson(i))
              .toList() ??
          [],
      warnings: (json['warnings'] as List<dynamic>?)
              ?.map((w) => w.toString())
              .toList() ??
          [],
      error: json['error'],
    );
  }

  bool get hasInteractions => interactions.isNotEmpty;
  bool get hasSevereInteractions =>
      interactions.any((i) => i.severity == InteractionSeverity.severe ||
          i.severity == InteractionSeverity.contraindicated);
}

/// Drug interaction model
class DrugInteraction {
  final String drug1;
  final String drug2;
  final InteractionSeverity severity;
  final String description;
  final String management;
  final String source;

  DrugInteraction({
    required this.drug1,
    required this.drug2,
    required this.severity,
    required this.description,
    required this.management,
    required this.source,
  });

  factory DrugInteraction.fromJson(Map<String, dynamic> json) {
    return DrugInteraction(
      drug1: json['drug1'] ?? '',
      drug2: json['drug2'] ?? '',
      severity: InteractionSeverity.fromString(json['severity'] ?? 'unknown'),
      description: json['description'] ?? '',
      management: json['management'] ?? '',
      source: json['source'] ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
        'drug1': drug1,
        'drug2': drug2,
        'severity': severity.name,
        'description': description,
        'management': management,
        'source': source,
      };
}

/// Interaction severity enum
enum InteractionSeverity {
  contraindicated,
  severe,
  moderate,
  mild,
  unknown;

  static InteractionSeverity fromString(String value) {
    switch (value.toLowerCase()) {
      case 'contraindicated':
        return InteractionSeverity.contraindicated;
      case 'severe':
        return InteractionSeverity.severe;
      case 'moderate':
        return InteractionSeverity.moderate;
      case 'mild':
        return InteractionSeverity.mild;
      default:
        return InteractionSeverity.unknown;
    }
  }

  String get displayName {
    switch (this) {
      case InteractionSeverity.contraindicated:
        return 'CONTRAINDICATED';
      case InteractionSeverity.severe:
        return 'SEVERE';
      case InteractionSeverity.moderate:
        return 'MODERATE';
      case InteractionSeverity.mild:
        return 'MILD';
      case InteractionSeverity.unknown:
        return 'UNKNOWN';
    }
  }

  int get colorValue {
    switch (this) {
      case InteractionSeverity.contraindicated:
        return 0xFFDC2626;
      case InteractionSeverity.severe:
        return 0xFFEA580C;
      case InteractionSeverity.moderate:
        return 0xFFD97706;
      case InteractionSeverity.mild:
        return 0xFF65A30D;
      case InteractionSeverity.unknown:
        return 0xFF6B7280;
    }
  }
}
