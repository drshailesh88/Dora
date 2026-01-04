import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../theme.dart';
import '../services/api_client.dart';
import '../models/medical_answer.dart';
import '../widgets/answer_card.dart';
import '../widgets/query_input.dart';

/// Provider for query state
final queryLoadingProvider = StateProvider<bool>((ref) => false);
final queryAnswersProvider = StateProvider<List<MedicalAnswer>>((ref) => []);

class QueryScreen extends ConsumerStatefulWidget {
  const QueryScreen({super.key});

  @override
  ConsumerState<QueryScreen> createState() => _QueryScreenState();
}

class _QueryScreenState extends ConsumerState<QueryScreen> {
  final ScrollController _scrollController = ScrollController();

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _handleQuery(String question) async {
    if (question.trim().isEmpty) return;

    ref.read(queryLoadingProvider.notifier).state = true;

    final client = ref.read(apiClientProvider);
    final answer = await client.query(question: question);

    ref.read(queryLoadingProvider.notifier).state = false;

    if (answer != null) {
      ref.read(queryAnswersProvider.notifier).update((state) => [...state, answer]);

      // Scroll to bottom
      Future.delayed(const Duration(milliseconds: 100), () {
        if (_scrollController.hasClients) {
          _scrollController.animateTo(
            _scrollController.position.maxScrollExtent,
            duration: const Duration(milliseconds: 300),
            curve: Curves.easeOut,
          );
        }
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final isLoading = ref.watch(queryLoadingProvider);
    final answers = ref.watch(queryAnswersProvider);

    return Scaffold(
      backgroundColor: DoraColors.bgSecondary,
      appBar: AppBar(
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: DoraColors.primary,
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(
                Icons.local_hospital,
                size: 18,
                color: DoraColors.textInverse,
              ),
            ),
            const SizedBox(width: 8),
            const Text('Dora'),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              ref.read(queryAnswersProvider.notifier).state = [];
            },
          ),
        ],
      ),
      body: Column(
        children: [
          // Answers list
          Expanded(
            child: answers.isEmpty
                ? _buildEmptyState()
                : ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.all(16),
                    itemCount: answers.length + (isLoading ? 1 : 0),
                    itemBuilder: (context, index) {
                      if (index == answers.length && isLoading) {
                        return _buildLoadingIndicator();
                      }
                      return Padding(
                        padding: const EdgeInsets.only(bottom: 16),
                        child: AnswerCard(answer: answers[index]),
                      );
                    },
                  ),
          ),

          // Query input
          QueryInput(
            onSubmit: _handleQuery,
            isLoading: isLoading,
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.local_hospital,
              size: 64,
              color: DoraColors.primary.withOpacity(0.5),
            ),
            const SizedBox(height: 24),
            Text(
              'Welcome to Dora',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            Text(
              'Ask any medical question and get evidence-based answers with citations.',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: DoraColors.textSecondary,
                  ),
            ),
            const SizedBox(height: 32),
            _buildExampleQuestions(),
          ],
        ),
      ),
    );
  }

  Widget _buildExampleQuestions() {
    final examples = [
      'What is the first-line treatment for type 2 diabetes?',
      'How to manage hypertensive crisis?',
      'Differential diagnosis for chest pain',
    ];

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      alignment: WrapAlignment.center,
      children: examples.map((q) => _buildExampleChip(q)).toList(),
    );
  }

  Widget _buildExampleChip(String question) {
    return InkWell(
      onTap: () => _handleQuery(question),
      borderRadius: BorderRadius.circular(20),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: DoraColors.primary.withOpacity(0.1),
          borderRadius: BorderRadius.circular(20),
        ),
        child: Text(
          question,
          style: const TextStyle(
            fontSize: 13,
            color: DoraColors.primary,
          ),
        ),
      ),
    );
  }

  Widget _buildLoadingIndicator() {
    return Container(
      padding: const EdgeInsets.all(24),
      child: const Center(
        child: Column(
          children: [
            SizedBox(
              width: 24,
              height: 24,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                valueColor: AlwaysStoppedAnimation(DoraColors.primary),
              ),
            ),
            SizedBox(height: 12),
            Text(
              'Searching knowledge base...',
              style: TextStyle(
                color: DoraColors.textSecondary,
                fontSize: 14,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
