/// Medical answer model
class MedicalAnswer {
  final String question;
  final String answer;
  final String confidence;
  final List<Citation> citations;
  final List<String> relatedQueries;
  final List<String> warnings;
  final bool patientContextUsed;
  final String modelUsed;
  final int latencyMs;
  final DateTime generatedAt;

  MedicalAnswer({
    required this.question,
    required this.answer,
    required this.confidence,
    required this.citations,
    this.relatedQueries = const [],
    this.warnings = const [],
    this.patientContextUsed = false,
    this.modelUsed = '',
    this.latencyMs = 0,
    DateTime? generatedAt,
  }) : generatedAt = generatedAt ?? DateTime.now();

  factory MedicalAnswer.fromJson(Map<String, dynamic> json) {
    return MedicalAnswer(
      question: json['question'] ?? '',
      answer: json['answer'] ?? '',
      confidence: json['confidence'] ?? 'unknown',
      citations: (json['citations'] as List<dynamic>?)
              ?.map((c) => Citation.fromJson(c))
              .toList() ??
          [],
      relatedQueries: (json['related_queries'] as List<dynamic>?)
              ?.map((q) => q.toString())
              .toList() ??
          [],
      warnings: (json['warnings'] as List<dynamic>?)
              ?.map((w) => w.toString())
              .toList() ??
          [],
      patientContextUsed: json['patient_context_used'] ?? false,
      modelUsed: json['model_used'] ?? '',
      latencyMs: json['latency_ms'] ?? 0,
      generatedAt: json['generated_at'] != null
          ? DateTime.parse(json['generated_at'])
          : DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() => {
        'question': question,
        'answer': answer,
        'confidence': confidence,
        'citations': citations.map((c) => c.toJson()).toList(),
        'related_queries': relatedQueries,
        'warnings': warnings,
        'patient_context_used': patientContextUsed,
        'model_used': modelUsed,
        'latency_ms': latencyMs,
        'generated_at': generatedAt.toIso8601String(),
      };

  /// Get confidence level as enum-like value
  ConfidenceLevel get confidenceLevel {
    switch (confidence.toLowerCase()) {
      case 'high':
        return ConfidenceLevel.high;
      case 'medium':
        return ConfidenceLevel.medium;
      case 'low':
        return ConfidenceLevel.low;
      default:
        return ConfidenceLevel.unknown;
    }
  }
}

/// Citation model
class Citation {
  final String title;
  final String source;
  final String? url;
  final int? page;
  final String? section;
  final double relevanceScore;

  Citation({
    required this.title,
    required this.source,
    this.url,
    this.page,
    this.section,
    this.relevanceScore = 0.0,
  });

  factory Citation.fromJson(Map<String, dynamic> json) {
    return Citation(
      title: json['title'] ?? '',
      source: json['source'] ?? '',
      url: json['url'],
      page: json['page'],
      section: json['section'],
      relevanceScore: (json['relevance_score'] ?? 0.0).toDouble(),
    );
  }

  Map<String, dynamic> toJson() => {
        'title': title,
        'source': source,
        'url': url,
        'page': page,
        'section': section,
        'relevance_score': relevanceScore,
      };
}

/// Confidence level enum
enum ConfidenceLevel {
  high,
  medium,
  low,
  unknown,
}

extension ConfidenceLevelExtension on ConfidenceLevel {
  String get displayName {
    switch (this) {
      case ConfidenceLevel.high:
        return 'High';
      case ConfidenceLevel.medium:
        return 'Medium';
      case ConfidenceLevel.low:
        return 'Low';
      case ConfidenceLevel.unknown:
        return 'Unknown';
    }
  }
}
